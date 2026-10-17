"""layui components for anywidget hosts such as Jupyter and marimo."""

from __future__ import annotations

from . import schema as lay
from .controls import (
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
from .schema import Node, to_jsonable
from .widget import Layui, LayuiWidget

__all__ = [
    "Button",
    "Checkbox",
    "ColorPicker",
    "DatePicker",
    "Input",
    "InputNumber",
    "Layui",
    "LayuiWidget",
    "Node",
    "Radio",
    "Rate",
    "Select",
    "Slider",
    "Switch",
    "Table",
    "Tabs",
    "Textarea",
    "lay",
    "to_jsonable",
]

try:  # pragma: no cover - importlib.metadata is not always populated
    from importlib.metadata import PackageNotFoundError
    from importlib.metadata import version as _version

    __version__ = _version("layui-anywidget")
except PackageNotFoundError:  # pragma: no cover - running from a source checkout
    try:
        from pathlib import Path

        import tomllib

        with open(Path(__file__).parent.parent / "pyproject.toml", "rb") as handle:
            __version__ = tomllib.load(handle)["project"]["version"]
    except (OSError, KeyError, tomllib.TOMLDecodeError):
        __version__ = "0.0.0"
