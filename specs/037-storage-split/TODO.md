# Spec 037: Storage split - TODO

Sequenced from the assessment in [STUDY.md](STUDY.md): the single scope item is gated, so nothing lands now.

## Deferred

- **Split PG-vs-CP storage by intent** - gate; trigger: the format-migration-path enabler (schema-expressiveness spec) has landed AND the 1.0.0 release window opens - block 1.0.0 on the split so the public surface ships the final storage contract, but keep it off the first tag; until the gate opens, new fields follow the existing uniform-mirror convention and every new field read routes through `read_field`, so the tree never grows a third hybrid state.
