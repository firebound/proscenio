# SPEC 013 - Mesh interior modes + gesture model redesign (design)

Date: 2026-05-28
Branch: TBD (see "Branch + PR strategy")
Predecessor: `2026-05-26-spec-013-stroke-redesign-design.md` (AS-AM1..AS-AM13)

## Context

Manual smoke on the AS-AM13 authoring polish (live preview + tooltip + statusbar + hover + contour/Stage-5 fixes) surfaced four follow-up problems, three of which are design-heavy:

1. Stage 2 (silhouette) cut overlay is orange, inconsistent with Stage 4 cut (red).
2. Stage 2 location-driven intent (inside = cut, outside = extend) is imprecise; modifier-driven (like Stage 4) is wanted.
3. Drawing fold/cut lines is awkward: modifiers must be held, lines cannot be axis-locked, and a straight 2-vert line creates a single long edge (no interior subdivision) that degrades the mesh.
4. The dense auto-fill interior is overkill for most 2D-skinning sprites. Spine generates a sparse triangulation; Proscenio should let the artist choose.

Four decisions were locked with the user (multiple-choice, 2026-05-28) and are recorded below.

## Locked decisions (AS-AM14 .. AS-AM17)

| # | Decision | Rationale |
|---|----------|-----------|
| AS-AM14 | Add an `interior_mode` enum: **SIMPLE** (Spine-like: Constrained Delaunay over the outer contour + holes + user fold/cut/steiner verts ONLY, no automatic interior fill) and **DENSE** (the current uniform grid + bone-density fill). Default **SIMPLE**. | Dense fill is overkill for the majority of flat 2D-skinning sprites (matches Spine / DragonBones defaults). DENSE stays for cape/hair/fine-border cases. Default SIMPLE because it fits most workflows. |
| AS-AM15 | The modal stage list becomes **mode-dependent**. SIMPLE drops `INNER_LOOPS`; `STEINER_PREVIEW` becomes a **triangulation preview** (shows the actual SIMPLE faces, the Spine "Generate" equivalent). DENSE keeps all 6 stages. Statusbar "N/M" reflects the active mode's count. | Inner loops + dense Steiner preview only make sense for DENSE. Hiding them in SIMPLE removes confusing dead steps and makes step 5 a true preview of what APPLY produces. |
| AS-AM16 | Fold/cut drawing becomes a **toggle-modal pen**: tapping Shift toggles fold-draw mode, Ctrl toggles cut-draw mode (no holding). In draw mode: LMB click places a vert (pen polyline); `X` / `Z` lock the next segment to the horizontal / vertical axis (Blender front-ortho XZ convention); mouse scroll or a typed digit sets the **subdivision count** inserted along each committed edge; RMB or Enter finishes the line; Esc cancels the in-progress line. Tapping the active modifier again (or finishing with no points) exits draw mode. Applies to BOTH Stage 2 and Stage 4. | Holding a modifier the whole stroke is fatiguing and blocks axis-lock / subdivision keys. A toggle pen frees the keyboard for X/Z + digits and matches Blender's knife/poly-build modality. Subdivisions stop straight fold/cut lines from becoming a single long edge that wrecks the triangulation. |
| AS-AM17 | Stage 2 (USER_OUTER) switches from location-driven to **modifier-driven**, unified with Stage 4: **Shift = extend**, **Ctrl = cut**, **Alt = delete**. Stage 2 cut overlay recolors from orange to **RED** (same as Stage 4 cut). | Reverses AS-AM4 (location-driven) + AS-AM9-REV (orange Stage 2 cut). Inside/outside aiming was imprecise; an explicit modifier removes ambiguity. One cut color across stages is less to learn. |

## Data model changes

- `ProscenioSkinningProps.automesh_interior_mode: EnumProperty` = `{SIMPLE, DENSE}`, default `SIMPLE`. Panel: dropdown in the Automesh authoring sub-box. Persists across `.blend` reloads.
- `StageParams` gains `interior_mode: Literal["SIMPLE", "DENSE"]` (frozen snapshot, dirty-detect aware).
- `Stroke` gains an optional `subdivisions: int` (default 0) recording the per-edge subdivision count chosen at draw time. `read/write_user_strokes` + `read/write_user_outer_strokes` round-trip it; `_parse_strokes` defaults missing to 0 (backward compatible with existing persisted strokes).
- Subdivision application is a pure helper (e.g. `core/automesh/stroke_geometry.subdivide_polyline(points, n) -> points`) inserting `n` evenly-spaced verts per edge. Applied at commit time (pen) and during free-draw resample (drag already resamples, so subdivisions mainly matter for pen straight segments).

## Step structure per mode

DENSE (unchanged, 6 stages):

```text
1/6 OUTER -> 2/6 USER_OUTER -> 3/6 INNER_LOOPS -> 4/6 USER_STEINERS -> 5/6 STEINER_PREVIEW -> 6/6 APPLY
```

SIMPLE (5 stages, INNER_LOOPS dropped, step 5 = triangulation preview):

```text
1/5 OUTER -> 2/5 USER_OUTER -> 3/5 USER_STEINERS -> 4/5 TRIANGULATION_PREVIEW -> 5/5 APPLY
```

Implementation: the modal holds an ordered `active_stages: list[AuthoringStage]` computed from `interior_mode` at invoke and whenever the mode changes mid-modal (TIMER dirty-detect). `_advance` / `_retreat` step through `active_stages` (index-based) instead of `AuthoringStage(self._stage +/- 1)`. Statusbar label derives "position/len(active_stages)" so numbering stays correct in both modes. The `AuthoringStage` enum keeps all 6 values; SIMPLE simply omits `INNER_LOOPS` from `active_stages` and relabels `STEINER_PREVIEW` -> "Triangulation preview".

## SIMPLE triangulation pipeline

`build_automesh` / `apply_mesh` gain an `interior_mode` path:

- SIMPLE: skip `_compute_steiner_points` (no uniform grid, no bone density). Feed CDT only: outer contour verts + hole loops + user fold/cut/steiner verts (with their subdivisions) as constraint edges/points. Post-CDT hole prune still runs. Result is a sparse triangulation whose only interior verts are the artist's.
- DENSE: current path unchanged.

The SIMPLE preview at step 4 (TRIANGULATION_PREVIEW) runs the same CDT the APPLY will run and draws the resulting edges/faces as a GPU overlay (wireframe), so the artist sees the real triangulation before committing - the Spine "Generate" preview.

Open question OQ1: do we run the full CDT for the live preview every TIMER tick, or only when entering step 4 / on explicit refresh? Recommendation: compute on stage-enter + on param dirty, cache the result; do NOT recompute every tick (CDT cost).

## Gesture state machine (AS-AM16)

Per stage (2 and 4), the capture state becomes a small machine:

```text
NEUTRAL
  tap Shift -> DRAW(fold)     tap Ctrl -> DRAW(cut)     hold Alt+click -> delete-at-cursor
DRAW(kind)
  LMB click           -> append pen vert (respect active axis lock)
  X / Z               -> toggle axis lock (horizontal / vertical); affects next vert
  scroll / digit 0-9  -> set subdivision count for the line (live preview updates)
  RMB / Enter         -> finish: commit polyline (kind, subdivisions) -> NEUTRAL
  Esc                 -> discard in-progress line -> NEUTRAL
  tap active modifier -> if no verts yet, exit to NEUTRAL; else ignored
  LMB drag            -> free-draw stroke (resampled), committed on release, stays in DRAW
```

Event-conflict resolution (modal already binds Enter=advance, Esc=cancel-modal, RMB=passthrough):

- In DRAW with >=1 pending vert: Enter/RMB finish the line, Esc discards the line - they do NOT advance/cancel the modal. In NEUTRAL: Enter advances stage, Esc cancels modal (today's behavior).
- Axis-lock + digit keys are only consumed in DRAW; otherwise passthrough.

Overlay: the live preview (AS-AM12 `_draw_live_preview`) extends to show (a) the axis-lock guide line from the last vert, and (b) the subdivision verts that will be inserted, so the artist sees the final segment density while drawing.

## Stage 2 remap + colors (AS-AM17)

- Remove the inside/outside intent resolution at PRESS; intent comes from the active draw-mode modifier (Shift=extend, Ctrl=cut, Alt=delete), identical dispatch to Stage 4.
- Overlay: Stage 2 cut uses the red cut color (drop the orange `_STROKE_VERT_COLOR_CUT_REMOVE`). Extend strokes keep a distinct color (e.g. green/blue) so extend vs cut read differently; fold is Stage-4-only.
- Tooltip text updates to the modifier vocabulary ("Extend", "Cut", "Delete").

## Risks / open questions

- OQ1 (above): CDT preview recompute cadence.
- OQ2: digit-typing subdivisions vs scroll - support both, or pick one? Recommendation: both; scroll for quick nudge, digit for exact.
- OQ3: does SIMPLE need a minimum interior density floor for very large flat sprites (huge triangles deform poorly)? Recommendation: ship pure-sparse first; add an optional "max edge length" subdivide pass later if smoke shows stretching.
- OQ4: Stage 2 in SIMPLE - extend/cut still relevant (they edit the silhouette, mode-independent). Keep Stage 2 in both modes. Confirmed: only INNER_LOOPS is mode-gated.
- RISK: the toggle-modal gesture rewrite is the riskiest piece (event routing, passthrough conflicts, modal feel). It is independent of the algorithm work and can ship in a later phase.

## Phasing + scope estimate

Two phases (can be two PRs or one bundle):

- Phase 1 - algorithm + steps + Stage 2 remap (~400 LOC + tests): `interior_mode` prop + StageParams + panel; SIMPLE CDT path in build_automesh/apply_mesh; mode-dependent `active_stages` + nav refactor; triangulation preview overlay; Stage 2 modifier-driven + cut red. Delivers the biggest user-visible win (sparse mesh + precise Stage 2).
- Phase 2 - gesture model rewrite (~450 LOC + tests): toggle-modal pen, X/Z axis lock, scroll/digit subdivisions, `Stroke.subdivisions` round-trip, live-preview extensions, event-conflict routing. Applies to Stage 2 + Stage 4.

Recommendation: Phase 1 first (lower risk, high value), Phase 2 second.

## Branch + PR strategy (needs user decision)

The AS-AM13 polish is committed on `feat/automesh-authoring-ux-polish` (6 commits) but not pushed. This new work rewrites the same overlay/operator files. Options:

- Bundle: continue on the polish branch; one larger PR (matches the user's bundle preference, avoids self-conflicts).
- Split: push the polish branch as its own PR now, branch this work off it (stacked) or off main after merge.
