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

function fakeWorkDoc(): Record<string, unknown> {
    return {
        trim: vi.fn(async () => {}),
        saveAs: { png: vi.fn(async () => {}) },
        closeWithoutSaving: vi.fn(async () => {}),
    };
}

// A folder that records every file write by name, so a test can read back
// the exact manifest JSON that landed on disk and assert its contents.
function recordingFolder(written: Record<string, string>): Record<string, unknown> {
    const makeFile = (name: string): Record<string, unknown> => ({
        name,
        write: vi.fn(async (content: string) => { written[name] = content; }),
    });
    const folder: Record<string, unknown> = {
        nativePath: "/out",
        createFile: vi.fn(async (name: string) => makeFile(name)),
        getEntry: vi.fn(),
    };
    folder.createFolder = vi.fn(async () => folder);
    return folder;
}

function meshLayer(name: string): Record<string, unknown> {
    return {
        name,
        visible: true,
        bounds: { left: 0, top: 0, right: 32, bottom: 32 },
        duplicate: vi.fn(async () => ({ merge: vi.fn() })),
    };
}

function rejectingLayer(name: string): Record<string, unknown> {
    return {
        name,
        visible: true,
        bounds: { left: 0, top: 0, right: 32, bottom: 32 },
        duplicate: vi.fn(async () => { throw new Error("duplicate rejected"); }),
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
        expect(result.entryCount).toBe(1);
    });

    it("writes a partial manifest with only the good entries when one layer's PNG fails", async () => {
        // Drives the real planner + writer + manifest serializer; the only
        // mock is the host PS API, and one layer's duplicate genuinely
        // rejects. The bad entry must be excluded from the manifest so it
        // never references a PNG that is not on disk.
        (app as MutableApp).activeDocument = {
            name: "hero.psd",
            width: 64,
            height: 64,
            layers: [meshLayer("good"), rejectingLayer("bad")],
        };
        vi.spyOn(app.documents, "add").mockResolvedValue(fakeWorkDoc() as never);
        const written: Record<string, string> = {};
        const folder = recordingFolder(written);

        const result = await runExport(opts, folder as unknown as UxpFolder);

        expect(result.kind).toBe("partial");
        expect(result.entryCount).toBe(1);
        expect(result.skippedEntryCount).toBe(1);
        expect(result.errors?.some((e) => e.includes("bad"))).toBe(true);

        // The manifest actually written to disk contains only "good".
        const manifestJson = written["hero.photoshop_exported.json"];
        expect(manifestJson).toBeDefined();
        const manifest = JSON.parse(manifestJson) as { layers: { name: string }[] };
        expect(manifest.layers).toHaveLength(1);
        expect(manifest.layers[0]?.name).toBe("good");
    });

    it("writes no manifest and returns failed when every layer's PNG fails", async () => {
        (app as MutableApp).activeDocument = {
            name: "hero.psd",
            width: 64,
            height: 64,
            layers: [rejectingLayer("bad")],
        };
        vi.spyOn(app.documents, "add").mockResolvedValue(fakeWorkDoc() as never);
        const written: Record<string, string> = {};
        const folder = recordingFolder(written);

        const result = await runExport(opts, folder as unknown as UxpFolder);

        expect(result.kind).toBe("failed");
        expect(result.errors?.some((e) => e.includes("bad"))).toBe(true);
        // Invariant: nothing written when no entry succeeded.
        expect(written["hero.photoshop_exported.json"]).toBeUndefined();
    });
});
