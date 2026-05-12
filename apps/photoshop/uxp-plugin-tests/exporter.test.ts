// Unit tests for the pure exporter logic (SPEC 010 Wave 10.2).
//
// These tests run in Node via vitest against synthetic Layer trees -
// the planner does no I/O, so no Photoshop runtime is required. Wave
// 10.3 adds an integration smoke test that drives a real PSD through
// the materialiser; this file covers only the deterministic shape of
// the manifest entries.

import { describe, expect, it } from "vitest";

import {
    buildExportPlan,
    buildManifest,
    indicesAreContiguousFromZero,
    matchIndexedFrame,
    qualifiesAsSpriteFrameGroup,
    sanitize,
} from "../src/controllers/exporter";
import type { ArtLayer, Layer, LayerSet } from "../src/types/layer";
import type { ManifestEntry } from "../src/types/manifest";

const DEFAULT_BOUNDS = { x: 0, y: 0, w: 10, h: 10 };

function art(
    name: string,
    bounds: ArtLayer["bounds"] = DEFAULT_BOUNDS,
    visible = true,
): ArtLayer {
    return { kind: "art", name, visible, bounds };
}

function set(name: string, layers: Layer[], visible = true): LayerSet {
    return { kind: "set", name, visible, layers };
}

const doc = { name: "fixture.psd", width: 256, height: 256 };
const fullOpts = { skipHidden: true, skipUnderscorePrefix: true };

describe("matchIndexedFrame", () => {
    it("matches pure digits", () => {
        expect(matchIndexedFrame("0")).toEqual({ convention: "digit", base: "", index: 0 });
        expect(matchIndexedFrame("12")).toEqual({ convention: "digit", base: "", index: 12 });
    });

    it("matches frame_<n> prefix variants", () => {
        expect(matchIndexedFrame("frame_3")).toEqual({
            convention: "frame_prefix",
            base: "",
            index: 3,
        });
        expect(matchIndexedFrame("FRAME-7")).toEqual({
            convention: "frame_prefix",
            base: "",
            index: 7,
        });
    });

    it("matches <base>_<n> group prefix", () => {
        expect(matchIndexedFrame("eye_0")).toEqual({
            convention: "group_prefix",
            base: "eye",
            index: 0,
        });
        expect(matchIndexedFrame("walk-2")).toEqual({
            convention: "group_prefix",
            base: "walk",
            index: 2,
        });
    });

    it("rejects names without an index", () => {
        expect(matchIndexedFrame("torso")).toBeNull();
        expect(matchIndexedFrame("_hidden")).toBeNull();
        expect(matchIndexedFrame("frame")).toBeNull();
    });
});

describe("indicesAreContiguousFromZero", () => {
    it("accepts contiguous 0..n sequences in any order", () => {
        expect(indicesAreContiguousFromZero([0, 1, 2])).toBe(true);
        expect(indicesAreContiguousFromZero([2, 0, 1])).toBe(true);
    });

    it("rejects sequences with gaps or wrong start", () => {
        expect(indicesAreContiguousFromZero([1, 2, 3])).toBe(false);
        expect(indicesAreContiguousFromZero([0, 2, 3])).toBe(false);
        expect(indicesAreContiguousFromZero([])).toBe(false);
    });
});

describe("qualifiesAsSpriteFrameGroup", () => {
    it("accepts a set of digit-named children", () => {
        const g = set("eye", [art("0"), art("1"), art("2")]);
        expect(qualifiesAsSpriteFrameGroup(g)).toBe(true);
    });

    it("accepts uniform <base>_<n> children", () => {
        const g = set("hand", [art("h_0"), art("h_1")]);
        expect(qualifiesAsSpriteFrameGroup(g)).toBe(true);
    });

    it("rejects when child conventions diverge", () => {
        const g = set("mix", [art("0"), art("frame_1")]);
        expect(qualifiesAsSpriteFrameGroup(g)).toBe(false);
    });

    it("rejects when bases diverge in group_prefix", () => {
        const g = set("mix", [art("a_0"), art("b_1")]);
        expect(qualifiesAsSpriteFrameGroup(g)).toBe(false);
    });

    it("rejects a single-child group", () => {
        const g = set("solo", [art("0")]);
        expect(qualifiesAsSpriteFrameGroup(g)).toBe(false);
    });

    it("rejects when indices are not contiguous from zero", () => {
        const g = set("eye", [art("1"), art("2"), art("3")]);
        expect(qualifiesAsSpriteFrameGroup(g)).toBe(false);
    });

    it("rejects when any child is a LayerSet", () => {
        const g = set("eye", [art("0"), set("nested", [art("a")])]);
        expect(qualifiesAsSpriteFrameGroup(g)).toBe(false);
    });

    it("ignores hidden and _-prefixed children when scoring", () => {
        const g = set("eye", [
            art("0"),
            art("1"),
            art("_helper"),
            art("hidden", undefined, false),
        ]);
        expect(qualifiesAsSpriteFrameGroup(g)).toBe(true);
    });
});

describe("sanitize", () => {
    it("replaces non-alphanumeric with underscore", () => {
        expect(sanitize("a/b.c")).toBe("a_b_c");
        expect(sanitize("hand-01")).toBe("hand-01");
        expect(sanitize("spine.001")).toBe("spine_001");
    });
});

describe("buildManifest", () => {
    it("emits polygons in scene order with z_order increasing", () => {
        const layers: Layer[] = [
            art("torso", { x: 10, y: 20, w: 100, h: 200 }),
            art("head", { x: 40, y: 0, w: 80, h: 80 }),
        ];
        const m = buildManifest(doc, layers, fullOpts);
        expect(m.format_version).toBe(1);
        expect(m.doc).toBe("fixture.psd");
        expect(m.size).toEqual([256, 256]);
        expect(m.pixels_per_unit).toBe(100);
        expect(m.layers).toHaveLength(2);
        expect(m.layers[0]).toMatchObject({
            kind: "polygon",
            name: "torso",
            path: "images/torso.png",
            position: [10, 20],
            size: [100, 200],
            z_order: 0,
        });
        expect(m.layers[1].z_order).toBe(1);
    });

    it("respects skipHidden and skipUnderscorePrefix", () => {
        const layers: Layer[] = [
            art("keep"),
            art("_hidden_by_name"),
            art("hidden_flag", undefined, false),
        ];
        const m = buildManifest(doc, layers, fullOpts);
        expect(m.layers).toHaveLength(1);
        expect(m.layers[0].name).toBe("keep");
    });

    it("includes underscore + hidden layers when toggles are off", () => {
        const layers: Layer[] = [
            art("keep"),
            art("_dev_helper"),
            art("hidden_flag", undefined, false),
        ];
        const m = buildManifest(doc, layers, {
            skipHidden: false,
            skipUnderscorePrefix: false,
        });
        expect(m.layers).toHaveLength(3);
    });

    it("joins nested group names with __", () => {
        const layers: Layer[] = [
            set("body", [
                set("upper", [art("torso")]),
            ]),
        ];
        const m = buildManifest(doc, layers, fullOpts);
        expect(m.layers).toHaveLength(1);
        expect(m.layers[0].name).toBe("body__upper__torso");
        expect((m.layers[0] as PolygonEntry).path).toBe("images/body__upper__torso.png");
    });

    it("collapses an indexed group into a sprite_frame entry", () => {
        const layers: Layer[] = [
            set("blink", [
                art("0", { x: 0, y: 0, w: 32, h: 32 }),
                art("1", { x: 0, y: 0, w: 40, h: 40 }),
                art("2", { x: 0, y: 0, w: 32, h: 32 }),
            ]),
        ];
        const m = buildManifest(doc, layers, fullOpts);
        const aggregated = m.layers.filter(
            (e): e is Extract<ManifestEntry, { kind: "sprite_frame" }> => e.kind === "sprite_frame",
        );
        expect(aggregated).toHaveLength(1);
        expect(aggregated[0].name).toBe("blink");
        expect(aggregated[0].size).toEqual([40, 40]);
        expect(aggregated[0].frames.map((f) => f.index)).toEqual([0, 1, 2]);
        expect(aggregated[0].frames[0].path).toBe("images/blink/0.png");
    });

    it("renumbers z_order after flat-sibling aggregation", () => {
        const layers: Layer[] = [
            art("head", { x: 0, y: 0, w: 10, h: 10 }),
            art("walk_0", { x: 0, y: 0, w: 20, h: 20 }),
            art("walk_1", { x: 0, y: 0, w: 30, h: 30 }),
            art("torso", { x: 0, y: 0, w: 50, h: 50 }),
        ];
        const m = buildManifest(doc, layers, fullOpts);
        expect(m.layers.map((e) => e.z_order)).toEqual([0, 1, 2]);
        const walk = m.layers.find((e) => e.name === "walk");
        expect(walk?.kind).toBe("sprite_frame");
    });

    it("drops layers with zero or missing bounds", () => {
        const layers: Layer[] = [
            art("ghost", null),
            art("flat", { x: 0, y: 0, w: 0, h: 50 }),
            art("keep"),
        ];
        const m = buildManifest(doc, layers, fullOpts);
        expect(m.layers).toHaveLength(1);
        expect(m.layers[0].name).toBe("keep");
    });
});

describe("flat-sibling sprite_frame aggregation (via buildManifest)", () => {
    it("does not aggregate when indices skip zero", () => {
        const layers: Layer[] = [art("walk_1"), art("walk_2")];
        const m = buildManifest(doc, layers, fullOpts);
        expect(m.layers.every((e) => e.kind === "polygon")).toBe(true);
    });

    it("does not aggregate when only one matching sibling exists", () => {
        const layers: Layer[] = [art("walk_0"), art("torso")];
        const m = buildManifest(doc, layers, fullOpts);
        expect(m.layers.every((e) => e.kind === "polygon")).toBe(true);
    });
});

describe("buildExportPlan", () => {
    it("emits one PngWrite per polygon with layerPath rooted at doc layers", () => {
        const layers: Layer[] = [
            set("body", [set("upper", [art("torso")])]),
            art("head"),
        ];
        const plan = buildExportPlan(doc, layers, fullOpts);
        expect(plan.writes).toHaveLength(2);
        expect(plan.writes[0]).toEqual({
            layerPath: ["body", "upper", "torso"],
            outputPath: "images/body__upper__torso.png",
        });
        expect(plan.writes[1]).toEqual({
            layerPath: ["head"],
            outputPath: "images/head.png",
        });
    });

    it("emits one PngWrite per frame for nested sprite_frame groups", () => {
        const layers: Layer[] = [
            set("blink", [art("0"), art("1"), art("2")]),
        ];
        const plan = buildExportPlan(doc, layers, fullOpts);
        expect(plan.writes).toHaveLength(3);
        expect(plan.writes[0]).toEqual({
            layerPath: ["blink", "0"],
            outputPath: "images/blink/0.png",
        });
        expect(plan.writes[2].layerPath).toEqual(["blink", "2"]);
    });

    it("emits one PngWrite per flat-aggregated sibling, preserving source names", () => {
        const layers: Layer[] = [
            art("walk_0"),
            art("walk_1"),
        ];
        const plan = buildExportPlan(doc, layers, fullOpts);
        expect(plan.writes).toHaveLength(2);
        expect(plan.writes[0].layerPath).toEqual(["walk_0"]);
        expect(plan.writes[0].outputPath).toBe("images/walk_0.png");
        expect(plan.writes[1].layerPath).toEqual(["walk_1"]);
    });
});
