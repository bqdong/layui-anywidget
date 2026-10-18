# /// script
# requires-python = ">=3.10"
# dependencies = ["layui-anywidget", "marimo"]
# ///

"""标签页 / Tabs — 对应 layui 文档 ``docs/tabs/index.md``。

标签页的每个面板都可以包含真实控件（不是静态 HTML 字符串），因此面板内的
输入同样参与状态同步。
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
            lay.tabs(
                lay.tab(
                    "用户",
                    lay.form(lay.input("tab_name", label="用户名")),
                    id="user",
                ),
                lay.tab(
                    "设置",
                    lay.form(lay.switch("tab_notify", label="通知")),
                    id="settings",
                ),
                lay.tab(
                    "关于",
                    lay.text("layui-anywidget 把 Python 的 schema 树渲染成 layui 组件。"),
                    id="about",
                ),
                model="active_tab",
            ),
        ],
        state={
            "tab_name": "Ada",
            "tab_notify": True,
            "active_tab": "user",
        },
    )
    widget_ui = mo.ui.anywidget(widget)
    return widget_ui


@app.cell
def cell_layout(event_panel, heading, mo, section, value_panel, widget_ui):
    mo.vstack(
        [
            heading(
                "标签页 Tabs",
                "标签页用于在有限空间内切换多组内容。切换时当前标签的 id 会写入 state，"
                "面板内的控件保持各自的绑定。",
            ),
            section("标签页", widget_ui),
            section("当前状态", value_panel(widget_ui), event_panel(widget_ui)),
        ]
    )
    return


if __name__ == "__main__":
    app.run()
