# /// script
# requires-python = ">=3.10"
# dependencies = ["layui-anywidget", "marimo"]
# ///

"""弹出层 / Layer — 对应 layui 文档 ``docs/layer/index.md``。

``lay.layer`` 渲染一个触发按钮，点击后调用 layui 的 ``layer`` API：
``kind`` 对应文档里的 ``layer.open`` / ``alert`` / ``confirm`` / ``msg`` /
``load`` / ``tips`` / ``prompt``；弹层的确认、取消与输入结果会转发到 Python。
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
def cell_widget(Layui, lay, mo):
    widget = Layui(
        theme="light",
        height="auto",
        schema=[
            lay.title("信息框", level=6),
            lay.div(
                lay.layer("这是一个对话框", trigger="Alert", kind="alert", id="alert"),
                lay.layer(
                    "一个询问框的示例？",
                    trigger="Confirm",
                    kind="confirm",
                    id="confirm",
                    events={"confirm": "layer_confirm", "cancel": "layer_cancel"},
                ),
                lay.layer("一段提示信息", trigger="Msg", kind="msg", id="msg"),
                # 加载层不会自动关闭；auto_close（毫秒）让演示自行收尾。
                lay.layer(
                    "正在加载…",
                    trigger="Load",
                    kind="load",
                    id="load",
                    auto_close=2000,
                ),
                class_="layui-btn-container",
            ),
            lay.title("页面层与贴士", level=6),
            lay.div(
                lay.layer(
                    "<div style='padding: 11px;'>任意 HTML 内容</div>",
                    trigger="Page",
                    kind="dialog",
                    options={"area": ["420px", "240px"], "title": "页面层"},
                    id="page",
                ),
                lay.layer("向上", trigger="Tips 上", kind="tips", options={"tips": 1}),
                lay.layer("默认向右", trigger="Tips 右", kind="tips"),
                lay.layer(
                    "自定义背景色", trigger="Tips 色", kind="tips", options={"tips": [1, "#16b777"]}
                ),
                class_="layui-btn-container",
            ),
            lay.title("输入框层", level=6),
            lay.div(
                lay.layer(
                    "请输入文本",
                    trigger="Prompt",
                    kind="prompt",
                    id="prompt",
                    events={"confirm": "layer_prompt"},
                ),
                lay.layer(
                    "请输入密令",
                    trigger="Prompt 密码",
                    kind="prompt",
                    id="prompt_password",
                    options={"title": "请输入密令", "formType": 1},
                    events={"confirm": "layer_prompt"},
                ),
                lay.layer(
                    "请输入多行文本",
                    trigger="Prompt 多行",
                    kind="prompt",
                    id="prompt_textarea",
                    options={"title": "请输入多行文本", "formType": 2},
                    events={"confirm": "layer_prompt"},
                ),
                class_="layui-btn-container",
            ),
        ],
        state={"layer_event": None, "layer_value": None},
    )
    widget_ui = mo.ui.anywidget(widget)
    return widget, widget_ui


@app.cell
def cell_events(Layui, widget):
    def record(event):
        # Layer layers are appended to document.body; the Python side only
        # sees the forwarded result, so store it for the panel below.
        if event.get("type") != "layer":
            return
        widget.update_values({"layer_event": event.get("event"), "layer_value": event.get("value")})

    # `on_event` returns the callback, and marimo would render that return
    # value as the cell output; discard it.
    _ = widget.on_event(record)
    return


@app.cell
def cell_layout(Layui, heading, mo, section, widget_ui):
    # Read through the anywidget wrapper so marimo re-renders this cell when
    # the event callback updates the widget state.
    state = widget_ui.value.get("state", {})
    last = state.get("layer_event") or "（尚无）"
    value = state.get("layer_value")
    mo.vstack(
        [
            heading(
                "弹出层 Layer",
                "弹出层组件 `layer` 是 Layui 最古老的组件，集众多弹层功能为一体："
                "信息框、询问框、提示框、加载层、贴士层与输入框层。",
            ),
            section("示例", widget_ui),
            section(
                "当前状态",
                mo.md(
                    f"**最近回调**：`{last}`" + (" · " + repr(value) if value is not None else "")
                ),
            ),
        ]
    )
    return


if __name__ == "__main__":
    app.run()
