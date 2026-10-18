# /// script
# requires-python = ">=3.10"
# dependencies = ["layui-anywidget", "marimo"]
# ///

"""Gallery of every layui component supported by layui-anywidget.

The top widget is a single ``Layui`` container with one section per
component.  Below it, a live JSON panel shows the widget's current
``state`` (every interactive component is bound to a key), and a second
panel shows the latest forwarded event.  Change anything above and both
update on the Python side.

Run with ``just demo-gallery`` (or ``marimo run --no-sandbox demos/gallery.py``).
"""

import marimo

app = marimo.App(width="full")


@app.cell
def __():
    import marimo as mo

    from layui_anywidget import Layui, lay

    return Layui, lay, mo


@app.cell
def __(Layui, lay, mo):
    def section(title, *children):
        return lay.div(
            lay.title(title, 3, style={"margin": "32px 0 16px"}),
            *children,
            style={"border-top": "1px solid #eee", "padding-top": "8px"},
        )

    gallery = Layui(
        theme="light",
        height="auto",
        schema=[
            section(
                "表单控件 / Form controls",
                lay.form(
                    lay.input("text", label="单行文本", placeholder="请输入姓名"),
                    lay.textarea("bio", label="多行文本", placeholder="介绍一下自己"),
                    lay.input_number("count", label="数字 (0–100)", min_value=0, max_value=100),
                    lay.select(
                        "city",
                        [
                            ("北京", "beijing"),
                            ("上海", "shanghai"),
                            ("广州", "guangzhou"),
                            ("深圳", "shenzhen"),
                        ],
                        label="下拉选择",
                    ),
                    lay.select(
                        "tags",
                        ["Python", "JavaScript", "Rust", "Go"],
                        label="多选 (multiple)",
                        multiple=True,
                    ),
                    lay.select(
                        "search_city",
                        ["北京", "上海", "广州", "深圳", "杭州", "成都"],
                        label="搜索选择 (lay-search)",
                        search=True,
                    ),
                    lay.radio(
                        "plan",
                        [("免费版", "free"), ("专业版", "pro"), ("团队版", "team")],
                        label="单选框",
                    ),
                    lay.checkbox("subscribe", "订阅更新", label="复选框"),
                    lay.switch("notify", label="开关", text="开|关"),
                    lay.slider("volume", label="滑块", min_value=0, max_value=100, step=5),
                    lay.slider(
                        "price_range",
                        label="区间滑块",
                        min_value=0,
                        max_value=1000,
                        step=100,
                        range=True,
                    ),
                    lay.colorpicker("color", label="颜色选择器", predefine=True),
                    lay.datepicker("date", label="日期选择"),
                    lay.datepicker("datetime", label="日期时间", type="datetime"),
                    lay.rate("score", label="评分", max_value=5),
                ),
            ),
            section(
                "按钮 / Buttons",
                lay.div(
                    lay.button("默认按钮", id="btn-default"),
                    lay.button("原始按钮", theme="primary", id="btn-primary"),
                    lay.button("危险按钮", theme="danger", id="btn-danger"),
                    lay.button("禁用按钮", id="btn-disabled", disabled=True),
                    lay.button("正常", theme="normal", id="btn-normal"),
                    lay.button("暖色", theme="warm", id="btn-warm"),
                    lay.button("圆角", class_="layui-btn-radius", id="btn-round"),
                    lay.button("小号", class_="layui-btn-sm", id="btn-sm"),
                    lay.badge("徽章", color="#1e9fff"),
                    lay.badge("危险", color="#ff5722"),
                    style={
                        "display": "flex",
                        "gap": "8px",
                        "flex-wrap": "wrap",
                        "align-items": "center",
                    },
                ),
                lay.text(
                    "每个按钮（除禁用外）都绑定了 click 事件；点击后"
                    "“当前值”面板中的 last_button / button_counts 会更新。",
                    style={"color": "#5f6368"},
                ),
            ),
            section(
                "选项卡 / Tabs",
                lay.tabs(
                    lay.tab(
                        "用户",
                        lay.input("tab_user", label="用户名"),
                        id="user",
                    ),
                    lay.tab(
                        "设置",
                        lay.switch("tab_setting", label="启用"),
                        id="settings",
                    ),
                    lay.tab("关于", lay.text("layui-anywidget 组件示例"), id="about"),
                    model="active_tab",
                ),
            ),
            section(
                "折叠面板 / Collapse",
                lay.collapse(
                    lay.collapse_item(
                        "面板一",
                        lay.text("第一个折叠面板的内容。"),
                        open=True,
                    ),
                    lay.collapse_item("面板二", lay.text("第二个折叠面板的内容。")),
                    lay.collapse_item(
                        "面板三（含交互控件）",
                        lay.checkbox("collapse_flag", "点击复选框", label=None),
                        lay.input("collapse_text", label="备注"),
                    ),
                ),
            ),
            section(
                "下拉菜单 / Dropdown",
                lay.dropdown(
                    lay.span("下拉菜单", class_="layui-btn layui-btn-primary"),
                    [
                        {"title": "选项一", "id": "item1"},
                        {"title": "选项二", "id": "item2"},
                        {"type": "divider"},
                        {"title": "选项三", "id": "item3"},
                    ],
                    id="dropdown",
                    updates={"click": "dropdown_choice"},
                ),
            ),
            section(
                "提示 / Layer",
                lay.div(
                    lay.button(
                        "点我提示",
                        id="alert-btn",
                        class_="layui-btn layui-btn-primary",
                        events={"click": "alert"},
                    ),
                    lay.div(
                        lay.span(
                            "按钮点击会弹出 layer 提示；事件与当前值会同步到页面底部的面板。",
                            style={"color": "#5f6368"},
                        )
                    ),
                ),
            ),
            section(
                "进度条 / Progress",
                # The first bar follows the slider directly: 0–100 with the
                # same state key. A derived-copy approach (writing another key
                # from `on_change`) races with the browser's whole-state
                # writes and can end up one step behind.
                lay.progress("progress_value", show_percent=True),
                lay.progress("progress2", show_percent=True, class_="layui-progress-big"),
                lay.slider("progress_value", label="调整进度", min_value=0, max_value=100, step=10),
            ),
            section(
                "导航 / Menu",
                lay.menu(
                    [
                        {"title": "首页", "id": "home"},
                        {
                            "title": "产品",
                            "id": "product",
                            "children": [
                                {"title": "产品一", "id": "p1"},
                                {"title": "产品二", "id": "p2"},
                            ],
                        },
                        {"title": "关于", "id": "about"},
                    ],
                    model="active_menu",
                ),
            ),
            section(
                "面包屑 / Breadcrumb",
                lay.breadcrumb(["首页", "组件", "面包屑"]),
            ),
            section(
                "轮播 / Carousel",
                lay.carousel(
                    *[
                        lay.div(
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
                        for index, color in enumerate(["#16baaa", "#1e9fff", "#ffb800"], 1)
                    ],
                    model="carousel_index",
                    height="180px",
                    autoplay=False,
                ),
            ),
            section(
                "分页 / Laypage（下方表格自带分页；此处为独立分页组件）",
                lay.laypage(120, page_key="page", limit=10),
            ),
            section(
                "表格 / Table",
                lay.table(
                    "rows",
                    [
                        {"field": "id", "title": "ID", "width": 80, "sort": True},
                        {"field": "name", "title": "姓名"},
                        {
                            "field": "score",
                            "title": "分数",
                            "sort": True,
                        },
                    ],
                    selectable=True,
                    page=True,
                ),
            ),
        ],
        state={
            "text": "Ada Lovelace",
            "bio": "第一个程序员",
            "count": 42,
            "city": "shanghai",
            "tags": ["Python", "Rust"],
            "search_city": "hangzhou",
            "plan": "pro",
            "subscribe": True,
            "notify": True,
            "volume": 60,
            "price_range": [200, 800],
            "color": "#16baaa",
            "date": "2026-10-17",
            "datetime": "2026-10-17 20:00:00",
            "score": 4,
            "tab_user": "ada",
            "tab_setting": True,
            "active_tab": "user",
            "collapse_flag": True,
            "collapse_text": "",
            "progress2": 30,
            "progress_value": 60,
            "active_menu": "home",
            "carousel_index": 0,
            "page": 1,
            "rows": [
                {"id": 1, "name": "Ada", "score": 98},
                {"id": 2, "name": "Grace", "score": 95},
                {"id": 3, "name": "Linus", "score": 91},
                {"id": 4, "name": "Guido", "score": 88},
                {"id": 5, "name": "Margaret", "score": 94},
            ],
            "selection": [],
            "dropdown_choice": None,
            "alert_count": 0,
            "last_button": None,
            "button_counts": {},
        },
    )
    widget = mo.ui.anywidget(gallery)
    return gallery, mo, section, widget


@app.cell
def __(gallery, mo):
    def track_button(event):
        # Every button forwards `click` by default; record which one fired so
        # the live panel can prove the binding works.
        if event.get("type") != "button" or not event.get("id"):
            return
        button_id = event["id"]
        counts = dict(gallery.state.get("button_counts", {}))
        counts[button_id] = counts.get(button_id, 0) + 1
        gallery.update_values({"last_button": button_id, "button_counts": counts})

    def show_alert(event):
        if event.get("event") == "alert":
            count = gallery.state.get("alert_count", 0) + 1
            gallery.update_values({"alert_count": count})
            mo.output.append(mo.md(f"收到第 {count} 次 `alert` 事件（按钮 id=`alert-btn`）"))

    gallery.on_event(track_button)
    gallery.on_event(show_alert)
    return


@app.cell
def __(widget):
    import json

    state = widget.value.get("state", {})
    live = {key: value for key, value in sorted(state.items()) if key != "rows"}
    live["rows"] = f"{len(state.get('rows', []))} 行"
    return json, live


@app.cell
def __(widget, mo):
    event = widget.value.get("event", {})
    recent = (
        f"`{event.get('event')}` · `{event.get('type')}` · `{event.get('id')}` = "
        f"`{event.get('value')}`"
        if event
        else "（尚无事件）"
    )
    return recent


@app.cell
def __(json, live, mo, recent, widget):
    mo.vstack(
        [
            widget,
            mo.md("## 当前值"),
            mo.md("每个交互组件都绑定到一个状态键，下面是 Python 端实时看到的 `state`："),
            mo.md(f"```json\n{json.dumps(live, ensure_ascii=False, indent=2)}\n```"),
            mo.md(f"**最近事件**：{recent}"),
        ]
    )
    return


if __name__ == "__main__":
    app.run()
