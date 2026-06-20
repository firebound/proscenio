# Spec 059: Skin coordination

Named attachment sets across slots, in the style of Spine skins: one switch swaps an attachment per slot across many slots at once. This is a coordination surface spanning three apps (the schema, the writer, and a runtime selector in Godot), and it leans on a Godot runtime layer the importer-only plugin deliberately does not have today. This spec decides the form, then builds it.

This spec is STUDY-first and is the heaviest of the open features. It is sequenced behind the storage and format work it depends on, so the scaffold marks the decision and the dependency, not a ready build.

## Scope

- Decide the form: first-class `skins[]` in the schema, versus an additive form expressed through the generated-animations path.
- Define the runtime selector in Godot that applies a skin (the layer the importer-only plugin lacks).
- Wire the chosen form end to end: schema, writer, runtime.

## Open questions (resolve before coding)

- Form: first-class `skins[]` depends on the format migration path (a v2 schema with a migrator), which is itself gated. The additive form via generated-animations does not depend on it, but carries runtime semantics that are fragile under attachment overrides. Which trade is right?
- Runtime layer: building a runtime selector means adding the first piece of an actual Godot runtime to a plugin scoped as import-only. Is that scope expansion warranted, and where does it live?

## Sources

Drains the `skin-coordination` spec-sized item in [`backlog.md`](../backlog.md). Depends on `format-migration-path` (see [`gated.md`](../gated.md)) for the first-class form, and is sequenced with the storage-split work (spec 037). The related `drive-slot-from-bone` capability stays in [`gated.md`](../gated.md).
