# Photoshop Plugin

A [UXP](https://developer.adobe.com/photoshop/uxp/) plugin (React + TypeScript) that turns a layered PSD into a manifest plus PNGs the Blender importer reads. The artist drives the whole export from inside Photoshop, never leaving the canvas.

The plugin ships four dockable panels under `Plugins > Proscenio ...`: **Proscenio Exporter**, **Proscenio Tags**, **Proscenio Validate**, and **Proscenio Debug**. They share one read of the open document, so a layer renamed in **Proscenio Tags** updates the preview in **Proscenio Validate** without a manual refresh. Each panel opens with an **Active document** section showing the document name and canvas size, with a `Refresh` button that re-reads Photoshop.

## What it does

- **Tag layers from their name.** Bracket markers (`[ignore]`, `[spritesheet]`, `[folder:name]`, and more) drive the export without touching the artwork. The full vocabulary lives in the [advanced Photoshop guide](../../00-guides/02-advanced/01-photoshop.md); the **Proscenio Tags** panel edits the same tags through controls instead of by hand.
- **Export.** A recursive layer walk produces one PNG per layer plus a manifest JSON. The manifest is validated before it is written, so a broken manifest never reaches disk. Entries whose PNG fails to write are dropped and reported rather than aborting the whole export, so the good entries still ship.
- **Spritesheets.** Marking a group as a spritesheet tags it `sprite` and exports one PNG per frame (`name/0.png`, `name/1.png`, ...). Composing those into a single sheet is the Blender importer's job, not Photoshop's.
- **Mirror back to PSD.** The plugin can rebuild a PSD from a manifest. This reconstructs the source layout; it does not round-trip Blender edits back into the PSD.

## Proscenio Exporter

The main panel. It owns the output folder, the export options, the export run, and the manifest-to-PSD import.

### Output folder

The **Output folder** section is where the export writes. The picked path persists across plugin reloads, so a session resumes against the same folder. `Pick folder` (or `Change folder` once one is set) opens the system picker; `Forget` drops the remembered folder and falls back to the empty state. If the folder is moved or deleted mid-session, the next export reports that it is no longer accessible and clears the stale reference so the panel re-prompts for a folder.

### Export options

The **Export options** section holds the toggles and conversion settings the export run reads.

- `Skip hidden layers` excludes layers that are hidden in Photoshop. It is on by default.
- The **Pixels per unit** section sets the manifest's `pixels_per_unit`, the conversion factor downstream tools use to turn PSD pixels into Blender and Godot world units. A higher value yields smaller world-space objects. The default is `100`. The section echoes the current canvas height in both pixels and resulting units as a sanity check, and a `Reset to 100` button restores the default. The value persists across reloads, and a manifest-to-PSD import seeds it from the imported manifest.
- The **Filename templates** section overrides the on-disk file names. The `mesh` template (default `{name}.png`) controls mesh PNG paths and accepts the `{name}` and `{kind}` tokens; the `sprite` template (default `{name}/{index}.png`) controls sprite frame paths and accepts `{name}` and `{index}`. The `images/` prefix and any `[folder:...]` subfolder are added automatically, so the template only governs the file portion. `Reset to defaults` restores both. A template that drops the token distinguishing its entries (a `mesh` template without `{name}`, a `sprite` template without `{index}`) collapses every entry onto one path and blocks the export rather than silently overwriting PNGs.

### Run export

The **Run export** section's `Export manifest + PNGs` button runs the full export. It is disabled until a document is open and an output folder is picked. The export writes the manifest as `<document-stem>.photoshop_exported.json` next to an `images/` folder of PNGs. The result line reports how many entries were written; on a partial run it lists the entries it skipped and why, so the artist can fix those layers and re-export.

### Re-export selected

The **Re-export selected** section rewrites only the PNG(s) for the layer currently selected in Photoshop, leaving the manifest JSON untouched. It shows the matched manifest entry name and kind, and is active only when the selected layer maps to an entry. Use it to refresh one element's art without a full export.

### Import (manifest to PSD)

The **Import (manifest to PSD)** section rebuilds a PSD from a manifest. `Import manifest as PSD` opens a picker for a Proscenio manifest JSON, validates it, then recreates the document with placed layers and one group per sprite. The new document is left open and unsaved on purpose - commit it with `File > Save As`. Invalid manifests and per-entry placement failures are reported inline; a single bad entry is skipped rather than aborting the whole import. This section is collapsed by default.

### Legacy migration

The **Legacy migration** section appears in the Exporter only when the open document has layers using the old `_layerName` skip convention. It converts those names to the `[ignore]` tag in bulk: it previews each rename (old name to new name, clicking a row selects that layer in Photoshop) and `Convert N layer(s) to [ignore]` applies them in one pass. The header carries a badge with the candidate count.

## Proscenio Tags

A layer-tree editor for the bracket tags, so the artist sets them through controls instead of typing them into layer names. Each row shows the layer's display name (tags stripped) and an inline strip of badges for its non-default tags (folder, path, scale, origin, origin marker, name pattern). Selecting a row's name selects that layer in Photoshop; group rows have a disclosure toggle to collapse their children.

Per row, the controls are:

- an `[ignore]` toggle (skip the layer on export);
- a `[merge]` toggle (groups only - flatten the group into one PNG);
- a kind dropdown - `auto`, `mesh` (Polygon2D), or `sprite` (Sprite2D);
- a blend dropdown - `none`, `mult`, `scrn`, or `add`, writing the `[blend:...]` tag;
- an expander (`+`) that opens the advanced fields for that row.

The advanced fields edit `[folder:NAME]`, `[path:NAME]`, `[scale:N]`, `[origin:X,Y]`, the `[origin]` marker, and (on groups) the `[name:PRE*SUF]` child-name pattern. Typed values are a local draft: nothing commits until `Apply`, and `Revert` discards the draft. A value the tag parser would reject blocks `Apply` and marks the offending field rather than writing nothing silently. The origin row's `From selection` button fills X and Y from the centre of the current Photoshop marquee selection.

Below the tree, the **Selected entry** section is a read-only inspector: for the layer selected in Photoshop it shows what the export will emit (name, position, size, origin, blend, subfolder, frame count) and the resolved on-disk PNG path(s).

## Proscenio Validate

A read-only panel that runs the export planner as a dry run and lists everything that needs attention before a real export. Its **Validate** section header shows a badge - the issue count, or `ok` when the manifest is clean. Issues come in groups:

- **Warnings** - advisory planner findings such as duplicate output paths, conflicting tags, a malformed spritesheet group, empty bounds, sub-pixel scale, or an `[origin]` marker outside a container that consumes it.
- **Skipped** - layers the planner left out and why (an `[ignore]` tag, hidden, empty bounds, or an origin-marker layer).
- **Manifest invalid** - blocking errors that stop the export, including a filename template that would collapse entries onto one path.

Clicking any warning or skipped row selects the offending layer in Photoshop so it is quick to fix. A document whose color profile is not sRGB raises a standalone advisory: colors outside the sRGB gamut clamp on export, because the engine reads PNGs as sRGB and ignores embedded profiles. Convert the document to sRGB (`Edit > Convert to Profile`) to author the colors the game will show.

## Proscenio Debug

A panel for inspecting the planned export and tuning logging. Its **Preview** section dry-runs the export (nothing is written) and lists the manifest entries with their kind, name, path, and any folder, blend, or origin annotations; the header badges the entry count. It also reports the document anchor (the pivot set by the first horizontal and vertical PSD guides, or `(canvas centre)` when no guides were authored), and the running totals of entries, skipped layers, and warnings. `Refresh` re-runs the dry run.

The **Debug logging** section sets how much the plugin logs to the UXP Developer Tools console. Pick a level (the default is `info`; `trace` or `debug` is for reproducing a bug, `off` silences it); the choice persists across reloads. Logs are tagged `[proscenio:<area>]` and read under `Plugins > Development > Developer Tools`.

## The manifest format

The export writes a Proscenio PSD manifest at `format_version: 1` - the current and only shipped version. Each layer becomes one entry whose `kind` is either `mesh` (a Polygon2D-backed element, the default for an art layer) or `sprite` (a Sprite2D-backed element, one or more frames). The manifest also carries the source document name, the canvas size, `pixels_per_unit`, and an optional document anchor. The exact field list is generated from the shared schema and rendered live under the Schema reference; this page does not restate it.

The manifest is validated with [ajv](https://ajv.js.org/) against that schema both before an export reaches disk and after a manifest is picked for import, so neither a malformed export nor a bad imported file gets past the boundary.

## How it is built

The code is layered: an adapter isolates the Adobe API, `lib/` holds the pure, testable tag and planning logic, and `api/` concentrates the side effects (file writes, the Photoshop API) so the domain stays platform-free.

See [Architecture](../../01-project/01-architecture.md) for how the plugin fits the pipeline.
