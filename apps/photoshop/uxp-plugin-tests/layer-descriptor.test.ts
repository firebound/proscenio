// Unit tests for the flat-descriptor -> nested Layer tree rebuild used by
// the spec-048 batchPlay multiGet read path. layer-descriptor imports only
// types from "../src/lib/layer" (erased at runtime), so it runs under plain
// vitest against loose object fakes - no host mock needed.
//
// The raw-descriptor field names below mirror the multiGet shape confirmed
// against a real PSD (see the "live-PSD descriptor envelopes" cases). The
// fold logic (tree shape, ordering) is the part under test here; the field
// mapper is a thin adapter.

import { describe, expect, it } from "vitest";

import { parseDescriptor, rebuildLayerTree } from "../src/lib/layer-descriptor";

type RawBounds = { top: number; left: number; bottom: number; right: number };

// Build a raw leaf (art layer) descriptor in the EXPECTED multiGet shape.
function rawArt(
    name: string,
    bounds: RawBounds | null,
    extra: Record<string, unknown> = {},
): Record<string, unknown> {
    return {
        name,
        visible: true,
        layerID: undefined,
        layerSection: "layerSectionContent",
        ...(bounds === null ? {} : { bounds }),
        ...extra,
    };
}

// Photoshop encodes a group as a START marker plus a CLOSING divider; the
// flat array (in PS bottom-up enumeration) carries the end divider first,
// the children, then the start marker. These helpers name the two markers
// so the ordering intent in each test is explicit.
function rawGroupStart(name: string, extra: Record<string, unknown> = {}): Record<string, unknown> {
    return { name, visible: true, layerID: undefined, layerSection: "layerSectionStart", ...extra };
}

function rawGroupEnd(extra: Record<string, unknown> = {}): Record<string, unknown> {
    return { name: "</Layer group>", visible: true, layerSection: "layerSectionEnd", ...extra };
}

describe("parseDescriptor", () => {
    it("maps a leaf descriptor to a parsed art entry", () => {
        const entry = parseDescriptor(rawArt("torso", { left: 10, top: 20, right: 40, bottom: 60 }));
        expect(entry).toEqual({
            section: "content",
            name: "torso",
            visible: true,
            id: undefined,
            bounds: { x: 10, y: 20, w: 30, h: 40 },
        });
    });

    it("classifies a group-start marker", () => {
        const entry = parseDescriptor(rawGroupStart("arm"));
        expect(entry?.section).toBe("start");
        expect(entry?.name).toBe("arm");
    });

    it("classifies a group-end divider", () => {
        const entry = parseDescriptor(rawGroupEnd());
        expect(entry?.section).toBe("end");
    });

    it("nulls zero/negative-area bounds (w<=0 || h<=0)", () => {
        const flat = parseDescriptor(rawArt("flat", { left: 5, top: 5, right: 5, bottom: 9 }));
        expect(flat?.bounds).toBeNull();
        const neg = parseDescriptor(rawArt("neg", { left: 5, top: 5, right: 2, bottom: 9 }));
        expect(neg?.bounds).toBeNull();
    });

    it("nulls missing bounds", () => {
        expect(parseDescriptor(rawArt("blank", null))?.bounds).toBeNull();
    });

    it("carries a numeric layer id when present", () => {
        const entry = parseDescriptor(rawArt("torso", null, { layerID: 314 }));
        expect(entry?.id).toBe(314);
    });

    it("leaves id undefined when the descriptor omits a numeric id", () => {
        const entry = parseDescriptor(rawArt("torso", null, { layerID: "not-a-number" }));
        expect(entry?.id).toBeUndefined();
    });

    it("returns null for an unparseable descriptor", () => {
        expect(parseDescriptor(null)).toBeNull();
        expect(parseDescriptor(42)).toBeNull();
        expect(parseDescriptor({ name: 5 })).toBeNull();
        expect(parseDescriptor({ name: "x", layerSection: "bogus" })).toBeNull();
    });
});

// Live-PSD descriptor shape, confirmed against doll_tagged_debug.psd via the
// spec-048 read probe: `layerSection` is an `{ _enum, _value }` envelope (not a
// bare string), and each bounds side is a `{ _unit, _value }` envelope under a
// `{ _obj: "rectangle" }` object. The mapper must accept both this real shape
// and the bare-string shape the other tests use.
function unit(value: number): { _unit: string; _value: number } {
    return { _unit: "pixelsUnit", _value: value };
}

function realSection(value: string): { _enum: string; _value: string } {
    return { _enum: "layerSectionType", _value: value };
}

function realArt(name: string, b: RawBounds, layerID: number): Record<string, unknown> {
    return {
        name,
        layerID,
        visible: true,
        layerSection: realSection("layerSectionContent"),
        bounds: {
            _obj: "rectangle",
            top: unit(b.top),
            left: unit(b.left),
            bottom: unit(b.bottom),
            right: unit(b.right),
        },
        layerKind: 1,
    };
}

describe("live-PSD descriptor envelopes (probe-confirmed)", () => {
    it("parses the enum-wrapped layerSection and envelope bounds", () => {
        const entry = parseDescriptor(
            realArt("arm.L", { left: 539, top: 340, right: 684, bottom: 594 }, 3),
        );
        expect(entry).toEqual({
            section: "content",
            name: "arm.L",
            visible: true,
            id: 3,
            bounds: { x: 539, y: 340, w: 145, h: 254 },
        });
    });

    it("classifies enum-wrapped start/end markers", () => {
        expect(parseDescriptor({ name: "g", layerSection: realSection("layerSectionStart") })?.section)
            .toBe("start");
        expect(
            parseDescriptor({ name: "</Layer group>", layerSection: realSection("layerSectionEnd") })
                ?.section,
        ).toBe("end");
    });

    it("rebuilds a real-shaped group + leaf top-down", () => {
        const tree = rebuildLayerTree([
            realArt("Camada 1", { left: 0, top: 0, right: 0, bottom: 0 }, 2),
            { name: "</Layer group>", layerSection: realSection("layerSectionEnd"), layerID: 46 },
            realArt("hand.R", { left: 0, top: 0, right: 5, bottom: 5 }, 5),
            { name: "hands", layerSection: realSection("layerSectionStart"), layerID: 40 },
        ]);
        expect(tree.map((l) => l.name)).toEqual(["hands", "Camada 1"]);
        const set = tree[0];
        expect(set?.kind).toBe("set");
        if (set?.kind === "set") {
            expect(set.id).toBe(40);
            expect(set.layers.map((l) => l.name)).toEqual(["hand.R"]);
        }
        const camada = tree[1];
        expect(camada?.kind).toBe("art");
        if (camada?.kind === "art") expect(camada.bounds).toBeNull();
    });
});

describe("rebuildLayerTree", () => {
    it("rebuilds a flat list top-down (top layer first)", () => {
        // PS enumerates bottom-up: index 0 is the bottom-most layer. The
        // produced Layer[] must be top-down, so "top" comes out first.
        const tree = rebuildLayerTree([
            rawArt("bottom", { left: 0, top: 0, right: 4, bottom: 4 }),
            rawArt("top", { left: 0, top: 0, right: 8, bottom: 8 }),
        ]);
        expect(tree.map((l) => l.name)).toEqual(["top", "bottom"]);
    });

    it("nests a single group's children", () => {
        // bottom-up flat: end divider, child, start marker.
        const tree = rebuildLayerTree([
            rawGroupEnd(),
            rawArt("hand", { left: 0, top: 0, right: 5, bottom: 5 }),
            rawGroupStart("arm"),
        ]);
        expect(tree).toHaveLength(1);
        const set = tree[0];
        expect(set?.kind).toBe("set");
        if (set?.kind === "set") {
            expect(set.name).toBe("arm");
            expect(set.layers.map((l) => l.name)).toEqual(["hand"]);
        }
    });

    it("nests a group within a group", () => {
        // Visual:
        //   outer (set)
        //     inner (set)
        //       finger (art)
        // bottom-up flat order:
        //   outer end, inner end, finger, inner start, outer start
        const tree = rebuildLayerTree([
            rawGroupEnd(),
            rawGroupEnd(),
            rawArt("finger", { left: 0, top: 0, right: 2, bottom: 2 }),
            rawGroupStart("inner"),
            rawGroupStart("outer"),
        ]);
        expect(tree).toHaveLength(1);
        const outer = tree[0];
        expect(outer?.kind).toBe("set");
        if (outer?.kind === "set") {
            expect(outer.name).toBe("outer");
            expect(outer.layers).toHaveLength(1);
            const inner = outer.layers[0];
            expect(inner?.kind).toBe("set");
            if (inner?.kind === "set") {
                expect(inner.name).toBe("inner");
                expect(inner.layers.map((l) => l.name)).toEqual(["finger"]);
            }
        }
    });

    it("produces an empty group as a set with no layers", () => {
        const tree = rebuildLayerTree([rawGroupEnd(), rawGroupStart("empty")]);
        expect(tree).toHaveLength(1);
        const set = tree[0];
        expect(set?.kind).toBe("set");
        if (set?.kind === "set") {
            expect(set.name).toBe("empty");
            expect(set.layers).toEqual([]);
        }
    });

    it("keeps top-down sibling order across a group and a leaf", () => {
        // bottom-up flat: a leaf at the bottom, then a group above it.
        //   group end, group child, group start, top leaf
        const tree = rebuildLayerTree([
            rawArt("under", { left: 0, top: 0, right: 4, bottom: 4 }),
            rawGroupEnd(),
            rawArt("child", { left: 0, top: 0, right: 3, bottom: 3 }),
            rawGroupStart("mid"),
            rawArt("over", { left: 0, top: 0, right: 5, bottom: 5 }),
        ]);
        expect(tree.map((l) => l.name)).toEqual(["over", "mid", "under"]);
    });

    it("uses the layer id when present and omits it otherwise", () => {
        const tree = rebuildLayerTree([
            rawArt("with-id", null, { layerID: 7 }),
            rawArt("no-id", null),
        ]);
        const withId = tree.find((l) => l.name === "with-id");
        const noId = tree.find((l) => l.name === "no-id");
        expect(withId?.id).toBe(7);
        expect(noId?.id).toBeUndefined();
    });

    it("skips unparseable entries without throwing", () => {
        const tree = rebuildLayerTree([
            rawArt("keep", { left: 0, top: 0, right: 4, bottom: 4 }),
            null,
            { name: 5 },
        ]);
        expect(tree.map((l) => l.name)).toEqual(["keep"]);
    });

    it("returns an empty tree for an empty input", () => {
        expect(rebuildLayerTree([])).toEqual([]);
    });
});
