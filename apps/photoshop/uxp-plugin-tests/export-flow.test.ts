// Export orchestrator. The runExport happy path (modal -> PNG writes ->
// manifest) is wired through the host mock.

import { afterEach, describe, expect, it, vi } from "vitest";

import { app } from "photoshop";

import { previewExport, runExport } from "../src/api/export-flow";
import type { UxpFolder } from "uxp";

type MutableApp = { activeDocument: unknown };

const opts = { skipHidden: true, pixelsPerUnit: 100 };

function artLayer(name: string): Record<string, unknown> {
    return { name, visible: true, bounds: { left: 0, top: 0, right: 32, bottom: 32 } };
}

function fakeFolder(): Record<string, unknown> {
    return {
        nativePath: "/out",
        createFile: vi.fn(async () => ({ name: "f", write: vi.fn(async () => {}) })),
        createFolder: vi.fn(async () => fakeFolder()),
        getEntry: vi.fn(),
    };
}

afterEach(() => {
    (app as MutableApp).activeDocument = null;
    vi.restoreAllMocks();
});

describe("previewExport", () => {
    it("reports no-document when none is open", () => {
        (app as MutableApp).activeDocument = null;
        expect(previewExport(opts)).toEqual({
            kind: "no-document",
            errors: ["No document is open."],
        });
    });

    it("returns an ok preview with a manifest for a simple document", () => {
        (app as MutableApp).activeDocument = {
            name: "hero.psd",
            width: 64,
            height: 64,
            layers: [artLayer("square")],
        };
        const preview = previewExport(opts);
        expect(preview.kind).toBe("ok");
        expect(preview.manifest).toBeDefined();
    });
});

describe("runExport", () => {
    it("reports no-document when none is open", async () => {
        (app as MutableApp).activeDocument = null;
        const folder = {} as unknown as UxpFolder;
        expect(await runExport(opts, folder)).toEqual({
            kind: "no-document",
            errors: ["No document is open."],
        });
    });

    it("writes the PNGs and manifest, returning ok", async () => {
        const layer = {
            name: "square",
            visible: true,
            bounds: { left: 0, top: 0, right: 32, bottom: 32 },
            duplicate: vi.fn(async () => ({ merge: vi.fn() })),
        };
        (app as MutableApp).activeDocument = {
            name: "hero.psd",
            width: 64,
            height: 64,
            layers: [layer],
        };
        const workDoc = {
            trim: vi.fn(async () => {}),
            saveAs: { png: vi.fn(async () => {}) },
            closeWithoutSaving: vi.fn(async () => {}),
        };
        vi.spyOn(app.documents, "add").mockResolvedValue(workDoc as never);
        const result = await runExport(opts, fakeFolder() as unknown as UxpFolder);
        expect(result.kind).toBe("ok");
        expect(result.manifestFile).toBe("hero.photoshop_exported.json");
    });
});
