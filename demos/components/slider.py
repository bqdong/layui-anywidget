# /// script
# requires-python = ">=3.10"
# dependencies = ["layui-anywidget", "marimo"]
# ///

"""滑块 / Slider — 对应 layui 文档 ``docs/slider/index.md``。"""

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
            lay.slider("volume", label="音量", min_value=0, max_value=100, step=5),
            lay.slider(
                "price", label="价格区间", min_value=0, max_value=1000, step=100, range=True
            ),
            lay.slider(
                "score", label="显示步进", min_value=0, max_value=10, step=1, show_step=True
            ),
            lay.slider("locked", label="禁用", min_value=0, max_value=100, disabled=True),
        ],
        state={
            "volume": 60,
            "price": [200, 800],
            "score": 5,
            "locked": 30,
        },
    )
    widget_ui = mo.ui.anywidget(widget)
    return widget_ui


@app.cell
def cell_layout(event_panel, heading, mo, section, value_panel, widget_ui):
    mo.vstack(
        [
            heading(
                "滑块 Slider",
                "滑块用于在给定区间内选择数值。支持单值、区间双滑块、步进展示和禁用状态。",
            ),
            section("滑块", widget_ui),
            section("当前状态", value_panel(widget_ui), event_panel(widget_ui)),
        ]
    )
    return


if __name__ == "__main__":
    app.run()
