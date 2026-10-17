"""The generic layui anywidget container."""

from __future__ import annotations

import inspect
import logging
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Any

import anywidget
import traitlets

from .schema import Node, to_jsonable

_STATIC = Path(__file__).parent / "static"
_THEMES = {"auto", "light", "dark"}
_LOGGER = logging.getLogger(__name__)

ChangeCallback = Callable[..., None]
EventCallback = Callable[..., None]


def _normalize_schema(schema: Any) -> list[Node]:
    if schema is None:
        return []
    if isinstance(schema, Mapping):
        schema = [schema]
    elif isinstance(schema, (str, bytes)):
        raise TypeError("schema must be a node mapping or a sequence of nodes")
    else:
        schema = list(schema)

    nodes: list[Node] = []
    for index, item in enumerate(schema):
        if not isinstance(item, Mapping):
            raise TypeError(f"schema item {index} must be a mapping, got {type(item).__name__}")
        node = to_jsonable(dict(item))
        if "type" not in node:
            raise ValueError(f"schema item {index} is missing the 'type' key")
        nodes.append(node)
    return nodes


def _normalize_state(state: Any) -> dict[str, Any]:
    if state is None:
        return {}
    if not isinstance(state, Mapping):
        raise TypeError("state must be a mapping")
    return to_jsonable(dict(state))


class Layui(anywidget.AnyWidget):
    """Render layui components from a declarative Python schema.

    Python builds a list of component nodes with :mod:`layui_anywidget.lay`;
    the browser resolves each node to the matching layui component.  A shared
    ``state`` dictionary carries bound values, while ``event`` carries the most
    recent browser event.

    Example:
        ```python
        import layui_anywidget as layui
        from layui_anywidget import lay

        widget = layui.Layui(
            lay.form(
                lay.input("name", label="Name"),
                lay.slider("level", label="Level"),
            ),
            state={"name": "", "level": 5},
        )
        widget
        ```
    """

    _esm = _STATIC / "layui-bridge.js"
    _css = _STATIC / "layui-anywidget.css"

    schema = traitlets.List(default_value=[]).tag(sync=True)
    state = traitlets.Dict(default_value={}).tag(sync=True)
    event = traitlets.Dict(default_value={}).tag(sync=True)

    theme = traitlets.Enum(tuple(sorted(_THEMES)), default_value="auto").tag(sync=True)
    height = traitlets.Unicode("auto").tag(sync=True)
    sync_throttle_ms = traitlets.Int(100).tag(sync=True)
    config = traitlets.Dict(default_value={}).tag(sync=True)
    loading_text = traitlets.Unicode("Loading layui…").tag(sync=True)
    ready = traitlets.Bool(False).tag(sync=True)
    error = traitlets.Unicode("").tag(sync=True)

    def __init__(
        self,
        schema: Node | Sequence[Node] | None = None,
        *,
        state: Mapping[str, Any] | None = None,
        theme: str = "auto",
        height: str = "auto",
        sync_throttle_ms: int = 100,
        config: Mapping[str, Any] | None = None,
        on_change: ChangeCallback | None = None,
        on_event: EventCallback | None = None,
        **kwargs: Any,
    ) -> None:
        if theme not in _THEMES:
            raise ValueError(f"theme must be one of {sorted(_THEMES)}")
        if sync_throttle_ms < 0:
            raise ValueError("sync_throttle_ms must be >= 0")

        self._change_callbacks: list[ChangeCallback] = []
        self._event_callbacks: list[EventCallback] = []
        self._last_state: dict[str, Any] = {}
        self._last_event_seq = 0

        nodes = _normalize_schema(schema)
        initial_state = _normalize_state(state)

        super().__init__(
            schema=nodes,
            state=initial_state,
            theme=theme,
            height=height,
            sync_throttle_ms=sync_throttle_ms,
            config=to_jsonable(dict(config or {})),
            **kwargs,
        )

        self._last_state = dict(initial_state)
        if on_change is not None:
            self.on_change(on_change)
        if on_event is not None:
            self.on_event(on_event)

        self._attach_observers()

    # -- observers ---------------------------------------------------------

    def _attach_observers(self) -> None:
        self.observe(self._handle_state_change, names="state")
        self.observe(self._handle_event, names="event")

    @traitlets.validate("schema")
    def _validate_schema(self, proposal: dict[str, Any]) -> list[Node]:
        return _normalize_schema(proposal["value"])

    @traitlets.validate("state")
    def _validate_state(self, proposal: dict[str, Any]) -> dict[str, Any]:
        return _normalize_state(proposal["value"])

    # -- callbacks ---------------------------------------------------------

    def on_change(self, callback: ChangeCallback) -> ChangeCallback:
        """Register a state-change callback receiving ``(state, changed)``."""

        if not callable(callback):
            raise TypeError("callback must be callable")
        self._change_callbacks.append(callback)
        return callback

    def on_event(self, callback: EventCallback) -> EventCallback:
        """Register a browser-event callback receiving the event mapping."""

        if not callable(callback):
            raise TypeError("callback must be callable")
        self._event_callbacks.append(callback)
        return callback

    def remove_change_callback(self, callback: ChangeCallback) -> None:
        self._change_callbacks.remove(callback)

    def remove_event_callback(self, callback: EventCallback) -> None:
        self._event_callbacks.remove(callback)

    # -- state helpers -----------------------------------------------------

    @property
    def values(self) -> dict[str, Any]:
        """A copy of the current state dictionary."""

        return dict(self.state)

    def get_value(self, key: str, default: Any = None) -> Any:
        """Read one state entry (``get_state`` is reserved by ipywidgets)."""

        return self.state.get(key, default)

    def set_values(self, **values: Any) -> None:
        """Merge JSON-safe values into state and sync the widget."""

        self.state = {**self.state, **to_jsonable(values)}

    def update_values(self, values: Mapping[str, Any]) -> None:
        """Merge a mapping into state and sync the widget."""

        if not isinstance(values, Mapping):
            raise TypeError("values must be a mapping")
        self.state = {**self.state, **to_jsonable(dict(values))}

    def update_schema(self, schema: Node | Sequence[Node] | None) -> None:
        """Replace the component tree; the browser re-renders it."""

        self.schema = _normalize_schema(schema)

    # -- internal ----------------------------------------------------------

    def _handle_state_change(self, change: dict[str, Any]) -> None:
        new_state = dict(change["new"])
        if new_state == self._last_state:
            return
        previous = self._last_state
        self._last_state = new_state
        changed = {key: value for key, value in new_state.items() if previous.get(key) != value}
        for key in previous:
            if key not in new_state:
                changed[key] = None
        if not changed:
            return
        self._invoke_change_callbacks(new_state, changed)

    def _invoke_change_callbacks(self, state: dict[str, Any], changed: dict[str, Any]) -> None:
        for callback in tuple(self._change_callbacks):
            try:
                _call_with_supported_args(callback, state, changed)
            except Exception:
                _LOGGER.exception("layui change callback failed")

    def _handle_event(self, change: dict[str, Any]) -> None:
        event = dict(change["new"])
        if not event:
            return
        sequence = event.get("seq")
        if isinstance(sequence, int):
            if sequence <= self._last_event_seq:
                return
            self._last_event_seq = sequence
        for callback in tuple(self._event_callbacks):
            try:
                callback(event)
            except Exception:
                _LOGGER.exception("layui event callback failed")


def _call_with_supported_args(callback: Callable[..., Any], *args: Any) -> None:
    """Call callbacks written for either one or two positional arguments."""

    try:
        signature = inspect.signature(callback)
    except (TypeError, ValueError):
        callback(*args)
        return

    positional = [
        parameter
        for parameter in signature.parameters.values()
        if parameter.kind in (parameter.POSITIONAL_ONLY, parameter.POSITIONAL_OR_KEYWORD)
    ]
    accepts_more = any(
        parameter.kind is parameter.VAR_POSITIONAL for parameter in signature.parameters.values()
    )
    if accepts_more or len(positional) >= len(args):
        callback(*args)
    else:
        callback(*args[: len(positional)])


LayuiWidget = Layui

__all__ = ["Layui", "LayuiWidget"]
