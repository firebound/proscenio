# PMD CPD duplication scan

Status: **scan done, findings triaged, no refactor started**. Exploratory pass to find code duplication that SonarQube misses.

## Problem

SonarQube (running locally) reports very little duplication on this repo. Its detector is line-based with a high threshold, so it only catches type-1 clones (exact copy-paste). The goal here was to surface the cheaper-to-miss families: type-2 (same structure, renamed identifiers) and type-3 (same structure with inserted or removed statements). Type-4 (same output, fully different logic) is out of reach for any cheap tool and stays a manual concern.

## Tool

PMD CPD (Copy-Paste Detector), token-based rather than line-based, so it matches structure through identifier renames and small gaps. Run via the official Docker image so no local Java install is needed (`pmdcode/pmd:latest`).

Command shape (per app, run from repo root):

```bash
docker run --rm -v "<repo>:/src" pmdcode/pmd:latest cpd \
    --minimum-tokens 35 \
    --language python \
    --dir /src/apps/blender \
    --no-fail-on-violation
```

On Windows the bind mount needs forward slashes (`/e/projects/...`) and `MSYS_NO_PATHCONV=1` under git-bash, or `${PWD}`-style forward-slash paths under PowerShell.

## Coverage

- `apps/blender` (180 Python files): scanned, `--language python`.
- `apps/photoshop` (73 TS + 21 TSX + 6 JS): scanned, `--language typescript`, `node_modules` excluded. TSX files may slip past the TypeScript tokenizer; jscpd with a babel tokenizer would close that gap if needed.
- `apps/godot` (35 GDScript files): not scanned. CPD has no GDScript tokenizer (nor does jscpd). No cheap tool exists for this app.
- `apps/docs`: only 3 real TS files (Docusaurus config), nothing to scan.

## Threshold tuning

`--minimum-tokens` controls the smallest block counted. Three passes:

- `50`: 45 blocks (blender) / 12 (photoshop). Misses mid-size clones.
- `20`: 453 / 216. Floods with noise. 77 percent of blender hits were 20-34 tokens: Blender API class boilerplate, import lines, three-line poll guards. Almost nothing actionable.
- `35`: 119 / 53. Sweet spot. Cuts most boilerplate noise while keeping the real signal. This is the kept result; raw output lives in `raw/`.

## Findings (at minimum-tokens 35)

### Blender API boilerplate (noise, not worth deduping)

Roughly 30 of the 85 production blocks are unavoidable Blender scaffolding: a 47-token block recurring across 40 operator and panel files (class header / registration), a 36-token block across 10 panels (`bl_space_type` / `bl_region_type` / `bl_category`), and per-subpanel poll/header headers (weight_paint repeats it 4-5 times). Blender requires these per-class attributes; deduping returns almost nothing.

### Real duplication worth refactoring

- `_resolve_image` is duplicated as a whole function across `operators/automesh/automesh.py` and `operators/automesh/automesh_authoring.py` (two blocks). Cleanest single fix: move to a shared helper.
- GPU line-draw sequence (`batch_for_shader` then blend / line-width set and reset) is copied inside `core/bpy_helpers/_shared/modal_overlay.py` (3x), `core/bpy_helpers/automesh/authoring_overlay.py`, and `core/bpy_helpers/skinning/weight_overlay.py`. Extract one `_draw_lines(shader, mode, verts, color, width)`.
- The MESH poll guard (`obj.type == "MESH"`) repeats across set_bone_mode, sidecar_io, automesh, uv_authoring, restore_weight_snapshot, preview_shader, edit_weights. Candidate for a `MeshOperatorMixin.poll`.
- Edge-building loop in `core/bpy_helpers/automesh/debug.py` lines 119 and 163 (137 tokens, the single largest block).
- Layer placement in `importers/photoshop/planes.py` lines 88 and 129.
- Selection-restore logic shared between `authoring_session.py` and `skinning/modal_session.py` (99 tokens).

### God-file smell (audit, not point-fix)

- `operators/automesh/automesh_authoring.py` (~1300 lines) shows 6-plus internal self-duplications plus cross-duplication with automesh.py. The duplication is a symptom of an inflated file; it wants a dedicated decomposition pass, not isolated edits.
- `core/bpy_helpers/automesh/authoring_overlay.py` has 5-plus internal duplications and cross-duplication with weight_overlay and automesh_authoring.

### Photoshop

All 9 production blocks concentrate in three files, mostly intra-file:

- `src/lib/planner.ts`: candidate-filter loop and optional spread-merge repeated (459/540, 755/767, 658/686).
- `src/api/export-flow.ts`: preview and run paths are near copy-paste of the same buildPlan-then-validate sequence (64/108/189, 140/209). Strongest unification target on this side.
- `src/api/import-flow.ts`: the placePngAt block (101/136), plus a cross-hit with png-writer.ts.

## Limitation

CPD only catches structural clones (type-1/2/3). Type-4 (logic that produces the same output through different syntax or algorithm) does not surface here and needs a manual or LLM-assisted read of suspect module pairs.

## Targets ranked by payoff

1. `_resolve_image` - whole-function cross-file clone, trivial clean fix.
2. export-flow.ts preview/run - 4 converging blocks, unify into one function.
3. GPU `_draw_lines` helper - 5-plus copies of the shader/blend sequence.
4. automesh_authoring.py - schedule a god-file decomposition, not a dedup pass.

## Raw outputs

- `raw/cpd-blender-t35.txt`: 119 blocks, full (includes tests and panels).
- `raw/cpd-blender-t35-prod.txt`: 85 blocks, production only (no `tests/`).
- `raw/cpd-photoshop-t35.txt`: 53 blocks, full.
- `raw/cpd-photoshop-t35-prod.txt`: 9 blocks, production only.
