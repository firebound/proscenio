// Unit tests for the spec-048 multiGet fast read. multiget-read imports
// { action } from "photoshop" at runtime, so this drives the host mock
// (vitest.config.ts test.alias) by configuring action.batchPlay. The pure
// flat-to-tree fold is covered separately in layer-descriptor.test.ts; here
// we cover the host-call adapter: result extraction and the null-on-failure
// fallback contract.

import { afterEach, describe, expect, it, vi } from "vitest";

import { action } from "photoshop";
import type { PsDocument } from "photoshop";

import { extractLayerList, readLayersViaMultiGet } from "../src/api/multiget-read";

type Mock = ReturnType<typeof vi.fn>;
const batchPlay = action.batchPlay as unknown as Mock;

afterEach(() => {
    batchPlay.mockReset();
    batchPlay.mockResolvedValue([]);
});

// A leaf descriptor in the live multiGet shape (layerSection is an
// { _enum, _value } envelope; bounds sides are { _unit, _value }).
function leaf(name: string, id: number): Record<string, unknown> {
    return {
        name,
        layerID: id,
        visible: true,
        layerSection: { _enum: "layerSectionType", _value: "layerSectionContent" },
        bounds: {
            _obj: "rectangle",
            top: { _unit: "pixelsUnit", _value: 0 },
            left: { _unit: "pixelsUnit", _value: 0 },
            bottom: { _unit: "pixelsUnit", _value: 8 },
            right: { _unit: "pixelsUnit", _value: 8 },
        },
    };
}

const docWithId = { id: 59 } as unknown as PsDocument;

describe("extractLayerList", () => {
    it("pulls the list out of the { list } envelope", () => {
        expect(extractLayerList([{ list: [1, 2, 3] }])).toEqual([1, 2, 3]);
    });

    it("accepts a `layers` key as a fallback", () => {
        expect(extractLayerList([{ layers: [1] }])).toEqual([1]);
    });

    it("takes a bare descriptor array as-is", () => {
        const bare = [{ name: "a" }];
        expect(extractLayerList(bare)).toEqual(bare);
    });

    it("returns null for a non-array result", () => {
        expect(extractLayerList(null)).toBeNull();
        expect(extractLayerList({ list: [] })).toBeNull();
    });
});

describe("readLayersViaMultiGet", () => {
    it("rebuilds the layer tree from a successful multiGet", async () => {
        batchPlay.mockResolvedValueOnce([{ list: [leaf("bottom", 1), leaf("top", 2)] }]);
        const layers = await readLayersViaMultiGet(docWithId);
        // Bottom-up source order -> top-down result.
        expect(layers?.map((l) => l.name)).toEqual(["top", "bottom"]);
    });

    it("returns null (fall back to DOM walk) when the doc has no id", async () => {
        const layers = await readLayersViaMultiGet({} as unknown as PsDocument);
        expect(layers).toBeNull();
        expect(batchPlay).not.toHaveBeenCalled();
    });

    it("returns null when batchPlay throws", async () => {
        batchPlay.mockRejectedValueOnce(new Error("descriptor error"));
        expect(await readLayersViaMultiGet(docWithId)).toBeNull();
    });

    it("returns null when the result list is empty", async () => {
        batchPlay.mockResolvedValueOnce([{ list: [] }]);
        expect(await readLayersViaMultiGet(docWithId)).toBeNull();
    });

    it("returns null when a non-empty list folds to an empty tree (shape drift)", async () => {
        // A descriptor whose section enum is unrecognised parses to null, so
        // the fold yields nothing - treat as a failed read, not an empty doc.
        batchPlay.mockResolvedValueOnce([
            { list: [{ name: "x", layerSection: { _enum: "layerSectionType", _value: "bogus" } }] },
        ]);
        expect(await readLayersViaMultiGet(docWithId)).toBeNull();
    });
});
