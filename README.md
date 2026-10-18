# layui-anywidget

layui 2.13.9 components for [anywidget](https://anywidget.dev), usable from
JupyterLab, Jupyter Notebook, and marimo. Python builds a declarative
component tree; the browser renders it with layui and keeps values in sync
through a shared `state` dictionary.

```python
import layui_anywidget as layui
from layui_anywidget import lay

widget = layui.Layui(
    lay.form(
        lay.input("name", label="姓名", placeholder="Ada Lovelace"),
        lay.select("lang", ["Python", "JavaScript", "Rust"], label="语言"),
        lay.slider("level", label="等级", min_value=0, max_value=10),
    ),
    state={"name": "", "lang": "Python", "level": 5},
)
widget
```

Single-value controls are available as classes:

```python
from layui_anywidget import Slider, Select, Table

level = Slider(5, min_value=0, max_value=10, label="等级")
level.value        # 5, updates when the browser slider moves
level.value = 8    # Python → browser

lang = Select("Python", ["Python", "JavaScript", "Rust"], label="语言")

table = Table(
    [{"name": "Ada", "score": 98}, {"name": "Grace", "score": 95}],
    [{"field": "name", "title": "姓名"}, {"field": "score", "title": "分数", "sort": True}],
    selectable=True,
)
table.value        # selected rows
```

## Install

```bash
uv add layui-anywidget
# or
pip install layui-anywidget
```

layui itself is bundled in the wheel; no CDN or network access is needed.

## Two layers

- **`Layui`** — the generic container. Build any component tree with `lay.*`
  helpers and share one `state` dictionary.
- **Controls** — `Input`, `InputNumber`, `Select`, `Checkbox`, `Switch`,
  `Radio`, `Slider`, `ColorPicker`, `DatePicker`, `Rate`, `Table`, `Tabs`,
  and `Button`, each with a synced `value` (or `clicks` for `Button`).

## Schema basics

A node is a dictionary with `type`, `props`, `children`, and optional binding
fields:

| Field | Meaning |
| --- | --- |
| `type` | layui component name (`"slider"`, `"table"`, …) or an HTML tag |
| `id` | Stable node id; drives the `lay-filter` and event payloads |
| `model` | Two-way bound state key |
| `bind` | One-way bindings, e.g. `{"data": "rows"}` for `table` |
| `events` | Events forwarded to Python (renamed via a mapping) |
| `updates` | Event name → state key; the event value is written to state |
| `visible` | `true`/`false`, a state key, or `{"key": ..., "equals": ...}` |
| `props` | layui render options |

```python
lay.node(
    "table",
    bind={"data": "rows"},
    props={"cols": [[{"field": "name", "title": "Name"}]]},
)
```

Available helpers include `lay.form`, `lay.field`, `lay.input`,
`lay.input_number`, `lay.textarea`, `lay.select`, `lay.checkbox`,
`lay.switch`, `lay.radio`, `lay.slider`, `lay.colorpicker`,
`lay.datepicker`, `lay.rate`, `lay.table`, `lay.tabs`, `lay.tab`,
`lay.collapse`, `lay.dropdown`, `lay.layer`, `lay.menu`, `lay.breadcrumb`,
`lay.progress`, `lay.carousel`, `lay.laypage`, `lay.button`, `lay.row`,
`lay.col`, `lay.div`, `lay.text`, `lay.title`, and `lay.node`.

`lay.layer` renders a trigger button and opens a layui popup on click:
`kind` is one of `dialog` / `alert` / `confirm` / `msg` / `load` / `tips` /
`prompt` / `iframe` / `photos` / `tab`, and `options` passes raw layui
options. Results reach Python as events (`confirm`, `cancel`, `prompt`,
`button`, `close`, `unlock`, `submit`). Popups can chain the way the docs'
examples do: `next=` / `next_cancel=` open a follow-up stage after an
alert/confirm/prompt, `actions=["close_all", "reopen", "next"]` gives custom
buttons behaviour, `tabs=[(title, node), ...]` opens real `layui-tabs`, and
`unlock="111111"` implements the lock-screen example.

## State and events

```python
widget.state           # {"name": "", "level": 5}
widget.set_values(level=8)
widget.update_values({"name": "Grace"})

widget.on_change(lambda state, changed: print(changed))
widget.on_event(lambda event: print(event["event"], event["id"], event["value"]))
```

Values flow through `state` (throttled, default 100 ms; set
`sync_throttle_ms=0` for immediate writes). Interaction events flow through
`event` with a monotonic `seq` so duplicate deliveries are ignored.

## marimo

```python
import marimo as mo
form = mo.ui.anywidget(widget)
form.value["state"]["level"]
```

## Theming and layout

`theme` accepts `"auto"` (default), `"light"`, or `"dark"`. `height` accepts
`"auto"` or any CSS length; a fixed height makes the widget scroll.

## Assets and isolation

- layui 2.13.9 (`layui.js` + `layui.css`) ships inside the wheel and is
  embedded in the bridge module; the browser loads it once per page.
- In Jupyter the widget renders into the light DOM; in marimo it renders into
  an open shadow root. The bridge injects the full layui stylesheet into the
  shadow root and a reset-free "core" stylesheet into the document, so layui
  popups (layer, datepicker, colorpicker, dropdown) and the slider drag
  overlay are styled without leaking layui's global `body` reset into the
  notebook.
- CSP note: the runtime uses an inline script injection; pages that forbid
  inline scripts cannot run the widget.

## Known limitations

- layui menu popups (dropdown) are appended to `document.body`, so they can
  visually overlap notebook chrome but are not clipped by the widget; select
  and date panels stay inside the widget.
- `layer.alert`-style service APIs are not exposed as Python functions.
- Tab bodies inside `lay.tabs` are static HTML in 0.1; interactive content
  belongs in the main tree.
- Only layui 2.13.9 is supported (3.0 alpha uses different class names and
  APIs).

## Demos

`demos/form.py` (generic container) and `demos/controls.py` (control classes)
are marimo apps:

```bash
marimo run demos/form.py
```

`demos/components/` has one demo per layui component, laid out like the layui
2.x documentation pages (title, intro quote, a section per feature, and the
live Python-side state underneath). Start with the index:

```bash
just demo-components          # pick any page
just demo-component layout    # one page, e.g. the grid demo
```

## Development

The project is managed with [uv](https://docs.astral.sh/uv/) (Python), a
[justfile](https://just.systems) (commands), and [prek](https://prek.j178.dev)
(git hooks). Node is only needed for the vendoring/build/test scripts.

```bash
just            # list recipes
just setup      # uv sync + install git hooks
just ci         # lint + tests + build-check (what CI runs)

just build      # regenerate static/layui-bridge.js from static/src/
just vendor     # re-vendor layui 2.13.9 from the CDN
just test       # pytest + node --test
just test-browser   # Playwright smoke test (light DOM + shadow root)
just demo       # run demos/form.py in marimo
just preview    # serve examples/preview.html
just package    # build sdist + wheel into dist/
```

`prek` runs ruff, pytest, and a check that the committed `layui-bridge.js`
matches its sources on every commit. Run `prek run --all-files` to check
everything manually.

## License

MIT. layui is MIT licensed (Copyright 2016-present Layui contributors).
