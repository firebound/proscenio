// Unit tests for the click-to-select api. Covers reading the active
// layer path (parent-chain walk, guards) and selecting a layer by id
// through the host mock's core.executeAsModal + action.batchPlay.

import { afterEach, describe, expect, it, vi } from "vitest";

import { action, app } from "photoshop";

import { readActiveLayerPath, selectLayerByPath } from "../src/api/ps-selection";

type MutableApp = { activeDocument: unknown };

afterEach(() => {
    (app as MutableApp).activeDocument = null;
    vi.restoreAllMocks();
});

describe("readActiveLayerPath", () => {
    it("returns null when no document is open", () => {
        (app as MutableApp).activeDocument = null;
        expect(readActiveLayerPath()).toBeNull();
    });

    it("returns null when not exactly one layer is active", () => {
        (app as MutableApp).activeDocument = { activeLayers: [{}, {}] };
        expect(readActiveLayerPath()).toBeNull();
    });

    it("returns null (does not throw) when activeLayers is null", () => {
        // Some UXP builds hand back null for the collection; the old code
        // read `.length` off it and threw. Must degrade to "no selection".
        (app as MutableApp).activeDocument = { activeLayers: null };
        expect(() => readActiveLayerPath()).not.toThrow();
        expect(readActiveLayerPath()).toBeNull();
    });

    it("builds the name chain from the leaf up to the document", () => {
        const doc: Record<string, unknown> = { width: 100, height: 100 };
        const arm = { name: "arm", parent: doc };
        const hand = { name: "hand", parent: arm };
        doc.activeLayers = [hand];
        (app as MutableApp).activeDocument = doc;
        expect(readActiveLayerPath()).toEqual(["arm", "hand"]);
    });
});

describe("selectLayerByPath", () => {
    it("ignores an empty path", async () => {
        const batchPlay = vi.spyOn(action, "batchPlay");
        await selectLayerByPath([]);
        expect(batchPlay).not.toHaveBeenCalled();
    });

    it("returns early when no document is open", async () => {
        (app as MutableApp).activeDocument = null;
        const batchPlay = vi.spyOn(action, "batchPlay");
        await selectLayerByPath(["a"]);
        expect(batchPlay).not.toHaveBeenCalled();
    });

    it("selects the resolved layer by id via batchPlay", async () => {
        const target = { name: "torso", id: 42 };
        (app as MutableApp).activeDocument = { layers: [target] };
        const batchPlay = vi.spyOn(action, "batchPlay").mockResolvedValue([]);
        await selectLayerByPath(["torso"]);
        expect(batchPlay).toHaveBeenCalledOnce();
        const descriptor = batchPlay.mock.calls[0]?.[0] as Array<{ _target: Array<{ _id: number }> }>;
        expect(descriptor[0]?._target[0]?._id).toBe(42);
    });
});
