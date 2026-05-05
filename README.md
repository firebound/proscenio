# Proscenio

Blender → Godot 4 pipeline for 2D cutout animation. Native `Skeleton2D` + `Bone2D` + `Polygon2D` output. No runtime, no GDExtension, no custom engine build.

> **Status:** pre-alpha. Format unstable. Not for production use.

## Why

The 2D cutout pipeline for Godot has gaps:

- **Spine2D** — paid, opaque format, GDExtension dependency, third-party-of-third-party support story.
- **COA Tools / coa_tools2** — Blender side alive (Blender 4.x and 5.x), Godot side broken or abandoned.
- **Godot 2D Bridge** — proves `Polygon2D` + `Skeleton2D` export works, but no animations and stuck on Godot 4.0.

Proscenio fills the gap: rig and animate in Blender, import into Godot 4 as native scenes (`.tscn`). After import, Godot does not know the asset came from Blender.

## Components

| Folder | Purpose |
| --- | --- |
| [`photoshop-exporter/`](photoshop-exporter/) | JSX script: PSD layers → sprites + position JSON |
| [`blender-addon/`](blender-addon/) | Blender 4.2+ addon: sprite import, rigging, animation, `.proscenio` export |
| [`godot-plugin/`](godot-plugin/) | Godot 4.3+ `EditorImportPlugin`: `.proscenio` → `.tscn` |
| [`schemas/`](schemas/) | `proscenio.schema.json` — versioned format spec, single source of truth |
| [`examples/`](examples/) | End-to-end sample assets (binary files via Git LFS) |

## Quickstart

The MVP is in progress. Full quickstart will land with the first end-to-end sample. The iteration loop, once both sides ship:

1. Author the character in Blender — bones, sprites, animations.
2. Run the Proscenio export operator to write a `.proscenio` next to the source.
3. Drop the `.proscenio` (and its atlas) into your Godot project. The importer regenerates a `.scn` automatically on every reimport.
4. **Wrap the imported scene** — instance the generated `.scn` in your own `.tscn` and attach scripts there. Scripts and extra nodes on the wrapper survive every re-export from Blender; the imported scene itself is regenerated each time. See [`examples/dummy/`](examples/dummy/) for the worked pattern.
5. Re-export from Blender whenever the rig or animation changes. Reimport is automatic.

## Documentation

- **Contributors and LLM agents:** start at [AGENTS.md](AGENTS.md) → [`.ai/skills/`](.ai/skills/)
- **Current plan:** [`specs/000-initial-plan/STUDY.md`](specs/000-initial-plan/STUDY.md) and [`specs/000-initial-plan/TODO.md`](specs/000-initial-plan/TODO.md)

## License

GPL-3.0-or-later. See [LICENSE](LICENSE).
