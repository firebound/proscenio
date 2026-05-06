# SPEC 006 — TODO

Stub. Will be expanded when work starts. See [STUDY.md](STUDY.md).

## Decision lock-in (deferred)

- [ ] D1 — manifest format final shape
- [ ] D2 — atlas: auto-pack vs leave per-PNG
- [ ] D3 — armature stub: auto from Z-order or always manual
- [x] D4 — `<name>_<index>` sprite_frame convention (already locked in SPEC 007 D4)
- [ ] D5 — re-import semantics (idempotent vs additive)
- [ ] D6 — PSD → Blender coord conversion
- [ ] D7 — `.psd` direct vs JSX-only

## Implementation (pending)

- [ ] `core/psd_naming.py` — bpy-free convention parser
- [ ] `blender-addon/importers/photoshop/__init__.py` — manifest reader + plane stamper + material builder
- [ ] `PROSCENIO_OT_import_photoshop` operator
- [ ] Panel: import button (file picker) in main sidebar
- [ ] `tests/test_psd_naming.py`

## Blocked on

- JSX exporter contract finalization. Today's exporter is scaffold; manifest shape may evolve before SPEC 006 ships.
