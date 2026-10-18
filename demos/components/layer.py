# /// script
# requires-python = ">=3.10"
# dependencies = ["layui-anywidget", "marimo"]
# ///

"""弹出层 / Layer — 对应 layui 文档 ``docs/layer/index.md`` 的全部示例。

``lay.layer`` 渲染一个触发按钮，点击后调用 layui 的 ``layer`` API。文档里的
每个示例（弹层类型、信息框、页面层、iframe、加载层、Tips、其他、异步按钮、
位置、方向、主题、更多）在这里都有对应按钮；确认、取消、输入、按钮与关闭
的结果会转发到 Python。
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
    PHOTOS = [
        {"src": "https://unpkg.com/outeres@0.1.1/demo/layer.png", "alt": "layer", "pid": 1},
        {"src": "https://unpkg.com/outeres@0.1.1/demo/000.jpg", "alt": "壁纸", "pid": 3},
        {
            "src": "https://unpkg.com/outeres@0.1.1/demo/outer-space.jpg",
            "alt": "浩瀚宇宙",
            "pid": 5,
        },
    ]

    def bar(*buttons):
        return lay.div(*buttons, class_="layui-btn-container")

    def icon_stage(icon):
        # 文档的图标轮播：点击确定后 icon + 1，走完 0-6 再给一条提示。
        if icon > 6:
            return {"kind": "msg", "content": "内置图标演示完毕", "options": {"icon": 1}}
        return {
            "kind": "alert",
            "content": "对话框图标依次演示",
            "options": {"icon": icon, "shade_close": True, "title": f"icon: {icon}"},
            "next": icon_stage(icon + 1),
        }

    widget = Layui(
        theme="light",
        height="auto",
        schema=[
            # --- 弹层类型（type.md） -----------------------------------------
            lay.title("弹层类型", level=3),
            bar(
                lay.layer("对话框内容", trigger="Alert", kind="alert", id="type-alert"),
                lay.layer(
                    "一个询问框的示例？",
                    trigger="Confirm",
                    kind="confirm",
                    btns=["确定", "关闭"],
                    id="type-confirm",
                    events={"confirm": "confirm", "cancel": "cancel", "button": "button"},
                    next=lay.layer("第一个回调", kind="msg", options={"icon": 1}),
                    next_cancel=lay.layer(
                        "第二个回调",
                        kind="msg",
                        options={"time": 20000},
                        btns=["明白了", "知道了"],
                    ),
                ),
                lay.layer("一段提示信息", trigger="Msg", kind="msg", id="type-msg"),
                lay.layer(
                    "<div style='padding: 11px;'>任意 HTML 内容</div>",
                    trigger="Page",
                    kind="dialog",
                    options={"area": ["420px", "240px"]},
                    id="type-page",
                ),
                lay.layer(
                    "https://www.layui.dev/",
                    trigger="Iframe",
                    kind="iframe",
                    title="iframe test",
                    options={"area": ["380px", "80%"], "shade_close": True},
                    id="type-iframe",
                ),
                lay.layer(
                    "正在加载…",
                    trigger="Load",
                    kind="load",
                    auto_close=3000,
                    id="type-load",
                ),
                lay.layer("一个 tips 层", trigger="Tips", kind="tips", options={"tips": 1}),
                lay.layer(
                    "密令输入框",
                    trigger="Prompt",
                    kind="prompt",
                    options={"formType": 1},
                    id="type-prompt",
                    events={"confirm": "prompt"},
                ),
                lay.layer(trigger="Photos", kind="photos", photos=PHOTOS, id="type-photos"),
            ),
            # --- 信息框（alert.md） -----------------------------------------
            lay.title("信息框", level=3),
            bar(
                lay.layer(
                    "对话框图标依次演示",
                    trigger="对话框带图标",
                    kind="alert",
                    id="alert-icon",
                    options={"icon": 0, "shade_close": True, "title": "icon: 0"},
                    next=icon_stage(1),
                ),
                lay.layer(
                    "一个询问框的示例？",
                    trigger="询问框",
                    kind="confirm",
                    id="alert-confirm",
                    options={"icon": 3},
                    events={"confirm": "confirm", "cancel": "cancel"},
                    next=lay.layer("点击确定的回调", kind="msg", options={"icon": 1}),
                    next_cancel=lay.layer("点击取消的回调", kind="msg"),
                ),
                lay.layer("深色提示框的示例", trigger="深色提示框", kind="msg", id="msg-dark"),
                lay.layer(
                    "浅色提示框的示例",
                    trigger="浅色提示框",
                    kind="msg",
                    options={"icon": 0},
                    id="msg-light",
                ),
                lay.layer(
                    "自定义按钮",
                    trigger="自定义按钮",
                    kind="alert",
                    btns=["按钮一", "按钮二", "按钮三"],
                    options={"btn_align": "c"},
                    id="alert-btns",
                    events={"button": "button"},
                ),
                lay.layer(
                    "在标题栏显示自动关闭倒计秒数",
                    trigger="关闭倒计时",
                    kind="alert",
                    countdown=True,
                    options={"time": 5000},
                    id="alert-countdown",
                ),
            ),
            # --- 页面层（page.md） -----------------------------------------
            lay.title("页面层", level=3),
            bar(
                lay.layer(
                    "<div style='padding: 16px;'>任意 HTML 内容</div>",
                    trigger="普通页面层",
                    kind="dialog",
                    id="page-basic",
                ),
                lay.layer(
                    trigger="捕获层",
                    kind="dialog",
                    capture=lay.div(
                        lay.div(
                            "弹出已经存在于页面中的一段元素",
                            style={"padding": "16px"},
                        )
                    ),
                    title="捕获层",
                    options={"shade": False},
                    id="page-capture",
                ),
                lay.layer(
                    "<div style='padding: 16px;'>任意 HTML 内容。可点击遮罩区域关闭。</div>",
                    trigger="剔除默认标题栏",
                    kind="dialog",
                    title=False,
                    options={"area": ["420px", "240px"], "closeBtn": 0, "shade_close": True},
                    id="page-titleless",
                ),
                lay.layer(
                    "<div style='padding: 11px;'>任意 HTML 内容"
                    "<div style='padding: 16px 0;'>"
                    "<button class='layui-btn' id='ID-test-layer-move'>拖拽此处移动弹层</button>"
                    "</div></div>",
                    trigger="绑定拖拽元素",
                    kind="dialog",
                    title=False,
                    options={"area": ["420px", "240px"], "move": "#ID-test-layer-move"},
                    id="page-move",
                ),
                lay.layer(
                    "<div class='layui-form' lay-filter='filter-test-layer' style='margin: 16px;'>"
                    "<div class='layui-form-item'>"
                    "<input type='text' name='username' placeholder='用户名'"
                    " class='layui-input'>"
                    "</div>"
                    "<div class='layui-form-item'>"
                    "<input type='password' name='password' placeholder='密码'"
                    " class='layui-input'>"
                    "</div>"
                    "<div class='layui-form-item'>"
                    "<input type='checkbox' name='remember' lay-skin='primary'"
                    " title='记住密码'>"
                    "</div>"
                    "<div class='layui-form-item'>"
                    "<button class='layui-btn layui-btn-fluid' lay-submit>登录</button>"
                    "</div></div>",
                    trigger="弹出任意自定义内容",
                    kind="dialog",
                    title="demo : layer + form",
                    options={"area": "350px", "resize": False, "shade_close": True},
                    events={"submit": "submit"},
                    id="page-custom",
                ),
            ),
            # --- iframe 层（iframe.md） ------------------------------------
            lay.title("iframe 层", level=3),
            bar(
                lay.layer(
                    "https://www.layui.dev/",
                    trigger="iframe 父子操作",
                    kind="iframe",
                    options={"area": ["680px", "520px"], "maxmin": True, "shade_close": True},
                    id="iframe-handle",
                ),
                lay.layer(
                    "https://player.youku.com/embed/XMzI1NjQyMzkwNA==",
                    trigger="弹出多媒体",
                    kind="iframe",
                    title=False,
                    options={
                        "area": ["630px", "360px"],
                        "shade": 0.8,
                        "closeBtn": 0,
                        "shade_close": True,
                    },
                    id="iframe-video",
                ),
                lay.layer(
                    ["https://www.layui.dev/", "no"],
                    trigger="禁止 iframe 滚动条",
                    kind="iframe",
                    options={"area": ["360px", "500px"], "skin": "layui-layer-rim"},
                    id="iframe-overflow",
                ),
                lay.layer(
                    "https://www.layui.dev/docs/2/",
                    trigger="弹出任意 URL 页面",
                    kind="iframe",
                    title="iframe 任意 URL",
                    options={"area": ["900px", "600px"], "maxmin": True, "shade_close": True},
                    id="iframe-url",
                ),
            ),
            # --- 加载层（load.md） -----------------------------------------
            lay.title("加载层", level=3),
            lay.text("每个 loading 示例均在 3 秒后自动模拟关闭。"),
            bar(
                lay.layer(trigger="风格1", kind="load", auto_close=3000, options={"icon": 0}),
                lay.layer(trigger="风格2", kind="load", auto_close=3000, options={"icon": 1}),
                lay.layer(trigger="风格3", kind="load", auto_close=3000, options={"icon": 2}),
                lay.layer(
                    "加载中",
                    trigger="风格4",
                    kind="msg",
                    auto_close=3000,
                    options={"icon": 16, "shade": 0.01},
                ),
            ),
            # --- Tips 层（tips.md） ----------------------------------------
            lay.title("Tips 层", level=3),
            bar(
                lay.layer("向上", trigger="显示在上", kind="tips", options={"tips": 1}),
                lay.layer("默认向右", trigger="显示在右", kind="tips"),
                lay.layer("向下", trigger="显示在下", kind="tips", options={"tips": 3}),
                lay.layer("向左", trigger="显示在左", kind="tips", options={"tips": 4}),
                lay.layer(
                    "可自定义任意主题色",
                    trigger="自定义背景色",
                    kind="tips",
                    options={"tips": [1, "#16b777"]},
                ),
                lay.layer(
                    "不会关闭之前的 tips",
                    trigger="允许多个 tips",
                    kind="tips",
                    options={"tips_more": True},
                ),
            ),
            # --- 其他（other.md） -----------------------------------------
            lay.title("其他", level=3),
            bar(
                lay.layer(
                    lay.tabs(
                        lay.tab("Title 1", lay.text("tabs content 111")),
                        lay.tab("Title 2", lay.text("tabs content 222")),
                        lay.tab("Title 3", lay.text("tabs content 333")),
                        id="layer-tabs",
                    ),
                    trigger="tab 层",
                    kind="tab",
                    options={"area": ["600px", "300px"], "shade_close": True},
                    id="other-tab",
                ),
                lay.layer(
                    "请输入文本",
                    trigger="prompt - 单行文本框层",
                    kind="prompt",
                    id="prompt-0",
                    events={"confirm": "prompt"},
                ),
                lay.layer(
                    "请输入密令",
                    trigger="prompt - 密令输入框层",
                    kind="prompt",
                    options={"formType": 1},
                    id="prompt-1",
                    events={"confirm": "prompt"},
                ),
                lay.layer(
                    "请输入文本",
                    trigger="prompt - 多行文本框层",
                    kind="prompt",
                    options={"formType": 2},
                    id="prompt-2",
                    events={"confirm": "prompt"},
                ),
                lay.layer(
                    trigger="photos - 单张图片层",
                    kind="photos",
                    photos=PHOTOS[:1],
                    options={"footer": False},
                    id="photos-one",
                ),
                lay.layer(
                    trigger="photos - 多张相册层",
                    kind="photos",
                    photos=PHOTOS,
                    id="photos-many",
                ),
            ),
            # --- 异步按钮（btnasync.md） ----------------------------------
            lay.title("异步按钮", level=3),
            lay.text("点击按钮后模拟 1 秒请求，期间按钮进入 loading 状态。"),
            bar(
                lay.layer(
                    "对话框内容",
                    trigger="alert",
                    kind="alert",
                    btn_async=True,
                    id="async-alert",
                ),
                lay.layer(
                    "一个询问框的示例？",
                    trigger="confirm",
                    kind="confirm",
                    btns=["确定", "关闭"],
                    btn_async=True,
                    id="async-confirm",
                ),
                lay.layer(
                    "第二个回调",
                    trigger="msg",
                    kind="msg",
                    btn_async=True,
                    options={"time": 20000},
                    btns=["明白了", "知道了"],
                    id="async-msg",
                ),
                lay.layer(
                    trigger="open",
                    kind="dialog",
                    btn_async=True,
                    options={"area": ["500px", "300px"]},
                    btns=["确定", "关闭"],
                    id="async-open",
                ),
                lay.layer(
                    "请输入值",
                    trigger="prompt(不支持)",
                    kind="prompt",
                    options={"formType": 2, "value": "初始值", "area": ["500px", "300px"]},
                    id="async-prompt",
                    events={"confirm": "prompt"},
                ),
            ),
            # --- 位置（offset.md） ----------------------------------------
            lay.title("位置", level=3),
            bar(
                *[
                    lay.layer(
                        f"<div style='padding: 16px;'>{label}</div>",
                        trigger=label,
                        kind="dialog",
                        options={
                            "offset": offset or ["200px", "280px"],
                            "area": "240px",
                            "shade": 0,
                            "btn_align": "c",
                        },
                        btns=["关闭全部"],
                        actions=["close_all"],
                        id=f"offset-{offset or 'any'}",
                    )
                    for label, offset in [
                        ("上", "t"),
                        ("右", "r"),
                        ("下", "b"),
                        ("左", "l"),
                        ("右上", "rt"),
                        ("右下", "rb"),
                        ("左下", "lb"),
                        ("左上", "lt"),
                        ("正中", "auto"),
                        ("任意", ""),
                    ]
                ]
            ),
            # --- 方向（direction.md） -------------------------------------
            lay.title("方向（抽屉）", level=3),
            bar(
                lay.layer(
                    "<div style='padding: 16px;'>任意 HTML 内容</div>",
                    trigger="从上往下",
                    kind="dialog",
                    options={
                        "offset": "t",
                        "anim": "slideDown",
                        "area": ["100%", "160px"],
                        "shade": 0.1,
                        "shade_close": True,
                    },
                ),
                lay.layer(
                    "<div style='padding: 16px;'>任意 HTML 内容</div>",
                    trigger="从右往左",
                    kind="dialog",
                    options={
                        "offset": "r",
                        "anim": "slideLeft",
                        "area": ["320px", "100%"],
                        "shade": 0.1,
                        "shade_close": True,
                    },
                ),
                lay.layer(
                    "<div style='padding: 16px;'>任意 HTML 内容</div>",
                    trigger="从下往上",
                    kind="dialog",
                    options={
                        "offset": "b",
                        "anim": "slideUp",
                        "area": ["100%", "160px"],
                        "shade": 0.1,
                        "shade_close": True,
                    },
                ),
                lay.layer(
                    "<div style='padding: 16px;'>任意 HTML 内容</div>",
                    trigger="从左往右",
                    kind="dialog",
                    options={
                        "offset": "l",
                        "anim": "slideRight",
                        "area": ["320px", "100%"],
                        "shade": 0.1,
                        "shade_close": True,
                    },
                ),
            ),
            # --- 主题（skin.md） ------------------------------------------
            lay.title("主题", level=3),
            lay.text("自定义主题通过 options.skin 引用样式类；样式随组件 CSS 一起注入页面。"),
            bar(
                lay.layer(
                    "墨绿风格，点击继续确认看深蓝",
                    trigger="墨绿与深蓝主题",
                    kind="alert",
                    options={"skin": "layui-layer-molv"},
                    next=lay.layer("深蓝", kind="alert", options={"skin": "layui-layer-lan"}),
                ),
                lay.layer(
                    "Windows 10 风格主题",
                    trigger="Win10 信息框",
                    kind="alert",
                    btns=["确定", "取消"],
                    options={"skin": "layui-layer-win10", "shade": 0.01},
                ),
                lay.layer(
                    "<div style='padding: 0 8px; height: 20px; line-height: 20px;"
                    " border-bottom: 1px solid #F0F0F0; box-sizing: border-box;"
                    " font-size: 12px;'>"
                    "<a href='javascript:;'>文件(F)</a>&nbsp;&nbsp;&nbsp;"
                    "<a href='javascript:;'>编辑(E)</a>&nbsp;&nbsp;&nbsp;"
                    "<a href='javascript:;'>格式(O)</a>&nbsp;&nbsp;&nbsp;"
                    "<a href='javascript:;'>查看(V)</a>&nbsp;&nbsp;&nbsp;"
                    "<a href='javascript:;'>帮助(H)</a>"
                    "</div>"
                    "<textarea style='position: absolute; top: 20px; width: 100%;"
                    " height: calc(100% - 20px); padding: 6px; border: none;"
                    " resize: none; overflow-y: scroll; box-sizing: border-box;'>"
                    "&#60;textarea&#62;</textarea>",
                    trigger="Win10 页面层",
                    kind="dialog",
                    options={
                        "skin": "layui-layer-win10",
                        "shade": 0.01,
                        "area": ["50%", "60%"],
                        "maxmin": True,
                        "title": "*无标题 - 记事本",
                    },
                ),
                lay.layer(
                    "自定义其他任意主题",
                    trigger="自定义任意主题",
                    kind="alert",
                    options={"skin": "law-layer-custom"},
                ),
            ),
            # --- 更多（more.md） -----------------------------------------
            lay.title("更多", level=3),
            bar(
                lay.layer(
                    "<div style='padding: 16px;'>任意 HTML 内容</div>",
                    trigger="最大化弹出",
                    kind="dialog",
                    options={"area": ["320px", "195px"], "maxmin": True},
                    full=True,
                ),
                lay.layer(
                    "浏览器滚动条已暂时屏蔽，关闭弹层后自动恢复",
                    trigger="弹出时屏蔽浏览器滚动条",
                    kind="alert",
                    options={"scrollbar": False},
                ),
                # 文档的页面锁屏：输入 111111 后点击右侧箭头（或回车）解锁。
                lay.layer(
                    "<div class='layui-form' style='position: absolute; top: 50%;"
                    " left: 50%; width: 300px; transform: translate(-50%, -50%);'>"
                    "<div style='margin-bottom: 8px;'>"
                    "<div class='layui-input-wrap'>"
                    "<input type='password' class='law-layer-pin'>"
                    "<div class='layui-input-suffix'>"
                    "<i class='layui-icon layui-icon-right'"
                    " data-law-unlock></i>"
                    "</div></div></div>"
                    "<div>输入 111111 后回车，即可退出锁屏示例</div>"
                    "</div>",
                    trigger="页面锁屏",
                    kind="dialog",
                    title=False,
                    unlock="111111",
                    options={
                        "type": 1,
                        "closeBtn": False,
                        "area": ["100%", "100%"],
                        "scrollbar": False,
                        "anim": -1,
                        "is_out_anim": False,
                        "resize": False,
                        "skin": "law-layer-lockscreen",
                    },
                    events={"unlock": "unlock"},
                    id="more-lockscreen",
                ),
                lay.layer(
                    "<div style='padding: 16px;'>任意 HTML 内容</div>",
                    trigger="自定义遮罩颜色和透明度",
                    kind="dialog",
                    options={
                        "area": ["320px", "195px"],
                        "shade": [0.9, "#000"],
                        "shade_close": True,
                    },
                ),
                lay.layer(
                    "<div style='padding: 16px;'>内容标记："
                    "按 ESC 键可关闭。多窗口会层叠置顶。</div>",
                    trigger="多窗口模式 + 层级置顶 + Esc 关闭",
                    kind="dialog",
                    options={
                        "area": ["390px", "260px"],
                        "shade": 0,
                        "maxmin": True,
                        "offset": ["120px", "260px"],
                    },
                    btns=["继续弹出", "全部关闭"],
                    actions=["reopen", "close_all"],
                    set_top=True,
                    esc_close=True,
                    id="more-stack",
                ),
            ),
        ],
        state={"last_event": None, "last_value": None, "button": None},
    )
    widget_ui = mo.ui.anywidget(widget)
    return widget, widget_ui


@app.cell
def cell_events(Layui, widget):
    def record(event):
        if event.get("type") != "layer":
            return
        value = event.get("value")
        if isinstance(value, dict):
            value = value.get("text") or value.get("index")
        elif event.get("event") == "open":
            value = event.get("raw", {}).get("index")
        widget.update_values({"last_event": event.get("event"), "last_value": value})

    # `on_event` returns the callback; discard it so marimo shows no output.
    _ = widget.on_event(record)
    return


@app.cell
def cell_layout(Layui, heading, mo, section, widget_ui):
    state = widget_ui.value.get("state", {})
    last = state.get("last_event") or "（尚无）"
    value = state.get("last_value")
    mo.vstack(
        [
            heading(
                "弹出层 Layer",
                "弹出层组件 `layer` 是 Layui 最古老的组件，集众多弹层功能为一体："
                "信息框、询问框、提示框、加载层、贴士层、输入框层、页面层与 iframe 层。",
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
