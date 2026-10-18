# /// script
# requires-python = ">=3.10"
# dependencies = ["layui-anywidget", "marimo"]
# ///

"""折叠面板 / Collapse — 对应 layui 文档 ``docs/panel/collapse.md``。"""

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
            lay.collapse(
                lay.collapse_item(
                    "面板一",
                    lay.text("默认展开的面板。"),
                    open=True,
                ),
                lay.collapse_item(
                    "面板二",
                    lay.text("点击标题展开或收起。"),
                ),
                lay.collapse_item(
                    "面板三（含交互控件）",
                    lay.form(
                        lay.checkbox("collapse_flag", "启用选项", label=None),
                        lay.input("collapse_text", label="备注"),
                    ),
                ),
            ),
            lay.collapse(
                lay.collapse_item("手风琴 A", lay.text("同一时间只展开一个面板。"), open=True),
                lay.collapse_item("手风琴 B", lay.text("展开 B 会收起 A。")),
                accordion=True,
            ),
        ],
        state={
            "collapse_flag": True,
            "collapse_text": "",
        },
    )
    widget_ui = mo.ui.anywidget(widget)
    return widget_ui


@app.cell
def cell_layout(event_panel, heading, mo, section, value_panel, widget_ui):
    mo.vstack(
        [
            heading(
                "折叠面板 Collapse",
                "折叠面板用于收纳内容。``open=True`` 让某一项默认展开，"
                "``accordion=True`` 让同一组内只展开一项。",
            ),
            section("折叠面板", widget_ui),
            section("当前状态", value_panel(widget_ui), event_panel(widget_ui)),
        ]
    )
    return


if __name__ == "__main__":
    app.run()
