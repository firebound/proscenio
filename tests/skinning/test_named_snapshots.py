"""Pure tests for the named + rolling-auto weight snapshots."""

from __future__ import annotations

from core.skinning.sidecar_schema import (
    AUTO_SNAPSHOT_CAP,
    SidecarEntry,
    WeightSidecar,
    add_auto_snapshot,
    add_named_snapshot,
    find_snapshot,
    from_json,
    to_json,
)


def _entry(weight: float) -> SidecarEntry:
    return SidecarEntry(
        uv_anchor=(0.0, 0.0), weights={"bone": weight}, provenance="user_paint"
    )


def _sidecar() -> WeightSidecar:
    return WeightSidecar(
        version=1, vertex_group_names=["bone"], mesh_topology_hash="h", entries=[]
    )


def test_add_named_snapshot_appends() -> None:
    sidecar = add_named_snapshot(_sidecar(), "pose-a", [_entry(0.5)])
    assert [s.name for s in sidecar.snapshots] == ["pose-a"]
    assert sidecar.snapshots[0].kind == "manual"
    assert sidecar.snapshots[0].entries[0].weights == {"bone": 0.5}


def test_saving_a_manual_name_again_overwrites_not_duplicates() -> None:
    sidecar = add_named_snapshot(_sidecar(), "pose-a", [_entry(0.1)])
    sidecar = add_named_snapshot(sidecar, "pose-a", [_entry(0.9)])
    assert [s.name for s in sidecar.snapshots] == ["pose-a"]
    assert sidecar.snapshots[0].entries[0].weights == {"bone": 0.9}


def test_auto_snapshots_roll_to_the_cap() -> None:
    sidecar = _sidecar()
    for i in range(AUTO_SNAPSHOT_CAP + 2):
        sidecar = add_auto_snapshot(sidecar, f"auto-{i}", [_entry(float(i))])
    names = [s.name for s in sidecar.snapshots]
    # Only the last AUTO_SNAPSHOT_CAP survive; the two oldest dropped.
    assert names == [f"auto-{i}" for i in range(2, AUTO_SNAPSHOT_CAP + 2)]
    assert all(s.kind == "auto" for s in sidecar.snapshots)


def test_auto_snapshot_cap_zero_drops_all() -> None:
    sidecar = add_auto_snapshot(_sidecar(), "auto-0", [_entry(0.0)], cap=0)
    assert [s for s in sidecar.snapshots if s.kind == "auto"] == []


def test_auto_roll_leaves_manual_snapshots_untouched() -> None:
    sidecar = add_named_snapshot(_sidecar(), "keep-me", [_entry(0.5)])
    for i in range(AUTO_SNAPSHOT_CAP + 1):
        sidecar = add_auto_snapshot(sidecar, f"auto-{i}", [_entry(float(i))])
    manual = [s for s in sidecar.snapshots if s.kind == "manual"]
    auto = [s for s in sidecar.snapshots if s.kind == "auto"]
    assert [s.name for s in manual] == ["keep-me"]
    assert len(auto) == AUTO_SNAPSHOT_CAP


def test_find_snapshot_by_name() -> None:
    sidecar = add_named_snapshot(_sidecar(), "pose-a", [_entry(0.3)])
    assert find_snapshot(sidecar, "pose-a") is not None
    assert find_snapshot(sidecar, "missing") is None


def test_snapshots_survive_json_round_trip() -> None:
    sidecar = add_named_snapshot(_sidecar(), "pose-a", [_entry(0.4)])
    sidecar = add_auto_snapshot(sidecar, "auto-0", [_entry(0.7)])

    restored = from_json(to_json(sidecar))

    assert [(s.name, s.kind) for s in restored.snapshots] == [
        ("pose-a", "manual"),
        ("auto-0", "auto"),
    ]
    assert restored.snapshots[0].entries[0].weights == {"bone": 0.4}


def test_legacy_payload_without_snapshots_parses_to_empty_list() -> None:
    legacy = '{"version": 1, "vertex_group_names": [], "mesh_topology_hash": "h", "entries": []}'
    assert from_json(legacy).snapshots == []
