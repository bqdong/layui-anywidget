// layui-anywidget bridge.
//
// Python builds a JSON schema tree and a shared state dictionary; this module
// resolves each node to a layui 2.13.9 component and keeps values in sync.
//
// The build step (scripts/build-bridge.mjs) embeds the vendored layui source
// and stylesheets into this file and concatenates static/src/renderers.js, so
// the result is a single self-contained ESM module. anywidget executes `_esm`
// from a Blob URL, where relative imports cannot be resolved.
//
// Host/runtime facts this code relies on:
//   - anywidget renders into the light DOM in Jupyter and into an open shadow
//     root inside <marimo-anywidget>; `el.getRootNode()` tells us which.
//   - layui's popup components (layer, laydate, colorpicker, dropdown) always
//     append to document.body, and the slider drag overlay lives there too, so
//     the document needs component CSS. The notebook's own reset must not be
//     touched, hence the reset-free "core" stylesheet.
//   - layui's form.render(type, filter) looks elements up with
//     document.querySelector when `filter` is a string. Inside a shadow root
//     that silently fails, so we always pass the element itself.

const LAYUI_VERSION = /*__LAYUI_VERSION__*/;
const LAYUI_SOURCE = /*__LAYUI_SOURCE__*/;
const LAYUI_CSS_FULL = /*__LAYUI_CSS_FULL__*/;
const LAYUI_CSS_CORE = /*__LAYUI_CSS_CORE__*/;
// Our own layout/theme rules. Hosts inject `_css` into the document, which
// misses shadow roots (marimo), so the bridge adds the same text to whichever
// scope it renders into.
const WIDGET_CSS = /*__LAYUI_CSS_WIDGET__*/;

// ---------------------------------------------------------------------------
// Assets
// ---------------------------------------------------------------------------

const STYLE_ATTR = "data-layui-anywidget";
const ROOT_CLASS = "law-root";
const MAX_RAW_DEPTH = 5;
const MAX_RAW_ITEMS = 200;

let bridgeStylePromise = null;
let coreStylePromise = null;
let scriptPromise = null;
let eventSequence = 0;

function injectStyle(scope, text, variant) {
  const style = document.createElement("style");
  style.setAttribute(STYLE_ATTR, variant);
  style.textContent = text;
  scope.appendChild(style);
  return style;
}

function loadWidgetStyles(scope) {
  if (scope.querySelector?.(`style[${STYLE_ATTR}="widget"]`)) return;
  injectStyle(scope, WIDGET_CSS, "widget");
}

function loadFullStyles(scope) {
  if (scope === document) {
    if (!bridgeStylePromise) {
      bridgeStylePromise = Promise.resolve(injectStyle(document.head, LAYUI_CSS_FULL, "base"));
    }
    loadWidgetStyles(document.head);
    return bridgeStylePromise;
  }
  if (!scope.__lawBaseStyle) {
    try {
      scope.__lawBaseStyle = injectStyle(scope, LAYUI_CSS_FULL, "base");
    } catch {
      /* a closed root or a non-DOM scope: nothing to do */
    }
  }
  loadWidgetStyles(scope);
  return Promise.resolve();
}

function loadCoreStyles() {
  if (!coreStylePromise) {
    const style = injectStyle(document.head, LAYUI_CSS_CORE, "core");
    style.setAttribute("data-variant", LAYUI_VERSION);
    coreStylePromise = Promise.resolve(style);
  }
  return coreStylePromise;
}

function loadLayui() {
  if (window.layui && window.layui.form) return Promise.resolve(window.layui);
  if (scriptPromise) return scriptPromise;

  scriptPromise = new Promise((resolve, reject) => {
    const script = document.createElement("script");
    script.setAttribute(STYLE_ATTR, "runtime");
    script.text = LAYUI_SOURCE;
    script.onerror = () => reject(new Error("layui script failed to execute"));
    document.head.appendChild(script);

    const started = Date.now();
    const poll = () => {
      if (window.layui && window.layui.form) {
        resolve(window.layui);
      } else if (Date.now() - started > 5000) {
        reject(new Error("layui did not register within 5s"));
      } else {
        setTimeout(poll, 16);
      }
    };
    poll();
  }).catch((error) => {
    scriptPromise = null;
    throw error;
  });

  return scriptPromise;
}

async function ensureRuntime(config, inDocument) {
  // The full stylesheet carries layui's global `body` reset. Only add it to
  // the document when the widget actually renders there (Jupyter's light
  // DOM); in a shadow root the full CSS goes into the root while the document
  // gets just the reset-free core for layui's body-level popups.
  await Promise.all([loadCoreStyles(), inDocument ? loadFullStyles(document) : null]);
  // Widget styles are reset-free and mostly `.law-root`-scoped, but layer
  // skins (`.law-layer-*`) style the body-level popup, so they must also reach
  // the document even when the widget itself lives in a shadow root.
  loadWidgetStyles(document.head);
  const layui = await loadLayui();
  if (config && typeof config === "object" && Object.keys(config).length) {
    layui.config(config);
  }
  return layui;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function setAttr(element, name, value) {
  if (value === null || value === undefined || value === false) return;
  element.setAttribute(name, value === true ? "" : String(value));
}

function applyClass(element, value) {
  if (!value) return;
  const classes = Array.isArray(value) ? value : String(value).split(/\s+/);
  classes.filter(Boolean).forEach((name) => element.classList.add(name));
}

function applyStyle(element, value) {
  if (!value) return;
  if (typeof value === "string") {
    element.style.cssText += value;
    return;
  }
  for (const [key, raw] of Object.entries(value)) {
    if (raw === null || raw === undefined) continue;
    const name = key.startsWith("--")
      ? key
      : key.replace(/[A-Z]/g, (c) => `-${c.toLowerCase()}`);
    element.style.setProperty(name, String(raw));
  }
}

// Convert arbitrary layui callback arguments to JSON-safe data.
// Stable identity for plain JSON data, used to recognise host echoes.
function fingerprint(value) {
  try {
    return JSON.stringify(value);
  } catch {
    return String(value);
  }
}

function jsonSafe(value, depth = 0, seen = new WeakSet()) {
  if (value === null || value === undefined) return null;
  const kind = typeof value;
  if (kind === "string") return value.length > 4000 ? value.slice(0, 4000) : value;
  if (kind === "number") return Number.isFinite(value) ? value : null;
  if (kind === "boolean") return value;
  if (kind === "bigint") return value.toString();
  if (kind === "function" || kind === "symbol") return null;
  if (value instanceof Date) return value.toISOString();
  if (kind !== "object") return String(value);
  if (typeof Node !== "undefined" && value instanceof Node) return null;
  if (value.nodeType && value.nodeName) return null;
  if (depth >= MAX_RAW_DEPTH) return null;
  if (seen.has(value)) return null;
  seen.add(value);
  try {
    if (Array.isArray(value)) {
      return value.slice(0, MAX_RAW_ITEMS).map((item) => jsonSafe(item, depth + 1, seen));
    }
    if (typeof value.toJSON === "function") {
      try {
        return jsonSafe(value.toJSON(), depth + 1, seen);
      } catch {
        /* fall through */
      }
    }
    const result = {};
    let count = 0;
    for (const key of Object.keys(value)) {
      if (count >= MAX_RAW_ITEMS) break;
      if (key === "this" || key.startsWith("__")) continue;
      const item = value[key];
      if (typeof item === "function" || typeof item === "symbol") continue;
      count += 1;
      result[key] = jsonSafe(item, depth + 1, seen);
    }
    return result;
  } finally {
    seen.delete(value);
  }
}

function isDark() {
  if (typeof document === "undefined") return false;
  const root = document.documentElement;
  if (root.classList.contains("dark") || root.classList.contains("dark-theme")) return true;
  if (root.getAttribute("data-theme") === "dark") return true;
  const notebook = document.querySelector(".jp-Notebook, marimo-app, body");
  if (notebook) {
    if (
      notebook.classList.contains("dark") ||
      notebook.classList.contains("dark-theme") ||
      notebook.getAttribute("data-theme") === "dark"
    ) {
      return true;
    }
  }
  return Boolean(window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches);
}

function resolveTheme(preference) {
  if (preference === "dark") return "dark";
  if (preference === "light") return "light";
  return isDark() ? "dark" : "light";
}

function isVisible(spec, state) {
  if (spec === undefined || spec === null || spec === true) return true;
  if (spec === false) return false;
  if (typeof spec === "string") return Boolean(state[spec]);
  if (typeof spec === "object") {
    const value = state[spec.key];
    if ("equals" in spec) return value === spec.equals;
    if ("not_equals" in spec) return value !== spec.not_equals;
    if (Array.isArray(spec.in)) return spec.in.includes(value);
    if ("truthy" in spec) return Boolean(value) === Boolean(spec.truthy);
  }
  return Boolean(spec);
}

function resolveStateRefs(value, state) {
  if (value === null || value === undefined) return value;
  if (Array.isArray(value)) return value.map((item) => resolveStateRefs(item, state));
  if (typeof value !== "object") return value;
  const keys = Object.keys(value);
  if (keys.length === 1 && ("$state" in value || "$bind" in value)) {
    return state[value.$state ?? value.$bind];
  }
  const result = {};
  for (const [key, item] of Object.entries(value)) {
    result[key] = resolveStateRefs(item, state);
  }
  return result;
}

// ---------------------------------------------------------------------------
// Session
// ---------------------------------------------------------------------------

class Session {
  constructor(model) {
    this.model = model;
    this.uid = `law${Math.random().toString(36).slice(2, 8)}`;
    this.mounts = [];
    this.pendingMounts = [];
    this.pending = new Map();
    this.flushTimer = null;
    this.schemaRef = null;
    this.listeners = [];
    this.renderer = null;
    // Values just written back from the host; layui re-emitting them must not
    // start a write → save_changes → write loop.
    this.echoes = new Map();
    this.applying = false;
  }

  get state() {
    return this.model.get("state") || {};
  }

  get throttle() {
    const value = this.model.get("sync_throttle_ms");
    return typeof value === "number" ? value : 100;
  }

  // layui event filters only need to be unique within one page, and the uid
  // keeps two widgets that use the same node ids from clobbering each other.
  filterFor(node, index = 0) {
    const base = node?.id || (node?.model ? `model-${node.model}` : `node-${index}`);
    return `${this.uid}-${String(base).replace(/[^A-Za-z0-9_-]/g, "_")}`;
  }

  setValue(key, value) {
    if (!key || this.applying) return;
    if (this.isEcho(key, value)) return;
    this.pending.set(key, value);
    if (this.throttle <= 0) {
      this.flush();
      return;
    }
    if (this.flushTimer !== null) return;
    this.flushTimer = setTimeout(() => {
      this.flushTimer = null;
      this.flush();
    }, this.throttle);
  }

  flush() {
    if (this.flushTimer !== null) {
      clearTimeout(this.flushTimer);
      this.flushTimer = null;
    }
    if (!this.pending.size) return;
    const writes = Object.fromEntries(this.pending);
    const next = { ...this.state, ...writes };
    this.pending.clear();
    for (const [key, value] of Object.entries(writes)) {
      this.echoes.set(key, fingerprint(value));
    }
    this.model.set("state", next);
    this.model.save_changes();
  }

  // True when `value` is what the widget itself just sent for `key`, i.e. the
  // host echoing our own write back. Consumes the echo.
  isEcho(key, value) {
    if (!this.echoes.has(key)) return false;
    const expected = this.echoes.get(key);
    const incoming = fingerprint(value);
    if (expected === incoming) {
      this.echoes.delete(key);
      return true;
    }
    return false;
  }

  // Applies a host state update without letting layui's resulting change
  // events flow back into state.
  applyFromHost(fn) {
    if (this.applying) return;
    this.applying = true;
    try {
      fn();
    } finally {
      this.applying = false;
    }
  }

  emit(event, node, value, raw, extra) {
    const payload = {
      seq: ++eventSequence,
      event: String(event || ""),
      type: node.type || null,
      id: node.id || null,
      model: node.model || null,
      value: jsonSafe(value),
      raw: jsonSafe(raw ?? null),
      state: jsonSafe({ ...this.state, ...Object.fromEntries(this.pending) }),
      timestamp: Date.now(),
      ...(extra || {}),
    };
    this.model.set("event", payload);
    this.model.save_changes();
  }

  listen(target, type, handler, options) {
    target.addEventListener(type, handler, options);
    this.listeners.push(() => target.removeEventListener(type, handler, options));
    return () => target.removeEventListener(type, handler, options);
  }

  // anywidget's model proxy exposes on/off rather than addEventListener.
  onModel(name, handler) {
    this.model.on(name, handler);
    this.listeners.push(() => this.model.off(name, handler));
    return () => this.model.off(name, handler);
  }

  dispose() {
    if (this.flushTimer !== null) {
      clearTimeout(this.flushTimer);
      this.flushTimer = null;
    }
    for (const cleanup of this.listeners.splice(0)) {
      try {
        cleanup();
      } catch {
        /* ignore */
      }
    }
    for (const mount of this.mounts.splice(0)) {
      try {
        mount.destroy?.();
      } catch (error) {
        console.warn("[layui-anywidget] destroy failed", error);
      }
    }
  }
}

/*__LAYUI_RENDERERS__*/

// ---------------------------------------------------------------------------
// Form controls
// ---------------------------------------------------------------------------

const FORM_TYPES = new Set([
  "input",
  "textarea",
  "select",
  "checkbox",
  "checkbox-group",
  "switch",
  "radio",
]);

function optionValue(item) {
  if (item && typeof item === "object") {
    return {
      label: item.label ?? item.text ?? item.title ?? item.value ?? "",
      value: item.value ?? item.label ?? item.text ?? "",
      disabled: Boolean(item.disabled),
    };
  }
  return { label: item, value: item, disabled: false };
}

function buildFormControl(node) {
  const props = node.props || {};
  let control;

  switch (node.type) {
    case "textarea":
      control = document.createElement("textarea");
      control.className = "layui-textarea";
      break;
    case "select":
      control = document.createElement("select");
      if (props.multiple) {
        // layui 2.13 decorates a select as a single-choice dropdown and
        // replaces the selection on every click, so `multiple` cannot survive
        // decoration. Keep the native control instead (`lay-ignore` makes
        // layui show it and skip its renderer).
        control.multiple = true;
        control.setAttribute("lay-ignore", "");
        control.className = "layui-input law-multiselect";
        control.size = Math.min(Math.max((props.options || []).length, 2), 5);
      }
      if (props.search) control.setAttribute("lay-search", "");
      for (const item of props.options || []) {
        const { label, value, disabled } = optionValue(item);
        const option = document.createElement("option");
        option.value = String(value ?? "");
        option.textContent = String(label ?? "");
        if (disabled) option.disabled = true;
        control.appendChild(option);
      }
      break;
    case "checkbox":
    case "switch": {
      control = document.createElement("input");
      control.type = "checkbox";
      if (node.type === "switch") control.setAttribute("lay-skin", "switch");
      else if (props.skin) control.setAttribute("lay-skin", props.skin);
      if (props.value !== undefined) control.value = String(props.value);
      if (props.title !== undefined) control.title = String(props.title);
      if (props.text !== undefined) {
        control.setAttribute("lay-text", node.type === "switch" ? props.text : props.text);
      }
      break;
    }
    case "checkbox-group": {
      // Several checkboxes sharing one bound list, e.g. `["a", "c"]`.
      const group = document.createElement("div");
      group.className = "law-inline";
      for (const item of props.options || []) {
        const { label, value, disabled } = optionValue(item);
        const input = document.createElement("input");
        input.type = "checkbox";
        input.name = node.id || "value";
        input.value = String(value);
        input.title = String(label);
        if (props.skin) input.setAttribute("lay-skin", props.skin);
        if (disabled) input.disabled = true;
        group.appendChild(input);
      }
      control = group;
      break;
    }
    case "radio": {
      if (Array.isArray(props.options)) {
        const group = document.createElement("div");
        group.className = "law-inline";
        for (const item of props.options) {
          const { label, value, disabled } = optionValue(item);
          const input = document.createElement("input");
          input.type = "radio";
          input.name = node.id || "value";
          input.value = String(value);
          input.title = String(label);
          if (props.skin) input.setAttribute("lay-skin", props.skin);
          if (disabled) input.disabled = true;
          group.appendChild(input);
        }
        control = group;
      } else {
        control = document.createElement("input");
        control.type = "radio";
        control.title = props.title ?? "";
        if (props.value !== undefined) control.value = String(props.value);
      }
      break;
    }
    default: {
      control = document.createElement("input");
      control.className = "layui-input";
      control.type = props.type || "text";
      if (props.placeholder !== undefined) control.placeholder = props.placeholder;
      if (props.readonly) control.readOnly = true;
      if (props.disabled) control.disabled = true;
      if (props.maxlength !== undefined) control.maxLength = props.maxlength;
      if (control.type === "number") {
        if (props.min !== undefined) control.min = props.min;
        if (props.max !== undefined) control.max = props.max;
        if (props.step !== undefined) control.step = props.step;
        if (props.precision !== undefined) control.setAttribute("lay-precision", props.precision);
      }
    }
  }
  return control;
}

function selectControls(node, control) {
  return (node.type === "radio" || node.type === "checkbox-group") && control.querySelectorAll
    ? control.querySelectorAll("input")
    : control;
}

// layui 2.13.9 resolves a form filter against the document because
// `form.render(type, filter)` only accepts a string and builds
// `$(".layui-form[lay-filter='...']')` from it. Elements inside a shadow root
// are therefore invisible to it. Running the render while the subtree hangs
// under document.body works, and moving it back keeps the decorated markup.
function withDocumentRuntime(el, fn) {
  const root = el.getRootNode();
  // A detached node (layui may call `done` before re-inserting the view) has
  // itself as its root; it still needs to hang under document.body for
  // document-rooted lookups to find it.
  if (!(root instanceof ShadowRoot) && root.isConnected) {
    fn();
    return;
  }
  const parent = el.parentNode;
  const next = el.nextSibling;
  const temp = document.createElement("div");
  document.body.appendChild(temp);
  temp.appendChild(el);
  try {
    fn();
  } finally {
    // Restore the exact position, not just the root: the form must stay
    // inside .law-root for layout and theming to apply.
    if (parent) parent.insertBefore(el, next);
    else if (root !== el) root.appendChild(el);
    else el.remove();
    temp.remove();
  }
}

// Re-decorate a control after a programmatic value change. The filter lookups
// above are rooted at the element's closest `.layui-form`, so the form is what
// has to move into the document.
function rerenderControl(layui, node, control) {
  const formEl = control.closest?.(".layui-form");
  const filter = formEl?.getAttribute("lay-filter");
  if (!formEl || !filter) return;
  if (node.type === "select") {
    withDocumentRuntime(formEl, () => layui.form.render("select", filter));
  } else if (
    ["checkbox", "checkbox-group", "switch", "radio"].includes(node.type)
  ) {
    // layui has no "switch" renderer; switch inputs are checkboxes with
    // `lay-skin="switch"` and are repainted by the checkbox pass.
    const formType = ["checkbox-group", "switch"].includes(node.type) ? "checkbox" : node.type;
    withDocumentRuntime(formEl, () => layui.form.render(formType, filter));
  }
}

function writeFormValue(node, control, value, layui) {
  const props = node.props || {};
  const controls = selectControls(node, control);
  const $ = layui.$;

  if (node.type === "checkbox-group") {
    const wanted = new Set((Array.isArray(value) ? value : []).map(String));
    $(controls).each(function () {
      this.checked = wanted.has(String(this.value));
    });
    return;
  }

  if (node.type === "select" && props.multiple && Array.isArray(value)) {
    const wanted = value.map((item) => String(item));
    $(control).val(wanted);
    return;
  }

  $(controls).each(function () {
    if (this.type === "checkbox") {
      this.checked = props.value !== undefined ? value === props.value : Boolean(value);
    } else if (this.type === "radio") {
      this.checked = String(this.value) === String(value);
    } else {
      this.value = value === null || value === undefined ? "" : value;
    }
  });
}

function readFormValue(node, control, layui) {
  const props = node.props || {};
  if (node.type === "checkbox-group") {
    const values = [];
    for (const input of control.querySelectorAll("input")) {
      if (input.checked) values.push(input.value);
    }
    return values;
  }
  if (node.type === "switch") {
    if (props.checked_value !== undefined || props.value !== undefined) {
      return control.checked ? props.checked_value ?? props.value : props.unchecked_value ?? "";
    }
    return control.checked;
  }
  if (node.type === "checkbox") {
    return props.value !== undefined ? (control.checked ? props.value : false) : control.checked;
  }
  if (node.type === "select" && props.multiple) {
    return layui.$(control).val() || [];
  }
  if (node.type === "radio") {
    return control.value;
  }
  return control.value;
}

function bindFormEvents(session, node, control, layui) {
  const form = layui.form;
  const filter = session.filterFor(node, 0);
  const formType = node.type === "switch" ? "switch" : node.type;
  const props = node.props || {};

  const write = (value, eventName) => {
    if (node.model) session.setValue(node.model, value);
    if (node.updates) {
      const key = node.updates[eventName] ?? node.updates[formType];
      if (key) session.setValue(key, value);
    }
    const renamed = node.events && (node.events[eventName] || node.events[formType]);
    session.emit(renamed || eventName, node, value, { value });
  };

  if (node.type === "select" && props.multiple) {
    // layui does not fire select events for `lay-ignore` controls.
    const commit = () => write(layui.$(control).val() || [], "select");
    session.listen(control, "change", commit);
    session.listen(control, "input", commit);
  } else if (
    ["select", "checkbox", "checkbox-group", "switch", "radio"].includes(node.type)
  ) {
    // layui fires `checkbox(filter)` for a checkbox group's inputs too; the
    // group's value is the list of checked values, not the single clicked one.
    const eventType = node.type === "checkbox-group" ? "checkbox" : formType;
    form.on(`${eventType}(${filter})`, (data) => {
      if (node.type === "radio") {
        write(data.value, "radio");
      } else if (node.type === "select" && props.multiple) {
        write(layui.$(control).val() || [], "select");
      } else {
        write(readFormValue(node, control, layui), eventType);
      }
    });
  } else {
    session.listen(control, "input", () => write(control.value, "input"));
    session.listen(control, "change", () => write(control.value, "change"));
  }

  return {
    destroy() {
      form.off?.(
        [`select(${filter})`, `checkbox(${filter})`, `switch(${filter})`, `radio(${filter})`],
        "form",
      );
    },
  };
}

function renderFormNode(session, node, layui, inForm = false) {
  const control = buildFormControl(node);
  control.setAttribute("name", node.id || "value");
  if (node.id) control.setAttribute("lay-filter", session.filterFor(node, 0));
  // layui reads `lay-filter` from each <input> for radios and checkbox
  // groups, not from the wrapping <div>.
  if (
    (node.type === "radio" || node.type === "checkbox-group") &&
    control.tagName === "DIV"
  ) {
    for (const input of control.querySelectorAll("input")) {
      input.setAttribute("lay-filter", session.filterFor(node, 0));
    }
  }
  const props = node.props || {};
  setAttr(control, "lay-ignore", props.ignore);
  setAttr(control, "lay-verify", props.verify);
  setAttr(control, "lay-reqtext", props.reqtext);
  setAttr(control, "autocomplete", props.autocomplete);
  // Non-text controls have no shared disabled path in buildFormControl.
  if (props.disabled && !(control instanceof HTMLInputElement) && control.tagName === "SELECT") {
    control.disabled = true;
  }

  const wrapper = document.createElement("div");
  // layui's stylesheet hides native selects/checkboxes/radios only inside
  // `.layui-form`. Standalone controls get a persistent `.layui-form` wrapper
  // so the decorated UI replaces the native control instead of sitting next
  // to it. Controls under a real `form` node already have one.
  const standalone = !inForm;
  if (standalone) {
    wrapper.className = "layui-form";
    wrapper.setAttribute("lay-filter", session.filterFor(node, 0));
  }
  wrapper.appendChild(control);

  const initial = session.state[node.model];
  if (initial !== undefined) writeFormValue(node, control, initial, layui);

  const events = bindFormEvents(session, node, control, layui);
  const formType = node.type === "switch" ? "switch" : node.type;

  return {
    el: wrapper,
    // Controls outside a `form` node still need a render pass. The wrapper is
    // itself a `.layui-form`, so move it into the document for layui's
    // document-rooted filter lookup and put it back afterwards.
    afterMount() {
      if (!standalone) return;
      const filter = wrapper.getAttribute("lay-filter");
      withDocumentRuntime(wrapper, () => layui.form.render(null, filter));
    },
    update(value) {
      writeFormValue(node, control, value, layui);
      // Re-rendering repaints layui's decorated UI for the new value.
      rerenderControl(layui, node, control);
    },
    destroy: events.destroy,
  };
}

// ---------------------------------------------------------------------------
// Tree rendering
// ---------------------------------------------------------------------------

function mountNode(session, node, layui, index, inForm = false) {
  if (!node || typeof node !== "object") return null;

  if (node.type === "text") {
    const tag = node.props?.tag || "span";
    const element = document.createElement(tag);
    element.textContent = node.text ?? "";
    applyClass(element, node.class);
    applyStyle(element, node.style);
    return { el: element };
  }

  if (node.type === "field") {
    const wrapper = document.createElement("div");
    wrapper.className = "law-field";
    const label = node.props?.label;
    if (label) {
      const labelEl = document.createElement("div");
      labelEl.className = "law-label";
      labelEl.textContent = label;
      wrapper.appendChild(labelEl);
    }
    const body = document.createElement("div");
    body.className = "law-field-body";
    renderChildren(session, node.children, body, layui);
    wrapper.appendChild(body);
    applyStyle(wrapper, node.style);
    return { el: wrapper };
  }

  if (node.type === "form") {
    const formEl = document.createElement("form");
    formEl.className = "layui-form";
    const formFilter = node.props?.["lay-filter"] || session.filterFor(node, index);
    formEl.setAttribute("lay-filter", formFilter);
    applyClass(formEl, node.class);
    renderChildren(session, node.children, formEl, layui, true);
    formEl.addEventListener("submit", (event) => {
      event.preventDefault();
    });
    formEl.addEventListener("click", (event) => {
      const submitter = event.target.closest?.("[lay-submit]");
      if (!submitter) return;
      event.preventDefault();
      const values = {};
      layui.$(formEl)
        .find("input,select,textarea")
        .each(function () {
          const name = this.name;
          if (!name) return;
          if (this.type === "checkbox") {
            values[name] = this.checked ? (this.value === "on" ? true : this.value) : false;
          } else if (this.type === "radio") {
            if (this.checked) values[name] = this.value;
          } else {
            values[name] = this.value;
          }
        });
      session.emit("submit", node, values, {
        values,
        filter: submitter.getAttribute("lay-filter") || null,
      });
    });
    return {
      el: formEl,
      afterMount() {
        withDocumentRuntime(formEl, () => layui.form.render(null, formFilter));
      },
    };
  }

  if (FORM_TYPES.has(node.type)) {
    return renderFormNode(session, node, layui, inForm);
  }

  if (COMPONENT_RENDERERS[node.type]) {
    return COMPONENT_RENDERERS[node.type]({
      node,
      session,
      layui,
      uid: session.uid,
      filter: session.filterFor(node, index),
      renderChildren: (children) => renderFragment(session, children, layui),
      renderNode: (child) => mountNode(session, child, layui, index, inForm)?.el ?? null,
    });
  }

  if (node.type === "button") {
    const props = node.props || {};
    const button = document.createElement("button");
    button.type = "button";
    button.className = props.theme ? `layui-btn layui-btn-${props.theme}` : "layui-btn";
    applyClass(button, node.class);
    applyClass(button, props.class_);
    if (props.html !== undefined) button.innerHTML = String(props.html);
    else button.textContent = node.text ?? node.children?.[0] ?? "按钮";
    if (node.id) button.setAttribute("data-law-id", node.id);
    setAttr(button, "lay-submit", props["lay-submit"]);
    setAttr(button, "lay-filter", props["lay-filter"]);
    if (props.disabled) button.disabled = true;
    applyStyle(button, node.style);
    session.listen(button, "click", () => {
      session.emit((node.events && node.events.click) || "click", node, null, {});
    });
    return { el: button };
  }

  // Plain element fallback (div, span, table markup, etc.).
  const element = document.createElement(node.type);
  for (const [key, raw] of Object.entries(node.props || {})) {
    if (key === "html") element.innerHTML = raw;
    else if (key === "style") applyStyle(element, raw);
    else setAttr(element, key === "class_" ? "class" : key, raw);
  }
  if (node.id) element.setAttribute("data-law-id", node.id);
  applyClass(element, node.class);
  applyStyle(element, node.style);
  renderChildren(session, node.children, element, layui);
  return { el: element };
}

function renderFragment(session, children, layui, inForm = false) {
  const fragment = document.createDocumentFragment();
  const list = Array.isArray(children) ? children : children ? [children] : [];
  list.forEach((child, index) => {
    if (child === null || child === undefined) return;
    if (typeof child === "string" || typeof child === "number") {
      fragment.appendChild(document.createTextNode(String(child)));
      return;
    }
    if (!isVisible(child.visible, session.state)) return;
    const mount = mountNode(session, child, layui, index, inForm);
    if (!mount) return;
    if (child.model || child.bind) session.mounts.push({ node: child, mount });
    // Components such as table measure layout at render time and break when
    // rendered into a detached fragment, so they defer until after mount.
    if (mount.afterMount) session.pendingMounts.push(mount);
    fragment.appendChild(mount.el);
  });
  return fragment;
}

function renderChildren(session, children, parent, layui, inForm = false) {
  parent.appendChild(renderFragment(session, children, layui, inForm));
}

function renderRoot(session, schema, el, layui) {
  el.innerHTML = "";
  session.mounts = [];
  session.pendingMounts = [];
  const nodes = Array.isArray(schema) ? schema : schema ? [schema] : [];
  el.appendChild(renderFragment(session, nodes, layui, false));
  const pending = session.pendingMounts;
  session.pendingMounts = [];
  for (const mount of pending) mount.afterMount();
}

// ---------------------------------------------------------------------------
// Entry point
// ---------------------------------------------------------------------------

async function render({ model, el }) {
  const session = new Session(model);
  el.classList.add(ROOT_CLASS);
  el.setAttribute("data-layui-version", LAYUI_VERSION);

  const applyTheme = () => {
    const theme = resolveTheme(model.get("theme"));
    el.setAttribute("data-theme", theme);
  };
  applyTheme();

  const applyHeight = () => {
    const height = model.get("height");
    if (height && height !== "auto") {
      el.style.height = height;
      el.style.overflowY = "auto";
    } else {
      el.style.height = "";
      el.style.overflowY = "";
    }
  };
  applyHeight();

  const placeholder = document.createElement("div");
  placeholder.className = "law-status";
  placeholder.textContent = model.get("loading_text") || "加载中…";
  el.appendChild(placeholder);

  let layui;
  try {
    const root = el.getRootNode();
    layui = await ensureRuntime(model.get("config"), !(root instanceof ShadowRoot));
    if (root instanceof ShadowRoot) await loadFullStyles(root);
    placeholder.remove();
    session.layui = layui;
    session.schemaRef = model.get("schema");
    renderRoot(session, model.get("schema"), el, layui);
    model.set("ready", true);
    model.set("error", "");
  } catch (error) {
    console.error("[layui-anywidget] render failed:", error);
    placeholder.className = "law-status law-status-error";
    placeholder.textContent = `layui 加载失败：${error.message}`;
    model.set("ready", false);
    model.set("error", String(error.message || error));
    return () => session.dispose();
  }

  session.onModel("change:schema", () => {
    if (model.get("schema") === session.schemaRef) return;
    session.schemaRef = model.get("schema");
    renderRoot(session, model.get("schema"), el, layui);
  });

  session.onModel("change:state", () => {
    const state = session.state;
    session.applyFromHost(() => {
      for (const { node, mount } of session.mounts) {
        if (!mount.update) continue;
        if (node.model && state[node.model] !== undefined) mount.update(state[node.model]);
        else if (node.bind) mount.update(resolveStateRefs(node.bind, state));
      }
    });
  });

  session.onModel("change:theme", applyTheme);
  session.onModel("change:height", applyHeight);

  return () => session.dispose();
}

export default { render };

export const __internals = {
  jsonSafe,
  isVisible,
  resolveStateRefs,
  resolveTheme,
  optionValue,
};
