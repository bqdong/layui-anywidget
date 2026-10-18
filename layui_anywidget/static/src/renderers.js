// Component renderers for non-form layui components.
//
// Each renderer receives an `api` object from the bridge and returns
// `{ el, update?, destroy? }`. Conventions follow the bridge:
//   - `add(el)` registers an element for teardown,
//   - `session.setValue(key, value)` for throttled value writes,
//   - `session.emit(event, node, value, raw)` for interaction events.
//
// This file is concatenated into static/layui-bridge.js by
// scripts/build-bridge.mjs; it is not a standalone module.

// --- shared helpers -------------------------------------------------------

function plainData(value) {
  return jsonSafe(value ?? null);
}

// layui writes bookkeeping fields (LAY_NUM, LAY_INDEX, ...) into the row
// objects it renders, so it must never see the live state array.
function cloneRows(rows) {
  if (!Array.isArray(rows)) return [];
  try {
    return structuredClone(rows);
  } catch {
    return JSON.parse(JSON.stringify(rows));
  }
}

function rowPayload(data) {
  if (!data || typeof data !== "object") return null;
  return {
    data: plainData(data.data ?? data),
    index: data.index ?? null,
    event: data.event ?? null,
  };
}

// --- slider ---------------------------------------------------------------

function renderSlider(api) {
  const { node, session, layui } = api;
  const props = { ...(node.props || {}) };
  const holder = document.createElement("div");
  const current = node.model ? session.state[node.model] : undefined;
  const initial = current !== undefined ? current : props.value ?? props.min_value ?? 0;

  const commit = (value, eventName) => {
    if (node.model) session.setValue(node.model, value);
    if (node.updates) {
      const key = node.updates[eventName] || node.updates.change || null;
      if (key) session.setValue(key, value);
    }
    const renamed = node.events && (node.events[eventName] || node.events.change);
    session.emit(renamed || eventName, node, value, { value });
  };

  const instance = layui.slider.render({
    elem: holder,
    min: props.min_value ?? 0,
    max: props.max_value ?? 100,
    step: props.step ?? 1,
    value: initial,
    range: Boolean(props.range),
    type: props.vertical ? "vertical" : "default",
    showstep: Boolean(props.show_step),
    tips: props.tips !== false,
    tipsAlways: Boolean(props.tips_always),
    input: Boolean(props.input),
    height: props.height ?? 200,
    disabled: Boolean(props.disabled),
    theme: props.theme || undefined,
    change(value) {
      commit(value, "change");
    },
    done(value) {
      commit(value, "done");
      session.flush();
    },
  });

  return {
    el: holder,
    update(value) {
      // layui re-fires change/done when the value is set programmatically.
      session.applyFromHost(() => instance?.setValue?.(value ?? props.min_value ?? 0));
    },
  };
}

// --- colorpicker ----------------------------------------------------------

function renderColorPicker(api) {
  const { node, session, layui } = api;
  const props = { ...(node.props || {}) };
  const holder = document.createElement("div");
  holder.className = "law-inline";
  const current = node.model ? session.state[node.model] : undefined;

  const instance = layui.colorpicker.render({
    elem: holder,
    color: current ?? props.color ?? "",
    format: props.format || "hex",
    alpha: Boolean(props.alpha),
    predefine: Boolean(props.predefine),
    colors: props.colors,
    size: props.size || undefined,
    change(value) {
      if (node.model) session.setValue(node.model, value);
      session.emit((node.events && node.events.change) || "change", node, value, { value });
    },
    done(value) {
      if (node.model) session.setValue(node.model, value);
      session.flush();
      session.emit((node.events && node.events.done) || "done", node, value, { value });
    },
  });

  return {
    el: holder,
    update(value) {
      // Colorpicker has no public setValue; re-render with the new color.
      if (value === undefined || value === null || value === current) return;
      holder.innerHTML = "";
      session.applyFromHost(() => layui.colorpicker.render({
        elem: holder,
        color: value,
        format: props.format || "hex",
        alpha: Boolean(props.alpha),
        predefine: Boolean(props.predefine),
      }));
    },
    destroy() {
      // `instance` is the component wrapper; removing the trigger element
      // also removes an open panel when layui's outside-click handler fires.
      holder.innerHTML = "";
    },
  };
}

// --- datepicker -----------------------------------------------------------

function renderDatePicker(api) {
  const { node, session, layui } = api;
  const props = { ...(node.props || {}) };
  const holder = document.createElement("div");
  holder.className = "law-inline";
  const current = node.model ? session.state[node.model] : undefined;
  const input = document.createElement("input");
  input.className = "layui-input";
  // layui identifies instances by this id; two datepickers in one widget
  // would otherwise share `api.uid` and look up the wrong instance.
  const dateId = `${api.uid}-${node.id || "date"}`;
  input.setAttribute("id", dateId);
  holder.appendChild(input);

  const emit = (value, eventName, raw) => {
    if (node.model) session.setValue(node.model, value);
    if (node.updates) {
      const key = node.updates[eventName];
      if (key) session.setValue(key, value);
    }
    session.emit((node.events && node.events[eventName]) || eventName, node, value, raw);
  };

  const options = {
    elem: input,
    type: props.type || "date",
    range: props.range || false,
    trigger: props.trigger || "click",
    done(value, date, endDate) {
      emit(value, "done", { value, date, endDate });
      session.flush();
    },
    change(value) {
      emit(value, "change", { value });
    },
  };
  // `laydate` merges its options with jQuery.extend, so an explicit
  // `undefined` overwrites the default instead of leaving it in place. It
  // defaults `min`/`max` to 1900/2099; passing `min: undefined` makes every
  // day except today unselectable.
  for (const key of ["format", "value", "min", "max", "theme", "position"]) {
    const value = key === "value" ? current ?? props.value : props[key];
    if (value !== undefined && value !== null && value !== "") options[key] = value;
  }
  layui.laydate.render(options);

  return {
    el: holder,
    update(value) {
      if (value === undefined || value === null) return;
      const laydate = layui.laydate;
      const inst = laydate.getInst?.(dateId);
      if (inst) {
        session.applyFromHost(() => inst.setValue(value).done().remove?.());
      } else {
        input.value = value;
      }
    },
  };
}

// --- table ----------------------------------------------------------------

function renderTable(api) {
  const { node, session, layui } = api;
  const props = { ...(node.props || {}) };
  const holder = document.createElement("div");
  const dataKey = node.bind?.data;
  const rows = cloneRows(dataKey ? session.state[dataKey] : props.data);
  const filter = api.filter;

  const tableId = `${api.uid}-${node.id || "table"}`;
  const tableFilter = api.filter;
  holder.setAttribute("lay-filter", tableFilter);
  let instance = null;

  const show = (tableData) => {
    instance = layui.table.render({
      elem: holder,
      id: tableId,
      cols: props.cols,
      data: tableData,
      page: props.page || false,
      limit: props.limit || 10,
      limits: props.limits,
      height: props.height || undefined,
      skin: props.skin,
      size: props.size,
      even: props.even,
      text: props.text,
      totalRow: props.total_row,
      defaultToolbar: props.default_toolbar,
      toolbar: props.toolbar,
      title: props.title,
      done(res, curr, count) {
        // layui renders its checkboxes with `form.render` scoped to the table
        // view, but that lookup runs from `document`. Inside a shadow root it
        // finds nothing, leaving the native checkboxes undecorated.
        // layui inserts the view as a *sibling* after the elem we passed.
        const view =
          holder.querySelector(".layui-table-view") ??
          (holder.nextElementSibling?.classList.contains("layui-table-view")
            ? holder.nextElementSibling
            : null);
        if (!view) return;
        // `done` re-fires after sort, page and data reloads, and layui has
        // re-created the raw checkboxes by then, so re-decorate every time.
        // No filter is passed: a filter turns into a document-rooted
        // `$('.layui-form[lay-filter=...]')` lookup that cannot see a shadow
        // root, so the document-wide pass has to do the work while the view
        // is temporarily attached to document.body.
        withDocumentRuntime(view, () => {
          // The filter must be re-read here; layui re-creates the view after
          // a sort and the new node carries a fresh filter value.
          const filter = view.getAttribute("lay-filter");
          if (filter) layui.form.render("checkbox", filter);
          else layui.form.render("checkbox");
        });
        registerTableEvents(layui, tableId, filter, node, session);
        if (node.events?.done) session.emit(node.events.done, node, { total: count }, { curr, count });
      },
    });
  };

  return {
    el: holder,
    // layui reads the holder's layout while rendering; run once attached.
    afterMount() {
      show(rows);
    },
    update(value) {
      if (!Array.isArray(value)) return;
      if (instance) instance.reloadData({ data: cloneRows(value) });
      else show(cloneRows(value));
    },
    destroy() {
      for (const eventName of TABLE_EVENTS) {
        layui.off(`${eventName}(${filter})`, "table");
      }
    },
  };
}

const TABLE_EVENTS = ["tool", "toolbar", "checkbox", "radio", "row", "rowDouble", "sort", "edit"];

function registerTableEvents(layui, tableId, filter, node, session) {
  const key = `${tableId}:${filter}`;
  session.__lawTableKeys = session.__lawTableKeys || new Set();
  if (session.__lawTableKeys.has(key)) return;
  session.__lawTableKeys.add(key);

  for (const eventName of TABLE_EVENTS) {
    layui.table.on(`${eventName}(${filter})`, (obj) => {
      const renamed = node.events && (node.events[eventName] || node.events.tool);
      const value =
        eventName === "tool"
          ? { event: obj.event, data: plainData(obj.data), index: obj.index }
          : eventName === "checkbox"
            ? { checked: obj.checked, type: obj.type, data: plainData(obj.data), index: obj.index }
            : rowPayload(obj);
      if (eventName === "checkbox" && node.updates) {
        const updateKey = node.updates.checkbox || node.updates.selection;
        if (updateKey) {
          const selected = layui.table.checkStatus(tableId).data || [];
          session.setValue(updateKey, plainData(selected));
        }
      }
      session.emit(renamed || eventName, node, value, rowPayload(obj));
    });
  }
}

// --- tabs -----------------------------------------------------------------

function renderTabs(api) {
  const { node, session, layui } = api;
  const props = { ...(node.props || {}) };
  const items = (node.children || []).filter((child) => child && child.type === "tab");
  const current = node.model ? session.state[node.model] : undefined;
  const header = items.map((item, index) => ({
    title: item.props?.title ?? `Tab ${index + 1}`,
    id: item.id || `tab${index + 1}`,
  }));
  // Render the tab shells first, then mount the real child nodes into each
  // body. Passing HTML strings would serialize nested controls and detach
  // them from the session (no layui decoration, no state binding).
  const body = items.map((item, index) => ({
    id: item.id || `tab${index + 1}`,
    content: "",
  }));
  const holder = document.createElement("div");
  const activeIndex = Math.max(0, header.findIndex((item) => item.id === current));

  const instance = layui.tabs.render({
    elem: holder,
    header,
    body,
    index: activeIndex,
    id: api.filter,
    trigger: props.trigger || "click",
    headerMode: props.header_mode || "auto",
    closable: Boolean(props.closable),
  });

  items.forEach((item, index) => {
    const id = item.id || `tab${index + 1}`;
    const panel = holder.querySelector(`.layui-tabs-item[lay-id="${id}"]`);
    if (!panel || !api.renderChildren) return;
    panel.appendChild(api.renderChildren(item.children));
  });

  // layui fires afterChange(<tabs id>) on its global event bus. The payload
  // is the tabs data() snapshot: { index, layid, ... }.
  const onAfterChange = (data) => {
    const index = Number.isInteger(data?.index) ? data.index : 0;
    const id =
      data?.thisHeaderItem?.attr?.("lay-id") ?? header[index]?.id ?? null;
    if (node.model) session.setValue(node.model, id);
    session.emit((node.events && node.events.change) || "change", node, id, { index, id });
  };
  layui.onevent("tabs", `afterChange(${api.filter})`, onAfterChange);

  return {
    el: holder,
    update(value) {
      const index = header.findIndex((item) => item.id === value);
      if (index >= 0) layui.tabs.change(api.filter, index, true);
    },
    destroy() {
      layui.off(`afterChange(${api.filter})`, "tabs");
    },
  };
}

// --- rate -----------------------------------------------------------------

function renderRate(api) {
  const { node, session, layui } = api;
  const props = { ...(node.props || {}) };
  const holder = document.createElement("div");
  const current = node.model ? session.state[node.model] : undefined;

  const instance = layui.rate.render({
    elem: holder,
    length: props.max_value ?? props.length ?? 5,
    value: current ?? props.value ?? 0,
    half: Boolean(props.half),
    text: Boolean(props.text),
    readonly: Boolean(props.readonly),
    theme: props.theme,
    choose(value) {
      if (node.model) session.setValue(node.model, value);
      session.flush();
      session.emit((node.events && node.events.choose) || "choose", node, value, { value });
    },
  });

  return {
    el: holder,
    update(value) {
      session.applyFromHost(() => instance?.setvalue?.(value ?? 0));
    },
  };
}

// --- dropdown -------------------------------------------------------------

function renderDropdown(api) {
  const { node, session, layui } = api;
  const props = { ...(node.props || {}) };
  const holder = document.createElement("span");
  holder.className = "law-inline";
  let trigger = api.renderNode ? api.renderNode((node.children || [])[0]) : null;
  if (!trigger) {
    trigger = document.createElement("span");
    trigger.className = "layui-btn layui-btn-primary";
    trigger.textContent = props.label || "菜单";
  }
  holder.appendChild(trigger);

  const instance = layui.dropdown.render({
    elem: trigger,
    data: props.data || [],
    trigger: props.trigger || "click",
    show: Boolean(props.show),
    closeOnClick: props.close_on_click !== false,
    className: props.class_name,
    style: props.style,
    click(data) {
      const id = data && (data.id ?? data.title);
      if (node.updates) {
        const key = node.updates.click || node.updates.select;
        if (key) session.setValue(key, plainData(data));
      }
      session.emit((node.events && node.events.click) || "click", node, id, plainData(data));
    },
  });

  return { el: holder, destroy() { instance?.close?.(); } };
}

// --- layer ----------------------------------------------------------------

// Turn the `capture` node into real DOM for layer's captured-element path.
// The wrapper is hidden (as the docs' capture element is): layer measures the
// content, then wraps it and shows it. `renderNode` is a mountNode bound to
// the layer's own node, so nested form controls still decorate/emit inside
// the popup.
function buildCapture(api, captureNode) {
  const holder = document.createElement("div");
  holder.setAttribute("data-law-capture", "");
  if (api.renderNode) {
    const rendered = api.renderNode(captureNode);
    if (rendered) holder.appendChild(rendered);
  }
  // layer shows captured content and restores the inline `display` on close;
  // start hidden so the element only appears inside the popup.
  holder.style.display = "none";
  return holder;
}

// `layer` is a JS-only API: the node renders a trigger button that opens the
// popup. layer appends the popup to document.body, so the document-level
// "core" stylesheet (reset-free layui CSS) covers it in both hosts.
//
// A "stage" is one popup description. The node props are the first stage;
// `next` / `next_cancel` (and the `next` button action) open follow-up stages,
// which is how the docs chain examples (icon tour, molv -> lan, confirm ->
// msg).
function renderLayer(api) {
  const { node, session, layui } = api;
  const props = { ...(node.props || {}) };
  const layer = layui.layer;
  const holder = document.createElement("span");
  holder.className = "law-inline";
  let trigger = api.renderNode ? api.renderNode((node.children || [])[0]) : null;
  if (!trigger) {
    trigger = document.createElement("span");
    trigger.className = "layui-btn layui-btn-primary";
    trigger.textContent = props.trigger || "打开";
  }
  holder.appendChild(trigger);
  // Layers live in document.body; remember them so teardown can close them.
  const indexes = new Set();

  const stageOf = (raw) => ({ ...raw, options: { ...(raw.options || {}) } });
  const emit = (stage, event, value, extra) => {
    const map = (stage && stage.events) || node.events || {};
    session.emit(map[event] || event, node, value, extra || {});
  };
  // Esc closes the newest layer that opted in (the docs' multi-window
  // example). One document listener serves every layer node.
  const escStack = (layer.__lawEscStack = layer.__lawEscStack || []);
  const unregisterEsc = (index) => {
    const position = escStack.indexOf(index);
    if (position !== -1) escStack.splice(position, 1);
  };
  const registerEsc = (stage, index) => {
    if (!stage.esc_close || index === undefined) return;
    unregisterEsc(index);
    escStack.unshift(index);
    if (layer.__lawEscBound) return;
    layer.__lawEscBound = true;
    document.addEventListener("keyup", (event) => {
      if (event.key !== "Escape" || !escStack.length) return;
      layer.close(escStack.shift());
    });
  };
  // layui options are camelCase (`shadeClose`, `btnAlign`, `tipsMore`); accept
  // the Python-friendly snake_case spellings and translate them.
  const SNAKE_OPTIONS = {
    shade_close: "shadeClose",
    btn_align: "btnAlign",
    tips_more: "tipsMore",
    close_btn: "closeBtn",
    is_out_anim: "isOutAnim",
    max_width: "maxWidth",
    move_type: "moveType",
    form_type: "formType",
    btn_async: "btnAsync",
    btns: "btn",
  };

  const openNext = (stage, key) => {
    const raw = stage[key];
    if (!raw) return;
    const next = Array.isArray(raw) ? raw[0] : raw;
    openStage(stageOf(next));
  };

  // Submit buttons inside popup HTML (the docs' layer + form example) cannot
  // run the page's own handler, so collect the fields and report them.
  const bindForm = (stage, layero) => {
    layero.on("click", "[lay-submit]", (event) => {
      event.preventDefault();
      const values = {};
      layero.find("input,select,textarea").each(function () {
        if (!this.name) return;
        if (this.type === "checkbox") {
          values[this.name] = this.checked ? (this.value === "on" ? true : this.value) : false;
        } else if (this.type === "radio") {
          if (this.checked) values[this.name] = this.value;
        } else {
          values[this.name] = this.value;
        }
      });
      emit(stage, "submit", values, { values });
      session.flush();
    });
  };

  // The docs' lock-screen example checks a password and closes only on a
  // match: `unlock` holds the expected value; elements marked
  // `data-law-unlock` (or Enter in the input) try it.
  const bindUnlock = (stage, layero, index) => {
    const input = layero.find("input")[0];
    const pass = String(stage.unlock);
    const attempt = () => {
      if (String(input && input.value).trim() === pass) {
        layer.close(index);
        emit(stage, "unlock", true);
        session.flush();
      } else {
        layer.msg("锁屏密码输入有误", { offset: "16px", anim: "slideDown" });
        input?.focus();
      }
    };
    layero.find("[data-law-unlock]").on("click", attempt);
    layui.$(input).on("keyup", (event) => {
      if (event.key === "Enter" || event.keyCode === 13) attempt();
    });
  };

  const optionsFor = (stage, ctx = {}) => {
    const options = { ...stage.options };
    for (const [snake, camel] of Object.entries(SNAKE_OPTIONS)) {
      if (snake in options) {
        options[camel] = options[snake];
        delete options[snake];
      }
    }
    // `auto_close` is not a layer option: every branch closes by index.
    const autoClose = Number(options.auto_close ?? stage.auto_close ?? 0);
    delete options.auto_close;
    // Non-enumerable so layer's option merge never sees or stores it.
    Object.defineProperty(options, "__autoClose", { value: autoClose, enumerable: false });
    if (stage.title !== undefined) options.title = stage.title;
    if (stage.btns) options.btn = [...stage.btns];
    if (stage.btn_async) options.btnAsync = true;
    // The docs' examples pass JS callbacks (`success`, `end`, `btn1`, ...)
    // that cannot cross the JSON boundary; the flags below generate the
    // common ones and forward their results as events instead.
    const end = options.end;
    // layer calls `end()` unbound, so the index has to come from the closure.
    options.end = () => {
      unregisterEsc(options.__index);
      indexes.delete(options.__index);
      // A button/confirm callback already reported the outcome; a bare
      // `close` would overwrite it in the host.
      if (!ctx.actionTaken) emit(stage, "close", null, { reason: "close" });
      if (typeof end === "function") end();
    };
    const success = options.success;
    options.success = (layero, index) => {
      options.__index = index;
      indexes.add(index);
      registerEsc(stage, index);
      // Content may carry a `.layui-form` (e.g. the login page example); the
      // form lives in document.body, so a document-wide render decorates it.
      if (typeof stage.content === "string" && stage.content.includes("layui-form")) {
        layui.form.render();
        bindForm(stage, layero);
      }
      if (stage.full) layer.full(index);
      if (stage.set_top) layer.setTop(layero);
      if (stage.unlock) bindUnlock(stage, layero, index);
      if (typeof success === "function") success(layero, index);
    };
    return options;
  };

  // `btnAsync`: the docs simulate a request inside the button callback; here
  // the promise resolves after `btn_async` milliseconds (1000 by default).
  const asyncify = (stage, fn) => {
    if (!stage.btn_async) return fn;
    const delay = typeof stage.btn_async === "number" ? stage.btn_async : 1000;
    return (index, layero, that) => {
      that.loading(true);
      return new Promise((resolve) => setTimeout(() => resolve(fn?.(index, layero, that)), delay));
    };
  };

  // Turn the docs' callback style buttons into events: every `btn` entry gets
  // a handler that reports its index and label, then performs its action.
  const attachButtons = (stage, options, ctx = {}) => {
    const btns = stage.btns;
    if (!btns) return;
    const kind = String(stage.kind || "dialog").toLowerCase();
    btns.forEach((label, index) => {
      const key = index === 0 ? "yes" : `btn${index + 1}`;
      options[key] = asyncify(stage, (buttonIndex) => {
        ctx.actionTaken = true;
        const payload = { index: buttonIndex ?? index, text: label };
        emit(stage, "button", payload, { button: payload });
        // In a confirm box the first two buttons are 确定/取消: report the
        // same outcome as layer.confirm's own callbacks, then follow-ups.
        if (kind === "confirm" && index === 0) {
          emit(stage, "confirm", true);
          openNext(stage, "next");
        } else if (kind === "confirm" && index === 1) {
          emit(stage, "cancel", false);
          openNext(stage, "next_cancel");
        }
        session.flush();
        const action = (stage.actions || [])[index];
        if (action === "close_all") layer.closeAll();
        else if (action === "reopen") queueMicrotask(() => openStage(stage));
        else if (action === "next") queueMicrotask(() => openNext(stage, "next"));
      });
    });
  };

  const openStage = (stage) => {
    const kind = String(stage.kind || "dialog").toLowerCase();
    const content = stage.content ?? "";
    // Shared with `optionsFor`'s `end`: suppresses a redundant close event.
    const ctx = { actionTaken: false };
    const done = (event, value, extra) => {
      ctx.actionTaken = true;
      emit(stage, event, value, extra);
      session.flush();
    };

    if (kind === "msg") {
      // No icon by default: that is layui's dark toast, as in the docs.
      const options = optionsFor(stage, ctx);
      attachButtons(stage, options, ctx);
      indexes.add(layer.msg(content, options));
      return;
    }
    if (kind === "confirm") {
      // `layer.confirm(content, opts, yes, cancel)` layers `opts` last, so
      // custom buttons (docs' "确定/关闭") override the default callbacks.
      const options = optionsFor(stage, ctx);
      attachButtons(stage, options, ctx);
      indexes.add(
        layer.confirm(
          content,
          options,
          (index) => {
            layer.close(index);
            done("confirm", true);
            openNext(stage, "next");
          },
          (index) => {
            layer.close(index);
            done("cancel", false);
            openNext(stage, "next_cancel");
          },
        ),
      );
      return;
    }
    if (kind === "alert") {
      const options = optionsFor(stage, ctx);
      attachButtons(stage, options, ctx);
      // Countdown alert: rewrite the title every second, as in the docs.
      if (stage.countdown) {
        const openSuccess = options.success;
        options.time = options.time ?? 5000;
        options.success = (layero, index) => {
          let left = Math.ceil(Number(options.time) / 1000);
          const tick = (start) => {
            if (!start) left -= 1;
            layer.title(
              `<span class="layui-font-red">${Math.max(left, 0)}</span> 秒后自动关闭`,
              index,
            );
            if (left > 0) options.__timer = setTimeout(() => tick(false), 1000);
          };
          tick(true);
          openSuccess(layero, index);
        };
        const openEnd = options.end;
        options.end = function () {
          clearTimeout(options.__timer);
          openEnd.apply(this, arguments);
        };
      }
      indexes.add(
        layer.alert(
          content,
          options,
          asyncify(stage, (index) => {
            layer.close(index);
            done("confirm", true);
            openNext(stage, "next");
          }),
        ),
      );
      return;
    }
    if (kind === "load") {
      // A loading layer never closes on its own. `auto_close` (ms) lets the
      // caller schedule it, since Python code cannot run inside the browser.
      const options = optionsFor(stage, ctx);
      const icon = Number(options.icon ?? 0);
      delete options.icon;
      const index = layer.load(icon, options);
      indexes.add(index);
      emit(stage, "open", index, { index });
      session.flush();
      if (options.__autoClose > 0) setTimeout(() => layer.close(index), options.__autoClose);
      return;
    }
    if (kind === "tips") {
      // A tip layer must not survive the widget being torn down.
      indexes.add(layer.tips(content, trigger, optionsFor(stage, ctx)));
      return;
    }
    if (kind === "prompt") {
      const options = optionsFor(stage, ctx);
      // layer.prompt takes only options: the docs pass the prompt text as
      // `title`, so use `content` when no title was given.
      if (options.title === undefined && typeof content === "string" && content) {
        options.title = content;
      }
      // layer.prompt's internal `yes` is merged *before* the caller's options,
      // so leave `yes` alone and only wire the second button.
      options.btn2 = (promptIndex) => {
        layer.close(promptIndex);
        done("cancel", null);
      };
      indexes.add(
        layer.prompt(options, (value, promptIndex) => {
          layer.close(promptIndex);
          done("confirm", value);
          openNext(stage, "next");
        }),
      );
      return;
    }
    if (kind === "photos") {
      const options = optionsFor(stage, ctx);
      options.photos = options.photos || {
        title: stage.photos_title || props.photos_title || "Photos",
        start: 0,
        data: stage.photos || props.photos || [],
      };
      indexes.add(layer.photos(options));
      return;
    }
    if (kind === "tab") {
      const options = optionsFor(stage, ctx);
      if (Array.isArray(stage.tabs)) {
        // Plain JSON tabs (HTML strings): layer.tab renders its own markup.
        options.tab = stage.tabs;
        indexes.add(layer.tab(options));
        emit(stage, "open", null);
        session.flush();
        return;
      }
      // The docs' `layer.tab` writes tab bodies as HTML strings, which would
      // detach interactive controls from the session. Open a page layer with
      // a real `lay.tabs` component mounted inside it instead.
      const tabsNode = stage.content;
      if (tabsNode && typeof tabsNode === "object" && api.renderNode) {
        const panel = document.createElement("div");
        panel.style.padding = "16px";
        panel.style.display = "none";
        const tabsEl = api.renderNode(tabsNode);
        if (tabsEl) {
          panel.appendChild(tabsEl);
          options.title = false;
        }
        // layer's captured-element path only works for elements that are
        // already under document.body, so park the panel there first.
        document.body.appendChild(panel);
        options.content = layui.$(panel);
        const end = options.end;
        options.end = () => {
          end();
          panel.remove();
        };
      } else {
        options.content = "<div></div>";
      }
      indexes.add(layer.open({ type: 1, ...options }));
      emit(stage, "open", null);
      session.flush();
      return;
    }

    // Page / iframe layer. Captured content is built per open: layer unwraps
    // and moves the element on close, so it cannot be reused.
    const options = optionsFor(stage, ctx);
    attachButtons(stage, options, ctx);
    if (stage.capture && api.renderNode) {
      // layer only handles captured elements that sit under document.body;
      // the popup unwraps it on close, and `end` removes the holder again.
      const capture = buildCapture(api, stage.capture);
      document.body.appendChild(capture);
      const end = options.end;
      options.end = () => {
        end();
        capture.remove();
      };
      options.content = layui.$(capture);
    } else {
      options.content = content;
    }
    const type = kind === "iframe" ? 2 : Number(stage.type ?? 1) || 1;
    indexes.add(layer.open({ type, ...options }));
    emit(stage, "open", null);
    session.flush();
  };

  trigger.addEventListener("click", (event) => {
    event.preventDefault?.();
    openStage(stageOf(props));
  });

  return {
    el: holder,
    destroy() {
      for (const index of indexes) {
        try {
          layer.close(index);
        } catch {
          /* the layer may already be closed */
        }
      }
      indexes.clear();
    },
  };
}

// --- progress -------------------------------------------------------------

function renderProgress(api) {
  const { node, session } = api;
  const props = { ...(node.props || {}) };
  const holder = document.createElement("div");
  holder.className = "layui-progress";
  if (props.class_) holder.classList.add(...String(props.class_).split(/\s+/).filter(Boolean));
  applyStyle(holder, node.style);
  const valueKey = node.bind?.value;
  const read = () => {
    const value = valueKey ? session.state[valueKey] : props.value;
    const number = Number(value ?? 0);
    return Math.max(0, Math.min(100, Number.isFinite(number) ? number : 0));
  };
  const paint = () => {
    const percent = `${read()}%`;
    holder.innerHTML = "";
    const bar = document.createElement("div");
    bar.className = "layui-progress-bar";
    bar.style.width = percent;
    if (props.show_percent !== false) {
      const label = document.createElement("span");
      label.className = "layui-progress-text";
      label.textContent = percent;
      bar.appendChild(label);
    }
    holder.appendChild(bar);
  };
  paint();
  return { el: holder, update: paint };
}

// --- collapse -------------------------------------------------------------

function renderCollapse(api) {
  const { node, layui } = api;
  const props = { ...(node.props || {}) };
  const holder = document.createElement("div");
  holder.className = "layui-collapse";
  if (props.accordion) holder.setAttribute("lay-accordion", "");
  if (props["lay-filter"] || node.id) {
    holder.setAttribute("lay-filter", props["lay-filter"] || node.id);
  }

  for (const item of node.children || []) {
    if (!item || item.type !== "collapse-item") continue;
    const itemEl = document.createElement("div");
    itemEl.className = "layui-colla-item";
    const titleEl = document.createElement("h2");
    titleEl.className = "layui-colla-title";
    titleEl.textContent = item.props?.title || "";
    const contentEl = document.createElement("div");
    // layui reads the initial state from the inline `display` value
    // (`"none"` means collapsed) and then drops `layui-show`, so an open
    // item must start with `display: block`.
    contentEl.className = "layui-colla-content";
    contentEl.style.display = item.props?.open ? "block" : "none";
    const body = api.renderChildren ? api.renderChildren(item.children) : null;
    if (body) contentEl.appendChild(body);
    itemEl.appendChild(titleEl);
    itemEl.appendChild(contentEl);
    holder.appendChild(itemEl);
  }

  // layui resolves `elem` through jQuery and its click handler is bound
  // synchronously, so an element argument does not need document scope.
  layui.collapse.render({ elem: layui.$(holder) });
  return { el: holder };
}

// --- menu (nav) -----------------------------------------------------------

function renderMenu(api) {
  const { node, session, layui } = api;
  const props = { ...(node.props || {}) };
  const holder = document.createElement("ul");
  holder.className = "layui-nav";
  const current = node.model ? session.state[node.model] : undefined;

  const renderItems = (parent, items, depth) => {
    for (const item of items || []) {
      const li = document.createElement("li");
      li.className = "layui-nav-item";
      if (item.active || item.id === current || item.id === props.active) {
        li.classList.add("layui-this");
      }
      if (item.id !== undefined) li.setAttribute("data-law-id", String(item.id));
      const link = document.createElement("a");
      link.href = item.href || "javascript:;";
      link.textContent = item.title ?? "";
      li.appendChild(link);
      if (Array.isArray(item.children) && item.children.length) {
        const child = document.createElement("dl");
        child.className = "layui-nav-child";
        renderItems(child, item.children, depth + 1);
        li.appendChild(child);
      }
      li.addEventListener("click", (event) => {
        event.preventDefault();
        if (node.model) session.setValue(node.model, item.id);
        session.emit((node.events && node.events.click) || "click", node, item.id, plainData(item));
      });
      parent.appendChild(li);
    }
  };
  renderItems(holder, props.items || [], 0);
  layui.nav?.render({ elem: layui.$(holder) });
  layui.element.render("nav", layui.$(holder));
  return {
    el: holder,
    update(value) {
      holder.querySelectorAll("li.layui-nav-item").forEach((li) => {
        li.classList.toggle("layui-this", li.getAttribute("data-law-id") === value);
      });
    },
  };
}

// --- breadcrumb -----------------------------------------------------------

function renderBreadcrumb(api) {
  const { node, layui } = api;
  const props = { ...(node.props || {}) };
  const holder = document.createElement("span");
  holder.className = "layui-breadcrumb";
  if (props["lay-separator"]) holder.setAttribute("lay-separator", props["lay-separator"]);
  for (const item of props.items || []) {
    const link = document.createElement("a");
    link.href = item.href || "javascript:;";
    link.textContent = item.title ?? "";
    holder.appendChild(link);
  }
  layui.breadcrumb?.render({ elem: layui.$(holder) });
  layui.element.render("breadcrumb", layui.$(holder));
  return { el: holder };
}

// --- carousel -------------------------------------------------------------

function renderCarousel(api) {
  const { node, session, layui } = api;
  const props = { ...(node.props || {}) };
  const holder = document.createElement("div");
  holder.className = "layui-carousel";
  const inner = document.createElement("div");
  inner.setAttribute("carousel-item", "");
  for (const child of node.children || []) {
    const item = document.createElement("div");
    if (typeof child === "string") {
      item.textContent = child;
    } else if (child && child.type) {
      const body = api.renderNode ? api.renderNode(child) : null;
      if (body) item.appendChild(body);
    }
    inner.appendChild(item);
  }
  holder.appendChild(inner);

  const current = node.model ? session.state[node.model] : undefined;
  const instance = layui.carousel.render({
    elem: holder,
    width: props.width || "100%",
    height: props.height || "280px",
    full: Boolean(props.full),
    arrow: props.arrow || "hover",
    indicator: props.indicator || "inside",
    autoplay: props.autoplay !== false,
    interval: props.interval || 3000,
    anim: props.anim || "",
    trigger: props.trigger || "click",
    index: typeof current === "number" ? current : 0,
    change(data) {
      if (node.model) session.setValue(node.model, data.index);
      session.emit((node.events && node.events.change) || "change", node, data.index, plainData(data));
    },
  });

  return { el: holder };
}

// --- laypage --------------------------------------------------------------

function renderLaypage(api) {
  const { node, session, layui } = api;
  const props = { ...(node.props || {}) };
  const holder = document.createElement("div");
  const read = () => {
    const value = node.bind?.curr ? session.state[node.bind.curr] : props.curr;
    return Number(value) || 1;
  };
  let curr = read();
  let rendered = false;

  const show = (page) => {
    curr = page;
    holder.innerHTML = "";
    layui.laypage.render({
      elem: holder,
      count: props.count ?? props.total ?? 0,
      limit: props.limit ?? 10,
      limits: props.limits,
      curr: page,
      layout: props.layout || ["prev", "page", "next", "skip", "count", "limit"],
      jump(obj, first) {
        if (first) return;
        const key = node.updates?.change || node.updates?.page;
        if (key) session.setValue(key, obj.curr);
        session.emit((node.events && node.events.change) || "change", node, obj.curr, plainData(obj));
      },
    });
    rendered = true;
  };

  return {
    el: holder,
    afterMount() {
      // laypage re-finds its own view with `document.getElementById`, which
      // cannot see nodes inside a shadow root; it therefore binds no click
      // handlers there. Render while the holder is temporarily attached to
      // document.body, then move it back with the handlers in place.
      withDocumentRuntime(holder, () => show(curr));
    },
    update(value) {
      if (!rendered || value === undefined || value === null) return;
      if (Number(value) === curr) return;
      withDocumentRuntime(holder, () => show(Number(value) || 1));
    },
  };
}

const COMPONENT_RENDERERS = {
  slider: renderSlider,
  colorpicker: renderColorPicker,
  datepicker: renderDatePicker,
  table: renderTable,
  tabs: renderTabs,
  rate: renderRate,
  dropdown: renderDropdown,
  layer: renderLayer,
  progress: renderProgress,
  collapse: renderCollapse,
  menu: renderMenu,
  breadcrumb: renderBreadcrumb,
  carousel: renderCarousel,
  laypage: renderLaypage,
};
