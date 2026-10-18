# /// script
# requires-python = ">=3.10"
# dependencies = ["layui-anywidget", "marimo"]
# ///

"""复选框 / Checkbox — 对应 layui 文档 ``docs/form/checkbox.md``。

单选框绑定布尔值；``checkbox_group`` 把一组复选框绑定为一个值列表。
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
            # 普通复选框
            lay.form(
                lay.checkbox("subscribe", "订阅更新", label="普通"),
                lay.checkbox("remember", "记住我", label="已勾选"),
                lay.checkbox("disabled_box", "禁用复选", label="禁用", disabled=True),
            ),
            # 原始风格 skin="primary"/默认
            lay.form(
                lay.checkbox("skin_primary", "原始风格", label="skin=primary", skin="primary"),
                lay.checkbox("skin_disabled", "禁用原始", skin="primary", disabled=True),
            ),
            # 复选框组（绑定为列表）
            lay.checkbox_group(
                "skills",
                ["Vue", "React", "Angular", "Svelte"],
                label="技能（多选组）",
            ),
        ],
        state={
            "subscribe": False,
            "remember": True,
            "disabled_box": False,
            "skin_primary": True,
            "skin_disabled": False,
            "skills": ["Vue"],
        },
    )
    widget_ui = mo.ui.anywidget(widget)
    return widget_ui


@app.cell
def cell_layout(event_panel, heading, mo, section, value_panel, widget_ui):
    mo.vstack(
        [
            heading(
                "复选框 Checkbox",
                "复选框通常用于多项选择。通过 `checkbox` 绑定单个布尔值，"
                "通过 `checkbox_group` 把多个选项绑定成一个值列表。",
            ),
            section("复选框", widget_ui),
            section("当前状态", value_panel(widget_ui), event_panel(widget_ui)),
        ]
    )
    return


if __name__ == "__main__":
    app.run()
