# /// script
# requires-python = ">=3.10"
# dependencies = ["layui-anywidget", "marimo"]
# ///

"""评分 / Rate — 对应 layui 文档 ``docs/rate/index.md``。"""

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
            lay.rate("score", label="评分", max_value=5),
            lay.rate("score_half", label="半星", max_value=5, half=True),
            lay.rate("score_text", label="显示文字", max_value=5, text=True),
            lay.rate("score_readonly", label="只读", max_value=5, readonly=True),
        ],
        state={
            "score": 4,
            "score_half": 3.5,
            "score_text": 3,
            "score_readonly": 5,
        },
    )
    widget_ui = mo.ui.anywidget(widget)
    return widget_ui


@app.cell
def cell_layout(event_panel, heading, mo, section, value_panel, widget_ui):
    mo.vstack(
        [
            heading(
                "评分 Rate",
                "评分组件用于快速打分。支持半星、文字提示、只读与自定义主题色。",
            ),
            section("评分", widget_ui),
            section("当前状态", value_panel(widget_ui), event_panel(widget_ui)),
        ]
    )
    return


if __name__ == "__main__":
    app.run()
