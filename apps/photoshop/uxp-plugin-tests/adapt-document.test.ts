// Unit tests for the Photoshop -> exporter Layer adapter. adapt-document
// imports only types from "photoshop" (erased at runtime), so it runs
// under plain vitest against duck-typed fakes - no host mock needed.

import { describe, expect, it } from "vitest";

import { adaptDocument, adaptLayer } from "../src/api/adapt-document";
import type { PsDocument, PsLayer } from "photoshop";

type RawBounds = { left: number; top: number; right: number; bottom: number };

function artLayer(name: string, bounds: RawBounds | null, visible = true): PsLayer {
    return { name, visible, bounds } as unknown as PsLayer;
}

function groupLayer(name: string, layers: PsLayer[], visible = true): PsLayer {
    return { name, visible, layers } as unknown as PsLayer;
}

function baseDoc(extra: Record<string, unknown>): PsDocument {
    return { name: "fixture.psd", width: 256, height: 128, layers: [], ...extra } as unknown as PsDocument;
}

describe("adaptLayer", () => {
    it("maps an art layer to translated bounds", () => {
        const layer = adaptLayer(artLayer("torso", { left: 10, top: 20, right: 40, bottom: 60 }));
        expect(layer).toEqual({
            kind: "art",
            name: "torso",
            visible: true,
            bounds: { x: 10, y: 20, w: 30, h: 40 },
        });
    });

    it("treats a layer with a .layers array as a group and adapts its children", () => {
        const layer = adaptLayer(
            groupLayer("arm", [artLayer("hand", { left: 0, top: 0, right: 5, bottom: 5 })]),
        );
        expect(layer.kind).toBe("set");
        if (layer.kind === "set") {
            expect(layer.layers).toHaveLength(1);
            expect(layer.layers[0]?.name).toBe("hand");
        }
    });

    it("nulls zero-area bounds", () => {
        const layer = adaptLayer(artLayer("flat", { left: 5, top: 5, right: 5, bottom: 9 }));
        if (layer.kind === "art") expect(layer.bounds).toBeNull();
    });

    it("nulls missing bounds", () => {
        const layer = adaptLayer(artLayer("blank", null));
        if (layer.kind === "art") expect(layer.bounds).toBeNull();
    });
});

describe("adaptDocument", () => {
    it("carries document info and adapts the layer list", () => {
        const doc = baseDoc({ layers: [artLayer("bg", { left: 0, top: 0, right: 10, bottom: 10 })] });
        const out = adaptDocument(doc);
        expect(out.info).toEqual({ name: "fixture.psd", width: 256, height: 128 });
        expect(out.layers).toHaveLength(1);
        expect(out.anchor).toBeUndefined();
    });

    it("extracts the first vertical + horizontal guide pair as the rounded anchor", () => {
        const doc = baseDoc({
            guides: [
                { direction: "horizontal", coordinate: 64.4 },
                { direction: "vertical", coordinate: 32.6 },
                { direction: "vertical", coordinate: 99 },
            ],
        });
        expect(adaptDocument(doc).anchor).toEqual([33, 64]);
    });

    it("omits the anchor when fewer than two guide directions exist", () => {
        const doc = baseDoc({ guides: [{ direction: "vertical", coordinate: 10 }] });
        expect(adaptDocument(doc).anchor).toBeUndefined();
    });

    it("treats a throwing guides getter as no anchor", () => {
        const doc = {
            name: "x.psd",
            width: 10,
            height: 10,
            layers: [],
            get guides(): never {
                throw new Error("guides unavailable");
            },
        } as unknown as PsDocument;
        expect(adaptDocument(doc).anchor).toBeUndefined();
    });
});
