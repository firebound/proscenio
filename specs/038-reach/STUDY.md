# Spec 038: Reach

Broaden the toolset toward a fully-free 1.0 by adding two new entry points into the existing PSD-manifest pipeline, without touching the Blender-side contract that already consumes it.

This STUDY supersedes the earlier scoping note for spec 038 (which assessed Krita / GIMP / GDExtension as gates). The direction has changed: a Krita plugin and a Blender-native layered-`.psd` importer are now committed prongs toward a free 1.0; GIMP, GDExtension, and Unity are explicit non-goals for this spec. The earlier audit's durable conclusion - that the import contract is a tool-agnostic PNG-per-layer set plus a JSON manifest, so a new producer is bounded - still holds and is the foundation this builds on.

## Problem statement

Today the only producer of a Proscenio PSD manifest is the Photoshop UXP plugin (`apps/photoshop/`, TypeScript). Adobe Photoshop is paid and closed; an artist who works entirely in free tools has no way into the pipeline even though the Blender addon and the Godot importer downstream are free. The free side of the toolchain is real but unreachable.

Two complementary fixes broaden reach:

1. **A Krita plugin** that ports the Photoshop plugin's authoring behavior - tag layers, walk the layer tree, and export a manifest plus per-layer PNGs that the Blender importer already reads. Krita is the dominant FOSS 2D paint tool and aligns directly with a Godot-FOSS audience. Krita plugins are Python (PyKrita / PyQt5), where the Photoshop plugin is TypeScript on UXP, so this is a behavior port across two unrelated runtimes - not a code share at the plugin layer.

2. **A Blender-native layered-`.psd` import** as a generic fallback for any program that can save a layered PSD (Krita itself, GIMP, Affinity, Clip Studio, Procreate exports, etc.). This reads the PSD's layer tree directly in Blender, derives the same manifest the importer already consumes, and stamps the scene. It has no in-app tagging UI, so tags must be inferred from layer names and group structure - the same bracket-tag vocabulary the artist would type anyway.

The two prongs are deliberately different in kind: the Krita plugin is the high-fidelity, in-app, tag-aware path for the one FOSS tool worth a dedicated plugin; the direct-PSD import is the low-fidelity, zero-plugin catch-all for everything else.

## Scope

In scope:

- A Krita Python plugin under a new `apps/krita/` that emits a v1 PSD manifest plus PNGs byte-compatible with what the Blender importer reads.
- A Blender operator that imports a layered `.psd` file directly, deriving a manifest in memory (or on disk) and stamping the scene through the existing `import_manifest` path.
- The schema-sharing question: how a Python plugin (Krita) and the Python Blender addon relate to the pydantic source of truth, versus the TS plugin that consumes generated TS bindings.

Explicit non-goals (this spec):

- **GIMP plugin.** The direct-PSD import already covers GIMP (GIMP exports layered PSD), so a dedicated GIMP plugin buys little over the generic fallback. Not built here.
- **GDExtension / C# / native Godot runtime.** `AGENTS.md` hard rule (GDScript-only, import-time only, no native runtime) stands. The five documented reopen triggers in `specs/gated.md` are unchanged; none is hit.
- **Unity exporter.** Out of the Godot-2D mission entirely.
- **Krita import** (manifest -> Krita document), the mirror of the Photoshop plugin's import leg. Deferred: the demand is export-into-the-pipeline, not round-trip; see Open questions.

## Repo study: the behavior to port and the contract to match

### The integration contract (tool-agnostic)

The Blender importer consumes a JSON manifest plus PNGs, never a raw `.psd`. The public entry point is `import_manifest(manifest_path, *, placement, root_bone_name)` in `apps/blender/importers/photoshop/__init__.py`; it calls `psd_manifest.load(path)` (`apps/blender/core/psd/psd_manifest.py`), which reads the JSON and validates it with `PsdManifest.model_validate(raw)` from `proscenio_models`. Any producer that writes a schema-valid manifest plus the PNGs it references is a first-class citizen with zero Blender-side change. This is the load-bearing fact for both prongs.

### The manifest schema (shared source of truth)

The schema is pydantic, in `packages/models/src/proscenio_models/psd_manifest.py`:

- `PsdManifest` (root): `format_version: Literal[1]`, `doc: str`, `size: UintPair`, `pixels_per_unit: float (gt=0)`, `anchor: UintPair | None`, `layers: list[Layer]`. `model_config` is `extra="forbid"` (strict - unknown keys fail validation).
- `Layer` is a discriminated union on `kind` (`_layer_discriminator`) over `MeshLayer` and `SpriteLayer`.
- `MeshLayer`: `kind: "mesh"`, `name`, `path`, `position`, `size`, `z_order`, optional `origin`, `blend_mode`, `subfolder`.
- `SpriteLayer`: `kind: "sprite"`, `name`, `position`, `size`, `z_order`, `frames: list[FrameEntry] (min_length=1)`, optional `origin`, `blend_mode`, `subfolder`.
- `FrameEntry`: `index: int (ge=0)`, `path: str`.
- `BlendMode = Literal["normal", "multiply", "screen", "additive"]`.
- `MANIFEST_FORMAT_VERSION = 1`.

The codegen (`packages/codegen/`) dumps this model to JSON Schema (`packages/codegen/src/proscenio_codegen/schema_dump.py` -> `packages/models/schemas/psd_manifest.schema.json`) and emits TypeScript bindings from that schema (`ts_emit.py` -> `apps/photoshop/src/schema_bindings/psd_manifest.ts`) and GDScript Resources (`godot_emit.py`). The Photoshop plugin's `apps/photoshop/src/lib/manifest.ts` re-exports the generated TS interfaces under friendly names (`MeshEntry`, `SpriteEntry`, `Manifest`).

### How the Photoshop plugin behaves (the port target)

The plugin is four UXP panels (`plugin/manifest.json`): **Proscenio Exporter**, **Proscenio Tags**, **Proscenio Validate**, **Proscenio Debug**. The feature set that matters for a manifest producer:

- **Tag vocabulary, name-canonical.** Tags live in the layer / group name as bracket tokens; the layer name is the source of truth (`apps/photoshop/src/lib/tag-parser.ts`). The locked vocabulary: `[ignore]`, `[merge]`, `[folder:name]`, `[mesh]`/`[poly]`/`[polygon]`, `[sprite]`, `[spritesheet]`, `[origin]` (marker) and `[origin:x,y]`, `[scale:n]`, `[blend:mode]`, `[path:name]`, `[name:pre*suf]` (group child-name macro). Unknown brackets pass through as display text. Tag matching is case-insensitive; values verbatim.
- **XMP mirror, best-effort.** `apps/photoshop/src/api/xmp.ts` additionally stamps the parsed `TagBag` into XMP under `urn:proscenio:tags:v1`, but the name always wins on conflict. This is a convenience mirror, not the canonical store.
- **Tagging UI.** The Tags panel offers an advanced-fields form that validates typed input against the same `tag-parser` validators and rewrites the layer name (`apps/photoshop/src/api/layer-rename.ts`).
- **The layer walk / planner.** `apps/photoshop/src/lib/planner.ts` (`buildExportPlan`) is the pure heart of the export. It recurses the layer tree, applies the tags, and produces the manifest plus a list of `PngWrite` jobs. Behaviors: `[ignore]` drops a layer; hidden layers drop when `skipHidden`; a single layer tagged `[sprite]` becomes a one-frame Sprite2D; a group tagged `[spritesheet]` (or a group whose children are all contiguous-from-zero digit names) becomes a multi-frame sprite; `[merge]` flattens a group into one PNG; `[folder]` and `[blend]` inherit from ancestor groups; `[scale]` rescales bounds; `[origin]` sets the pivot; z-order is a counter in walk order. It emits warnings (duplicate path, conflicting tags, malformed sprite frames, empty bounds, sub-pixel scale, origin outside container) and blocking errors (filename-template collapse that would overwrite PNGs).
- **The PNG export.** `apps/photoshop/src/api/png-writer.ts` isolates each source layer onto a temp document, optionally merges a group, trims the transparent border, and saves a compressed PNG. Bounds come from Photoshop's already-trimmed `layer.bounds`.
- **Layer view abstraction.** The planner runs on a host-agnostic `Layer` shape (`apps/photoshop/src/lib/layer.ts`: `ArtLayer` / `LayerSet`, with `name`, `visible`, `bounds`, optional stable `id`). The UXP adapter (`adapt-document.ts`) maps Photoshop's DOM onto it; unit tests pass plain trees. This is the seam a Krita port mirrors: write a Krita adapter onto the same conceptual `Layer` shape.
- **Document-level fields.** `pixels_per_unit` (persisted across reloads), `anchor` from the first horizontal + vertical guide, `doc` name, `size`.
- **Output layout.** Manifest JSON written next to the chosen output folder; PNGs under `images/` (and `images/<subfolder>/` for `[folder:name]`), two-space-indented JSON with a trailing newline (`apps/photoshop/src/api/manifest-writer.ts`). The plugin also validates with ajv before any disk write.

The plugin also has an import leg (manifest -> fresh PSD, `apps/photoshop/src/api/import-flow.ts`) and a legacy-migration leg. Neither is in scope for the Krita port's first cut.

### How the Blender addon ships Python deps (the precedent for bundling)

`apps/blender/blender_manifest.toml` declares `license = ["SPDX:GPL-3.0-or-later"]` and a `wheels = [...]` list. Blender 4.2+ installs those wheels into the extension's isolated site-packages, so the addon does `import pydantic` / `import proscenio_models` without polluting Blender's bundled Python. The bundled wheels today: `proscenio_models`, `pydantic`, `pydantic_core` (per-platform / per-ABI: cp311 for Blender 4.2 LTS Python 3.11, cp313 for Blender 5.x Python 3.13), `annotated_types`, `typing_extensions`, `typing_inspection`. This is the proven pattern a direct-PSD import extends (add a `psd-tools` wheel and its deps).

## Web research: Krita plugin facts and PSD-reading facts

### Krita Python plugin architecture

Krita plugins are Python, run inside Krita's embedded CPython, and use the `krita` module plus PyQt5 for UI ([Krita manual howto](https://docs.krita.org/en/user_manual/python_scripting/krita_python_plugin_howto.html), [Krita Scripting School](https://scripting.krita.org/lessons/plugins-create)).

File layout (a plugin named `proscenio`):

```text
pykrita/
  proscenio/
    __init__.py        # `from .proscenio import *`
    proscenio.py       # the plugin code
  proscenio.desktop    # plugin descriptor
```

The `.desktop` descriptor is a KDE service file:

```ini
[Desktop Entry]
Type=Service
ServiceTypes=Krita/PythonPlugin
X-KDE-Library=proscenio
X-Python-2-Compatible=false
Name=My Own Plugin
Comment=...
```

Plugin types ([howto](https://docs.krita.org/en/user_manual/python_scripting/krita_python_plugin_howto.html)):

- **Extension** - a global plugin that adds actions / menu items. Subclass `krita.Extension`, implement `setup(self)` and `createActions(self, window)`, register with `Krita.instance().addExtension(MyExtension(Krita.instance()))`. Actions are created via `window.createAction("id", "Display Name", "tools/scripts")` and connected to `action.triggered`.
- **Docker** - a dockable panel. Subclass `krita.DockWidget`, implement `canvasChanged(self, canvas)`, set content with `setWidget(QWidget)`, register a `DockWidgetFactory("id", DockWidgetFactoryBase.DockRight, MyDocker)` via `Krita.instance().addDockWidgetFactory(...)`.
- Optional `.action` XML file under `share/actions/` for keyboard shortcuts.

The document / layer API ([Krita scripting school - layers](https://scripting.krita.org/lessons/layers), [Document class apidoc](https://apidoc.krita.maou-maou.fr/kapi-class-Document.html)):

- `Krita.instance()` is the application entry; `Krita.instance().activeDocument()` (or `application.activeDocument()`) returns the active `Document`.
- Layers are **Nodes**. `Document.topLevelNodes()` returns the top of the tree; each `Node` has `childNodes()` for recursion, `name()`, `visible()`, `opacity()`, `blendingMode()` (a string like `"normal"`, `"multiply"`), `bounds()` (a `QRect`, the node's content rectangle), `type()` (`"paintlayer"`, `"grouplayer"`, `"filelayer"`, etc.), and `position()`. A node can be found by name with `Document.nodeByName()`.
- Pixel / PNG export: a `Node` can be saved to a file via `Node.save(filename, xRes, yRes, exportConfiguration, bounds)`, or the whole document via `Document.exportImage(filename, InfoObject)` / `Document.saveAs(...)`. For per-layer PNGs, the practical path is to read each node's `bounds()` and either `Node.save(...)` that node or `projectionPixelData(...)` over the node bounds and hand the bytes to a PNG encoder. (Confirm the exact `Node.save` signature against the running Krita build during implementation; the API has drifted across 4.x / 5.x.)

Packaging and install ([howto](https://docs.krita.org/en/user_manual/python_scripting/krita_python_plugin_howto.html)): a plugin is the `proscenio/` folder plus `proscenio.desktop` dropped into the Krita resources `pykrita/` directory, then enabled in **Settings > Configure Krita > Python Plugin Manager**. Krita also reads plugins packaged as a `.zip` action/resource bundle for one-click install in recent versions; the canonical install is still the `pykrita` folder. PyQt5 is available inside Krita's Python; third-party pure-Python packages can be vendored alongside the plugin (placed on `sys.path` from the plugin folder) but Krita provides no dependency resolver, so anything beyond the standard library and PyQt5 must be shipped with the plugin.

### Reading a layered PSD in Python (`psd-tools`)

[`psd-tools`](https://github.com/psd-tools/psd-tools) ([PyPI](https://pypi.org/project/psd-tools/), [API docs](https://psd-tools.readthedocs.io/en/latest/reference/psd_tools.api.layers.html)) is the standard Python reader.

- License: **MIT** (the prompt anticipated GPL-3.0; the repository's `LICENSE` is in fact MIT - "Copyright (c) 2019 Kota Yamaguchi", standard MIT text, confirmed at [LICENSE](https://github.com/psd-tools/psd-tools/blob/main/LICENSE) and the PyPI `License: MIT` classifier). This materially changes the licensing calculus below.
- API: `PSDImage.open(path)` returns the document; iterate it as a tree. Each layer exposes `name`, `bbox` / `bounds` (a `(left, top, right, bottom)` tuple), `visible`, `opacity`, `blend_mode` (a `BlendMode` enum), `kind`, `is_group()`, and `is_visible()`. Group layers are iterable over children. Raster layers composite to a Pillow image via `layer.composite()` / `layer.topil()`; the whole document via `psd.composite()`.
- What is recoverable: group hierarchy and names, per-layer bounds, visibility, opacity, blend mode, raster pixels, and (with caveats) masks and smart objects (`SmartObjectLayer.smart_object`). Adjustment / fill layers and most effects are partially supported. Vector masks and some blend modes (e.g. dissolve) are not fully composited.
- Dependencies: `Pillow` (image IO) and `numpy` (raw pixel arrays); pure-Python otherwise. Optional `[composite]` extra adds `aggdraw` / `scipy` / `scikit-image` for advanced effect rendering, which this spec does not need.

## Feature parity matrix: Photoshop plugin -> Krita plugin

Each Photoshop-plugin behavior, the Krita Python API that implements it, and a feasibility verdict.

| PS feature | What it does | Krita equivalent | Verdict | Notes |
| --- | --- | --- | --- | --- |
| Layer tree walk | Recurse art layers + groups | `Document.topLevelNodes()` + `Node.childNodes()` recursion | feasible | The planner is host-agnostic; write a Krita adapter onto the `Layer` shape (group = `type()=="grouplayer"`). |
| Layer name as canonical tag store | Tags in `name`, parsed by `tag-parser` | `Node.name()` read/write | feasible | Same bracket vocabulary; the parser logic ports 1:1 to Python. |
| Visibility | Skip hidden when `skipHidden` | `Node.visible()` | feasible | Direct. |
| Layer bounds (trimmed) | `layer.bounds` already trimmed | `Node.bounds()` (`QRect`) | feasible-with-care | Krita `bounds()` is the node content rect; verify it excludes fully-transparent margins, else trim on export. |
| Group = LayerSet | Distinguish set vs art | `Node.type()` (`"grouplayer"` vs `"paintlayer"`) | feasible | File layers / clone layers map to art for our purposes. |
| `[merge]` flatten group | Flatten descendants to one PNG | `Node.mergeDown()` on a duplicate, or composite the group's projection over its bounds | feasible | Use a scratch document / duplicate so the source is untouched (mirrors the PS temp-doc approach). |
| `[spritesheet]` / digit-children auto-detect | Multi-frame sprite | planner logic unchanged; only the adapter differs | feasible | Pure-logic; ports with the planner. |
| `[origin]` / `[origin:x,y]` pivot | Per-entry pivot in pixels | `Node.bounds()` center for marker; literal for `[origin:x,y]` | feasible | Same math as PS. |
| `[scale]`, `[folder]`, `[blend]`, `[path]`, `[name]` | Manifest field shaping | planner logic | feasible | Pure-logic. |
| `blend_mode` from layer | Read blend, write field | `Node.blendingMode()` returns a string | partial | Krita's blend-id strings ("normal", "multiply", "screen", "add"/"linear_dodge") need mapping to the `BlendMode` literal; only the four supported modes survive, rest warn. |
| Per-layer PNG export | Isolate, trim, save PNG | `Node.save(...)` over node bounds, or `projectionPixelData` -> Pillow -> PNG | feasible | Confirm `Node.save` signature against the target Krita build; fall back to projection bytes + Pillow encode. |
| Document anchor from guides | First H+V guide -> `anchor` | `Document.horizontalGuides()` / `verticalGuides()` | feasible | Krita exposes guide lists; pick first of each. |
| `pixels_per_unit`, persisted | PPU field + storage | PyQt widget + `Krita.instance().writeSetting(...)` / `readSetting(...)` | feasible | Krita has a per-plugin settings store. |
| Tagging UI (advanced form) | Validated form rewrites name | PyQt5 Docker with form fields | feasible | More work than the export leg; the validators port from `tag-parser`. |
| Validate panel | ajv against schema, warnings | jsonschema (or pydantic) against the dumped schema / model | feasible | See schema-sharing options - Python can validate against the model directly. |
| Manifest write | 2-space JSON + trailing newline | `json.dumps(..., indent=2)` + `"\n"` | feasible | Match the PS writer byte-for-byte so committed fixtures stay stable. |
| sRGB color advisory | Doc color-profile check | `Document.colorProfile()` | feasible | Surface a "not sRGB" advisory like the PS Validate panel. |
| Import leg (manifest -> doc) | Re-stamp a PSD | `Document` + `Node` creation, `setPixelData` | out-of-scope | Deferred; export is the demand. |
| Legacy migration | Old-tag -> new-tag rewrite | n/a | out-of-scope | No legacy Krita corpus exists. |

Verdict summary: every export-path feature is feasible in the Krita Python API; the only partial is the blend-mode string mapping (cosmetic, warn-and-drop), and the only meaningful new work is re-authoring the PyQt tagging UI. Import and legacy-migration are out of scope.

## Architecture: code / schema sharing between the TS plugin and the Krita Python plugin

The user's key question: can the Krita plugin reuse `proscenio_models` (pydantic) directly, or the dumped JSON Schema, or must it duplicate?

The TS plugin consumes **generated TS bindings** (`json-schema-to-typescript` over the dumped JSON Schema) because TypeScript cannot run pydantic. The Krita plugin is Python, so it has options the TS plugin does not.

### Option A - reuse `proscenio_models` pydantic inside the Krita plugin (vendor the wheel)

Ship `proscenio_models` + `pydantic` + `pydantic_core` (+ `annotated_types`, `typing_extensions`) alongside the Krita plugin, exactly as the Blender addon already does in `apps/blender/wheels/`. The plugin then does `from proscenio_models import PsdManifest`, builds the model in code, and `PsdManifest(...).model_dump(...)` produces the JSON. Validation is the constructor.

- Pros: one source of truth, identical validation semantics to the Blender consumer, no schema drift, the exact precedent already works in the Blender extension.
- Cons: `pydantic_core` is a Rust extension with a per-platform / per-Python-ABI wheel. Krita's embedded Python ABI must match an available `pydantic_core` wheel. Krita 5.2 ships Python 3.10; the Blender bundle today pins cp311 / cp313, so a cp310 wheel would have to be added. Bundling a compiled extension into Krita's embedded interpreter is riskier than the Blender case (Blender's wheel installer handles ABI selection; Krita has no such mechanism - the plugin would have to put the right wheel on `sys.path` itself).

### Option B - consume the dumped JSON Schema and validate with `jsonschema` (pure Python)

Build the manifest as plain dicts, then validate against `packages/models/schemas/psd_manifest.schema.json` with the pure-Python `jsonschema` package (no compiled extension).

- Pros: no Rust dependency, no ABI matching, trivially bundles into Krita. Validates against the same artifact the docs site renders, so it tracks the schema. Mirrors how the TS plugin relates to the schema (both consume the dumped artifact, not the model).
- Cons: the manifest is hand-built dicts, not typed records, so the planner has no static typing on its output (the TS plugin gets that from the generated interfaces; Python would lean on tests). The schema must be shipped with the plugin (a small JSON file - cheap).

### Option C - duplicate the schema in the plugin

Re-declare the manifest shape inside the Krita plugin.

- Pros: zero external deps.
- Cons: a fourth copy of the contract to drift (pydantic, JSON Schema, TS bindings, GDScript already exist). Rejected on principle - the repo's whole architecture is single-source-of-truth via codegen.

### Recommendation

**Option B** for the Krita plugin: build dicts, validate against the dumped JSON Schema with `jsonschema`. It avoids the compiled-extension ABI hazard inside Krita's embedded Python, it keeps the contract single-sourced (the schema is generated from pydantic), and it matches the conceptual model the TS plugin already follows (consume the dumped artifact). The shared asset is the JSON Schema file plus the planner logic re-expressed in Python; the planner is pure and already proven, so porting it is mechanical and test-covered. Revisit Option A only if a future need for true typed records in the plugin outweighs the bundling risk - and only after confirming a `pydantic_core` wheel exists for Krita's exact Python ABI.

The planner logic itself (the tag walk) cannot be shared with the TS plugin regardless of option - it lives in `apps/photoshop/src/lib/planner.ts` as TypeScript. The Krita plugin re-implements it in Python. The durable shared asset across all three producers (PS, Krita, direct-PSD) is the schema, not the walk.

## Architecture: Blender-native layered-`.psd` import

### Where it hooks in

A new operator `PROSCENIO_OT_import_layered_psd` parallel to the existing `PROSCENIO_OT_import_photoshop` (`apps/blender/operators/import_photoshop.py`), wired into the Pipeline > Import panel. It uses `ImportHelper` with `filter_glob = "*.psd"`. A new module `apps/blender/importers/psd_direct/` (or `core/psd/psd_reader.py`) reads the `.psd`, derives a `PsdManifest`, and feeds it into the existing pipeline. The cleanest reuse is to build a `proscenio_models.PsdManifest` in memory and call the existing stamper path; the importer's `import_manifest` takes a path today, so either add a `import_from_manifest(manifest, base_dir)` sibling that skips the disk read, or write the derived manifest + extracted PNGs to a temp folder and call `import_manifest` unchanged. Writing to disk is the lower-risk first cut (it reuses the entire stamping path verbatim and leaves the extracted assets inspectable), so prefer that for the first version.

### What reads the PSD

`psd-tools` (MIT), bundled as a wheel in `apps/blender/wheels/` alongside `Pillow` and `numpy`, following the existing wheel pattern in `blender_manifest.toml`. `PSDImage.open(path)` gives the layer tree; recurse it, read `name` / `bounds` / `visible` / `blend_mode` / `is_group()`, and `layer.composite().save(png_path)` (Pillow) for each exported layer's PNG.

### Mapping PSD layers to the manifest

The PSD layer tree maps onto the same `Layer` abstraction the planner uses, then runs the **same tag-and-walk logic** the Krita and PS plugins run. This is the crucial alignment: the direct-PSD import is not a second taxonomy - it parses the identical bracket-tag vocabulary out of PSD layer names. A layer named `head [origin]` or a group named `walk [spritesheet]` means exactly what it means in Photoshop. So the Python planner port written for the Krita plugin is reused here (or both share a `packages/`-level pure planner - see Open questions). PSD bounds come from `layer.bbox`; blend modes map from the PSD blend enum to the four-value `BlendMode`, warn-and-drop on unsupported; `pixels_per_unit` defaults to the manifest default (100) since a raw PSD carries no Proscenio PPU; `anchor` is omitted (PSD guides are not reliably exposed by `psd-tools` for this; default to none).

### What is lost versus a native plugin

The decisive tradeoff: **there is no in-app tagging UI.** With Photoshop or Krita, the artist tags layers inside the paint tool with a validated form. With a raw PSD, tags can only come from the layer names the artist already typed, or from group structure. The options for expressing intent:

1. **Infer from bracket tags in layer names** (recommended). The artist types `[mesh]`, `[spritesheet]`, `[origin]`, etc. into layer names in whatever tool they use. This is exactly the canonical store the PS plugin already treats as authoritative (the name wins; XMP is only a mirror), so it is not a downgrade in fidelity - it is the same contract minus the convenience form. Document the vocabulary in the artist guide so a GIMP / Affinity user knows the tokens.
2. **Infer kind from structure** (fallback defaults): a group of digit-named children is a spritesheet (already the planner's auto-detect); an untagged art layer is a mesh; a plain group recurses. This means a totally untagged PSD still imports as a stack of meshes - a sensible zero-config default.
3. **Post-import Blender authoring** (already exists): after a structural import, the artist refines element kind, slots, and rig in Blender's panels. The direct-PSD path leans on this; it gets the art into Blender, and Blender's existing tools do the rest.

So the loss is the in-app form and the XMP mirror, not the data model. The gain is universal reach. Document the tradeoff plainly in the guide: "tag your layer names with the bracket vocabulary before exporting a PSD, or accept the all-meshes default and refine in Blender."

## DECISIONS

| # | Question | Options | Decision | Rationale |
| --- | --- | --- | --- | --- |
| 1 | Build a Krita plugin at all | (a) yes (b) gate on demand | **(a) yes** | Krita is the FOSS 2D paint tool; a free-1.0 mission needs a free producer. The earlier gate was about roadmap symmetry; the new direction commits to it. |
| 2 | Krita plugin location | (a) `apps/krita/` (b) inside `apps/photoshop/` (c) `packages/` | **(a) `apps/krita/`** | Mirrors `apps/photoshop/`; it is a deliverable app with its own runtime and release artifact. |
| 3 | Schema reuse in Krita | (a) pydantic wheel (b) JSON Schema + `jsonschema` (c) duplicate | **(b) JSON Schema + `jsonschema`** | Avoids the `pydantic_core` Rust-ABI hazard in Krita's embedded Python; single-sources the contract via the dumped schema; matches how the TS plugin relates to the schema. Revisit (a) only if typed records become necessary and a matching ABI wheel exists. |
| 4 | Share the tag-and-walk planner | (a) re-port per producer (b) one pure Python planner package shared by Krita + direct-PSD | **(b) one shared pure planner** | The Krita plugin and the direct-PSD importer are both Python and run identical tag logic; a single pure module (under `packages/` or `apps/blender/core`) avoids a second drift. The TS planner stays separate (different language). |
| 5 | Direct-PSD: build a GIMP plugin instead | (a) GIMP plugin (b) generic direct-PSD import | **(b) generic direct-PSD import** | One importer covers GIMP, Affinity, Clip Studio, Procreate, and Krita-saved PSDs. A GIMP-specific plugin buys little over the generic path. |
| 6 | PSD reader library | (a) `psd-tools` (b) hand-roll a PSD parser | **(a) `psd-tools`** | Mature, MIT-licensed, reads groups / bounds / blend / raster; hand-rolling the PSD binary format is unjustified. |
| 7 | Licensing of `psd-tools` in the GPL-3.0 addon | (a) blocks (b) compatible | **(b) compatible** | `psd-tools` is MIT (verified), and Pillow is the permissive PIL/MIT-CMU license; MIT is GPL-3.0-compatible, so bundling into the GPL-3.0-or-later addon is fine. (The prompt's GPL-3.0 concern does not apply.) |
| 8 | How direct-PSD expresses tags | (a) require a tag form (b) infer from bracket tags in names, default untagged to meshes | **(b) infer from names, sane default** | No in-app UI exists for a raw PSD; the bracket-tag name is already the canonical store, so name inference is the same contract, and an untagged PSD still imports as a refine-in-Blender mesh stack. |
| 9 | Direct-PSD reuse of the stamper | (a) in-memory manifest into a new entry point (b) write derived manifest + PNGs to a temp/sidecar folder, call existing `import_manifest` | **(b) temp/sidecar folder first cut** | Reuses the entire proven stamping path verbatim, leaves extracted assets inspectable, lowest risk. Add an in-memory entry point later if temp-folder IO proves a bottleneck. |
| 10 | Krita import leg (manifest -> Krita doc) | (a) build now (b) defer | **(b) defer** | The demand is into-the-pipeline export; round-trip is not requested. Revisit on demand. |
| 11 | GDExtension / Unity | (a) in this spec (b) out | **(b) out** | Non-goals; the AGENTS.md hard rule and the five documented GDExtension triggers stand unchanged. |

## Risks and unknowns

- **Krita API drift across versions.** The `Node.save` / `projectionPixelData` signatures and the blend-mode id strings differ between Krita 4.x and 5.x. Pin a target minimum (Krita 5.2, the current stable) and verify signatures against it; do not promise 4.x.
- **Krita embedded Python ABI.** Krita 5.2 ships Python 3.10. If Option A is ever revisited, a cp310 `pydantic_core` wheel must exist; under the recommended Option B this risk is avoided (pure-Python `jsonschema` only).
- **Per-layer trim fidelity in Krita.** Whether `Node.bounds()` is the tight content rect or includes transparent margin affects manifest `position` / `size`. Must be verified; trim on export if needed (the PS plugin relies on PS already trimming).
- **`psd-tools` composite fidelity.** Adjustment layers, clipping masks, layer effects, and smart objects do not all composite faithfully. For cutout art (flat raster layers) this is fine; document that effects-heavy PSDs may not round-trip pixel-perfect.
- **Blender bundle size and ABI matrix.** Adding `psd-tools` + `Pillow` + `numpy` wheels grows the addon and adds platform/ABI wheels to maintain (Pillow and numpy are compiled). This is the same maintenance treadmill as the existing `pydantic_core` matrix, scaled up. Confirm the addon size and CI bundling stay manageable.
- **CI / test matrix growth.** A Krita plugin is a new GUI app in the manual-test surface (the scarcest resource, per the earlier audit). Mitigate by keeping the planner pure and headless-testable (the PS plugin's vitest-on-pure-planner precedent) so only the thin Krita adapter needs manual verification.
- **Manifest byte-stability across producers.** The committed parity fixtures assume the PS writer's exact formatting. Both new producers must match the 2-space-indent + trailing-newline shape or fixtures churn.

## Open questions for the user

1. **Where does the shared Python planner live?** A new `packages/proscenio_planner/` (importable by both the Krita plugin via its bundle and the Blender addon via the wheel pattern), or inside `apps/blender/core/psd/` (and the Krita plugin vendors a copy)? A `packages/` home is cleaner but adds a package; the `core/psd` home avoids a package but couples the Krita plugin to a Blender path.
2. **Krita minimum version.** Target Krita 5.2 only, or also attempt 4.x (which would constrain the API surface and add a test target)?
3. **Direct-PSD anchor / guides.** Accept "no anchor from raw PSD" (root bone at default), or invest in reading PSD guides via the raw `psd-tools` low-level API for parity with the PS guide-anchor feature?
4. **Krita tagging UI scope for v1.** Ship the export leg only first (tags via layer names, like the direct-PSD path), or include the full PyQt advanced-fields tagging Docker in the first cut? The export leg alone is a much smaller, faster deliverable.
5. **Krita install / distribution.** Ship as a `pykrita` folder (manual copy), a one-click `.zip` resource bundle, or submit to the Krita plugin repository? Affects packaging work and the release pipeline.

## Phasing (shape only, not a TODO)

- **Phase 0 - shared planner.** Extract / port the pure tag-and-walk planner to Python (one module), with the PS planner's test suite re-expressed as Python tests. No DCC dependency.
- **Phase 1 - direct-PSD import in Blender.** Bundle `psd-tools` + Pillow + numpy wheels; new operator + reader that derives a manifest (using the Phase 0 planner) and reuses `import_manifest`. The cheapest reach win, fully headless-testable.
- **Phase 2 - Krita export plugin.** `apps/krita/` plugin: Krita adapter onto the `Layer` shape, the Phase 0 planner, per-node PNG export, `jsonschema` validation against the dumped schema, manifest write matching the PS byte shape. Export leg first; tags via layer names.
- **Phase 3 - Krita tagging UI.** PyQt5 Docker with the validated advanced-fields form, porting the `tag-parser` validators. Optional polish once the export leg ships.

## Sources

- [Krita Scripting School - create a plugin](https://scripting.krita.org/lessons/plugins-create)
- [Krita Scripting School - layers](https://scripting.krita.org/lessons/layers)
- [Krita Manual - how to make a Krita Python plugin](https://docs.krita.org/en/user_manual/python_scripting/krita_python_plugin_howto.html)
- [Krita Manual - introduction to Python scripting](https://docs.krita.org/en/user_manual/python_scripting/introduction_to_python_scripting.html)
- [Krita Python API - Document class](https://apidoc.krita.maou-maou.fr/kapi-class-Document.html)
- [Krita Manual - pre-installed Python plugins](https://docs.krita.org/en/reference_manual/default_python_plugins.html)
- [psd-tools on GitHub](https://github.com/psd-tools/psd-tools)
- [psd-tools LICENSE (MIT)](https://github.com/psd-tools/psd-tools/blob/main/LICENSE)
- [psd-tools on PyPI](https://pypi.org/project/psd-tools/)
- [psd-tools API - layers reference](https://psd-tools.readthedocs.io/en/latest/reference/psd_tools.api.layers.html)
