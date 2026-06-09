# Code-duplication refactor - execution

The scan and triage are complete (see [STUDY.md](STUDY.md), [SUMMARY.md](SUMMARY.md), [FINDINGS-TYPE4.md](FINDINGS-TYPE4.md), [COVERAGE.md](COVERAGE.md)). This TODO is the execution plan for the part worth a dedicated pass.

## Status

Shipped on `refactor/025-dedup-high-tier` (behavior-preserving; gates green: ruff + ruff format + mypy 169 + pytest 621 + Blender 7/7 fixtures + 50 operators):

- **N2 - done.** `core/_shared/pg_cp_fallback.CPCarrier` is now the one CP read-Protocol (the `region` / `hydrate` / `validation._shared` copies deleted and routed in); `region._read_field`, `validation._shared.read_element_type` / `read_int`, `slots.read_slot_default` all route through `read_field`; `hydrate` reads via `.get` + a sentinel. Presence rule A (`is not None`) pinned by 3 new `test_pg_cp_fallback` cases; `.get` added to the hydrate/region/mirror test mocks. `mirror._CPWriter` (the write-Protocol) correctly left separate.
- **N1 - done.** New bpy-free `core/_shared/material_images.py` (`iter_material_node_images` / `iter_material_images` / `first_material_image`; `import bpy` only under `TYPE_CHECKING`, bodies via `getattr`). All 8 sites routed: automesh.py + automesh_authoring.py (the D1 byte-identical copies), writer `sprites._iter_tex_images` + `scene_discovery._iter_linked_images`, `atlas_pack/_paths.first_texture_image_name`, panel `_draw_sprite` size probe, `atlas_collect._find_first_image`, `validation.export._iter_object_atlas_filepaths`. The `TYPE_CHECKING`-only bpy import is what let the duck-typed, import-without-bpy modules (atlas_collect, validation - the latter `monkeypatch`es `bpy=None`) route through it. Subsumes D1.
- **D6 - partial (done for the single-batch cluster).** New `modal_overlay.draw_batch(prim, verts, color, *, line_width|point_size)`. Routed the 7 verbatim single-batch draws: `modal_overlay` `draw_line_3d` / `draw_dashed_line_3d` / `draw_circle_3d` + the text-panel bg, and `authoring_overlay` `_draw_polyline` / `_draw_edges` / `_draw_points`.

### Left intact / deferred (opportunistic)

- **D6 multi-batch renderers - left by design.** `authoring_overlay._draw_polylines`, `_draw_user_strokes`, `_draw_live_preview`, `_draw_delete_hover` (+ `_draw_stroke_lines`) and `weight_overlay._draw_color_groups` set the blend state once and loop several batches under a single `bind` (mixing POINTS + LINES per stroke). Collapsing each batch into `draw_batch` would re-cycle GPU state per batch and break the shared bind, so they keep their loop. Different shape, not the single-batch tail.
- **D4 `_image_filename` twins** (`sprites` vs `scene_discovery`) - not folded; that one is a "reconcile the empty-name return (`None` vs `""`)" decision, separate from the N1 image walk. Opportunistic.

### Open gate (keeps 025 open until cleared)

- **D6 in-editor visual smoke (workstation).** Headless registers the overlays but never invokes the POST_VIEW/POST_PIXEL draw callbacks, so the `draw_batch` routing is import/registration-verified only. Confirm at a GUI Blender: Automesh Authoring overlay (outer/inner polylines, Steiner + user dots, SIMPLE triangulation wireframe), Quick Armature preview line + anchor circle + dashed guide, the cursor tooltip panel. A draw regression here is a new bug. 025 stays open until this passes.

## Scope policy

The finding set splits cleanly into two halves with different handling:

- **HIGH tier - dedicated pass (this TODO).** Three families where a canonical helper either does not exist or is bypassed by 8-10 call sites: **N1** (find-texture-image), **N2** (PG/CP read + Protocol), **D6** (GPU draw). These have large fan-out and real drift risk, and several of them de-risk upcoming backlog work (N2 underlies the 1.0.0 PG-vs-CP storage split; N1 underlies the atlas-exclude and sprite-appearance features; D6 underlies the onion-skin / region-paint / pose-preview overlays). D1-D4 are subsumed by N1/N2.
- **Long tail - opportunistic, NOT a pass.** D7-D15, N9-N26, N17-N19 and the trivia. The STUDY says it directly: "D7-D12 as opportunistic cleanups when touching those modules". Each rides along with the next feature or fix that edits its file. Do not schedule a monolithic sweep for these; folding them in piecemeal avoids a large behavior-preserving diff with no feature behind it.

## Gates (run after each item; all behavior-preserving)

```sh
uvx ruff check apps/blender/
uvx ruff format --check apps/blender/
uv run --with mypy mypy --config-file apps/blender/pyproject.toml
uv run pytest tests/
```

Plus the in-Blender suites (registration + scenario integration):

```sh
& "E:\Program Files\Blender Foundation\Blender 5.1\blender.exe" --background --python apps/blender/tests/run_operator_tests.py
& "E:\Program Files\Blender Foundation\Blender 5.1\blender.exe" --background --python apps/blender/tests/run_tests.py
```

Each item is a pure consolidation: callers route to one helper, output unchanged. The suites are the proof; no new feature tests needed (add a unit for the new helper where it is pure).

## Item 1 - N1: one `iter_material_images(obj)` (largest fan-out)

The `for node in material.node_tree.nodes: if node.type == "TEX_IMAGE" and node.image` walk is hand-written in ~10 places, each returning a slightly different shape (image / name / size / filepath, or setting it). A canonical `iter_shader_nodes` exists in `core/bpy_helpers/_shared/_bpy_compat.py` but most sites ignore it.

- **New helper:** `iter_material_images(obj) -> Iterator[bpy.types.Image]` (or a small module exposing `first_material_image` / `iter_material_images` / image-size / image-filepath derivations on top of one walk). Home: `core/bpy_helpers/_shared/` (bpy-bound) since it touches `node_tree`.
- **Call sites to route through it** (from FINDINGS N1, verify each at edit time):
  - `operators/automesh/automesh.py:53` `_find_tex_image`
  - `operators/automesh/automesh_authoring.py:1283` `_find_tex_image` (the D1 copy)
  - `core/bpy_helpers/atlas/atlas_collect.py:98` `_find_first_image`
  - `panels/_draw_sprite.py:67` `_first_tex_image_size`
  - `core/validation/export.py:125` `_texture_image_filepath` + `_iter_object_atlas_filepaths`
  - `exporters/godot/writer/sprites.py:144` `_iter_tex_images`
  - `operators/atlas_pack/_paths.py:14` `first_texture_image_name` + `swap_image_in_materials`
- **Subsumes D1** (`_resolve_image` / `_find_tex_image` automesh copy) and **D4** (writer `_image_filename` shares the same image-resolve root - reconcile the empty-name return: `None` vs `""`).
- **Watch:** sites differ in what they return. The helper yields images; each caller keeps its own thin derivation (name, size, filepath) over the shared walk. `swap_image_in_materials` is a writer, not a reader - it sets the image; keep it separate or give the module a paired setter.
- **Unit:** the walk is bpy-bound, so cover via the operator suite; if any pure slice extracts, unit it.

## Item 2 - N2: one PG/CP read helper + one read-Protocol (decision-gated)

`core/_shared/pg_cp_fallback.py` already provides `read_field` + `read_bool_flag`, but the same "PG first, CP fallback, else default" logic is hand-rolled in `core/_shared/region.py:34` `_read_field`, `core/validation/_shared.py:22` `read_element_type` + `read_int`, and `exporters/godot/writer/slots.py:56` `read_slot_default`. They have **already drifted** in presence semantics.

The backing read-Protocol is defined **4 times** (FINDINGS says 5 - corrected: the 5th, `core/mirror.py:74` `_CPWriter`, is a write-Protocol via `__setitem__` and stays):

- `pg_cp_fallback._CPCarrier` - `.get(key, default)`
- `region._CPLookup` - `__contains__` + `__getitem__`
- `hydrate._CPLookup` - `__contains__` + `__getitem__`
- `validation/_shared._CPLookup` - `__contains__` + `__getitem__` + `.get`

### Decision (confirm before coding)

| # | Decision | Options | Recommend |
| --- | --- | --- | --- |
| N2-1 | Canonical READ Protocol | **A** `_CPCarrier` (`.get`, self-guarding, one method, already used by the two canonical helpers) / **B** `_CPLookup` (`__contains__`+`__getitem__`) | **A** |
| N2-2 | Presence rule | **A** `is not None` + `_missing` sentinel (explicit PG value incl `False`/`0`/`""` wins; None/absent -> CP; CP None/absent -> default) / **B** `hasattr` (field-declared wins even if None; registered PG never consults CP) / **C** truthiness (falsy -> CP; reintroduces the CP-True-over-PG-False bug `read_bool_flag` already fixed) | **A** |

Rationale for A+A: it is the rule `read_field` + the already-fixed `read_bool_flag` use, so only the bypassing copies migrate inward - the canonical helpers do not change. `.get` works on real `bpy.types.Object` (IDProperty dict) and on the `SimpleNamespace` mocks. One narrow behavior change under A: a *registered* PG sitting at its type-default no longer falls through to a legacy CP - irrelevant on the headless writer path (`props is None` there), which is the only live export caller.

### Work (after A+A confirmed)

- Keep `_CPCarrier` as the one read-Protocol in `pg_cp_fallback.py`; delete the three `_CPLookup` copies (region, hydrate, validation/_shared) and import the shared one. Relocate `mirror._CPWriter` beside it for tidiness (optional; it stays a distinct write-Protocol).
- `region._read_field` -> delete, route to `read_field`. `validation/_shared.read_element_type` -> `read_field(..., default="mesh")`. `read_int` -> keep its float-string tolerance (real domain logic - a CP holds user junk) but read via `_CPCarrier.get` + `is not None`. `slots.read_slot_default` -> `read_field(..., default="")`.
- `hydrate.hydrate_object` reads via `_CPLookup` for the one-shot copy; switch to `.get(key, _missing)` so it shares the Protocol.
- **Subsumes and enlarges D5.** **Preps the 1.0.0 backlog item** "Split PropertyGroup vs Custom Property storage by intent" - that rewrite changes *which* fields carry a CP, not *how* a CP-backed field is read, so this consolidation is the foundation it builds on, not throwaway.
- **Unit:** `pg_cp_fallback` is pure - add cases pinning the A+A presence rule (explicit `False`/`0`/`""` on PG wins; None/absent -> CP; CP absent -> default) so the rule cannot silently regress.

## Item 3 - D6: one `_draw_batch(prim, verts, color, width)` (largest single cluster)

The `batch_for_shader` -> `blend_set("ALPHA")` -> `line_width_set` -> `bind` -> `uniform_float("color")` -> `batch.draw` -> reset sequence repeats across ~8-10 overlay sites:

- `core/bpy_helpers/_shared/modal_overlay.py:43` `draw_line_3d`, `draw_dashed_line_3d`, `draw_circle_3d`
- `core/bpy_helpers/automesh/authoring_overlay.py` `_draw_polyline`, `_draw_polylines`, `_draw_edges`, `_draw_points`, `_draw_user_strokes`, `_draw_delete_hover`, `_draw_live_preview`
- `core/bpy_helpers/skinning/weight_overlay.py:76` `_draw_color_groups`

- **New primitive:** `_draw_batch(shader, prim_type, verts, color, *, line_width=None)` in `core/bpy_helpers/_shared/modal_overlay.py` (the existing home of the draw helpers). Each call site builds its batch via the primitive; per-site geometry (dashing, circle tessellation) stays at the site, only the bind/blend/draw/reset tail collapses.
- **Watch:** GPU draw runs only in a live modal - the headless gates do not exercise it. After the refactor, **in-editor visual smoke required** at the workstation: Automesh Authoring overlay (polyline / points / live preview / delete-hover), Quick Armature preview lines, Edit Weights color-group overlay. A draw regression here is invisible to CI. List this as the one item with a non-headless verification.
- **Extends N6** (cyclic loop-edge construction) and the authoring/weight overlay clusters; fold those in while here if cheap.

## After the HIGH tier

Backlog features become new specs (per the sequencing decision - dedup-prep first). Each lands on the consolidated helpers above; when a feature edits a file carrying a long-tail finding (D7-D15 / N9-N26), fold that finding into the same commit. Prune this spec once N1+N2+D6 ship and the tail policy is recorded here.
