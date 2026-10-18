# /// script
# requires-python = ">=3.10"
# dependencies = ["layui-anywidget", "marimo"]
# ///

"""表单 / Form — 对应 layui 文档 ``docs/form/index.md``。

``lay.form`` 组合多个控件；``lay.submit`` 生成 ``lay-submit`` 按钮，点击后把
整个表单的字段值作为事件转发到 Python。
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
            lay.form(
                lay.input("username", label="用户名", placeholder="请输入用户名"),
                lay.input("password", label="密码", type="password"),
                lay.radio("role", [("用户", "user"), ("管理员", "admin")], label="角色"),
                lay.checkbox("agree", "同意协议", label="协议"),
                lay.select(
                    "city",
                    ["北京", "上海", "广州"],
                    label="城市",
                ),
                lay.div(
                    lay.submit("提交", filter="demo-submit"),
                    lay.button("重置", theme="primary", class_="layui-btn-primary"),
                    style={"text-align": "right"},
                ),
                filter="demo-form",
            ),
        ],
        state={
            "username": "",
            "password": "",
            "role": "user",
            "agree": False,
            "city": "beijing",
            "submitted": None,
        },
    )

    def on_submit(event):
        # 表单事件：payload 里有 values（name -> value）与 filter。
        if event.get("event") != "submit":
            return
        widget.update_values({"submitted": event.get("values")})

    widget.on_event(on_submit)
    widget_ui = mo.ui.anywidget(widget)
    return widget_ui


@app.cell
def cell_layout(event_panel, heading, mo, section, value_panel, widget_ui):
    mo.vstack(
        [
            heading(
                "表单 Form",
                '表单是 layui 最核心的能力之一：控件放在 `class="layui-form"` 容器内被统一装饰，'
                "带 `lay-submit` 的按钮会提交整个表单。",
            ),
            section("综合表单", widget_ui),
            section("当前状态", value_panel(widget_ui), event_panel(widget_ui)),
        ]
    )
    return


if __name__ == "__main__":
    app.run()
