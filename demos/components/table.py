# /// script
# requires-python = ">=3.10"
# dependencies = ["layui-anywidget", "marimo"]
# ///

"""表格 / Table — 对应 layui 文档 ``docs/table/index.md``。"""

import marimo

app = marimo.App(width="medium")


@app.cell
def cell_imports():
    import marimo as mo
    from _shared import event_panel, heading, section, value_panel

    from layui_anywidget import Layui, lay

    ROWS = [
        {"id": 1, "name": "Ada", "city": "London", "score": 98},
        {"id": 2, "name": "Grace", "city": "New York", "score": 95},
        {"id": 3, "name": "Linus", "city": "Helsinki", "score": 91},
        {"id": 4, "name": "Guido", "city": "Amsterdam", "score": 88},
        {"id": 5, "name": "Margaret", "city": "New York", "score": 94},
        {"id": 6, "name": "Alan", "city": "London", "score": 97},
        {"id": 7, "name": "Barbara", "city": "Philadelphia", "score": 93},
        {"id": 8, "name": "Ken", "city": "Boston", "score": 90},
        {"id": 9, "name": "Dennis", "city": "New York", "score": 86},
        {"id": 10, "name": "Bjarne", "city": "Aarhus", "score": 92},
        {"id": 11, "name": "James", "city": "London", "score": 89},
        {"id": 12, "name": "Radia", "city": "New York", "score": 96},
    ]

    return Layui, ROWS, event_panel, heading, lay, mo, section, value_panel


@app.cell
def cell_widget(Layui, ROWS, lay, mo):
    widget = Layui(
        theme="light",
        height="auto",
        schema=[
            lay.table(
                "rows",
                [
                    {"field": "id", "title": "ID", "width": 70, "sort": True},
                    {"field": "name", "title": "姓名"},
                    {"field": "city", "title": "城市"},
                    {"field": "score", "title": "分数", "sort": True},
                ],
                selectable=True,
                page=True,
            ),
            lay.text("勾选行后，选中的行会写入 state.selection："),
        ],
        state={"rows": ROWS, "selection": []},
    )
    widget_ui = mo.ui.anywidget(widget)
    return widget_ui


@app.cell
def cell_layout(event_panel, heading, mo, section, value_panel, widget_ui):
    mo.vstack(
        [
            heading(
                "表格 Table",
                "表格用于展示结构化数据。``lay.table`` 从 state 键读取行数据，"
                "支持排序、分页与多选；行数据变化时表格自动刷新。",
            ),
            section("表格", widget_ui),
            section("当前状态", value_panel(widget_ui, ["selection"]), event_panel(widget_ui)),
        ]
    )
    return


if __name__ == "__main__":
    app.run()
