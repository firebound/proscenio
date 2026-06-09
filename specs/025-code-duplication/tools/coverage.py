"""Emit a file-by-file coverage matrix for the type-4 audit.

Reuses ast_scan.collect() so the function set is identical to the audit.
Marks, per file: function counts, whether it tripped any automated signal
(skeleton group / call-overlap pair / name collision), and whether its
bodies were read by hand during the audit.
"""

from __future__ import annotations

import collections
from itertools import combinations

import ast_scan  # same directory

# Files whose function bodies were opened and read during the audit.
MANUALLY_READ = {
    "core/bpy_helpers/_shared/modal_overlay.py",
    "core/bpy_helpers/automesh/base_sprite.py",
    "core/mirror.py",
    "core/bpy_helpers/automesh/debug.py",
    "core/bpy_helpers/automesh/authoring_session.py",
    "core/bpy_helpers/skinning/modal_session.py",
    "operators/automesh/automesh.py",
    "operators/automesh/automesh_authoring.py",
    "exporters/godot/writer/scene_discovery.py",
    "exporters/godot/writer/sprites.py",
    "importers/photoshop/planes.py",
    "core/validation/active_element.py",
    "core/validation/active_slot.py",
    "core/_shared/pg_cp_fallback.py",
    "core/_shared/region.py",
    "panels/_draw_mesh.py",
    "panels/_draw_sprite.py",
    "operators/export_flow.py",
    "operators/armature/quick_armature.py",
    "core/bpy_helpers/automesh/authoring_pipeline.py",
    "properties/_dynamic_items.py",
    "properties/scene_props.py",
}

FRAMEWORK = {
    "register", "unregister", "poll", "execute", "draw", "invoke", "modal",
    "cancel", "draw_header", "draw_header_preset", "draw_item", "__init__",
    "__call__", "_finish",
}


def main() -> None:
    funcs = ast_scan.collect()

    # --- recompute the three automated signals, tag the files they touch ---
    flagged: dict[str, set[str]] = collections.defaultdict(set)

    prod = [f for f in funcs if not f.is_test]

    # skeleton groups
    by_skel: dict[str, list] = collections.defaultdict(list)
    for f in prod:
        if f.skel_len >= 12:
            by_skel[f.skel_hash].append(f)
    for g in by_skel.values():
        if len(g) > 1:
            for f in g:
                flagged[f.file].add("skeleton")

    # call-overlap pairs
    rich = [f for f in prod if len(f.call_set) >= 4]
    for a, b in combinations(rich, 2):
        if a.skel_hash == b.skel_hash:
            continue
        if ast_scan.jaccard(a.call_set, b.call_set) >= 0.6:
            flagged[a.file].add("call-overlap")
            flagged[b.file].add("call-overlap")

    # name collisions
    byname: dict[str, list] = collections.defaultdict(list)
    for f in prod:
        leaf = f.qual.split(".")[-1]
        if leaf in FRAMEWORK or leaf.startswith("__"):
            continue
        byname[leaf].append(f)
    for fs in byname.values():
        files = {f.file for f in fs}
        if len(files) > 1:
            for f in fs:
                flagged[f.file].add("name-collision")

    # --- per-file rollup ---
    per_file: dict[str, dict[str, int]] = collections.defaultdict(
        lambda: {"prod": 0, "test": 0}
    )
    for f in funcs:
        per_file[f.file]["test" if f.is_test else "prod"] += 1

    files = sorted(per_file)
    n_read = sum(1 for x in files if x in MANUALLY_READ)
    n_flag = sum(1 for x in files if flagged.get(x))

    print("# Type-4 audit - file-by-file coverage\n")
    print(f"Files: {len(files)}. Functions: {sum(v['prod'] + v['test'] for v in per_file.values())} "
          f"(production {sum(v['prod'] for v in per_file.values())}, "
          f"test {sum(v['test'] for v in per_file.values())}).")
    print(f"Every file got Tier A (automated AST signals). "
          f"{n_flag} files tripped a signal; {n_read} files were read by hand (Tier B).\n")
    print("Legend: A = automated AST scan (all). B = bodies read by hand. "
          "signals = which automated lists the file appeared in.\n")
    print("| File | prod | test | signals | read |")
    print("|------|-----:|-----:|---------|:----:|")
    for x in files:
        sig = ",".join(sorted(flagged.get(x, set()))) or "-"
        read = "B" if x in MANUALLY_READ else ""
        v = per_file[x]
        print(f"| {x} | {v['prod']} | {v['test']} | {sig} | {read} |")


if __name__ == "__main__":
    main()
