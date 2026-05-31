# scripts/debug/

Ad-hoc probes for inspecting Blender internals. Each script is standalone, runs once via headless Blender, and writes its output to a sibling file in this folder (gitignored).

These are not part of any pipeline. They land here when "I want to know what shape this object has at runtime" was the question; the script stays committed for the next time the same question comes up.

## Current probes

- `inspect_action.py` - dumps the Action / layer / strip structure of every action in the open `.blend`. Useful for tracking Blender API changes across releases when the writer breaks on a new version.
- `inspect_blend.py` - dumps armatures, meshes, materials, actions, and custom properties relevant to the Proscenio writer. Useful when authoring or debugging the exporter against an unfamiliar fixture.

## Run

```text
blender --background <path/to/fixture.blend> --python scripts/debug/<probe>.py
```

Output lands at `scripts/debug/<probe>.out` next to the script. Headless Blender on Windows does not flush stdout reliably, so the scripts write to file directly.
