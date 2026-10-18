# /// script
# requires-python = ">=3.10"
# dependencies = ["layui-anywidget", "marimo"]
# ///

"""单选框 / Radio — 对应 layui 文档 ``docs/form/radio.md``。"""

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
                lay.radio(
                    "gender",
                    [("男", "male"), ("女", "female"), ("保密", "secret")],
                    label="性别",
                ),
                lay.radio(
                    "plan",
                    [("免费版", "free"), ("专业版", "pro"), ("团队版", "team")],
                    label="套餐",
                ),
                lay.radio(
                    "skin",
                    [("原始风格", "a"), ("另一种", "b")],
                    label="皮肤",
                    skin="primary",
                ),
            ),
        ],
        state={"gender": "secret", "plan": "pro", "skin": "a"},
    )
    widget_ui = mo.ui.anywidget(widget)
    return widget_ui


@app.cell
def cell_layout(event_panel, heading, mo, section, value_panel, widget_ui):
    mo.vstack(
        [
            heading(
                "单选框 Radio",
                "单选框用于互斥选项。`lay.radio` 接收一个 ``(label, value)`` 列表，"
                "并把选中的 value 同步到 state。",
            ),
            section("单选框", widget_ui),
            section("当前状态", value_panel(widget_ui), event_panel(widget_ui)),
        ]
    )
    return


if __name__ == "__main__":
    app.run()
