# Handoff — Spec 074 (Blender code-audit remediation)

> Scratch handoff to resume on another device. **Delete before merging.**
> Date: 2026-06-30. Branch: `fix/074-phase-2-medium-correctness` (stacked on the
> PR #180 branch `fix/074-high-severity-correctness`).

---

## 1. PR #180 — review resolved (pushed)

PR #180 = spec 074 **Phase 1** (high-severity correctness). All CodeRabbit / CodeQL
feedback was triaged and the true items fixed in commit **`aa73cc3`** (pushed to
`fix/074-high-severity-correctness`), with replies on each thread + a consolidated PR
comment.

| Item | Verdict | Action |
|---|---|---|
| `cspell.json` lists 2 deleted files (`bugs-found.md`, `ui-feedback.md`) | true | removed both entries |
| `decisions.md:331` orphaned ref to the deleted "UI-feedback backlog" | true | reworded |
| 2 nitpicks: test-side `contextlib.suppress` masks the `_finish` contract | true | call `_finish` directly |
| ast-grep `json.dumps`→`jsonify` | false positive (jsonify is Flask) | skipped, explained |
| LanguageTool PT nits + "photoshop"/"statusbar" | false positive / out of scope | skipped, explained |
| CodeRabbit "CI failure `core.geometry_2d`" | stale | CI green on HEAD; module re-exported; not touched by the PR |

CI on #180 is green; CodeQL has no alerts. **Only remaining #180 work: human review + merge.**

---

## 2. Spec 074 Phase 2 — 9 of 11 items done (4 commits, local only)

Branch `fix/074-phase-2-medium-correctness`, **not yet pushed**. Commits (newest first):

- **`184490a`** — `unweighted-vertex-zero-column`: `build_sprite_weights` picks a
  deterministic real-bone fallback from `known_groups` when the attach bone isn't a
  real bone, so a zero-weight vertex never exports an all-zero (undeformed) column.
- **`488ffb7`** — `tablet-pressure-resets-tracker`: a mid-stroke pressure dip no longer
  flips+resets the Edit Weights tracker (gated on a new `_stroke_active` flag), so the
  post-dip tail of a stroke still flips to `user_paint` on release.
- **`5db44af`** — modal-lifecycle leak cluster (4 items): overlay register/refresh
  rollback on partial failure; `empty_overlay_handles()` fixes the missing
  `outer_preview` key; Manual Draw invoke calls `_finish` on setup failure;
  Edit Weights gains a `cancel()` hook.
- **`56913ff`** — provenance cluster (3 items): regen after a picker rig-switch flags
  `rig_mismatch` (was a silent orphan); a corrupt-sidecar regen now WARNS the
  provenance loss; named-snapshot restore rebuilds groups from the snapshot's own
  weights (not the renamed live baseline).

### Verification (all green locally)
- In-Blender operator suite: **271 passed** (`run_operator_tests.py`).
- Export goldens: **8/8** byte-identical (`run_tests.py`).
- Pure writer tests pass; **ruff check + format clean** on every changed file.
- Each fix has a guard test verified **red → green** (TDD).
- mypy: changed files are either in the `ignore_errors` tier (`core.bpy_helpers.*`,
  `operators.*`) or trivially type-clean (`core/skinning/sidecar_schema.py`).

---

## 3. Two items deliberately NOT in Phase 2

- **`animated-delta-rest-rotation`** — **deferred to its own PR** (O4 decision, user's
  choice). It's "heavier than medium": a correct fix needs a per-frame posed-parent
  bake (scene-step, like `sprite_frame_animations._bake_track`), not a formula tweak.

- **`feet-landing-ignores-origin-offset`** — **carried out of this session** because it's
  the only remaining item that touches **strict-mypy** code (`importers/photoshop`),
  and the strict gate can't run in the current environment (no `uv`/fake-bpy stubs).
  Do it where `uv run mypy` works.
  - **Confirmed reachable:** `importers/photoshop/__init__.py` `_anchor_meshes_at_feet`
    computes `bottom = obj.location.z - half_h` (assumes a centered pivot). Sprite
    layers with `[origin]` shift the pivot off-center and **do** flow into
    `result.meshes` (`__init__.py:135-138` → `stamp_sprite` → `result.meshes.append`),
    so their landing math is off by the origin offset.
  - **Fix approach:** read the true geometry bottom instead of the size-based estimate,
    e.g. `min((obj.matrix_world @ v.co).z for v in expect_mesh(obj).vertices)` (keeps
    the common no-origin case byte-identical). `_Placement.geometry_offset` is the baked
    local-XY offset if you prefer the TODO's "add the baked Z offset" route.
  - **Guard:** add to `apps/blender/tests/operators/test_import_placement.py` — build a
    manifest inline with a `"kind": "sprite"` layer carrying an `origin`, `placement="landed"`,
    no anchor; assert the sprite's visual bottom lands on Z=0.
  - **mypy caveat:** iterating `mesh.vertices` in a strict file may trip fake-bpy stubs
    ("MeshVertices not iterable/indexable"). Verify with `uv run mypy` and use
    `expect_mesh` / a helper / a scoped `type: ignore` if needed.

Full item list + decisions live in `specs/074-blender-code-audit-remediation/TODO.md`
and `STUDY.md`. Phase 3–6 (cleanups, low-sev bugs, test-quality, dead-module removal)
are untouched. Structural decomposition is spec 075.

---

## 4. Local gate setup (reference — paths are from the previous machine)

No `uv` on the box; gates were run via a local Blender + a standalone ruff:

```bash
# In-Blender operator tests + goldens (Blender 5.1). One-time: install deps into
# Blender's bundled Python (it disables user-site, so --target a path it reads):
blender --background --python-expr "import ensurepip; ensurepip.bootstrap(); import subprocess,sys; subprocess.check_call([sys.executable,'-m','pip','install','--no-index','--find-links','apps/blender/wheels/','pydantic','proscenio-models'])"
blender --background --python-expr "import subprocess,sys; subprocess.check_call([sys.executable,'-m','pip','install','--target','<addons>/modules','pytest'])"

blender --background --python apps/blender/tests/run_operator_tests.py            # 271 passed
blender --background --python apps/blender/tests/run_operator_tests.py -- -k NAME  # subset
blender --background --python apps/blender/tests/run_tests.py                       # goldens 8/8

# Pure writer tests (need proscenio_models on the path):
PYTHONPATH=packages/models/src python -m pytest tests/writer/test_sprites.py

# Lint (pinned ruff 0.15.19 to match CI):
python -m ruff check <files>
python -m ruff format --check <files>
```

**Preferred once back on a full dev box:** `uv run ruff check`, `uv run ruff format --check`,
`uv run mypy --config-file apps/blender/pyproject.toml`, `uv run pytest tests/`, then the
two in-Blender runs. That closes the strict-mypy gap that blocked `feet-landing`.

---

## 5. Next steps — pick one

1. **(Recommended)** Push `fix/074-phase-2-medium-correctness` and open the Phase 2 PR
   now (note the 2 deferrals in the body); `feet-landing` + `animated-delta-rest-rotation`
   land as follow-up PRs.
2. Do **`feet-landing`** first (run `uv run mypy` to close the strict gate), then open a
   complete Phase 2 PR.
3. Some other order.

Also pending independently: **`keyframe-slot-index-drift`** — the 6th high-severity item
deferred out of Phase 1 (needs the O3 binding-mechanism decision; touches the export
round-trip + `slot_swap`/`slot_cycle` goldens).
