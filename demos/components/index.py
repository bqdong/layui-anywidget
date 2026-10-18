# /// script
# requires-python = ">=3.10"
# dependencies = ["layui-anywidget", "marimo"]
# ///
"""组件示例索引 — 按 layui 文档的组件分类列出每个演示页面。

每个 ``demos/components/<组件>.py`` 都是一个独立的 marimo 应用，结构与
layui 2.x 文档页一致：标题 → 引言 → 各功能的 ``<h2>`` 段落 → 当前值面板。
"""

import marimo

app = marimo.App(width="medium")


@app.cell
def cell_imports():
    import marimo as mo

    return (mo,)


@app.cell
def cell_index(mo):
    groups = [
        ("布局", ["layout"]),
        ("表单", ["input", "select", "checkbox", "radio", "switch", "form"]),
        ("展示", ["table", "laypage", "menu", "tabs", "collapse", "progress", "badge"]),
        (
            "交互",
            ["layer", "dropdown", "datepicker", "colorpicker", "slider", "rate", "carousel"],
        ),
        ("按钮", ["button"]),
        ("其他", ["breadcrumb"]),
    ]
    blocks = []
    for title, names in groups:
        items = "\n".join(
            f"- [`{name}.py`](./{name}.py) · 运行："
            f"`uv run marimo run --no-sandbox demos/components/{name}.py`"
            for name in names
        )
        blocks.append(mo.md(f"### {title}\n{items}"))
    mo.vstack([mo.md("# layui 组件示例"), *blocks])
    return


if __name__ == "__main__":
    app.run()
