# /// script
# requires-python = ">=3.10"
# dependencies = ["layui-anywidget", "marimo"]
# ///

"""输入框 / Input — 对应 layui 文档 ``docs/form/input.md``。

layui 的输入框由 ``class="layui-input"`` 建立；``lay.input`` / ``lay.textarea``
把它们绑定到 state 键，输入即同步到 Python。
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
            # 基本输入框
            lay.form(
                lay.input("name", label="用户名", placeholder="请输入用户名"),
                lay.input("email", label="邮箱", placeholder="name@example.com"),
                lay.input("password", label="密码", type="password", placeholder="请输入密码"),
                lay.input("search", label="搜索", placeholder="搜索…"),
            ),
            # 多行文本
            lay.textarea(
                "bio",
                label="简介",
                placeholder="请输入内容",
                style={"min-height": "90px"},
            ),
            # 数字输入框
            lay.form(
                lay.input_number("age", label="年龄", min_value=0, max_value=120, step=1),
                lay.input_number("price", label="价格", min_value=0, max_value=1000, step=0.5),
                lay.input_number(
                    "count", label="数量 (步进 5)", min_value=0, max_value=100, step=5
                ),
            ),
            # 禁用与只读
            lay.form(
                lay.input("disabled_input", label="禁用", disabled=True),
                lay.input("readonly_input", label="只读", readonly=True),
            ),
        ],
        state={
            "name": "",
            "email": "",
            "password": "",
            "search": "",
            "bio": "",
            "age": 18,
            "price": 9.9,
            "count": 20,
            "disabled_input": "不可编辑",
            "readonly_input": "只读内容",
        },
    )
    widget_ui = mo.ui.anywidget(widget)
    return widget_ui


@app.cell
def cell_layout(event_panel, heading, mo, section, value_panel, widget_ui):
    mo.vstack(
        [
            heading(
                "输入框 Input",
                "输入框是我们日常开发中使用频率最高的表单元素。layui 的输入框统一由 "
                '`class="layui-input"` 定义，支持文本框、密码框、数字框与多行文本。',
            ),
            section("基本输入框", widget_ui),
            section("当前状态", value_panel(widget_ui), event_panel(widget_ui)),
        ]
    )
    return


if __name__ == "__main__":
    app.run()
