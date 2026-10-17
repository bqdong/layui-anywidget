"""Ready-made single-value controls built on the generic :class:`Layui`."""

from __future__ import annotations

import logging
from collections.abc import Callable, Iterable, Mapping, Sequence
from typing import Any

import traitlets

from . import schema as lay
from .schema import Node, to_jsonable
from .widget import Layui

_LOGGER = logging.getLogger(__name__)

ValueCallback = Callable[..., None]


class _Control(Layui):
    """Base class bridging ``state["value"]`` and a synced ``value`` trait."""

    node_type: str = ""
    multiple: bool = False

    value = traitlets.Any().tag(sync=True)

    def __init__(
        self,
        value: Any,
        *,
        schema: Node | Sequence[Node] | None = None,
        on_change: ValueCallback | None = None,
        on_event: Callable[..., None] | None = None,
        **kwargs: Any,
    ) -> None:
        self._sync_guard = False
        self._value_callbacks: list[ValueCallback] = []
        json_value = to_jsonable(value)
        state = {**(kwargs.pop("state", None) or {}), "value": json_value}
        super().__init__(
            schema or self.build_schema(json_value),
            state=state,
            on_event=on_event,
            **kwargs,
        )
        self._sync_guard = True
        self.set_trait("value", json_value)
        if on_change is not None:
            self.on_value_change(on_change)
        self.observe(self._on_external_value, names="value")

    # Subclasses build their node tree from the initial value.
    def build_schema(self, value: Any) -> Node | Sequence[Node]:  # pragma: no cover - abstract
        raise NotImplementedError

    def on_value_change(self, callback: ValueCallback) -> ValueCallback:
        """Register ``callback(value)``; runs after the value trait updates."""

        if not callable(callback):
            raise TypeError("callback must be callable")
        self._value_callbacks.append(callback)
        return callback

    def _on_external_value(self, change: dict[str, Any]) -> None:
        if not self._sync_guard:
            return
        value = change["new"]
        self._sync_guard = False
        try:
            if self.state.get("value") != value:
                self.update_values({"value": value})
        finally:
            self._sync_guard = True

    def _on_control_state_change(self, change: dict[str, Any]) -> None:
        state = change["new"] or {}
        previous = change["old"] or {}
        if state.get("value") == previous.get("value"):
            return
        value = state.get("value")
        if self._sync_guard:
            self._sync_guard = False
            try:
                self.set_trait("value", value)
            finally:
                self._sync_guard = True
        for callback in tuple(self._value_callbacks):
            try:
                callback(value)
            except Exception:
                _LOGGER.exception("layui control callback failed")

    def _attach_observers(self) -> None:
        # The value mirror must run before the user-facing state callback so
        # `value` is current when `on_change` fires.
        self.observe(self._on_control_state_change, names="state")
        self.observe(self._handle_event, names="event")


def _field(node: Node, label: str | None) -> Node:
    return lay.field(node, label=label) if label else node


# ---------------------------------------------------------------------------
# Text-like controls
# ---------------------------------------------------------------------------


class Input(_Control):
    """Single-line text input."""

    node_type = "input"

    def __init__(
        self,
        value: str = "",
        *,
        label: str | None = None,
        placeholder: str | None = None,
        on_change: ValueCallback | None = None,
        **kwargs: Any,
    ) -> None:
        self._label = label
        self._placeholder = placeholder
        super().__init__(value, on_change=on_change, **kwargs)

    def build_schema(self, value: Any) -> Node:
        props = {"placeholder": self._placeholder}
        if value:
            props["value"] = value
        return _field(
            lay.node("input", id="value", model="value", props=props),
            self._label,
        )


class Textarea(_Control):
    """Multi-line text input."""

    node_type = "textarea"

    def __init__(
        self,
        value: str = "",
        *,
        label: str | None = None,
        on_change: ValueCallback | None = None,
        **kwargs: Any,
    ) -> None:
        self._label = label
        super().__init__(value, on_change=on_change, **kwargs)

    def build_schema(self, value: Any) -> Node:
        return _field(lay.node("textarea", id="value", model="value"), self._label)


class InputNumber(_Control):
    """Numeric input with min/max/step."""

    node_type = "input"

    def __init__(
        self,
        value: float = 0,
        *,
        label: str | None = None,
        min_value: float | None = None,
        max_value: float | None = None,
        step: float | None = None,
        on_change: ValueCallback | None = None,
        **kwargs: Any,
    ) -> None:
        if min_value is not None and max_value is not None and min_value > max_value:
            raise ValueError("min_value must be <= max_value")
        if step is not None and step <= 0:
            raise ValueError("step must be positive")
        self._label = label
        self._min = min_value
        self._max = max_value
        self._step = step
        value = _clamp_number(value, min_value, max_value)
        super().__init__(value, on_change=on_change, **kwargs)

    def build_schema(self, value: Any) -> Node:
        props: dict[str, Any] = {"type": "number"}
        if self._min is not None:
            props["min"] = self._min
        if self._max is not None:
            props["max"] = self._max
        if self._step is not None:
            props["step"] = self._step
        return _field(lay.node("input", id="value", model="value", props=props), self._label)

    def _on_external_value(self, change: dict[str, Any]) -> None:
        value = _clamp_number(change["new"], self._min, self._max)
        if value != change["new"]:
            self.set_trait("value", value)
            return
        super()._on_external_value(change)


class Select(_Control):
    """Single or multi select."""

    node_type = "select"

    def __init__(
        self,
        value: Any = None,
        options: Iterable[Any] = (),
        *,
        label: str | None = None,
        multiple: bool = False,
        search: bool = False,
        on_change: ValueCallback | None = None,
        **kwargs: Any,
    ) -> None:
        normalized = lay.options(options)
        if value is None:
            if multiple:
                value = []
            elif normalized:
                value = normalized[0]["value"]
        if multiple and not isinstance(value, (list, tuple)):
            value = [value]
        self._label = label
        self._options = normalized
        self._multiple = multiple
        self._search = search
        self.multiple = multiple
        super().__init__(value, on_change=on_change, **kwargs)

    def build_schema(self, value: Any) -> Node:
        props: dict[str, Any] = {"options": self._options}
        if self._multiple:
            props["multiple"] = True
        if self._search:
            props["search"] = True
        return _field(lay.node("select", id="value", model="value", props=props), self._label)

    def set_options(self, options: Iterable[Any]) -> None:
        """Replace the option list (rebuilds the node tree)."""

        self._options = lay.options(options)
        self.update_schema(self.build_schema(self.value))


class Checkbox(_Control):
    """Boolean checkbox (or a custom on-value when ``checked_value`` is set)."""

    node_type = "checkbox"

    def __init__(
        self,
        value: bool = False,
        *,
        label: str | None = None,
        text: str = "",
        checked_value: Any = None,
        on_change: ValueCallback | None = None,
        **kwargs: Any,
    ) -> None:
        self._label = label
        self._text = text
        self._checked_value = checked_value
        super().__init__(value, on_change=on_change, **kwargs)

    def build_schema(self, value: Any) -> Node:
        props: dict[str, Any] = {}
        if self._text:
            props["title"] = self._text
        if self._checked_value is not None:
            props["value"] = self._checked_value
        return _field(lay.node("checkbox", id="value", model="value", props=props), self._label)


class Radio(_Control):
    """Radio group."""

    node_type = "radio"

    def __init__(
        self,
        value: Any = None,
        options: Iterable[Any] = (),
        *,
        label: str | None = None,
        on_change: ValueCallback | None = None,
        **kwargs: Any,
    ) -> None:
        normalized = lay.options(options)
        if value is None and normalized:
            value = normalized[0]["value"]
        self._label = label
        self._options = normalized
        super().__init__(value, on_change=on_change, **kwargs)

    def build_schema(self, value: Any) -> Node:
        return _field(
            lay.node("radio", id="value", model="value", props={"options": self._options}),
            self._label,
        )


class Switch(_Control):
    """Boolean switch."""

    node_type = "switch"

    def __init__(
        self,
        value: bool = False,
        *,
        label: str | None = None,
        text: str | None = "ON|OFF",
        checked_value: Any = None,
        unchecked_value: Any = None,
        on_change: ValueCallback | None = None,
        **kwargs: Any,
    ) -> None:
        self._label = label
        self._text = text
        self._checked_value = checked_value
        self._unchecked_value = unchecked_value
        super().__init__(value, on_change=on_change, **kwargs)

    def build_schema(self, value: Any) -> Node:
        props: dict[str, Any] = {}
        if self._text:
            props["text"] = self._text
        if self._checked_value is not None:
            props["checked_value"] = self._checked_value
        if self._unchecked_value is not None:
            props["unchecked_value"] = self._unchecked_value
        return _field(lay.node("switch", id="value", model="value", props=props), self._label)


# ---------------------------------------------------------------------------
# Value widgets
# ---------------------------------------------------------------------------


class Slider(_Control):
    """layui slider; ``value`` is a number or a ``[start, end]`` list in range mode."""

    node_type = "slider"

    def __init__(
        self,
        value: float | Sequence[float] = 0,
        *,
        label: str | None = None,
        min_value: float = 0,
        max_value: float = 100,
        step: float = 1,
        range: bool = False,
        vertical: bool = False,
        show_step: bool = False,
        tips: bool = True,
        on_change: ValueCallback | None = None,
        **kwargs: Any,
    ) -> None:
        if step <= 0:
            raise ValueError("step must be positive")
        if min_value >= max_value:
            raise ValueError("min_value must be < max_value")
        if range:
            if not isinstance(value, (list, tuple)) or len(value) != 2:
                raise ValueError("range sliders need a [start, end] value")
            low, high = sorted(float(v) for v in value)
            value = [
                _clamp_number(low, min_value, max_value),
                _clamp_number(high, min_value, max_value),
            ]
        else:
            value = _clamp_number(float(value), min_value, max_value)
        self._label = label
        self._min = min_value
        self._max = max_value
        self._step = step
        self._range = range
        self._vertical = vertical
        self._show_step = show_step
        self._tips = tips
        self.multiple = range
        super().__init__(value, on_change=on_change, **kwargs)

    def build_schema(self, value: Any) -> Node:
        return _field(
            lay.node(
                "slider",
                id="value",
                model="value",
                props={
                    "min_value": self._min,
                    "max_value": self._max,
                    "step": self._step,
                    "range": self._range,
                    "vertical": self._vertical,
                    "show_step": self._show_step,
                    "tips": self._tips,
                },
            ),
            self._label,
        )

    def set_value(self, value: float, index: int = 0) -> None:
        """Move one handle (or the single handle when index is ignored)."""

        if self._range:
            current = list(self.value)
            current[index] = value
            self.value = current
        else:
            self.value = value


class ColorPicker(_Control):
    """layui colorpicker."""

    node_type = "colorpicker"

    def __init__(
        self,
        value: str = "",
        *,
        label: str | None = None,
        format: str = "hex",
        alpha: bool = False,
        predefine: bool = False,
        on_change: ValueCallback | None = None,
        **kwargs: Any,
    ) -> None:
        self._label = label
        self._format = format
        self._alpha = alpha
        self._predefine = predefine
        super().__init__(value, on_change=on_change, **kwargs)

    def build_schema(self, value: Any) -> Node:
        return _field(
            lay.node(
                "colorpicker",
                id="value",
                model="value",
                props={
                    "format": self._format,
                    "alpha": self._alpha,
                    "predefine": self._predefine,
                    "color": value,
                },
            ),
            self._label,
        )


class DatePicker(_Control):
    """layui laydate date/time picker."""

    node_type = "datepicker"

    def __init__(
        self,
        value: str = "",
        *,
        label: str | None = None,
        type: str = "date",
        range: bool | str = False,
        format: str | None = None,
        min_value: str | None = None,
        max_value: str | None = None,
        on_change: ValueCallback | None = None,
        **kwargs: Any,
    ) -> None:
        self._label = label
        self._type = type
        self._range = range
        self._format = format
        self._min = min_value
        self._max = max_value
        super().__init__(value, on_change=on_change, **kwargs)

    def build_schema(self, value: Any) -> Node:
        props: dict[str, Any] = {"type": self._type, "range": self._range}
        if self._format:
            props["format"] = self._format
        if self._min is not None:
            props["min"] = self._min
        if self._max is not None:
            props["max"] = self._max
        if value:
            props["value"] = value
        return _field(lay.node("datepicker", id="value", model="value", props=props), self._label)


class Rate(_Control):
    """Star rating."""

    node_type = "rate"

    def __init__(
        self,
        value: float = 0,
        *,
        label: str | None = None,
        max_value: int = 5,
        half: bool = False,
        text: bool = False,
        on_change: ValueCallback | None = None,
        **kwargs: Any,
    ) -> None:
        if max_value <= 0:
            raise ValueError("max_value must be positive")
        self._label = label
        self._max = max_value
        self._half = half
        self._text = text
        super().__init__(value, on_change=on_change, **kwargs)

    def build_schema(self, value: Any) -> Node:
        return _field(
            lay.node(
                "rate",
                id="value",
                model="value",
                props={
                    "max_value": self._max,
                    "half": self._half,
                    "text": self._text,
                    "value": value,
                },
            ),
            self._label,
        )


# ---------------------------------------------------------------------------
# Composite controls
# ---------------------------------------------------------------------------


class Table(Layui):
    """layui table with row data and selected rows synced to Python."""

    data = traitlets.List(default_value=[]).tag(sync=True)

    def __init__(
        self,
        data: Iterable[Mapping[str, Any]] = (),
        columns: Iterable[Mapping[str, Any]] = (),
        *,
        selectable: bool = False,
        page: bool = False,
        height: int | str | None = None,
        on_change: Callable[..., None] | None = None,
        **kwargs: Any,
    ) -> None:
        rows = to_jsonable(list(data))
        cols = [dict(column) for column in columns]
        if not cols:
            cols = [{"field": key, "title": key} for key in (rows[0] if rows else {})]
        node = lay.table(
            "rows",
            cols,
            selectable=selectable,
            page=page,
            height=height,
            events=["checkbox", "tool", "row"] if selectable else ["tool", "row"],
        )
        self._selectable = selectable
        super().__init__(
            node,
            state={"rows": rows, "selection": []},
            on_change=on_change,
            **dict(kwargs, data=rows),
        )
        self._sync_guard = False
        self.observe(self._on_data_trait, names="data")
        self.observe(self._on_state_rows, names="state")
        self._sync_guard = True

    def _on_data_trait(self, change: dict[str, Any]) -> None:
        if not self._sync_guard:
            return
        self._sync_guard = False
        try:
            self.update_values({"rows": to_jsonable(change["new"])})
        finally:
            self._sync_guard = True

    def _on_state_rows(self, change: dict[str, Any]) -> None:
        rows = self.state.get("rows", [])
        if self.data != rows:
            self._sync_guard = False
            try:
                self.set_trait("data", rows)
            finally:
                self._sync_guard = True

    @property
    def selection(self) -> list[dict[str, Any]]:
        """Rows currently checked in the browser."""

        return list(self.state.get("selection", []))

    @property
    def rows(self) -> list[dict[str, Any]]:
        return list(self.state.get("rows", []))

    def set_rows(self, rows: Iterable[Mapping[str, Any]]) -> None:
        self.data = to_jsonable(list(rows))


class Tabs(Layui):
    """layui tabs whose active tab id is stored in ``state["active"]``."""

    def __init__(
        self,
        tabs: Mapping[str, Sequence[Node] | Node],
        *,
        active: str | None = None,
        on_change: Callable[..., None] | None = None,
        **kwargs: Any,
    ) -> None:
        items = [
            lay.tab(
                title,
                *(content if isinstance(content, (list, tuple)) else [content]),
                id=str(title),
            )
            for title, content in tabs.items()
        ]
        if not items:
            raise ValueError("tabs needs at least one entry")
        current = active if active is not None else items[0]["id"]
        super().__init__(
            lay.tabs(*items, model="active"),
            state={"active": current},
            on_change=on_change,
            **kwargs,
        )

    @property
    def active(self) -> str | None:
        return self.state.get("active")

    def select(self, tab_id: str) -> None:
        self.update_values({"active": tab_id})


class Button(Layui):
    """layui button with a click counter and callback."""

    clicks = traitlets.Int(0).tag(sync=True)
    last_click = traitlets.Dict(default_value={}).tag(sync=True)

    def __init__(
        self,
        label: str = "按钮",
        *,
        theme: str | None = "primary",
        on_click: Callable[..., None] | None = None,
        **kwargs: Any,
    ) -> None:
        node = lay.button(label, id="button", theme=theme)
        super().__init__(node, **kwargs)
        self._click_callbacks: list[Callable[..., None]] = []
        if on_click is not None:
            self.on_click(on_click)
        self.observe(self._on_click_event, names="event")

    def on_click(self, callback: Callable[..., None]) -> Callable[..., None]:
        if not callable(callback):
            raise TypeError("callback must be callable")
        self._click_callbacks.append(callback)
        return callback

    def _on_click_event(self, change: dict[str, Any]) -> None:
        event = change["new"] or {}
        if event.get("event") != "click":
            return
        self.clicks += 1
        self.last_click = event
        for callback in tuple(self._click_callbacks):
            try:
                callback(event)
            except Exception:
                _LOGGER.exception("layui button callback failed")


def _clamp_number(value: Any, minimum: float | None, maximum: float | None) -> Any:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return value
    if minimum is not None:
        number = max(number, minimum)
    if maximum is not None:
        number = min(number, maximum)
    return int(number) if number.is_integer() else number


__all__ = [
    "Button",
    "Checkbox",
    "ColorPicker",
    "DatePicker",
    "Input",
    "InputNumber",
    "Radio",
    "Rate",
    "Select",
    "Slider",
    "Switch",
    "Table",
    "Tabs",
    "Textarea",
]
