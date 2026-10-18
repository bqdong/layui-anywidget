"""Shared helpers for the per-component demos.

Each demo follows the layout of the layui 2.x documentation pages
(``docs/<component>/index.md`` in the layui repository): a title, a
blockquote-style introduction, one section per feature, and — because these
are live widgets — the current Python-side values underneath.
"""

from __future__ import annotations

import json
from typing import Any

import marimo as mo


def heading(title: str, quote: str) -> Any:
    """Title plus the layui-style intro quote."""

    return mo.vstack(
        [
            mo.md(f"# {title}"),
            mo.callout(mo.md(quote), kind="info"),
        ],
        gap=0.5,
    )


def section(title: str, *blocks: Any) -> Any:
    """An ``<h2>`` section with its example blocks."""

    return mo.vstack([mo.md(f"## {title}"), *blocks], gap=0.75)


def value_panel(ui: Any, keys: list[str] | None = None) -> Any:
    """The bound state as a field/value table plus a JSON copy.

    ``keys`` restricts the table to the given keys so a demo can hide
    bookkeeping entries such as ``last_button``.
    """

    state = dict(ui.value.get("state", {}))
    if keys is not None:
        state = {key: state.get(key) for key in keys}
    rows = "\n".join(
        f"| `{key}` | `{json.dumps(value, ensure_ascii=False)}` |" for key, value in state.items()
    )
    body = json.dumps(state, ensure_ascii=False, indent=2, default=str)
    return mo.vstack(
        [
            mo.md("## 当前值"),
            mo.md("下面是 Python 端实时看到的 `state`："),
            mo.md(f"| 键 | 值 |\n| --- | --- |\n{rows}"),
            mo.accordion({"完整 JSON": mo.md(f"```json\n{body}\n```")}),
        ]
    )


def event_panel(ui: Any) -> Any:
    """The latest forwarded browser event, as the docs' `on` example."""

    event = ui.value.get("event") or {}
    if not event:
        text = "（尚无事件）"
    else:
        text = (
            f"`{event.get('event')}` · `{event.get('type')}` · "
            f"`{event.get('id')}` = `{json.dumps(event.get('value'), ensure_ascii=False)}`"
        )
    return mo.md(f"**最近事件**：{text}")


def card(*children: Any) -> Any:
    """Group a demo's widget with a short description."""

    return mo.vstack(children, gap=0.5)
