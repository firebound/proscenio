# Photoshop Plugin

A [UXP](https://developer.adobe.com/photoshop/uxp/) panel (React + TypeScript) that turns a layered PSD into a manifest plus PNGs the Blender importer reads. The artist drives the whole export from inside Photoshop, never leaving the canvas.

## What it does

- **Tag layers from their name.** Bracket markers (`[ignore]`, `[spritesheet]`, `[folder:name]`, and more) drive the export without touching the artwork; a tagging panel ships too. Full vocabulary in the [advanced Photoshop guide](../00-guides/01-advanced/01-photoshop.md).
- **Export.** A recursive layer walk produces one PNG per layer plus a manifest JSON. The manifest is validated before it is written, so a broken manifest never reaches disk.
- **Spritesheets.** Marking a group as a spritesheet tags it `sprite_frame` and exports one PNG per frame (`name/0.png`, `name/1.png`, ...). Composing those into a single sheet is the Blender importer's job, not Photoshop's.
- **Mirror back to PSD.** The plugin can rebuild a PSD from a manifest. This reconstructs the source layout; it does not round-trip Blender edits back into the PSD.

## How it is built

The code is layered: an adapter isolates the Adobe API, the domain holds the pure, testable tag and planning logic, and the `io/` layer concentrates the side effects (file writes, the Photoshop API) so the domain stays platform-free. The manifest is validated with [ajv](https://ajv.js.org/) against the schema before anything reaches disk.

See [Architecture](../01-project/01-architecture.md) for how the plugin fits the pipeline.
