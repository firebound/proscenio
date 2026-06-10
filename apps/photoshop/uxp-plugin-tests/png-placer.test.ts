// PSD-side PNG placer. Drives the host mock's app.open with a fake source
// doc/layer.

import { afterEach, describe, expect, it, vi } from "vitest";

import { app } from "photoshop";

import { moveLayerIntoGroup, placePngAt } from "../src/api/png-placer";
import type { PsDocument, PsLayer } from "photoshop";
import type { UxpFile } from "uxp";

const pngFile = { name: "torso.png" } as unknown as UxpFile;
const targetDoc = {} as unknown as PsDocument;

function srcDocWith(layer: unknown): { layers: unknown[]; closeWithoutSaving: ReturnType<typeof vi.fn> } {
    return {
        layers: layer === null ? [] : [layer],
        closeWithoutSaving: vi.fn(async () => {}),
    };
}

afterEach(() => {
    vi.restoreAllMocks();
});

describe("placePngAt", () => {
    it("warns when the PNG has no layers", async () => {
        vi.spyOn(app, "open").mockResolvedValue(srcDocWith(null) as never);
        const result = await placePngAt(targetDoc, pngFile, 0, 0, 10, 10);
        expect(result.layer).toBeNull();
        expect(result.warning).toContain("no layers");
    });

    it("warns when bounds are unreadable", async () => {
        const layer = { bounds: { left: "x", top: 0, right: 10, bottom: 10 }, duplicate: vi.fn() };
        vi.spyOn(app, "open").mockResolvedValue(srcDocWith(layer) as never);
        const result = await placePngAt(targetDoc, pngFile, 0, 0, 10, 10);
        expect(result.layer).toBeNull();
        expect(result.warning).toContain("unreadable");
    });

    it("duplicates, translates, and closes the source document", async () => {
        const duped = { translate: vi.fn(async () => {}) };
        const srcLayer = {
            bounds: { left: 5, top: 5, right: 15, bottom: 15 },
            duplicate: vi.fn(async () => duped),
        };
        const srcDoc = srcDocWith(srcLayer);
        vi.spyOn(app, "open").mockResolvedValue(srcDoc as never);
        const result = await placePngAt(targetDoc, pngFile, 100, 200, 10, 10);
        expect(result.layer).toBe(duped);
        expect(srcLayer.duplicate).toHaveBeenCalledWith(targetDoc);
        expect(duped.translate).toHaveBeenCalledWith(95, 195);
        expect(srcDoc.closeWithoutSaving).toHaveBeenCalledOnce();
    });

    it("warns on a size mismatch but still places the layer", async () => {
        const duped = { translate: vi.fn(async () => {}) };
        const srcLayer = {
            bounds: { left: 0, top: 0, right: 50, bottom: 50 },
            duplicate: vi.fn(async () => duped),
        };
        vi.spyOn(app, "open").mockResolvedValue(srcDocWith(srcLayer) as never);
        const result = await placePngAt(targetDoc, pngFile, 0, 0, 10, 10);
        expect(result.layer).toBe(duped);
        expect(result.warning).toContain("differ from manifest");
    });
});

describe("moveLayerIntoGroup", () => {
    it("moves the layer to the end of the group", async () => {
        const move = vi.fn(async () => {});
        const layer = { move } as unknown as PsLayer;
        const group = {} as unknown as PsLayer;
        await moveLayerIntoGroup(layer, group);
        expect(move).toHaveBeenCalledWith(group, "placeAtEnd");
    });
});
