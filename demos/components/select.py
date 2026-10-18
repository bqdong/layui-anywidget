# /// script
# requires-python = ">=3.10"
# dependencies = ["layui-anywidget", "marimo"]
# ///

"""选择框 / Select — 对应 layui 文档 ``docs/form/select.md``。

``lay.select`` 生成 layui 的下拉选择；``multiple=True`` 时保留原生多选
（layui 的装饰版本不支持多选），``search=True`` 开启输入搜索。
"""

import marimo

app = marimo.App(width="medium")


@app.cell
def cell_imports():
    import marimo as mo
    from _shared import event_panel, heading, section, value_panel

    from layui_anywidget import Layui, lay

    cities = ["北京", "上海", "广州", "深圳", "杭州", "成都", "武汉", "西安"]
    city_options = [
        ("北京", "beijing"),
        ("上海", "shanghai"),
        ("广州", "guangzhou"),
        ("深圳", "shenzhen"),
        ("杭州", "hangzhou"),
        ("成都", "chengdu"),
    ]
    return Layui, cities, city_options, event_panel, heading, lay, mo, section, value_panel


@app.cell
def cell_widget(Layui, cities, city_options, lay, mo):
    widget = Layui(
        theme="light",
        height="auto",
        schema=[
            # 基础选择框：值可以是 (label, value)
            lay.form(
                lay.select("city", city_options, label="城市"),
            ),
            # 搜索选择框
            lay.form(
                lay.select("search_city", cities, label="搜索选择", search=True),
            ),
            # 多选
            lay.form(
                lay.select(
                    "tags",
                    ["Python", "JavaScript", "Rust", "Go", "TypeScript"],
                    label="语言（多选）",
                    multiple=True,
                ),
            ),
            # 禁用：用 lay-ignore 保留原生控件（原生 select 的禁用由浏览器处理）
            lay.form(
                lay.select("locked", cities, label="禁用", ignore=True, disabled=True),
            ),
        ],
        state={
            "city": "shanghai",
            "search_city": "杭州",
            "tags": ["Python"],
            "locked": "beijing",
        },
    )
    widget_ui = mo.ui.anywidget(widget)
    return widget_ui


@app.cell
def cell_layout(event_panel, heading, mo, section, value_panel, widget_ui):
    mo.vstack(
        [
            heading(
                "选择框 Select",
                "选择框是表单中常见的元素，layui 会将原生 `select` 渲染为可定制的下拉框，"
                "支持搜索、多选（原生控件）与禁用状态。",
            ),
            section("基础与搜索选择", widget_ui),
            section("当前状态", value_panel(widget_ui), event_panel(widget_ui)),
        ]
    )
    return


if __name__ == "__main__":
    app.run()
