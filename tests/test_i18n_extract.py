"""Tests for the i18n msgid extractor (spec 072, Track A2).

Pure pytest, no Blender: the extractor is a bpy-free ``ast`` walk over the
addon source. It produces the ``(msgctxt, msgid)`` catalog (what actually
translates: Blender-auto-translated static strings + ``text=`` overrides +
``iface()`` calls) plus a worklist of deferred f-string dynamic strings.
Contexts follow the empirical Blender probe: operators translate under
``"Operator"``, everything else under ``"*"``.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts" / "blender"))

from extract_i18n import extract_from_source  # noqa: E402  - sys.path setup above

SAMPLE = """\
import bpy
from ..core.bpy_helpers.i18n import iface
from ..core._shared.report import report_info, report_warn


class PROSCENIO_OT_thing(bpy.types.Operator):
    bl_label = "Do Thing"
    bl_description = "Does the thing"


class PROSCENIO_PT_panel(bpy.types.Panel):
    bl_label = "My Panel"


class Props(bpy.types.PropertyGroup):
    field: bpy.props.StringProperty(name="Field Name", description="A field")
    mode: bpy.props.EnumProperty(
        items=[
            ("A", "Alpha", "The alpha mode"),
            ("B", "Beta", "The beta mode"),
        ],
    )

    def draw(self, context):
        self.layout.label(text="Inline label")
        self.layout.prop(context.scene, "field", text="Prop Label")
        self.layout.operator("proscenio.thing", text="Op Button")
        self.layout.label(text=f"dynamic {self.field}")
        report_info(self, "A literal report")
        report_warn(self, f"dynamic {self.mode}")
        x = iface("Wrapped dynamic")
        y = iface("With op context", "Operator")
"""


def _catalog(source: str) -> set[tuple[str, str]]:
    return set(extract_from_source(source).catalog)


def test_operator_label_and_description_use_operator_context() -> None:
    cat = _catalog(SAMPLE)
    assert ("Operator", "Do Thing") in cat
    assert ("Operator", "Does the thing") in cat


def test_panel_label_uses_default_context() -> None:
    assert ("*", "My Panel") in _catalog(SAMPLE)


def test_property_name_and_description() -> None:
    cat = _catalog(SAMPLE)
    assert ("*", "Field Name") in cat
    assert ("*", "A field") in cat


def test_enum_items_name_and_description() -> None:
    cat = _catalog(SAMPLE)
    assert {"Alpha", "The alpha mode", "Beta", "The beta mode"} <= {m for _, m in cat}


def test_enum_item_identifier_is_not_translated() -> None:
    """The enum identifier (tuple[0]) is a stable key, never a msgid."""
    assert ("*", "A") not in _catalog(SAMPLE)
    assert ("*", "B") not in _catalog(SAMPLE)


def test_iface_calls_with_and_without_context() -> None:
    cat = _catalog(SAMPLE)
    assert ("*", "Wrapped dynamic") in cat
    assert ("Operator", "With op context") in cat


def test_fstring_forms_are_not_catalog_entries() -> None:
    """f-strings are not translatable as-is; A3 rewrites them to iface templates."""
    cat = _catalog(SAMPLE)
    assert ("*", "dynamic {self.field}") not in cat
    assert ("*", "dynamic {self.mode}") not in cat


def test_report_literals_go_to_catalog_via_central_translation() -> None:
    """report.py routes messages through iface, so fixed report literals translate."""
    res = extract_from_source(SAMPLE)
    assert ("*", "A literal report") in set(res.catalog)
    assert "A literal report" not in {u.text for u in res.unwrapped}


def test_ui_text_literals_go_to_catalog() -> None:
    """label/prop/operator text= literals auto-translate (translate=True default),
    so they are catalog entries - no iface() wrapping needed."""
    cat = _catalog(SAMPLE)
    assert ("*", "Inline label") in cat
    assert ("*", "Prop Label") in cat
    assert ("*", "Op Button") in cat


def test_fstring_dynamic_calls_are_flagged_unwrapped() -> None:
    """f-string label/report args are flagged for A3 (as f-strings) too."""
    res = extract_from_source(SAMPLE)
    fstring_flags = {u.text: u.is_fstring for u in res.unwrapped}
    assert fstring_flags.get("dynamic {self.field}") is True
