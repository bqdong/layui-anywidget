# /// script
# requires-python = ">=3.10"
# dependencies = ["layui-anywidget", "marimo"]
# ///

"""开关 / Switch — 对应 layui 文档 ``docs/form/switch.md``。"""

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
                lay.switch("notify", label="通知", text="开|关"),
                lay.switch("dark", label="夜间模式", text="ON|OFF"),
                lay.switch("disabled_switch", label="禁用", disabled=True),
                # 自定义值：勾选时同步 "enabled"，否则 "disabled"
                lay.switch(
                    "status", label="状态值", checked_value="enabled", unchecked_value="disabled"
                ),
            ),
        ],
        state={
            "notify": True,
            "dark": False,
            "disabled_switch": True,
            "status": "enabled",
        },
    )
    widget_ui = mo.ui.anywidget(widget)
    return widget_ui


@app.cell
def cell_layout(event_panel, heading, mo, section, value_panel, widget_ui):
    mo.vstack(
        [
            heading(
                "开关 Switch",
                "开关是复选框的另一种形态，通常用于设置项的开启与关闭。"
                "可通过 ``checked_value`` / ``unchecked_value`` 同步自定义值。",
            ),
            section("开关", widget_ui),
            section("当前状态", value_panel(widget_ui), event_panel(widget_ui)),
        ]
    )
    return


if __name__ == "__main__":
    app.run()
