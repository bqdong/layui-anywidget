"""Tests for the generic Layui container."""

from __future__ import annotations

import json

import pytest

from layui_anywidget import Layui, lay


class TestConstruction:
    def test_empty_widget(self) -> None:
        widget = Layui()
        assert widget.schema == []
        assert widget.state == {}
        assert widget.ready is False

    def test_schema_mapping_normalized_to_list(self) -> None:
        widget = Layui(lay.input("name"))
        assert isinstance(widget.schema, list)
        assert widget.schema[0]["type"] == "field"

    def test_schema_sequence(self) -> None:
        widget = Layui([lay.div("a"), lay.div("b")])
        assert len(widget.schema) == 2

    def test_schema_missing_type_rejected(self) -> None:
        with pytest.raises(ValueError, match="missing the 'type' key"):
            Layui([{"props": {}}])  # type: ignore[list-item]

    def test_schema_item_not_mapping_rejected(self) -> None:
        with pytest.raises(TypeError, match="must be a mapping"):
            Layui(["nope"])  # type: ignore[list-item]

    def test_schema_string_rejected(self) -> None:
        with pytest.raises(TypeError):
            Layui("nope")  # type: ignore[arg-type]

    def test_state_must_be_mapping(self) -> None:
        with pytest.raises(TypeError, match="state must be a mapping"):
            Layui(state=[("a", 1)])  # type: ignore[arg-type]

    def test_state_is_json_normalized(self) -> None:
        from datetime import date

        widget = Layui(state={"day": date(2026, 10, 17)})
        assert widget.state == {"day": "2026-10-17"}
        json.dumps(widget.state)

    def test_invalid_theme(self) -> None:
        with pytest.raises(ValueError, match="theme"):
            Layui(theme="neon")

    def test_negative_throttle(self) -> None:
        with pytest.raises(ValueError, match="sync_throttle_ms"):
            Layui(sync_throttle_ms=-1)

    def test_theme_and_height(self) -> None:
        widget = Layui(theme="dark", height="400px")
        assert widget.theme == "dark"
        assert widget.height == "400px"

    def test_config_is_json_normalized(self) -> None:
        widget = Layui(config={"base_style_id": "x"})
        assert widget.config == {"base_style_id": "x"}


class TestStateHelpers:
    def test_set_values_merges(self) -> None:
        widget = Layui(state={"a": 1, "b": 2})
        widget.set_values(b=3)
        assert widget.state == {"a": 1, "b": 3}

    def test_set_values_rejects_unserializable(self) -> None:
        widget = Layui()
        with pytest.raises(TypeError):
            widget.set_values(fn=len)

    def test_update_values(self) -> None:
        widget = Layui()
        widget.update_values({"x": 1})
        assert widget.values == {"x": 1}
        widget.values["x"] = 99  # copy, not the live trait
        assert widget.state["x"] == 1

    def test_get_value(self) -> None:
        widget = Layui(state={"a": 1})
        assert widget.get_value("a") == 1
        assert widget.get_value("missing", "fallback") == "fallback"

    def test_update_schema(self) -> None:
        widget = Layui(lay.div("a"))
        widget.update_schema(lay.div("b"))
        assert widget.schema[0]["type"] == "div"
        assert widget.schema[0]["children"] == ["b"]


class TestCallbacks:
    def test_on_change_gets_state_and_changed(self) -> None:
        seen: list[tuple] = []
        callback = lambda state, changed: seen.append((state, changed))  # noqa: E731
        widget = Layui(state={"a": 1}, on_change=callback)
        widget.set_values(a=2)
        assert seen == [({"a": 2}, {"a": 2})]

    def test_on_change_single_argument_callback(self) -> None:
        seen: list[dict] = []
        widget = Layui(state={"a": 1})
        widget.on_change(seen.append)  # type: ignore[arg-type]
        widget.set_values(a=2)
        assert seen == [{"a": 2}]

    def test_removed_change_callback_not_called(self) -> None:
        seen: list[dict] = []
        widget = Layui()
        callback = widget.on_change(seen.append)  # type: ignore[arg-type]
        widget.remove_change_callback(callback)
        widget.set_values(a=1)
        assert seen == []

    def test_change_callback_errors_are_logged_not_raised(self) -> None:
        def boom(state, changed):
            raise RuntimeError("boom")

        widget = Layui(on_change=boom)
        widget.set_values(a=1)  # must not raise
        assert widget.state == {"a": 1}

    def test_on_event_deduplicates_by_seq(self) -> None:
        seen: list[dict] = []
        widget = Layui(on_event=seen.append)
        widget.event = {"seq": 1, "event": "click"}
        widget.event = {"seq": 1, "event": "click"}
        widget.event = {"seq": 2, "event": "change"}
        assert [event["seq"] for event in seen] == [1, 2]

    def test_on_event_requires_callable(self) -> None:
        widget = Layui()
        with pytest.raises(TypeError):
            widget.on_event(1)  # type: ignore[arg-type]

    def test_on_change_requires_callable(self) -> None:
        widget = Layui()
        with pytest.raises(TypeError):
            widget.on_change(1)  # type: ignore[arg-type]
