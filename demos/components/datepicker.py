# /// script
# requires-python = ">=3.10"
# dependencies = ["layui-anywidget", "marimo"]
# ///

"""日期与时间选择 / Laydate — 对应 layui 文档 ``docs/laydate/index.md``。"""

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
                lay.datepicker("date", label="选择日"),
                lay.datepicker("datetime", label="日期时间", type="datetime"),
                lay.datepicker("year", label="选择年", type="year"),
                lay.datepicker("month", label="选择月", type="month"),
                lay.datepicker(
                    "range",
                    label="日期范围",
                    range="~",
                ),
                lay.datepicker(
                    "bounded",
                    label="限定区间",
                    min_value="2026-10-01",
                    max_value="2026-12-31",
                ),
            ),
        ],
        state={
            "date": "2026-10-18",
            "datetime": "2026-10-18 20:00:00",
            "year": "2026",
            "month": "2026-10",
            "range": "",
            "bounded": "2026-10-18",
        },
    )
    widget_ui = mo.ui.anywidget(widget)
    return widget_ui


@app.cell
def cell_layout(event_panel, heading, mo, section, value_panel, widget_ui):
    mo.vstack(
        [
            heading(
                "日期与时间选择 Laydate",
                "laydate 提供年、月、日、时间与范围选择，支持格式、最小/最大日期等约束。"
                "选择结果会同步到 state。",
            ),
            section("日期与时间选择", widget_ui),
            section("当前状态", value_panel(widget_ui), event_panel(widget_ui)),
        ]
    )
    return


if __name__ == "__main__":
    app.run()
