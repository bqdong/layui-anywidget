# /// script
# requires-python = ">=3.10"
# dependencies = ["layui-anywidget", "marimo"]
# ///

"""A layui form rendered as a marimo widget.

Run with `marimo edit demos/form.py` (or `marimo run demos/form.py`).
"""

import marimo

app = marimo.App(width="medium")


@app.cell
def __():
    import marimo as mo

    from layui_anywidget import Layui, lay

    widget = Layui(
        lay.form(
            lay.input("name", label="姓名", placeholder="Ada Lovelace"),
            lay.select("lang", ["Python", "JavaScript", "Rust"], label="语言"),
            lay.slider("level", label="等级", min_value=0, max_value=10, step=1),
            lay.switch("subscribe", label="订阅"),
            lay.colorpicker("color", label="主题色"),
            lay.datepicker("date", label="日期"),
            lay.rate("score", label="评分"),
            lay.button("等级 +1", id="inc", theme="primary"),
            lay.submit("提交"),
        ),
        theme="light",
        state={
            "name": "Ada",
            "lang": "Python",
            "level": 6,
            "subscribe": True,
            "color": "#16baaa",
            "date": "2026-10-17",
            "score": 3,
        },
    )

    def handle_event(event):
        if event["event"] == "click" and event["id"] == "inc":
            widget.set_values(level=min(10, widget.state["level"] + 1))

    widget.on_event(handle_event)
    form = mo.ui.anywidget(widget)
    return form, mo, widget


@app.cell
def __(form, mo):
    state = form.value.get("state", {})
    event = form.value.get("event", {})
    mo.vstack(
        [
            form,
            mo.md(f"```python\n{state!r}\n```"),
            mo.md(f"最近事件：`{event.get('event')}` on `{event.get('id')}`"),
        ]
    )
    return


if __name__ == "__main__":
    app.run()
