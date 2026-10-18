# /// script
# requires-python = ">=3.10"
# dependencies = ["layui-anywidget", "marimo"]
# ///

"""进度条 / Progress — 对应 layui 文档 ``docs/progress/index.md``。

``lay.progress`` 的数值来自 state 键，随对应滑块的变化实时更新。
"""

import marimo

app = marimo.App(width="medium")


@app.cell
def cell_imports():
    import marimo as mo
    from _shared import event_panel, heading, section, value_panel

    from layui_anywidget import Layui, lay

    return Layui, event_panel, heading, lay, mo, section, value_panel


@app.cell
def cell_widget(Layui, lay, mo):
    widget = Layui(
        theme="light",
        height="auto",
        schema=[
            lay.progress("pct", show_percent=True),
            lay.progress("pct", show_percent=True, class_="layui-progress-big"),
            lay.progress("pct", show_percent=False),
            lay.slider("pct", label="调整进度", min_value=0, max_value=100, step=10),
        ],
        state={"pct": 40},
    )
    widget_ui = mo.ui.anywidget(widget)
    return widget_ui


@app.cell
def cell_layout(event_panel, heading, mo, section, value_panel, widget_ui):
    mo.vstack(
        [
            heading(
                "进度条 Progress",
                "进度条用于表示任务的完成度。数值来自一个 state 键，"
                "因此拖动下方滑块时，所有绑定该键的进度条会一起变化。",
            ),
            section("进度条", widget_ui),
            section("当前状态", value_panel(widget_ui), event_panel(widget_ui)),
        ]
    )
    return


if __name__ == "__main__":
    app.run()
