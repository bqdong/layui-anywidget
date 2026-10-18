# /// script
# requires-python = ">=3.10"
# dependencies = ["layui-anywidget", "marimo"]
# ///

"""面包屑 / Breadcrumb — 对应 layui 文档 ``docs/nav/breadcrumb.md``。"""

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
            lay.breadcrumb(["首页", "组件", "面包屑"]),
            lay.breadcrumb(["首页", "组件", "导航", "面包屑"], **{"lay-separator": ">"}),
        ],
        state={},
    )
    widget_ui = mo.ui.anywidget(widget)
    return widget_ui


@app.cell
def cell_layout(heading, mo, section, widget_ui):
    mo.vstack(
        [
            heading(
                "面包屑 Breadcrumb",
                "面包屑用于展示当前页面在层级结构中的位置。",
            ),
            section("面包屑", widget_ui),
        ]
    )
    return


if __name__ == "__main__":
    app.run()
