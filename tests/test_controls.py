"""Tests for the ready-made control classes."""

from __future__ import annotations

import json
from typing import ClassVar

import pytest

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
    Tabs,
    Textarea,
)


def _control_node(control) -> dict:
    """Return the inner control node (unwrapping a ``field`` wrapper)."""

    node = control.schema[0]
    if node["type"] == "field":
        return node["children"][0]
    return node


class TestInputControls:
    def test_input_initial_sync(self) -> None:
        control = Input("Ada", label="Name")
        assert control.value == "Ada"
        assert control.state["value"] == "Ada"
        node = _control_node(control)
        assert node["type"] == "input"
        assert node["model"] == "value"

    def test_input_placeholder(self) -> None:
        assert _control_node(Input("", placeholder="type"))["props"]["placeholder"] == "type"

    def test_textarea(self) -> None:
        assert _control_node(Textarea("x"))["type"] == "textarea"

    def test_value_set_in_python_writes_state(self) -> None:
        control = Input("a")
        control.value = "b"
        assert control.state["value"] == "b"

    def test_state_set_from_browser_mirrors_value(self) -> None:
        control = Input("a")
        control.update_values({"value": "typed"})
        assert control.value == "typed"

    def test_value_callback(self) -> None:
        seen: list = []
        control = Input("a", on_change=seen.append)
        control.update_values({"value": "b"})
        assert seen == ["b"]

    def test_callback_not_fired_for_unrelated_state(self) -> None:
        seen: list = []
        control = Input("a", on_change=seen.append)
        control.update_values({"other": 1})
        assert seen == []

    def test_no_infinite_loop(self) -> None:
        control = Input("a")
        control.value = "b"
        assert control.state["value"] == "b"
        control.update_values({"value": "b"})
        assert control.value == "b"

    def test_input_number_clamps(self) -> None:
        assert InputNumber(15, min_value=0, max_value=10).value == 10
        assert InputNumber(-5, min_value=0, max_value=10).value == 0

    def test_input_number_external_clamp_kept_in_range(self) -> None:
        control = InputNumber(5, min_value=0, max_value=10)
        control.update_values({"value": 99})
        assert control.value == 10
        assert control.state["value"] == 99  # state keeps the raw browser value

    def test_input_number_validation(self) -> None:
        with pytest.raises(ValueError):
            InputNumber(0, min_value=10, max_value=1)
        with pytest.raises(ValueError):
            InputNumber(0, step=0)


class TestSelectControls:
    def test_select_defaults_to_first_option(self) -> None:
        control = Select(None, ["Python", "Rust"])
        assert control.value == "Python"

    def test_select_keeps_given_value(self) -> None:
        assert Select("Rust", ["Python", "Rust"]).value == "Rust"

    def test_select_options_normalized(self) -> None:
        control = Select("a", [{"label": "A", "value": "a"}])
        assert _control_node(control)["props"]["options"] == [{"label": "A", "value": "a"}]

    def test_select_multiple_wraps_value(self) -> None:
        control = Select("a", ["a", "b"], multiple=True)
        assert control.value == ["a"]
        assert _control_node(control)["props"]["multiple"] is True

    def test_select_multiple_default_empty(self) -> None:
        assert Select(None, ["a"], multiple=True).value == []

    def test_select_search(self) -> None:
        assert _control_node(Select("a", ["a"], search=True))["props"]["search"] is True

    def test_set_options_rebuilds_schema(self) -> None:
        control = Select("a", ["a"])
        control.set_options(["b", "c"])
        assert [item["value"] for item in _control_node(control)["props"]["options"]] == ["b", "c"]


class TestToggleControls:
    def test_checkbox_boolean(self) -> None:
        control = Checkbox(True, text="Agree")
        assert control.value is True
        assert _control_node(control)["props"]["title"] == "Agree"

    def test_checkbox_custom_value(self) -> None:
        assert _control_node(Checkbox("no", checked_value="yes"))["props"]["value"] == "yes"

    def test_switch(self) -> None:
        control = Switch(True, checked_value="on", unchecked_value="off")
        assert control.value is True
        props = _control_node(control)["props"]
        assert props["checked_value"] == "on"
        assert props["unchecked_value"] == "off"
        assert props["text"] == "ON|OFF"

    def test_radio(self) -> None:
        control = Radio(None, ["x", "y"])
        assert control.value == "x"
        assert _control_node(control)["props"]["options"] == [
            {"label": "x", "value": "x"},
            {"label": "y", "value": "y"},
        ]


class TestSlider:
    def test_single_value_clamped(self) -> None:
        assert Slider(120, max_value=100).value == 100

    def test_single_value_keeps_int(self) -> None:
        control = Slider(5, max_value=10)
        assert control.value == 5
        assert isinstance(control.value, int)

    def test_range_sorted(self) -> None:
        assert Slider([80, 20], range=True).value == [20, 80]

    def test_range_requires_pair(self) -> None:
        with pytest.raises(ValueError, match="range sliders"):
            Slider(5, range=True)

    def test_invalid_bounds(self) -> None:
        with pytest.raises(ValueError, match="min_value"):
            Slider(0, min_value=10, max_value=1)

    def test_invalid_step(self) -> None:
        with pytest.raises(ValueError, match="step"):
            Slider(0, step=0)

    def test_set_value_single(self) -> None:
        control = Slider(5)
        control.set_value(30)
        assert control.value == 30

    def test_set_value_range_index(self) -> None:
        control = Slider([20, 80], range=True)
        control.set_value(10, index=0)
        assert control.value == [10, 80]

    def test_browser_update_mirrors(self) -> None:
        control = Slider(5)
        control.update_values({"value": 42})
        assert control.value == 42

    def test_schema_props(self) -> None:
        props = _control_node(Slider(5, min_value=1, max_value=9, step=2))["props"]
        assert props["min_value"] == 1
        assert props["max_value"] == 9
        assert props["step"] == 2


class TestOtherValueControls:
    def test_colorpicker(self) -> None:
        control = ColorPicker("#16baaa", format="rgb", alpha=True)
        props = _control_node(control)["props"]
        assert props["color"] == "#16baaa"
        assert props["format"] == "rgb"
        assert props["alpha"] is True

    def test_datepicker(self) -> None:
        control = DatePicker("2026-10-17", min_value="2026-01-01")
        props = _control_node(control)["props"]
        assert props["value"] == "2026-10-17"
        assert props["min"] == "2026-01-01"
        assert props["type"] == "date"

    def test_rate(self) -> None:
        props = _control_node(Rate(3, max_value=5, half=True))["props"]
        assert props == {"max_value": 5, "half": True, "text": False, "value": 3}

    def test_rate_validation(self) -> None:
        with pytest.raises(ValueError):
            Rate(0, max_value=0)


class TestTable:
    ROWS: ClassVar[list[dict]] = [{"name": "Ada", "score": 98}, {"name": "Grace", "score": 95}]
    COLS: ClassVar[list[dict]] = [
        {"field": "name", "title": "Name"},
        {"field": "score", "title": "Score"},
    ]

    def test_rows_and_columns(self) -> None:
        table = Table(self.ROWS, self.COLS)
        assert table.rows == self.ROWS
        assert table.data == self.ROWS
        node = table.schema[0]
        assert node["bind"] == {"data": "rows"}
        assert node["props"]["cols"] == [self.COLS]

    def test_columns_inferred(self) -> None:
        table = Table(self.ROWS)
        assert [col["field"] for col in table.schema[0]["props"]["cols"][0]] == ["name", "score"]

    def test_selectable_adds_checkbox_column(self) -> None:
        table = Table(self.ROWS, self.COLS, selectable=True)
        assert table.schema[0]["props"]["cols"][0][0] == {"type": "checkbox", "fixed": "left"}
        assert "checkbox" in table.schema[0]["events"]

    def test_set_rows_updates_state_and_trait(self) -> None:
        table = Table(self.ROWS, self.COLS)
        table.set_rows([{"name": "Lin", "score": 100}])
        assert table.rows == [{"name": "Lin", "score": 100}]
        assert table.data == [{"name": "Lin", "score": 100}]

    def test_browser_rows_update_trait(self) -> None:
        table = Table(self.ROWS, self.COLS)
        table.update_values({"rows": [{"name": "Lin", "score": 100}]})
        assert table.data == [{"name": "Lin", "score": 100}]

    def test_selection(self) -> None:
        table = Table(self.ROWS, self.COLS, selectable=True)
        table.update_values({"selection": [self.ROWS[1]]})
        assert table.selection == [self.ROWS[1]]

    def test_rows_json_normalized(self) -> None:
        table = Table([{"when": __import__("datetime").date(2026, 1, 1)}])
        assert table.rows == [{"when": "2026-01-01"}]
        json.dumps(table.state)


class TestTabs:
    def test_tabs_build(self) -> None:
        tabs = Tabs({"One": "a", "Two": ["b"]})
        node = tabs.schema[0]
        assert node["type"] == "tabs"
        assert [child["id"] for child in node["children"]] == ["One", "Two"]
        assert tabs.active == "One"

    def test_explicit_active(self) -> None:
        assert Tabs({"One": "a", "Two": "b"}, active="Two").active == "Two"

    def test_select(self) -> None:
        tabs = Tabs({"One": "a", "Two": "b"})
        tabs.select("Two")
        assert tabs.active == "Two"

    def test_empty_rejected(self) -> None:
        with pytest.raises(ValueError):
            Tabs({})


class TestButton:
    def test_click_event_increments(self) -> None:
        button = Button("Go")
        assert button.clicks == 0
        button.event = {"seq": 1, "event": "click", "id": "button"}
        assert button.clicks == 1
        assert button.last_click["seq"] == 1

    def test_non_click_event_ignored(self) -> None:
        button = Button("Go")
        button.event = {"seq": 1, "event": "change"}
        assert button.clicks == 0

    def test_on_click_callback(self) -> None:
        seen: list[dict] = []
        button = Button("Go", on_click=seen.append)
        button.event = {"seq": 1, "event": "click"}
        assert len(seen) == 1

    def test_callback_error_logged_not_raised(self) -> None:
        def boom(event):
            raise RuntimeError("boom")

        button = Button("Go", on_click=boom)
        button.event = {"seq": 1, "event": "click"}  # must not raise
        assert button.clicks == 1
