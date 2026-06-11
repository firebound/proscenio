# Spec 038: Reach

New export surfaces, taken on only when warranted.

## Scope

- **Krita exporter**.
- **GIMP exporter**.
- **GDExtension / C# escape hatch** - built only if a documented trigger is hit.

## Study

### Surface notes

- There is no code - all three items are green-field by design. `apps/` holds blender, docs, godot, and photoshop only; no Krita or GIMP code exists anywhere in the tree, no `apps/godot-csharp` exists, and [`AGENTS.md`](../../AGENTS.md) hard rule #3 (no GDExtension, no native runtime; the Godot plugin is GDScript-only and runs only at editor import time) is intact. The whole surface of this spec is two one-line backlog entries plus one well-documented architecture-revisit entry.
- The integration contract for a new DCC exporter already exists and is tool-agnostic. The Blender side consumes a PNG-per-layer set plus a manifest, not a raw `.psd` (`import_manifest`, [`__init__.py:42-68`](../../apps/blender/importers/photoshop/__init__.py)), so a Krita or GIMP exporter is a plugin in that DCC emitting the same manifest, with zero Blender-side changes. Prior art exists for both (coa_tools2 ships a Krita 4.x exporter and a GIMP path, per the [backlog entries](../backlog.md#krita-exporter)), which bounds a future port - but each port still buys a whole new GUI app in the manual test matrix, a new release artifact, a new plugin-API treadmill to track, and a new bug surface in a tool that is not part of the daily flow.
- Krita has a plausible audience but zero demand signal on record. The backlog entry is one line ("works in Krita 4.x. Phase 2 port-forward target"); no bug report, fixture, user request, or workflow note anywhere in the backlogs mentions Krita. The audience argument is real - Krita is the main FOSS 2D art tool and aligns with a Godot-FOSS user base, and today the only manifest producer is the Photoshop UXP plugin, so a Krita-only artist genuinely has no entry into the pipeline. That makes this a gate on demand rather than a drop: the moment a real Krita workflow asks, the port is bounded (emit the existing manifest contract); until then, scheduling it is speculation that multiplies the scarcest resource.
- GIMP is a weaker copy of the Krita case by the backlog's own ranking ("lower priority - fewer 2D animation users on GIMP"). Everything that gates Krita gates GIMP harder, and a future GIMP port would follow the Krita port's manifest pattern anyway, so the standing row adds planning weight and zero information. The durable knowledge - the manifest contract and the coa_tools2 prior art - is already written down and survives the row's deletion; git history recovers the rest if demand ever appears.
- The GDExtension / C# escape hatch is already a well-formed gate - the job is to keep it, not re-derive it. The [backlog entry](../backlog.md#gdextension--c-escape-hatch) documents five concrete reopen triggers (deep Firebound runtime integration becoming a GDScript-adapter bottleneck; `Polygon2D` skinning measured over frame budget on a real game scene; live-link streaming throughput beyond GDScript parsing; JSON parse time as import-loop pain on large projects; in-Godot round-trip authoring of `.proscenio`), and even sketches the future shape (separate optional `apps/godot-csharp/`, feature-flagged, mono-only cut documented openly, import-time only). The triggers are measurable, and none is hit today: no performance report, no live link, no binary format, and no in-Godot authoring exists anywhere in the backlogs. The entry is deliberately filed under "Architecture revisits (not slated)" - prior art recorded so a future trigger discussion starts warm, which is exactly what a gate should look like.

### Assessment

| Item | Flow value | Test burden | Bug surface | Underuse risk | Verdict | Why |
| --- | --- | --- | --- | --- | --- | --- |
| Krita exporter | 2 | 5 | 4 | 4 | gate | plausible FOSS audience but zero demand on record; when a real Krita workflow asks, the port targets the existing manifest contract |
| GIMP exporter | 1 | 5 | 4 | 5 | drop | weaker copy of the Krita case by the backlog's own ranking; the manifest contract and coa_tools2 prior art outlive the row |
| GDExtension / C# escape hatch | 2 | 5 | 5 | 5 | gate | five measurable triggers already documented, none hit; the hard rule stands until one is measured for real |

### Verdict summary

0 now, 0 defer, 2 gate, 1 drop.

Nothing in this spec is scheduled work - the spec is a fence, and the audit says the fence is in the right place. The Krita gate waits on a concrete demand signal (a real artist or contributor with a Krita-based workflow), at which point the port is bounded because the PNG-plus-manifest import contract is already tool-agnostic; the GDExtension gate keeps the five documented triggers as written and reopens only when one is hit and measured, never on language preference alone. GIMP drops: propose pruning its backlog row, since any future port would ride the Krita pattern and the prior art is already recorded. Every item here would add an entire app (or a native runtime) to the manual-GUI test matrix - the scarcest resource - so the bar for opening any of these gates is a demand signal or a measurement, never roadmap symmetry.
