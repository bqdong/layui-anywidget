# /// script
# requires-python = ">=3.10"
# dependencies = ["layui-anywidget", "marimo"]
# ///
"""徽章 / Badge — 对应 layui 文档 ``docs/badge/index.md``。"""

import marimo

app = marimo.App(width="medium")


@app.cell
def cell_imports():
    import marimo as mo
    from _shared import heading, section

    from layui_anywidget import Layui, lay

    return Layui, heading, lay, mo, section


@app.cell
def cell_widget(Layui, lay, mo):
    widget = Layui(
        theme="light",
        height="auto",
        schema=[
            lay.div(
                lay.badge("默认"),
                lay.badge("绿色", color="#16b777"),
                lay.badge("蓝色", color="#1e9fff"),
                lay.badge("橙色", color="#ffb800"),
                lay.badge("红色", color="#ff5722"),
                style={"display": "flex", "gap": "8px", "flex-wrap": "wrap"},
            ),
            lay.div(
                lay.span("消息", class_="layui-text"),
                lay.span(" ", class_="layui-badge"),
                lay.span("角标", class_="layui-text"),
                lay.span("3", class_="layui-badge-dot"),
                lay.span("点点", class_="layui-text"),
                lay.span("2", class_="layui-badge-rim"),
                style={"display": "inline-flex", "gap": "4px", "align-items": "center"},
            ),
        ],
        state={},
    )
    widget_ui = mo.ui.anywidget(widget)
    return widget_ui


@app.cell
def cell_layout(heading, mo, section, widget_ui):
    mo.vstack(
        [
            heading(
                "徽章 Badge",
                "徽章用于标记数量或状态。``lay.badge`` 生成一个徽章，颜色通过 "
                "``color`` 指定（写入 layui 的 ``lay-badge-color`` 属性）。",
            ),
            section("徽章", widget_ui),
        ]
    )
    return


if __name__ == "__main__":
    app.run()
