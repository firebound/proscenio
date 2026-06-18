// Unit tests for the active-document reads. active-document imports
// { app } from "photoshop" at runtime, so this drives the host mock
// (vitest.config.ts test.alias) by setting app.activeDocument.

import { afterEach, describe, expect, it, vi } from "vitest";

import { action, app } from "photoshop";

import {
    readActiveLayerTree,
    readActiveLayerTreeAsync,
    readDocSnapshot,
} from "../src/api/active-document";

type MutableApp = { activeDocument: unknown };
type Mock = ReturnType<typeof vi.fn>;
const batchPlay = action.batchPlay as unknown as Mock;

afterEach(() => {
    (app as MutableApp).activeDocument = null;
    batchPlay.mockReset();
    batchPlay.mockResolvedValue([]);
});

describe("readDocSnapshot", () => {
    it("returns null when no document is open", () => {
        (app as MutableApp).activeDocument = null;
        expect(readDocSnapshot()).toBeNull();
    });

    it("reads the name and size of the active document", () => {
        (app as MutableApp).activeDocument = {
            name: "hero.psd",
            width: 512,
            height: 256,
            layers: [],
        };
        expect(readDocSnapshot()).toEqual({ name: "hero.psd", width: 512, height: 256 });
    });
});

describe("readActiveLayerTree", () => {
    it("returns null when no document is open", () => {
        (app as MutableApp).activeDocument = null;
        expect(readActiveLayerTree()).toBeNull();
    });

    it("adapts the active document's layer tree", () => {
        (app as MutableApp).activeDocument = {
            name: "hero.psd",
            width: 10,
            height: 10,
            layers: [{ name: "bg", visible: true, bounds: { left: 0, top: 0, right: 4, bottom: 4 } }],
        };
        const tree = readActiveLayerTree();
        expect(tree?.info.name).toBe("hero.psd");
        expect(tree?.layers).toHaveLength(1);
        expect(tree?.layers[0]?.name).toBe("bg");
    });
});

describe("readActiveLayerTreeAsync", () => {
    it("returns null when no document is open", async () => {
        (app as MutableApp).activeDocument = null;
        expect(await readActiveLayerTreeAsync()).toBeNull();
    });

    it("uses the multiGet fast path when it succeeds", async () => {
        (app as MutableApp).activeDocument = {
            id: 7,
            name: "fast.psd",
            width: 10,
            height: 10,
            // DOM-walk layers differ from the multiGet result so the test
            // proves the multiGet path won, not the fallback.
            layers: [{ name: "dom-walk", visible: true, bounds: { left: 0, top: 0, right: 4, bottom: 4 } }],
        };
        batchPlay.mockResolvedValueOnce([
            {
                list: [
                    {
                        name: "from-multiget",
                        layerID: 1,
                        visible: true,
                        layerSection: { _enum: "layerSectionType", _value: "layerSectionContent" },
                        bounds: {
                            top: { _value: 0 },
                            left: { _value: 0 },
                            bottom: { _value: 8 },
                            right: { _value: 8 },
                        },
                    },
                ],
            },
        ]);
        const tree = await readActiveLayerTreeAsync();
        expect(tree?.info.name).toBe("fast.psd");
        expect(tree?.layers.map((l) => l.name)).toEqual(["from-multiget"]);
    });

    it("falls back to the DOM walk when multiGet returns an unusable result", async () => {
        (app as MutableApp).activeDocument = {
            // No id -> readLayersViaMultiGet returns null -> DOM-walk fallback.
            name: "fallback.psd",
            width: 10,
            height: 10,
            layers: [{ name: "bg", visible: true, bounds: { left: 0, top: 0, right: 4, bottom: 4 } }],
        };
        const tree = await readActiveLayerTreeAsync();
        expect(tree?.layers.map((l) => l.name)).toEqual(["bg"]);
    });
});
