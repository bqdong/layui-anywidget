# /// script
# requires-python = ">=3.10"
# dependencies = ["layui-anywidget", "marimo"]
# ///

"""颜色选择器 / Colorpicker — 对应 layui 文档 ``docs/colorpicker/index.md``。"""

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
            lay.form(
                lay.colorpicker("color", label="颜色 (hex)"),
                lay.colorpicker("color_rgba", label="带透明度", format="rgb", alpha=True),
                lay.colorpicker("color_predefine", label="预设色板", predefine=True),
                lay.colorpicker("color_small", label="小尺寸", size="sm"),
            ),
        ],
        state={
            "color": "#16baaa",
            "color_rgba": "rgba(30, 159, 255, 0.8)",
            "color_predefine": "#ff5722",
            "color_small": "#1e9fff",
        },
    )
    widget_ui = mo.ui.anywidget(widget)
    return widget_ui


@app.cell
def cell_layout(event_panel, heading, mo, section, value_panel, widget_ui):
    mo.vstack(
        [
            heading(
                "颜色选择器 Colorpicker",
                "颜色选择器提供拾色面板与预设色板。支持 `hex` / `rgb` 格式、透明度通道"
                "以及不同的尺寸。",
            ),
            section("颜色选择器", widget_ui),
            section("当前状态", value_panel(widget_ui), event_panel(widget_ui)),
        ]
    )
    return


if __name__ == "__main__":
    app.run()
