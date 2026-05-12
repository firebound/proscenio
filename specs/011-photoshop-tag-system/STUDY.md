# SPEC 011 - Photoshop tag system + tagging UI

## Problem

The UXP exporter (SPEC 010) infers per-layer behaviour from layer **names** alone:

- `_<name>` -> skip
- group with numeric children (`0`, `1`, ...) -> sprite_frame
- top-level siblings `eye_0`, `eye_1` -> flat sprite_frame
- hidden flag -> skip (toggle)

That works for the smallest case, breaks down everywhere else:

- No way to mark a layer explicitly as `polygon` vs `sprite_frame` vs `spritesheet` when the auto-detection guesses wrong.
- No per-layer pivot. The mesh world position is the bbox top-left of the trimmed PSD layer; lateral rigging (knee, shoulder) wants an artist-chosen pivot.
- No way to opt a layer into the deferred deformable-mesh path (SPEC 002 / SPEC 008).
- No subfolder routing on disk. All PNGs land in `images/`.
- Underscore prefix is overloaded: artists already use `_color_ref` for swatches; the same prefix is the only way to say "skip this".
- No multi-layer flatten. Hair drawn in 3 layers (so the artist can reorder) has no way to say "export as one image".
- No document-level anchor; PSD ruler origin is ignored.
- No validator. The user discovers naming bugs only when the Blender import fails.

Spine's PhotoshopToSpine script solves most of these via **inline bracket tags** in layer names (`[ignore]`, `[merge]`, `[folder:name]`, `[origin]`, ...). The pattern is battle-tested. Adobe Character Animator solves a different slice via **semantic keywords** (`Head`, `Body`, `+Left Pupil`). Live2D Cubism via **prefix glyphs** (`#`, `*`, `?`, `!`, `:`).

SPEC 011 adopts the bracket-tag approach as the primary input format, layers a **plugin-UI tag inspector** on top (artist clicks instead of typing), and stores the chosen tags both in the layer name (visible everywhere PSD opens) and as a parallel XMP record on the layer for tools that want structured access.

Pre-1.0 PoC means **no backward-compatibility constraint**: the `_<name>` legacy prefix is dropped entirely once `[ignore]` ships. Schema version bumps freely.

## Reference: prior art

### Spine PhotoshopToSpine (bracket tags)

| Tag | Applies to | Function |
| --- | --- | --- |
| `[bone]` / `[bone:name]` | layer + group | bone hierarchy node |
| `[slot]` / `[slot:name]` | layer + group | named slot |
| `[skin]` / `[skin:name]` | layer + group | skin variant (subfolder) |
| `[scale:n]` | both | layer scale, attachment inverse |
| `[rotate:n]` | both | layer rotation, attachment inverse |
| `[pad:n]` | both | extra padding pixels |
| `[folder]` / `[folder:name]` | both | output subfolder |
| `[overlay]` | both | clipping mask for layers below |
| `[trim]` / `[trim:false]` / `[trim:canvas]` / `[trim:mask]` | both | whitespace handling |
| `[mesh]` / `[mesh:name]` | layer | mesh attachment / linked mesh |
| `[path:name]` | layer | filename override |
| `[origin]` | layer | layer center sets origin; no PNG output |
| `[ignore]` | both | skip |
| `[merge]` | group | flatten children into 1 PNG |
| `[bones]` / `[slots]` | group | shorthand: tag every child |
| `[name:pre*suf]` | group | child-name pattern rewrite |
| `[!bones]` / `[!slots]` / ... | both | escape parent tag |

Plus: PSD ruler origin = (0,0) of the editor. Recognises Normal / Multiply / Screen / LinearDodge blend modes.

### Live2D Cubism (prefix glyphs)

| Prefix | Function |
| --- | --- |
| `#name` | ignored |
| `*group` | never merge |
| `?layer` | force include (even invisible) |
| `:eye` | auto split L / R |
| `!layer` | purge masks before merge |

### Adobe Character Animator (semantic keywords + `+`)

- `+Name` prefix = warp-independent (moves separately from parent group).
- Auto-tagging by keyword: `Head`, `Body`, `Left Eye`, `Right Eye`, `+Left Pupil`, `+Right Pupil`, `Left Blink`, `Right Blink`, `+Left Eyebrow`, `+Right Eyebrow`, `Mouth`, `Jaw`.
- Head turner views by group name: `Frontal`, `Left Profile`, `Left Quarter`, `Right Quarter`, `Right Profile`.

### Aseprite

- Filename templates: `{layer}-frame-{frame01}.png` configurable per export.
- PSD section dividers -> Aseprite folders (Layer.isGroup).
- UTF-16BE -> UTF-8 sanitization on import.

### Cocos Creator

- 9-slice metadata per sprite (`l`, `t`, `r`, `b` insets) for scalable UI tiles.
- Sidecar `.meta` with UUID + crop data.

### COA Tools (Blender, Proscenio's ancestor)

- Group name = unique sprite name.
- Top-of-stack -> first.
- JSON sidecar with coordinates (became this project's manifest).

## Locked decisions

### D1 - Primary tag syntax: bracket tags in layer name (Spine-style)

`[tag]` and `[tag:value]` anywhere in the layer or group name. Survives PSD save / share / version control; works in any image editor that exposes layer names (Krita, GIMP, future DCCs).

Rationale: zero infrastructure (no XMP read path), visible to the artist in the Layers panel, easy to grep in scripts. The `[bracket]` form is unmistakable - it cannot collide with normal English layer names like "Folder for arms".

### D2 - Secondary tag storage: XMP per-layer (for the plugin UI)

When the plugin-UI tag inspector toggles a tag, it does **both**:

1. Rewrites the layer name to add / remove the bracket tag.
2. Updates a parallel record in the layer's XMP metadata under the `proscenio:v1` namespace.

The exporter reads XMP first; falls back to bracket-tag parsing if XMP is absent (works for layers tagged in non-Proscenio editors). XMP is the canonical store inside the plugin; bracket tags are the **interchange format**.

Rationale: artists can author and inspect tags by eye in the Layers panel without opening the plugin. Power users get a clickable UI. No conflict because the plugin keeps the two in sync.

### D3 - Drop the `_<name>` skip convention

Removed before 1.0. `[ignore]` replaces it. Migration step: when the plugin loads a PSD with `_` layers, it surfaces a one-click "Convert `_` prefixes to `[ignore]`" action in the panel.

Rationale: pre-1.0 PoC, no production users to break. Reserving `_` as a prefix collides with artist conventions (`_color_ref`, `_notes`). One way to express skip is better than two.

### D4 - Drop the implicit `<base>_<index>` flat-aggregation fallback

Removed. Sprite_frame groups must be either:

1. A LayerSet tagged `[spritesheet]` whose children are valid frame names. The tag name `[spritesheet]` is the industry-recognised term (Aseprite, Unity, Spine all use it); the parser maps the tag value to `kind: "sprite_frame"` in the manifest at emit time.
2. Auto-detected from a LayerSet whose all-visible children are pure-digit (`0`, `1`, `2`, ...) - the only auto-detection path that survives.

Top-level siblings `eye_0`, `eye_1` no longer collapse. Rationale: the fallback is responsible for half the "why did this layer get treated as a sprite_frame?" confusion and never composes well with explicit tags.

### D5 - Tag taxonomy v1 (in scope for SPEC 011)

| Tag | Applies | Function | Notes |
| --- | --- | --- | --- |
| `[ignore]` | layer + group | skip entirely | replaces `_<name>` |
| `[merge]` | group | flatten visible children into one PNG | A4 |
| `[folder:name]` | both | output PNGs into `images/<name>/...` instead of `images/` | A3 |
| `[polygon]` | group | kind override: emit one polygon entry for the group's flattened render | C2 |
| `[sprite]` | layer | same as `[polygon]` for a leaf layer; no auto-detection needed | C2 |
| `[spritesheet]` | group | kind override: emit a sprite_frame entry; children are frames | C2 |
| `[mesh]` | layer | mark layer as deformable mesh source (SPEC 002 / 008 will read this) | C2 |
| `[origin]` | layer | a marker layer inside a group; its center becomes the group's pivot. No PNG output for the marker itself | C1 |
| `[origin:x,y]` | both | explicit pivot in PSD pixels (alternative to marker layer) | C1 |
| `[scale:n]` | both | per-layer scale override at export; the manifest carries the resulting size | E1 |
| `[blend:mode]` | layer | blend mode override emitted in manifest (`normal`, `multiply`, `screen`, `additive`) | D3 |
| `[path:name]` | layer | filename override on disk (different from manifest entry `name`) | A1 |
| `[name:pre*suf]` | group | pattern macro: rewrites every child's `name` field with `*` substituting the original child name. E.g. `[name:hero_*]` on a group with children `arm`, `leg` -> manifest names `hero_arm`, `hero_leg` | F5 |

Filename templating is exposed as a panel-level setting, not as a tag (one setting affects the entire export, no per-layer override needed). See D8.

Deferred to a follow-up SPEC or `specs/backlog.md`: `[skin:name]`, `[rotate:n]`, `[overlay]`, `[trim:*]`, `[bone]`, `[slot]`, `[bones]`, `[slots]`, `[!*]` escapes, `[slice:l,t,r,b]` (Cocos 9-slice), `[isolated]` (Character Animator's `+` warp-independent), pseudo-keyword recognition (`Head`, `Mouth`, ...), head-turner view groups.

Out of scope permanently: `[scale]+trim` Spine wobble bug class (we use deterministic scale-before-trim - E1).

### D6 - Document-level conventions

- **First horizontal + first vertical PSD guide** define the document anchor (origin). Manifest gains a top-level `anchor: [px, px]` field; Blender importer translates the root bone position. (D2 in the v1 list above, but document-level rather than layer-level - keeping numbering consistent with the master tag taxonomy.)
- **Layer color labels are NOT a tagging channel.** Dropped from SPEC 011 v1. Single source of truth = bracket tag (canonical, visible in the Layers panel and grep-able) + XMP mirror written by the panel. Letting a layer color also drive tag inference would split the source of truth between two channels and let them disagree silently. Color labels can still be inspected by the panel as a passive badge in a future iteration, but they never set tag semantics in this SPEC.

### D7 - Manifest schema bump to v2

The new tag taxonomy needs schema fields:

- `format_version: 2`.
- `anchor: [px, px]` optional at document level.
- Per-entry: `origin: [px, px]` optional, `blend_mode: "normal" | "multiply" | "screen" | "additive"` optional, `subfolder: string` optional, `is_mesh: boolean` optional.
- `kind` gains `"mesh"` for deformable mesh layers (a `polygon` superset; mesh is rendered as a polygon when no deformation rig is bound).

Schema v1 importer continues to work for legacy manifests through the importer's existing format_version check; SPEC 010's UXP exporter switches to v2 wholesale.

### D8 - Plugin UI: the mini-app

The exporter panel grows three new tabs (or sections - implementation choice):

1. **Tags** - a hierarchical layer tree mirroring the PSD's Layers panel. Each row has:
   - Layer thumbnail (16 / 24 px).
   - Layer name with bracket tags rendered as badges.
   - Checkboxes for binary tags (`[ignore]`, `[merge]`).
   - Dropdowns for kind override (`auto` / `polygon` / `sprite` / `spritesheet` / `mesh`).
   - "Set origin from selection" button (uses the currently selected pixels' center as `[origin:x,y]`).
   - Color-label indicator (synced with the configured color-map).
2. **Validate** - list of warnings before export: duplicate names after sanitize, sprite_frame index gaps, unrelated tags on the same layer, empty bbox layers, etc. Each row clickable -> selects the offending layer in PS.
3. **Export** - the current 10.4 panel, plus:
   - "Reveal output for selected layer" button that shows the path / kind that would result from the current state.
   - **Filename template** setting (F6) controlling the on-disk path under `images/`. Tokens: `{name}` (sanitized entry name), `{group}` (parent group path joined by `/`), `{layer}` (raw leaf layer name), `{kind}` (`polygon` / `sprite_frame` / `mesh`), `{index}` (frame index for sprite_frame frames only). Default template: `{name}.png` for polygons, `{name}/{index}.png` for sprite_frame frames - matches the SPEC 010 layout. Stored in `localStorage` per plugin. Per-layer override available via the `[path:name]` tag.

The tree refreshes on PS notifications (`select`, `make`, `delete` document events) so the panel stays live as the artist works.

### D9 - Authoring entrypoint: bracket tags first, panel second

The artist can author tags two ways:

1. **Type the bracket** in the Layers panel: rename `arm` -> `arm [ignore]`. Plugin sees the change on next refresh.
2. **Click in the panel**: checkbox / dropdown / "Set origin from selection". Plugin writes the bracket tag to the layer name AND the XMP record.

Both paths converge. The bracket tag is the canonical "what is the artist saying"; the XMP record is the canonical "what does the plugin think the artist is saying". When they disagree, the bracket tag wins (it survived a save / share / round-trip; the XMP might have been stripped).

### D10 - Plugin-UI mini-app scope

The full mini-app is a single React panel with React-managed state. No new dependencies beyond what 10.x ships. The hierarchy view is a regular `<sp-tree>` (Spectrum) or a simple `<ul>` tree with collapse / expand state. Live updates come from `action.addNotificationListener` (open, close, select, make).

Plan: implement the Tags tab first (most value), then Validate, then the Reveal-output helper in the Export tab.

## Things explicitly NOT in SPEC 011

- `[skin]` and full skin variant export. Different output topology (multi-manifest); separate SPEC if a real character demands it.
- `[bone]` / `[slot]`. Proscenio's Blender side already owns the rig; tagging bones in PSD duplicates that responsibility. If a future "PSD-first rigger" SPEC lands, revisit.
- `[overlay]` clipping masks. Tied to Spine's render model; Blender's render is different.
- Pseudo-keyword auto-tagging (`Head`, `Mouth`, ...). Tight coupling to a specific rig template; harder to generalise across project types.
- Head-turner view groups. Specific to face puppetry; out of Proscenio's stated 2D-cutout scope.

## Open questions

- **Tag spelling**. Locked at `[spritesheet]` - industry-recognised term (Aseprite, Unity, Spine). The parser performs a one-line lookup at emit time to translate to the `kind: "sprite_frame"` manifest field. The translation cost is one dict entry, vastly outweighed by artist familiarity.
- **Polygon vs Sprite**. Should `[polygon]` (group) and `[sprite]` (layer) be aliases for the same kind? The manifest only has `polygon` today. Decide at implementation - probably yes, both write `kind: "polygon"`, the tag name is just a hint for the panel UI.
- **Color label conflict resolution**. Resolved by D6: color labels are not a tagging channel in this SPEC, so there is no conflict.
- **XMP support floor**. Resolved by SPEC 010 Wave 10.7 bump (PS 25 / CC 2024+). `uxp.xmp` ships there; no fallback needed for the plugin's minimum-supported PS.
- **Validator severity**. Locked at warn-never-block (D13). Errors render inline in the Validate tab, the Export button stays enabled. Same posture as `pnpm run typecheck`.

## Sequencing relative to other work

- Lands after SPEC 010 Wave 10.7 (JSX retirement). Before then, the UXP plugin is still in parity-mirror mode with the JSX baseline; introducing tag semantics breaks the byte-equality oracle.
- Coordinates with deferred SPEC 002 (sprite_frame mesh) and SPEC 008 (UV animation) via the `[mesh]` tag - implementation can ship as a no-op marker first, then wire up when those SPECs unblock.
- Schema v2 in this SPEC implies a Blender importer update (read `anchor`, `origin`, `blend_mode` fields). Tracked as a small companion task on the addon side; no separate SPEC.
