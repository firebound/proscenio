# Spec 055: Re-import contract - TODO

Candidate work, pending the STUDY decisions. Rows finalize once the contract is locked; the measurement step is unconditional and comes first.

## Measure (unconditional, before any decision)

- [ ] Round-trip the Photoshop weights case: import manifest, skin and paint weights, edit the PSD placement, re-import, inspect whether painted values survive. Record the result against `planes.py` and `tests/operators/test_psd_reimport.py`.
- [ ] Round-trip the armature reuse case: confirm whether `import_manifest` calling `build_root_armature` every run destroys rotation / parenting / weights. `importers/photoshop/__init__.py:68-91`.

## Photoshop re-import (one of)

- [ ] If weights survive by design: correct `docs/00-guides/01-advanced/01-photoshop.md` to state the sidecar reprojection, and keep the code.
- [ ] If the reprojection is an unintended change: restore the documented behavior or relabel the weight-operation matrix, with a test pinning the chosen contract.
- [ ] Resolve the armature rebuild: reuse the existing armature when shape is unchanged, or correct the doc claim. `importers/photoshop/__init__.py:68-91`.

## Godot reimporter (one of)

- [ ] Build the diff/merge reimporter in `reimporter.gd` that preserves user edits across re-import.
- [ ] Drop the non-destructive claim from the header and the docs, and document the wrapper-scene instancing pattern as the supported path.

## After the contract lands

- [ ] Make `FLOW-REIMPORT-WEIGHTS-01` in the QA Companion checklist assert the locked behavior.
