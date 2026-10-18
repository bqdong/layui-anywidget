# /// script
# requires-python = ">=3.10"
# dependencies = ["layui-anywidget", "marimo"]
# ///

"""栅格布局 / Grid — 对应 layui 文档 ``docs/layout/grid.md``。

``lay.row`` / ``lay.col`` 输出 layui 的 ``layui-row`` / ``layui-col-*`` 类：
一行分 12 列，可组合 ``xs``/``sm``/``md``/``lg``/``xl`` 适配不同屏幕，
并用 ``gap``/``offset`` 控制列间距与偏移。
"""

import marimo

app = marimo.App(width="medium")


@app.cell
def cell_imports():
    import marimo as mo
    from _shared import heading, section

    from layui_anywidget import Layui, lay

    return Layui, heading, lay, mo, section


@app.cell
def cell_widget(Layui, lay):
    def cell(text: str, color: str | None = None, **sizes):
        """One grid column with a visible background, as in the docs examples."""
        return lay.col(
            lay.div(
                text,
                style={
                    "padding": "10px 0",
                    "font-size": "13px",
                    "text-align": "center",
                    "color": "#fff" if color else "inherit",
                    "background": color or "#f2f2f2",
                    "border-radius": "2px",
                },
            ),
            **sizes,
        )

    widget = Layui(
        theme="light",
        height="auto",
        schema=[
            # 常规布局：12 等分
            lay.title("12 等分", level=6),
            lay.row(cell("6/12", "#16b777", md=6), cell("6/12", md=6)),
            lay.row(*[cell(f"{i}/12", md=1) for i in range(1, 13)]),
            lay.row(
                cell("4/12", "#16b777", md=4),
                cell("4/12", "#1e9fff", md=4),
                cell("4/12", md=4),
            ),
            # 列间隔
            lay.title("列间隔（gap=15）", level=6),
            lay.row(
                cell("1/4", "#16b777", md=3),
                cell("1/4", md=3),
                cell("1/4", "#16b777", md=3),
                cell("1/4", md=3),
                gap=15,
            ),
            # 列偏移
            lay.title("列偏移", level=6),
            lay.row(
                cell("4/12", "#16b777", md=4),
                cell("偏移 4 列", "#1e9fff", md=4, offset=4),
            ),
            # 响应式：手机堆叠，桌面并排
            lay.title("响应式（xs:12 | md:6）", level=6),
            lay.row(
                cell("xs:12 | md:6", "#16b777", xs=12, md=6),
                cell("xs:12 | md:6", "#1e9fff", xs=12, md=6),
            ),
            # 栅格嵌套
            lay.title("栅格嵌套", level=6),
            lay.row(
                lay.col(
                    lay.row(
                        cell("内部 4", "#16b777", md=4),
                        cell("内部 8", md=8),
                    ),
                    md=6,
                ),
                cell("外层 6", "#1e9fff", md=6),
            ),
        ],
        state={},
    )
    return widget


@app.cell
def cell_layout(heading, mo, section, widget):
    mo.vstack(
        [
            heading(
                "栅格布局 Grid",
                "Layui 栅格是一套响应式布局方案，采用容器横向 `12` 等分规则，"
                "预设了 `xs`/`sm`/`md`/`lg`/`xl` 五组断点类，"
                "一套系统即可适配桌面、平板与手机。",
            ),
            section("示例", widget),
        ]
    )
    return


if __name__ == "__main__":
    app.run()
