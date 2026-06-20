# Spec 059: Skin coordination - TODO

Pending the form call in the STUDY and the format-migration dependency. Rows finalize once the form is locked and the dependency resolves.

## After the form is locked

- [ ] Define the skin representation in the schema (first-class `skins[]` riding the format migration, or the additive generated-animations form).
- [ ] Emit the skin data from the writer.
- [ ] Build the Godot runtime selector that applies a skin (swaps the chosen attachment per slot across the named set), defining its place in the import-only plugin's scope.
- [ ] Define the override semantics: how a per-slot attachment override interacts with an active skin.
- [ ] End-to-end fixture and test: a multi-slot character with two named skins switches all slots with one call.
