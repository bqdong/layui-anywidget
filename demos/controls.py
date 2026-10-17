# /// script
# requires-python = ">=3.10"
# dependencies = ["layui-anywidget", "marimo"]
# ///

"""Ready-made control classes with Python-side value access.

Each control is a standalone widget with a synced ``value``. To compose many
bound controls in one tree, use ``Layui`` with ``lay.*`` helpers instead (see
``demos/form.py``).
"""

import marimo

app = marimo.App(width="medium")


@app.cell
def __():
    import marimo as mo

    from layui_anywidget import (
        Button,
        Checkbox,
        ColorPicker,
        DatePicker,
        Input,
        InputNumber,
        Radio,
        Rate,
        Select,
        Slider,
        Switch,
        Table,
    )

    return (
        Button,
        Checkbox,
        ColorPicker,
        DatePicker,
        Input,
        InputNumber,
        Radio,
        Rate,
        Select,
        Slider,
        Switch,
        Table,
        mo,
    )


@app.cell
def __(Input, InputNumber, Select, Slider, Switch, mo):
    # mo.ui.anywidget turns the value trait into a reactive marimo value.
    name = mo.ui.anywidget(Input("Ada", label="Name", placeholder="Type a name", theme="light"))
    language = mo.ui.anywidget(
        Select("Python", ["Python", "JavaScript", "Rust"], label="Language", theme="light")
    )
    count = mo.ui.anywidget(InputNumber(5, min_value=0, max_value=10, label="Count", theme="light"))
    level = mo.ui.anywidget(Slider(5, min_value=0, max_value=10, label="Level", theme="light"))
    notify = mo.ui.anywidget(Switch(True, label="Notify", theme="light"))
    mo.vstack([name, language, count, level, notify])
    return count, language, level, name, notify


@app.cell
def __(Checkbox, ColorPicker, DatePicker, Radio, Rate, mo):
    theme = mo.ui.anywidget(ColorPicker("#16baaa", label="Color", theme="light"))
    day = mo.ui.anywidget(DatePicker("2026-10-17", label="Date", theme="light"))
    stars = mo.ui.anywidget(Rate(3, label="Rating", theme="light"))
    plan = mo.ui.anywidget(Radio("free", ["free", "pro", "team"], label="Plan", theme="light"))
    accept = mo.ui.anywidget(Checkbox(True, label="Terms", text="I accept", theme="light"))
    mo.hstack([theme, day, stars, plan, accept], justify="start", wrap=True)
    return accept, day, plan, stars, theme


@app.cell
def __(Button, Table, level, mo):
    table_widget = Table(
        [{"name": "Ada", "score": 98}, {"name": "Grace", "score": 95}],
        [{"field": "name", "title": "Name"}, {"field": "score", "title": "Score", "sort": True}],
        selectable=True,
        page=False,
        theme="light",
    )
    table = mo.ui.anywidget(table_widget)
    reset = Button("Reset level", on_click=lambda _: level.widget.set_value(5))
    # Button's `theme` argument styles the button itself, so set the widget
    # theme on the trait instead.
    reset.theme = "light"
    mo.vstack([table, reset])
    return reset, table


@app.cell
def __(
    accept,
    count,
    day,
    language,
    level,
    mo,
    name,
    notify,
    plan,
    stars,
    table,
    theme,
):
    mo.md(
        f"""
        **Values**

        | Control | Value |
        | --- | --- |
        | Name | `{name.value.get("value")}` |
        | Language | `{language.value.get("value")}` |
        | Count | `{count.value.get("value")}` |
        | Level | `{level.value.get("value")}` |
        | Notify | `{notify.value.get("value")}` |
        | Color | `{theme.value.get("value")}` |
        | Date | `{day.value.get("value")}` |
        | Rating | `{stars.value.get("value")}` |
        | Plan | `{plan.value.get("value")}` |
        | Terms | `{accept.value.get("value")}` |
        | Selected rows | `{table.value.get("state", {}).get("selection")}` |
        """
    )
    return


if __name__ == "__main__":
    app.run()
