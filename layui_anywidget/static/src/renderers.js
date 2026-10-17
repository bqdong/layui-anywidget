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
  input.setAttribute("id", api.uid);
  holder.appendChild(input);

  const emit = (value, eventName, raw) => {
    if (node.model) session.setValue(node.model, value);
    if (node.updates) {
      const key = node.updates[eventName];
      if (key) session.setValue(key, value);
    }
    session.emit((node.events && node.events[eventName]) || eventName, node, value, raw);
  };

  layui.laydate.render({
    elem: input,
    type: props.type || "date",
    range: props.range || false,
    format: props.format || undefined,
    value: current ?? props.value ?? undefined,
    min: props.min ?? undefined,
    max: props.max ?? undefined,
    theme: props.theme,
    trigger: props.trigger || "click",
    position: props.position,
    done(value, date, endDate) {
      emit(value, "done", { value, date, endDate });
      session.flush();
    },
    change(value) {
      emit(value, "change", { value });
    },
  });

  return {
    el: holder,
    update(value) {
      if (value === undefined || value === null) return;
      const laydate = layui.laydate;
      const inst = laydate.getInst?.(input);
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
  // Tab bodies use layui's HTML-string mode; nested widgets are rendered to
  // markup once, so tab content is static in 0.1.
  const body = items.map((item, index) => {
    const container = document.createElement("div");
    if (api.renderChildren) container.appendChild(api.renderChildren(item.children));
    return { id: item.id || `tab${index + 1}`, content: container.innerHTML };
  });
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

// --- progress -------------------------------------------------------------

function renderProgress(api) {
  const { node, session, layui } = api;
  const props = { ...(node.props || {}) };
  const holder = document.createElement("div");
  holder.className = "layui-progress";
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
  const { node, session, layui } = api;
  const props = { ...(node.props || {}) };
  const holder = document.createElement("div");
  holder.className = "layui-collapse";
  if (props.accordion) holder.setAttribute("lay-accordion", "");

  for (const item of node.children || []) {
    if (!item || item.type !== "collapse-item") continue;
    const itemEl = document.createElement("div");
    itemEl.className = "layui-colla-item";
    const titleEl = document.createElement("h2");
    titleEl.className = "layui-colla-title";
    titleEl.textContent = item.props?.title || "";
    const contentEl = document.createElement("div");
    contentEl.className = "layui-colla-content" + (item.props?.open ? " layui-show" : "");
    const body = api.renderChildren ? api.renderChildren(item.children) : null;
    if (body) contentEl.appendChild(body);
    itemEl.appendChild(titleEl);
    itemEl.appendChild(contentEl);
    holder.appendChild(itemEl);
  }

  layui.collapse.render({ elem: layui.$(holder) });
  layui.element.render("collapse", layui.$(holder));
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
  });

  layui.element.on(`carousel(${api.filter})`, () => {});
  instance.on?.("change", (data) => {
    if (node.model) session.setValue(node.model, data.index);
    session.emit((node.events && node.events.change) || "change", node, data.index, plainData(data));
  });

  return { el: holder };
}

// --- laypage --------------------------------------------------------------

function renderLaypage(api) {
  const { node, session, layui } = api;
  const props = { ...(node.props || {}) };
  const holder = document.createElement("div");
  const curr = node.bind?.curr ? session.state[node.bind.curr] : props.curr ?? 1;
  const instance = layui.laypage.render({
    elem: holder,
    count: props.count ?? props.total ?? 0,
    limit: props.limit ?? 10,
    limits: props.limits,
    curr: curr ?? 1,
    layout: props.layout || ["prev", "page", "next", "skip", "count", "limit"],
    jump(obj, first) {
      if (first) return;
      const key = node.updates?.change || node.updates?.page;
      if (key) session.setValue(key, obj.curr);
      session.emit((node.events && node.events.change) || "change", node, obj.curr, plainData(obj));
    },
  });
  return {
    el: holder,
    update(value) {
      instance?.config && (instance.config.curr = value);
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
  progress: renderProgress,
  collapse: renderCollapse,
  menu: renderMenu,
  breadcrumb: renderBreadcrumb,
  carousel: renderCarousel,
  laypage: renderLaypage,
};
