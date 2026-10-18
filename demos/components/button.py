# /// script
# requires-python = ">=3.10"
# dependencies = ["layui-anywidget", "marimo"]
# ///

"""按钮 / Button — 对应 layui 文档 ``docs/button/index.md``。

向任意标签设定 ``class="layui-btn"`` 建立按钮；这里用 ``lay.button`` 生成同样的
标记，并把每次点击转发到 Python（``Layui.on_event``）。
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
            lay.div(
                # 按钮主题
                lay.div(
                    lay.button("默认按钮", id="theme-default"),
                    lay.button("蓝色按钮", class_="layui-bg-blue", id="theme-blue"),
                    lay.button("橙色按钮", class_="layui-bg-orange", id="theme-orange"),
                    lay.button("红色按钮", class_="layui-bg-red", id="theme-red"),
                    lay.button("紫色按钮", class_="layui-bg-purple", id="theme-purple"),
                    lay.button("禁用按钮", disabled=True, id="theme-disabled"),
                    class_="layui-btn-container",
                ),
                lay.div(
                    lay.button(
                        "主色按钮",
                        theme="primary",
                        class_="layui-border-green",
                        id="border-green",
                    ),
                    lay.button(
                        "普通按钮",
                        theme="primary",
                        class_="layui-border",
                        id="border-plain",
                    ),
                    class_="layui-btn-container",
                ),
            ),
            # 按钮尺寸
            lay.div(
                lay.button("大型按钮", class_="layui-btn-lg", id="size-lg"),
                lay.button("默认按钮", id="size-default"),
                lay.button("小型按钮", class_="layui-btn-sm", id="size-sm"),
                lay.button("迷你按钮", class_="layui-btn-xs", id="size-xs"),
                lay.button(
                    "流体按钮（宽度自适应）",
                    class_="layui-btn-fluid",
                    id="size-fluid",
                ),
                class_="layui-btn-container",
            ),
            # 按钮圆角
            lay.div(
                lay.button(
                    "原始按钮", theme="primary", class_="layui-btn-radius", id="radius-primary"
                ),
                lay.button("默认按钮", class_="layui-btn-radius", id="radius-default"),
                lay.button(
                    "百搭按钮", theme="normal", class_="layui-btn-radius", id="radius-normal"
                ),
                lay.button("暖色按钮", theme="warm", class_="layui-btn-radius", id="radius-warm"),
                lay.button(
                    "警告按钮", theme="danger", class_="layui-btn-radius", id="radius-danger"
                ),
                class_="layui-btn-container",
            ),
            # 按钮图标（图标用 HTML 片段插入）
            lay.div(
                lay.button(
                    "按钮",
                    id="icon-down",
                    class_="layui-btn",
                    html='按钮 <i class="layui-icon layui-icon-down layui-font-12"></i>',
                ),
                lay.button(
                    "",
                    id="icon-left",
                    html='<i class="layui-icon layui-icon-left"></i>',
                ),
                lay.button(
                    "",
                    id="icon-edit",
                    html='<i class="layui-icon layui-icon-edit"></i>',
                ),
                lay.button(
                    "",
                    id="icon-share",
                    html='<i class="layui-icon layui-icon-share"></i>',
                ),
                class_="layui-btn-container",
            ),
            # 按钮组合
            lay.div(
                lay.button("增加", id="group-add"),
                lay.button("编辑", id="group-edit"),
                lay.button("删除", theme="danger", id="group-delete"),
                class_="layui-btn-group",
            ),
            # 按钮容器（纯展示）
            lay.div(
                lay.button("按钮一", id="container-1"),
                lay.button("按钮二", id="container-2"),
                lay.button("按钮三", id="container-3"),
                class_="layui-btn-container",
            ),
        ],
        state={
            "last_button": None,
            "button_counts": {},
            "click_payload": None,
        },
    )

    def track(event):
        # 每个 button 默认转发 click；id 为空（如禁用按钮不会触发）时忽略。
        if event.get("type") != "button" or not event.get("id"):
            return
        button_id = event["id"]
        counts = dict(widget.state.get("button_counts", {}))
        counts[button_id] = counts.get(button_id, 0) + 1
        widget.update_values(
            {
                "last_button": button_id,
                "button_counts": counts,
                "click_payload": event.get("raw"),
            }
        )

    widget.on_event(track)
    widget_ui = mo.ui.anywidget(widget)
    return widget, widget_ui


@app.cell
def cell_events(event_panel, heading, mo, section, value_panel, widget_ui):
    mo.vstack(
        [
            heading(
                "按钮 Button",
                '向任意 `HTML` 标签设定 `class="layui-btn"` 建立一个基础按钮。'
                "通过追加格式为 `layui-btn-{type}` 的 `class` 来定义其它按钮风格。"
                "内置的按钮 `class` 可以进行任意组合，从而形成更多种按钮风格。",
            ),
            section("按钮主题", widget_ui),
            section(
                "当前状态",
                value_panel(widget_ui, ["last_button", "button_counts", "click_payload"]),
                event_panel(widget_ui),
            ),
        ]
    )
    return


if __name__ == "__main__":
    app.run()
