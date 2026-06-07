// Unit tests for the active-document reads. active-document imports
// { app } from "photoshop" at runtime, so this drives the host mock
// (vitest.config.ts test.alias) by setting app.activeDocument.

import { afterEach, describe, expect, it } from "vitest";

import { app } from "photoshop";

import { readActiveLayerTree, readDocSnapshot } from "../src/api/active-document";

type MutableApp = { activeDocument: unknown };

afterEach(() => {
    (app as MutableApp).activeDocument = null;
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
