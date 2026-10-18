"""JSON-friendly schema helpers and the ``lay`` constructor namespace."""

from __future__ import annotations

import dataclasses
import math
from collections.abc import Iterable, Mapping, Sequence
from datetime import date, datetime, time
from enum import Enum
from pathlib import Path
from typing import Any

Node = dict[str, Any]


def to_jsonable(value: Any, _seen: set[int] | None = None) -> Any:
    """Convert common Python values to values ``json.dumps`` can serialize.

    Widget schema and state travel through the Jupyter comm as JSON, so this
    is the single boundary where values are checked.  numpy scalars/arrays,
    pandas timestamps, enums, dataclasses, dates, and paths are converted;
    callables and arbitrary objects raise ``TypeError``.
    """

    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError(f"Non-finite float is not JSON serializable: {value!r}")
        return value
    if isinstance(value, Enum):
        return to_jsonable(value.value, _seen)
    if isinstance(value, (datetime, date, time)):
        return value.isoformat()
    if isinstance(value, Path):
        return str(value)

    if _seen is None:
        _seen = set()

    if isinstance(value, Mapping):
        marker = id(value)
        if marker in _seen:
            raise ValueError("Circular reference in widget schema/state")
        _seen.add(marker)
        try:
            return {str(key): to_jsonable(item, _seen) for key, item in value.items()}
        finally:
            _seen.remove(marker)

    if isinstance(value, (list, tuple, set, frozenset)):
        marker = id(value)
        if marker in _seen:
            raise ValueError("Circular reference in widget schema/state")
        _seen.add(marker)
        try:
            return [to_jsonable(item, _seen) for item in value]
        finally:
            _seen.remove(marker)

    # numpy arrays and pandas objects expose tolist()/item()/isoformat().
    if hasattr(value, "tolist"):
        return to_jsonable(value.tolist(), _seen)
    if hasattr(value, "item") and not hasattr(value, "__dict__"):
        return to_jsonable(value.item(), _seen)
    if hasattr(value, "isoformat"):
        return value.isoformat()
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return to_jsonable(dataclasses.asdict(value), _seen)

    raise TypeError(
        "Value is not JSON serializable for a layui widget: "
        f"{type(value).__name__}. Pass a string, number, bool, list, or dict "
        "instead."
    )


# ---------------------------------------------------------------------------
# Node construction
# ---------------------------------------------------------------------------


def _event_map(events: Any) -> dict[str, str] | None:
    if events is None:
        return None
    if isinstance(events, str):
        return {events: events}
    if isinstance(events, Mapping):
        return {str(key): str(value) for key, value in events.items()}
    return {str(event): str(event) for event in events}


def _children(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, (str, bytes, Mapping)):
        return [value]
    if isinstance(value, Iterable):
        return list(value)
    return [value]


def node(
    component: str,
    *children: Any,
    id: str | None = None,
    model: str | None = None,
    bind: Mapping[str, str] | None = None,
    events: Mapping[str, str] | Sequence[str] | str | None = None,
    updates: Mapping[str, str] | None = None,
    props: Mapping[str, Any] | None = None,
    class_: str | Sequence[str] | None = None,
    style: Mapping[str, Any] | str | None = None,
    visible: Any = None,
    text: Any = None,
    children_key: Sequence[Any] | None = None,
    **kwargs: Any,
) -> Node:
    """Build a declarative layui node.

    Args:
        component: Component type such as ``"slider"``, ``"table"``, or a plain
            HTML tag such as ``"div"``.
        children: Child nodes, strings, or numbers.
        id: Stable node id.  It is used to derive the layui ``lay-filter`` and
            is included in event payloads; auto-generated when omitted.
        model: State key bound two-way to the component value.
        bind: Mapping of component prop to state key for one-way bindings,
            e.g. ``{"data": "rows"}``.
        events: Event names to forward to Python.  A string or sequence maps
            each name to itself; a mapping allows renaming.
        updates: Mapping of event name to state key; the event value is written
            to state before the event is forwarded.
        props: Static component props, passed to the layui render options.
        class_: Extra CSS class or classes on the component root.
        style: Inline style (CSS string or mapping).
        visible: Boolean, state key, or ``{"key": ..., "equals": ...}``.
        text: Text content for ``type="text"`` nodes.
        children_key: Alias for ``children`` (useful when a prop is named
            ``children``).
        **kwargs: Additional static props; these win over ``props``.
    """

    if not isinstance(component, str) or not component:
        raise TypeError("component must be a non-empty string")

    result: Node = {"type": component}

    if id is not None:
        result["id"] = str(id)
    if model is not None:
        result["model"] = str(model)
    if bind:
        result["bind"] = {str(key): str(value) for key, value in bind.items()}
    if events is not None:
        mapped = _event_map(events)
        if mapped:
            result["events"] = mapped
    if updates:
        result["updates"] = {str(key): str(value) for key, value in updates.items()}
    if class_ is not None:
        result["class"] = class_
    if style is not None:
        result["style"] = style
    if visible is not None:
        result["visible"] = visible
    if text is not None:
        result["text"] = text

    merged: dict[str, Any] = dict(props or {})
    merged.update(kwargs)
    if merged:
        result["props"] = merged

    all_children = list(children) + _children(children_key)
    if all_children:
        result["children"] = all_children

    return to_jsonable(result)


# ---------------------------------------------------------------------------
# Option normalization
# ---------------------------------------------------------------------------


def options(values: Iterable[Any]) -> list[dict[str, Any]]:
    """Normalize scalars/mappings/pairs into ``{"label", "value"}`` dicts."""

    result: list[dict[str, Any]] = []
    for item in values:
        if isinstance(item, Mapping):
            data = dict(item)
            label = data.pop("label", None)
            value = data.pop("value", label)
            if label is None:
                label = value
            if value is None:
                value = label
            entry: dict[str, Any] = {"label": label, "value": value}
            entry.update(data)
            result.append(entry)
        elif isinstance(item, (tuple, list)) and len(item) == 2:
            result.append({"label": item[0], "value": item[1]})
        else:
            result.append({"label": item, "value": item})
    return result


# ---------------------------------------------------------------------------
# Form controls
# ---------------------------------------------------------------------------


def field(*children: Any, label: str | None = None, **props: Any) -> Node:
    """Wrap content in a ``.layui-form-item`` with an optional label.

    The ``field`` node type is rendered by the bridge as a form item; a child
    may itself be a ``field``, in which case only the innermost label applies.
    """

    props = dict(props)
    if label is not None:
        props["label"] = label
    return node("field", *children, props=props)


def form(*children: Any, filter: str | None = None, **props: Any) -> Node:
    """Build a layui form container."""

    props = dict(props)
    if filter:
        props["lay-filter"] = filter
    return node("form", *children, class_="layui-form", props=props)


def input(
    key: str,
    *,
    label: str | None = None,
    placeholder: str | None = None,
    textarea: bool = False,
    events: Mapping[str, str] | Sequence[str] | str | None = None,
    **props: Any,
) -> Node:
    """Build a text input or textarea bound to ``state[key]``."""

    if placeholder is not None:
        props.setdefault("placeholder", placeholder)
    return field(
        node(
            "textarea" if textarea else "input",
            id=key,
            model=key,
            events=events,
            props=props,
        ),
        label=label,
    )


def textarea(
    key: str,
    *,
    label: str | None = None,
    events: Mapping[str, str] | Sequence[str] | str | None = None,
    **props: Any,
) -> Node:
    return input(key, label=label, textarea=True, events=events, **props)


def input_number(
    key: str,
    *,
    label: str | None = None,
    min_value: float | None = None,
    max_value: float | None = None,
    step: float | None = None,
    events: Mapping[str, str] | Sequence[str] | str | None = None,
    **props: Any,
) -> Node:
    """Build a numeric input bound to ``state[key]``."""

    if min_value is not None:
        props["min"] = min_value
    if max_value is not None:
        props["max"] = max_value
    if step is not None:
        props["step"] = step
    props["type"] = "number"
    return field(
        node("input", id=key, model=key, events=events, props=props),
        label=label,
    )


def select(
    key: str,
    values: Iterable[Any] = (),
    *,
    label: str | None = None,
    multiple: bool = False,
    search: bool = False,
    events: Mapping[str, str] | Sequence[str] | str | None = None,
    **props: Any,
) -> Node:
    """Build a select bound to ``state[key]``."""

    props["options"] = options(values)
    if multiple:
        props["multiple"] = True
    if search:
        props["search"] = True
    return field(
        node("select", id=key, model=key, events=events, props=props),
        label=label,
    )


def checkbox(
    key: str,
    text: str = "",
    *,
    label: str | None = None,
    value: Any = None,
    events: Mapping[str, str] | Sequence[str] | str | None = None,
    **props: Any,
) -> Node:
    """Build a checkbox bound to ``state[key]``.

    Without ``value`` the bound state is a boolean.  Passing ``value`` makes
    the checked state report that value instead (layui's ``value``/``on``
    convention), or use ``multiple=True`` for a list of checked values with
    ``checkbox_group``.
    """

    props = dict(props)
    if value is not None:
        props["value"] = value
    if text:
        props["title"] = text
    control = node("checkbox", id=key, model=key, events=events, props=props)
    return field(control, label=label)


def checkbox_group(
    key: str,
    values: Iterable[Any] = (),
    *,
    label: str | None = None,
    **props: Any,
) -> Node:
    """Build a group of checkboxes bound to ``state[key]`` as a list."""

    props = dict(props)
    props["options"] = options(values)
    return field(
        node("checkbox-group", id=key, model=key, props=props),
        label=label,
    )


def switch(
    key: str,
    *,
    label: str | None = None,
    text: str | None = None,
    checked_value: Any = None,
    unchecked_value: Any = None,
    events: Mapping[str, str] | Sequence[str] | str | None = None,
    **props: Any,
) -> Node:
    """Build a switch bound to ``state[key]`` (boolean unless values given)."""

    props = dict(props)
    if text is not None:
        props["text"] = text
    if checked_value is not None:
        props["checked_value"] = checked_value
    if unchecked_value is not None:
        props["unchecked_value"] = unchecked_value
    return field(
        node("switch", id=key, model=key, events=events, props=props),
        label=label,
    )


def radio(
    key: str,
    values: Iterable[Any] = (),
    *,
    label: str | None = None,
    events: Mapping[str, str] | Sequence[str] | str | None = None,
    **props: Any,
) -> Node:
    """Build a radio group bound to ``state[key]``."""

    props["options"] = options(values)
    return field(
        node("radio", id=key, model=key, events=events, props=props),
        label=label,
    )


def button(
    label_text: str = "按钮",
    *,
    id: str | None = None,
    theme: str | None = None,
    class_: str | Sequence[str] | None = None,
    events: Mapping[str, str] | str | None = None,
    html: str | None = None,
    **props: Any,
) -> Node:
    """Build a layui button. Clicks are forwarded by default.

    ``events`` is a name or mapping; click payloads reach Python through
    ``Layui.on_event`` (or the ``Button`` control's ``on_click``). Pass
    ``html`` for icon markup such as
    ``'<i class="layui-icon layui-icon-edit"></i>'``; it replaces the label.
    """

    event_map = _event_map(events) or {}
    if not isinstance(events, Mapping):
        # A sequence would be split into per-character event names; only a
        # single event string makes sense for a button.
        event_map = {"click": events} if events else {}
    event_map.setdefault("click", "click")
    props = dict(props)
    if theme is not None:
        props["theme"] = theme
    if class_ is not None:
        props["class_"] = class_
    if html is not None:
        props["html"] = html
    return node("button", label_text, id=id, events=event_map, class_="layui-btn", props=props)


def submit(
    label_text: str = "提交",
    *,
    filter: str | None = None,
    theme: str = "primary",
    **props: Any,
) -> Node:
    """Build a ``lay-submit`` button wired to ``form.on("submit(filter)")``."""

    props["lay-submit"] = True
    if filter:
        props["lay-filter"] = filter
    return button(label_text, theme=theme, **props)


# ---------------------------------------------------------------------------
# Value widgets
# ---------------------------------------------------------------------------


def slider(
    key: str,
    *,
    label: str | None = None,
    min_value: float = 0,
    max_value: float = 100,
    step: float = 1,
    range: bool = False,
    vertical: bool = False,
    show_step: bool = False,
    tips: bool = True,
    events: Mapping[str, str] | Sequence[str] | str | None = None,
    **props: Any,
) -> Node:
    """Build a layui slider bound to ``state[key]``."""

    props.update(
        {
            "min_value": min_value,
            "max_value": max_value,
            "step": step,
            "range": range,
            "vertical": vertical,
            "show_step": show_step,
            "tips": tips,
        }
    )
    return field(
        node("slider", id=key, model=key, events=events, props=props),
        label=label,
    )


def colorpicker(
    key: str,
    *,
    label: str | None = None,
    format: str = "hex",
    alpha: bool = False,
    predefine: bool = False,
    events: Mapping[str, str] | Sequence[str] | str | None = None,
    **props: Any,
) -> Node:
    return field(
        node(
            "colorpicker",
            id=key,
            model=key,
            events=events,
            props={"format": format, "alpha": alpha, "predefine": predefine, **props},
        ),
        label=label,
    )


def datepicker(
    key: str,
    *,
    label: str | None = None,
    type: str = "date",
    range: bool | str = False,
    format: str | None = None,
    min_value: str | None = None,
    max_value: str | None = None,
    events: Mapping[str, str] | Sequence[str] | str | None = None,
    **props: Any,
) -> Node:
    props.update({"type": type, "range": range})
    if format:
        props["format"] = format
    if min_value is not None:
        props["min"] = min_value
    if max_value is not None:
        props["max"] = max_value
    return field(
        node("datepicker", id=key, model=key, events=events, props=props),
        label=label,
    )


def rate(
    key: str,
    *,
    label: str | None = None,
    max_value: int = 5,
    half: bool = False,
    text: bool = False,
    events: Mapping[str, str] | Sequence[str] | str | None = None,
    **props: Any,
) -> Node:
    return field(
        node(
            "rate",
            id=key,
            model=key,
            events=events,
            props={"max_value": max_value, "half": half, "text": text, **props},
        ),
        label=label,
    )


# ---------------------------------------------------------------------------
# Display widgets
# ---------------------------------------------------------------------------


def table(
    data_key: str,
    columns: Iterable[Mapping[str, Any]],
    *,
    label: str | None = None,
    selectable: bool = False,
    page: bool = False,
    height: int | str | None = None,
    events: Mapping[str, str] | Sequence[str] | str | None = None,
    updates: Mapping[str, str] | None = None,
    **props: Any,
) -> Node:
    """Build a layui table whose rows come from ``state[data_key]``.

    Args:
        data_key: State key containing the row list.
        columns: layui column definitions, e.g.
            ``{"field": "name", "title": "姓名", "sort": True}``.
        selectable: Enable the checkbox column.
        page: Enable client-side pagination.
        height: Fixed table height (layui supports ``"full-<offset>"`` too).
        events: Forwarded table events, e.g. ``["tool", "row", "checkbox"]``.
    """

    cols = [dict(column) for column in columns]
    if selectable:
        cols.insert(0, {"type": "checkbox", "fixed": "left"})
    props = dict(props)
    props["cols"] = [cols]
    if page:
        props.setdefault("page", True)
    if height is not None:
        props["height"] = height
    event_map = _event_map(events) or {}
    if selectable:
        event_map.setdefault("checkbox", "checkbox")
    return node(
        "table",
        id=data_key,
        bind={"data": data_key},
        events=event_map,
        updates={"checkbox": "selection", **(updates or {})} if selectable else updates,
        props=props,
    )


def tabs(*items: Node, model: str | None = None, **props: Any) -> Node:
    """Build a layui tabs component from :func:`tab` children."""

    return node("tabs", *items, model=model, props=props)


def tab(title: str, *children: Any, id: str | None = None, **props: Any) -> Node:
    props.setdefault("title", title)
    return node("tab", *children, id=id, props=props)


def collapse(*items: Node, accordion: bool = False, **props: Any) -> Node:
    props.setdefault("accordion", accordion)
    return node("collapse", *items, class_="layui-collapse", props=props)


def collapse_item(title: str, *children: Any, **props: Any) -> Node:
    props.setdefault("title", title)
    return node("collapse-item", *children, props=props)


def dropdown(
    trigger: Node | str,
    items: Iterable[Any],
    *,
    trigger_event: str = "click",
    events: Mapping[str, str] | Sequence[str] | str | None = None,
    updates: Mapping[str, str] | None = None,
    **props: Any,
) -> Node:
    """Build a dropdown menu.

    ``items`` accepts ``{"title": ..., "id": ...}`` mappings, plain strings,
    or ``{"type": "divider"}`` separators.
    """

    normalized: list[dict[str, Any]] = []
    for item in items:
        if isinstance(item, str):
            normalized.append({"title": item, "id": item})
            continue
        entry = dict(item)
        # layui marks a separator with the literal type "-" and ignores
        # entries whose type it does not know (they render as normal items).
        if entry.get("type") == "divider":
            entry = {"type": "-"}
        normalized.append(entry)
    trigger_node = (
        trigger
        if isinstance(trigger, dict)
        else node("span", trigger, class_="layui-btn layui-btn-primary")
    )
    event_map = _event_map(events) or {"click": "click"}
    props = {**props, "data": normalized, "trigger": trigger_event}
    return node(
        "dropdown",
        trigger_node,
        id=props.pop("id", None),
        events=event_map,
        updates=updates,
        props=props,
    )


def menu(items: Iterable[Any], *, model: str | None = None, **props: Any) -> Node:
    normalized: list[dict[str, Any]] = []
    for item in items:
        if isinstance(item, str):
            normalized.append({"title": item, "id": item})
        else:
            normalized.append(dict(item))
    return node("menu", model=model, class_="layui-nav", props={"items": normalized, **props})


def breadcrumb(items: Iterable[Any], **props: Any) -> Node:
    normalized = [dict(item) if isinstance(item, Mapping) else {"title": item} for item in items]
    return node("breadcrumb", class_="layui-breadcrumb", props={"items": normalized, **props})


def progress(value_key: str, *, show_percent: bool = True, **props: Any) -> Node:
    return node(
        "progress",
        bind={"value": value_key},
        class_="layui-progress",
        props={"show_percent": show_percent, **props},
    )


def carousel(
    *items: Node | str,
    model: str | None = None,
    height: str | None = None,
    **props: Any,
) -> Node:
    props = dict(props)
    if height is not None:
        props["height"] = height
    return node("carousel", *items, model=model, props=props)


def laypage(total: int, *, page_key: str | None = None, limit: int = 10, **props: Any) -> Node:
    bind = {"curr": page_key} if page_key else None
    return node(
        "laypage",
        bind=bind,
        updates={"change": page_key} if page_key else None,
        props={"count": total, "limit": limit, **props},
    )


# ---------------------------------------------------------------------------
# Layout and native elements
# ---------------------------------------------------------------------------


def div(
    *children: Any,
    class_: str | Sequence[str] | None = None,
    style: Mapping[str, Any] | str | None = None,
    **props: Any,
) -> Node:
    return node("div", *children, class_=class_, style=style, props=props)


def span(
    *children: Any,
    class_: str | Sequence[str] | None = None,
    style: Mapping[str, Any] | str | None = None,
    **props: Any,
) -> Node:
    return node("span", *children, class_=class_, style=style, props=props)


def row(
    *children: Any,
    gap: int | str | None = None,
    class_: str | Sequence[str] | None = None,
    **props: Any,
) -> Node:
    """A ``layui-row`` grid row.

    Args:
        gap: Column gutter shorthand: ``15`` or ``"15"`` becomes
            ``layui-col-space15``.
    """

    classes = ["layui-row"]
    if gap is not None:
        classes.append(f"layui-col-space{gap}")
    if class_:
        classes.append(class_ if isinstance(class_, str) else " ".join(class_))
    return node("div", *children, class_=" ".join(classes), props=props)


def col(
    *children: Any,
    span: int | None = None,
    xs: int | None = None,
    sm: int | None = None,
    md: int | None = None,
    lg: int | None = None,
    xl: int | None = None,
    offset: int | None = None,
    class_: str | Sequence[str] | None = None,
    **props: Any,
) -> Node:
    """A grid column.

    Args:
        span: Shorthand for ``md`` (the common desktop size).
        xs, sm, md, lg, xl: Columns out of 12 at each breakpoint.
        offset: Left offset in columns at the ``md`` breakpoint.
    """

    sizes = {"xs": xs, "sm": sm, "md": md, "lg": lg, "xl": xl}
    if span is not None:
        sizes["md"] = span
    classes = [f"layui-col-{name}{value}" for name, value in sizes.items() if value is not None]
    if offset is not None:
        classes.append(f"layui-col-md-offset{offset}")
    if not classes:
        classes.append("layui-col")
    if class_:
        classes.append(class_ if isinstance(class_, str) else " ".join(class_))
    return node("div", *children, class_=" ".join(classes), props=props)


def text(value: Any, tag: str = "span", *, class_: Any = None, **props: Any) -> Node:
    return node("text", text=value, class_=class_, props={"tag": tag, **props})


def title(value: Any, level: int = 1, *, class_: Any = None, **props: Any) -> Node:
    return node("text", text=value, class_=class_, props={"tag": f"h{level}", **props})


def hr() -> Node:
    return node("hr")


def badge(content: Any, *, color: str | None = None, **props: Any) -> Node:
    props = dict(props)
    if color:
        props["lay-badge-color"] = color
    return node("span", content, class_="layui-badge", props=props)


__all__ = [
    "Node",
    "badge",
    "breadcrumb",
    "button",
    "carousel",
    "checkbox",
    "checkbox_group",
    "col",
    "collapse",
    "collapse_item",
    "colorpicker",
    "datepicker",
    "div",
    "dropdown",
    "field",
    "form",
    "hr",
    "input",
    "input_number",
    "laypage",
    "menu",
    "node",
    "options",
    "progress",
    "radio",
    "rate",
    "row",
    "select",
    "slider",
    "span",
    "submit",
    "switch",
    "tab",
    "table",
    "tabs",
    "text",
    "textarea",
    "title",
    "to_jsonable",
]
