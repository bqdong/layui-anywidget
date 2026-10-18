# /// script
# requires-python = ">=3.10"
# dependencies = ["layui-anywidget", "marimo"]
# ///

"""轮播 / Carousel — 对应 layui 文档 ``docs/carousel/index.md``。"""

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
    def slide(index: int, color: str):
        return lay.div(
            lay.span(
                f"第 {index} 页",
                style={"font-size": "32px", "font-weight": "600"},
            ),
            style={
                "display": "flex",
                "align-items": "center",
                "justify-content": "center",
                "height": "100%",
                "background": color,
                "color": "#fff",
            },
        )

    widget = Layui(
        theme="light",
        height="auto",
        schema=[
            lay.carousel(
                slide(1, "#16baaa"),
                slide(2, "#1e9fff"),
                slide(3, "#ffb800"),
                model="index",
                height="180px",
                autoplay=False,
            ),
            lay.carousel(
                slide(1, "#393d49"),
                slide(2, "#ff5722"),
                model="index_auto",
                height="140px",
                autoplay=True,
                interval=2000,
                anim="fade",
            ),
            lay.text("切换轮播时索引写入 state："),
        ],
        state={"index": 0, "index_auto": 0},
    )
    widget_ui = mo.ui.anywidget(widget)
    return widget_ui


@app.cell
def cell_layout(event_panel, heading, mo, section, value_panel, widget_ui):
    mo.vstack(
        [
            heading(
                "轮播 Carousel",
                "轮播用于循环展示多组内容。支持自动播放、淡入淡出动画与指示器；"
                "当前页索引会同步到 state。",
            ),
            section("轮播", widget_ui),
            section("当前状态", value_panel(widget_ui), event_panel(widget_ui)),
        ]
    )
    return


if __name__ == "__main__":
    app.run()
