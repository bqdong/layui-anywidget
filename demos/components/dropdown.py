# /// script
# requires-python = ">=3.10"
# dependencies = ["layui-anywidget", "marimo"]
# ///

"""下拉菜单 / Dropdown — 对应 layui 文档 ``docs/dropdown/index.md``。"""

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
                lay.dropdown(
                    lay.span("下拉菜单", class_="layui-btn layui-btn-primary"),
                    [
                        {"title": "选项一", "id": "item1"},
                        {"title": "选项二", "id": "item2"},
                        {"type": "divider"},
                        {"title": "选项三", "id": "item3"},
                    ],
                    id="dropdown",
                    updates={"click": "choice"},
                ),
                lay.dropdown(
                    lay.span("悬停触发", class_="layui-btn layui-btn-primary"),
                    [{"title": "A", "id": "a"}, {"title": "B", "id": "b"}],
                    id="dropdown_hover",
                    trigger_event="mouseenter",
                    updates={"click": "hover_choice"},
                ),
                lay.dropdown(
                    lay.span("带图标", class_="layui-btn"),
                    [
                        {"title": "编辑", "id": "edit"},
                        {"title": "分享", "id": "share"},
                        {"title": "删除", "id": "delete"},
                    ],
                    id="dropdown_icon",
                    updates={"click": "icon_choice"},
                ),
            ),
        ],
        state={
            "choice": None,
            "hover_choice": None,
            "icon_choice": None,
        },
    )
    widget_ui = mo.ui.anywidget(widget)
    return widget_ui


@app.cell
def cell_layout(event_panel, heading, mo, section, value_panel, widget_ui):
    mo.vstack(
        [
            heading(
                "下拉菜单 Dropdown",
                "下拉菜单用于收纳一组操作。点击（或悬停）触发器展开，选中项会写入绑定的 "
                "state 键，同时转发 `click` 事件。",
            ),
            section("下拉菜单", widget_ui),
            section("当前状态", value_panel(widget_ui), event_panel(widget_ui)),
        ]
    )
    return


if __name__ == "__main__":
    app.run()
