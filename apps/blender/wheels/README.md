# apps/blender/wheels/

Bundled Python wheels installed alongside the Proscenio Blender addon.

Blender 4.2 added extension manifests that ship third-party wheels in an isolated `site-packages` per extension. The addon imports `pydantic` and `proscenio_models` from this bundle; Blender's own bundled Python stays untouched.

## Bundle contents

| Wheel | Origin | Why bundled |
| --- | --- | --- |
| `pydantic-*.whl` | PyPI, pure Python | Domain-model runtime: validators, discriminated unions, schema dump. |
| `pydantic_core-*-<plat>.whl` (5 platforms x 2 ABIs) | PyPI, Rust-backed | Pydantic's parser core. Per-platform wheels: Linux x86_64 / aarch64, macOS x86_64 / arm64, Windows amd64. Two ABIs: cp311 for Blender 4.2 LTS (Python 3.11), cp313 for Blender 5.x (Python 3.13). Blender installs the wheel matching the running interpreter. |
| `annotated_types-*.whl` | PyPI, pure Python | Required by `pydantic`. |
| `typing_extensions-*.whl` | PyPI, pure Python | Required by `pydantic`. |
| `typing_inspection-*.whl` | PyPI, pure Python | Required by `pydantic`. |
| `proscenio_models-*.whl` | Local, built from `packages/models/` | The typed `.proscenio` domain model. |

Pinned versions in `apps/blender/blender_manifest.toml` mirror the resolutions in the workspace `uv.lock`, so the bundled addon and the workspace dev environment run the same pydantic.

## Regenerating the bundle

Run from the repository root with `uv` and `pip` available on `PATH`:

```powershell
# Pure-Python wheels - one download serves every platform
$pure = @(
    "pydantic==2.13.4",
    "annotated-types==0.7.0",
    "typing-extensions==4.15.0",
    "typing-inspection==0.4.2"
)
foreach ($pkg in $pure) {
    pip download $pkg --no-deps --only-binary=:all: `
        -d apps/blender/wheels `
        --python-version 3.11
}

# pydantic-core - one wheel per platform Blender supports.
# macOS x86_64 ships under the broader macosx_10_12_x86_64 tag on PyPI
# (forward-compatible with 11.0+); arm64 ships under macosx_11_0_arm64.
$platforms = @(
    "manylinux2014_x86_64",
    "manylinux2014_aarch64",
    "macosx_10_12_x86_64",
    "macosx_11_0_arm64",
    "win_amd64"
)
# Two ABIs: cp311 (Blender 4.2 LTS) + cp313 (Blender 5.x). Blender picks
# the wheel matching the running interpreter at install time.
$abis = @(
    @{ pyver = "3.11"; abi = "cp311" },
    @{ pyver = "3.13"; abi = "cp313" }
)
foreach ($plat in $platforms) {
    foreach ($a in $abis) {
        pip download pydantic-core==2.46.4 --no-deps --only-binary=:all: `
            -d apps/blender/wheels `
            --platform $plat --python-version $a.pyver --implementation cp --abi $a.abi
    }
}

# proscenio-models - built from the workspace
uv build packages/models --wheel --out-dir apps/blender/wheels
```

After regenerating, update the `wheels = [...]` block in `blender_manifest.toml` to match the new filenames (versions bumped, platform suffixes changed, etc).

## When to bump

- A pinned dependency in `packages/models/pyproject.toml` or `packages/codegen/pyproject.toml` gets bumped.
- A pydantic security advisory or behavior change matters.
- Blender lifts the minimum Python version and a newer ABI tag becomes the target.

Old wheels are not source-of-truth: drop them when bumping; CI fixture validation + the round-trip tests catch any model regression.
