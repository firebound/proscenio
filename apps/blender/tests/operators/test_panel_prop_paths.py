"""Panel-draw smoke test: every ``layout.prop(data, name)`` a Proscenio panel
issues must name a property that actually exists on ``data``'s RNA.

Panel ``draw()`` is not otherwise exercised headlessly, so a wrong prop path -
e.g. after the ProscenioSkinningProps nesting (spec 075), a stale
``.prop(skinning, "automesh_resolution")`` that should now be
``.prop(skinning.automesh, "resolution")`` - would pass every other gate and only
break interactively. This drives each panel's draw with a recording layout stub +
the real fixture context and asserts each recorded prop path resolves.
"""

from __future__ import annotations

from types import SimpleNamespace

import bpy


class _RecLayout:
    """A UILayout stand-in: chainable, records prop() / prop_search() targets."""

    def __init__(self, calls: list[tuple[object, str]]) -> None:
        self._calls = calls
        # Writable UILayout attributes some draws set.
        self.alignment = "EXPAND"
        self.active = True
        self.enabled = True
        self.alert = False
        self.use_property_split = False
        self.use_property_decorate = False
        self.operator_context = "INVOKE_DEFAULT"
        self.scale_x = 1.0
        self.scale_y = 1.0
        self.ui_units_x = 0.0

    def prop(self, data: object, prop_name: str, *_a: object, **_k: object) -> None:
        self._calls.append((data, prop_name))

    def prop_search(self, data: object, prop_name: str, *_a: object, **_k: object) -> None:
        self._calls.append((data, prop_name))

    def operator(self, *_a: object, **_k: object) -> SimpleNamespace:
        # Draws set attributes on the returned operator properties struct.
        return SimpleNamespace()

    def panel(self, *_a: object, **_k: object) -> tuple[_RecLayout, _RecLayout]:
        return self, self

    def row(self, *_a: object, **_k: object) -> _RecLayout:
        return self

    def column(self, *_a: object, **_k: object) -> _RecLayout:
        return self

    def column_flow(self, *_a: object, **_k: object) -> _RecLayout:
        return self

    def box(self, *_a: object, **_k: object) -> _RecLayout:
        return self

    def split(self, *_a: object, **_k: object) -> _RecLayout:
        return self

    def grid_flow(self, *_a: object, **_k: object) -> _RecLayout:
        return self

    def __getattr__(self, _name: str):
        # label / separator / template_* / menu / any other layout call: a no-op
        # that keeps the chain alive and swallows args.
        return lambda *_a, **_k: self


_PANEL_MODULES = ("mesh_generation", "weight_paint")


def _proscenio_panels() -> list[type]:
    import importlib

    panels: list[type] = []
    for name in _PANEL_MODULES:
        mod = importlib.import_module(f"proscenio.panels.{name}")
        for attr in vars(mod).values():
            if (
                isinstance(attr, type)
                and getattr(attr, "bl_idname", "").startswith("PROSCENIO_PT")
                and hasattr(attr, "draw")
            ):
                panels.append(attr)
    return panels


def _activate(name: str) -> bpy.types.Object:
    obj = bpy.data.objects[name]
    bpy.context.view_layer.objects.active = obj
    for other in bpy.context.selected_objects:
        other.select_set(False)
    obj.select_set(True)
    return obj


def test_panel_prop_paths_resolve_on_their_data(automesh_fixture):
    """Drive every Mesh Generation + Weight Paint panel's draw() and assert each
    prop path names a real RNA property - the guard for the skinning-nesting
    rename (spec 075), whose panel prop strings are otherwise untested."""
    _activate("hand")
    # Debug pipeline is gated behind the debug preference; enable it so its
    # panel draws and its `skinning.debug.stage` prop path is exercised too.
    addon = bpy.context.preferences.addons.get("proscenio")
    if addon is not None and hasattr(addon.preferences, "debug_mode"):
        addon.preferences.debug_mode = True

    calls: list[tuple[object, str]] = []
    layout = _RecLayout(calls)
    drew: list[str] = []
    for panel in _proscenio_panels():
        poll = getattr(panel, "poll", None)
        if poll is not None and not poll(bpy.context):
            continue
        panel.draw(SimpleNamespace(layout=layout), bpy.context)  # type: ignore[arg-type]
        drew.append(panel.bl_idname)

    assert drew, "no Mesh Generation / Weight Paint panel drew - fixture activation failed"
    unresolved = [
        (type(data).__name__, name)
        for data, name in calls
        if getattr(data, "bl_rna", None) is not None and name not in data.bl_rna.properties
    ]
    assert not unresolved, f"panel prop paths that do not resolve on their PG: {unresolved}"

    # The nested skinning fields specifically must have been hit by the panels
    # above, so the rename's prop strings are actually covered (not vacuously).
    hit = {(type(d).__name__, n) for d, n in calls}
    # Mesh Generation must draw automesh.resolution; Weight Paint bind.init_mode.
    assert ("ProscenioAutomeshProps", "resolution") in hit
    assert ("ProscenioBindProps", "init_mode") in hit
