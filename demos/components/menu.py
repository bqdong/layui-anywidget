# /// script
# requires-python = ">=3.10"
# dependencies = ["layui-anywidget", "marimo"]
# ///

"""导航菜单 / Nav — 对应 layui 文档 ``docs/nav/index.md``。"""

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
    items = [
        {"title": "首页", "id": "home"},
        {
            "title": "产品",
            "id": "product",
            "children": [
                {"title": "产品一", "id": "p1"},
                {"title": "产品二", "id": "p2"},
            ],
        },
        {"title": "关于", "id": "about"},
    ]
    widget = Layui(
        theme="light",
        height="auto",
        schema=[
            lay.menu(items, model="active_menu"),
            lay.menu(items, model="active_menu_side", class_="layui-nav layui-nav-tree"),
        ],
        state={"active_menu": "home", "active_menu_side": "p1"},
    )
    widget_ui = mo.ui.anywidget(widget)
    return widget_ui


@app.cell
def cell_layout(event_panel, heading, mo, section, value_panel, widget_ui):
    mo.vstack(
        [
            heading(
                "导航菜单 Nav",
                "导航菜单用于页面级导航。选中项的 id 会写入 state，也支持树形（子菜单）结构。",
            ),
            section("导航菜单", widget_ui),
            section("当前状态", value_panel(widget_ui), event_panel(widget_ui)),
        ]
    )
    return


if __name__ == "__main__":
    app.run()
