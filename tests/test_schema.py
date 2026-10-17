"""Tests for JSON normalization and schema helpers."""

from __future__ import annotations

import dataclasses
import json
from datetime import date, datetime, time
from enum import Enum
from pathlib import Path

import pytest

from layui_anywidget import lay
from layui_anywidget.schema import to_jsonable


class Color(Enum):
    RED = "red"


@dataclasses.dataclass
class Point:
    x: int
    y: int


class TestToJsonable:
    def test_scalars_pass_through(self) -> None:
        for value in (None, True, False, 0, 1.5, "x"):
            assert to_jsonable(value) == value

    def test_non_finite_float_rejected(self) -> None:
        with pytest.raises(ValueError):
            to_jsonable(float("nan"))
        with pytest.raises(ValueError):
            to_jsonable(float("inf"))

    def test_enum_and_datetime(self) -> None:
        assert to_jsonable(Color.RED) == "red"
        assert to_jsonable(datetime(2026, 10, 17, 1, 2, 3)) == "2026-10-17T01:02:03"
        assert to_jsonable(date(2026, 10, 17)) == "2026-10-17"
        assert to_jsonable(time(1, 2)) == "01:02:00"

    def test_path_and_dataclass(self) -> None:
        assert to_jsonable(Path("/tmp/x")) == "/tmp/x"
        assert to_jsonable(Point(1, 2)) == {"x": 1, "y": 2}

    def test_set_becomes_list(self) -> None:
        assert sorted(to_jsonable({1, 2})) == [1, 2]

    def test_circular_reference_rejected(self) -> None:
        data: dict = {}
        data["self"] = data
        with pytest.raises(ValueError, match="Circular"):
            to_jsonable(data)

    def test_repeated_but_not_circular_reference_allowed(self) -> None:
        shared = {"a": 1}
        assert to_jsonable([shared, shared]) == [{"a": 1}, {"a": 1}]

    def test_callable_rejected(self) -> None:
        with pytest.raises(TypeError, match="not JSON serializable"):
            to_jsonable(len)

    def test_result_is_json_serializable(self) -> None:
        value = {"a": [Point(1, 2), Color.RED, date(2026, 1, 1)]}
        json.dumps(to_jsonable(value))


class TestNode:
    def test_minimal_node(self) -> None:
        assert lay.node("div") == {"type": "div"}

    def test_rejects_empty_type(self) -> None:
        with pytest.raises(TypeError):
            lay.node("")  # type: ignore[arg-type]

    def test_children_and_kwargs(self) -> None:
        result = lay.node("div", "hi", 3, props={"a": 1}, b=2)
        assert result == {"type": "div", "props": {"a": 1, "b": 2}, "children": ["hi", 3]}

    def test_event_string_and_sequence(self) -> None:
        assert lay.node("x", events="click")["events"] == {"click": "click"}
        assert lay.node("x", events=["click", "hover"])["events"] == {
            "click": "click",
            "hover": "hover",
        }

    def test_event_mapping(self) -> None:
        assert lay.node("x", events={"click": "pressed"})["events"] == {"click": "pressed"}

    def test_children_key_alias(self) -> None:
        node = lay.node("x", "a", children_key=("b", "c"))
        assert node["children"] == ["a", "b", "c"]

    def test_style_and_visible(self) -> None:
        node = lay.node("x", style={"color": "red"}, visible={"key": "show", "equals": True})
        assert node["style"] == {"color": "red"}
        assert node["visible"] == {"key": "show", "equals": True}

    def test_text_field(self) -> None:
        assert lay.node("x", text="hi")["text"] == "hi"


class TestOptions:
    def test_scalars_pairs_and_mappings(self) -> None:
        result = lay.options(["a", ("B", 2), {"label": "C", "value": 3}, {"value": 4}])
        assert result == [
            {"label": "a", "value": "a"},
            {"label": "B", "value": 2},
            {"label": "C", "value": 3},
            {"label": 4, "value": 4},
        ]

    def test_extra_mapping_keys_preserved(self) -> None:
        result = lay.options([{"label": "A", "value": 1, "disabled": True}])
        assert result == [{"label": "A", "value": 1, "disabled": True}]

    def test_select_helper_normalizes(self) -> None:
        node = lay.select("lang", ["Python", "Rust"], label="Lang")
        assert node["type"] == "field"
        select = node["children"][0]
        assert select["type"] == "select"
        assert select["model"] == "lang"
        assert select["props"]["options"] == [
            {"label": "Python", "value": "Python"},
            {"label": "Rust", "value": "Rust"},
        ]
        assert node["props"]["label"] == "Lang"


class TestFormHelpers:
    def test_input_binds_state_key(self) -> None:
        node = lay.input("name", label="Name", placeholder="Ada")
        control = node["children"][0]
        assert node["type"] == "field"
        assert control["type"] == "input"
        assert control["id"] == "name"
        assert control["model"] == "name"
        assert control["props"]["placeholder"] == "Ada"

    def test_textarea(self) -> None:
        assert lay.textarea("bio")["children"][0]["type"] == "textarea"

    def test_input_number(self) -> None:
        props = lay.input_number("n", min_value=0, max_value=9, step=2)["children"][0]["props"]
        assert props == {"min": 0, "max": 9, "step": 2, "type": "number"}

    def test_checkbox_custom_value(self) -> None:
        control = lay.checkbox("agree", value="yes")["children"][0]
        assert control["props"]["value"] == "yes"

    def test_checkbox_text(self) -> None:
        control = lay.checkbox("agree", text="I agree")["children"][0]
        assert control["props"]["title"] == "I agree"

    def test_checkbox_group(self) -> None:
        node = lay.checkbox_group("tags", ["a", "b"])
        container = node["children"][0]
        assert container["props"]["group_model"] == "tags"
        assert [child["id"] for child in container["children"]] == ["tags-a", "tags-b"]

    def test_switch_custom_values(self) -> None:
        props = lay.switch("s", checked_value="on", unchecked_value="off")["children"][0]["props"]
        assert props == {"checked_value": "on", "unchecked_value": "off"}

    def test_radio(self) -> None:
        control = lay.radio("r", ["x", "y"])["children"][0]
        assert control["type"] == "radio"
        assert len(control["props"]["options"]) == 2

    def test_button_forwards_click(self) -> None:
        node = lay.button("Go", theme="primary")
        assert node["type"] == "button"
        assert node["events"] == {"click": "click"}
        assert node["class"] == "layui-btn"
        assert node["props"]["theme"] == "primary"

    def test_submit_marks_lay_submit(self) -> None:
        node = lay.submit("Send")
        assert node["props"]["lay-submit"] is True
        assert node["props"]["theme"] == "primary"

    def test_form_class(self) -> None:
        assert lay.form(lay.input("a"))["class"] == "layui-form"


class TestValueHelpers:
    def test_slider_defaults(self) -> None:
        props = lay.slider("s", max_value=10)["children"][0]["props"]
        assert props["min_value"] == 0
        assert props["max_value"] == 10
        assert props["range"] is False

    def test_colorpicker(self) -> None:
        props = lay.colorpicker("c", format="rgb", alpha=True)["children"][0]["props"]
        assert props == {"format": "rgb", "alpha": True, "predefine": False}

    def test_datepicker_min_max(self) -> None:
        node = lay.datepicker("d", min_value="2026-01-01", max_value="2026-12-31")
        props = node["children"][0]["props"]
        assert props["min"] == "2026-01-01"
        assert props["max"] == "2026-12-31"

    def test_rate(self) -> None:
        props = lay.rate("r", max_value=10, half=True)["children"][0]["props"]
        assert props == {"max_value": 10, "half": True, "text": False}


class TestDisplayHelpers:
    def test_table_cols_wrapped(self) -> None:
        node = lay.table("rows", [{"field": "name", "title": "Name"}])
        assert node["type"] == "table"
        assert node["bind"] == {"data": "rows"}
        assert node["props"]["cols"] == [[{"field": "name", "title": "Name"}]]

    def test_table_selectable_prepends_checkbox(self) -> None:
        node = lay.table("rows", [{"field": "name"}], selectable=True, page=True)
        cols = node["props"]["cols"][0]
        assert cols[0] == {"type": "checkbox", "fixed": "left"}
        assert node["props"]["page"] is True

    def test_tabs_and_tab(self) -> None:
        node = lay.tabs(lay.tab("One", "a"), lay.tab("Two", "b"), model="active")
        assert node["type"] == "tabs"
        assert node["model"] == "active"
        assert [child["props"]["title"] for child in node["children"]] == ["One", "Two"]

    def test_collapse(self) -> None:
        node = lay.collapse(lay.collapse_item("More", "body"), accordion=True)
        assert node["class"] == "layui-collapse"
        assert node["props"]["accordion"] is True
        assert node["children"][0]["type"] == "collapse-item"

    def test_dropdown_items(self) -> None:
        node = lay.dropdown("Menu", ["A", {"title": "B", "id": "b"}])
        assert node["type"] == "dropdown"
        assert node["props"]["data"] == [
            {"title": "A", "id": "A"},
            {"title": "B", "id": "b"},
        ]

    def test_progress_binds_value(self) -> None:
        node = lay.progress("pct")
        assert node["bind"] == {"value": "pct"}
        assert node["class"] == "layui-progress"

    def test_laypage_updates_page_key(self) -> None:
        node = lay.laypage(100, page_key="page")
        assert node["bind"] == {"curr": "page"}
        assert node["updates"] == {"change": "page"}

    def test_text_and_title(self) -> None:
        assert lay.text("hi")["props"]["tag"] == "span"
        assert lay.title("hi", level=2)["props"]["tag"] == "h2"

    def test_badge(self) -> None:
        node = lay.badge("new", color="red")
        assert node["class"] == "layui-badge"
        assert node["props"]["lay-badge-color"] == "red"

    def test_layout(self) -> None:
        assert lay.row()["class"] == "layui-row"
        assert lay.col(span=4)["class"] == "layui-col-md4"
