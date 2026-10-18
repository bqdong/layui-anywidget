# /// script
# requires-python = ">=3.10"
# dependencies = ["layui-anywidget", "marimo"]
# ///

"""分页 / Laypage — 对应 layui 文档 ``docs/laypage/index.md``。"""

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
            lay.laypage(120, page_key="page", limit=10),
            lay.laypage(
                300,
                page_key="page2",
                limit=20,
                layout=["prev", "page", "next"],
                theme="#1e9fff",
            ),
            lay.laypage(
                50,
                page_key="page3",
                limit=5,
                layout=["count", "prev", "page", "next", "skip"],
            ),
        ],
        state={"page": 1, "page2": 1, "page3": 1},
    )
    widget_ui = mo.ui.anywidget(widget)
    return widget_ui


@app.cell
def cell_layout(event_panel, heading, mo, section, value_panel, widget_ui):
    mo.vstack(
        [
            heading(
                "分页 Laypage",
                "分页用于承载大量数据。当前页会写入绑定的 state 键；"
                "``layout`` 决定显示哪些功能区（上一页、页码、下一页、跳页、总数、每页条数）。",
            ),
            section("分页", widget_ui),
            section("当前状态", value_panel(widget_ui), event_panel(widget_ui)),
        ]
    )
    return


if __name__ == "__main__":
    app.run()
