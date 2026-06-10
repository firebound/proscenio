// PNG writer IO core. Drives the host mock's app.documents.add (temp doc)
// plus fake source layers and folders.

import { afterEach, describe, expect, it, vi } from "vitest";

import { app } from "photoshop";

import { runWrites } from "../src/api/png-writer";
import type { PngWrite } from "../src/lib/planner";
import type { PsDocument } from "photoshop";
import type { UxpFolder } from "uxp";

function fakeWorkDoc(): {
    trim: ReturnType<typeof vi.fn>;
    saveAs: { png: ReturnType<typeof vi.fn> };
    closeWithoutSaving: ReturnType<typeof vi.fn>;
} {
    return {
        trim: vi.fn(async () => {}),
        saveAs: { png: vi.fn(async () => {}) },
        closeWithoutSaving: vi.fn(async () => {}),
    };
}

function write(layerPath: string[], outputPath: string, merge = false): PngWrite {
    return { layerPath, outputPath, merge };
}

afterEach(() => {
    vi.restoreAllMocks();
});

describe("runWrites", () => {
    it("skips a write whose source layer is missing", async () => {
        const doc = { width: 10, height: 10, layers: [] } as unknown as PsDocument;
        const folder = {} as unknown as UxpFolder;
        const results = await runWrites(doc, folder, [write(["ghost"], "ghost.png")]);
        expect(results[0]?.ok).toBe(false);
        expect(results[0]?.skippedReason).toContain("ghost");
    });

    it("writes a found layer to PNG and closes the temp doc", async () => {
        const layer = { name: "torso", duplicate: vi.fn(async () => ({ merge: vi.fn() })) };
        const doc = { width: 64, height: 32, layers: [layer] } as unknown as PsDocument;
        const workDoc = fakeWorkDoc();
        vi.spyOn(app.documents, "add").mockResolvedValue(workDoc as never);
        const folder = { createFile: vi.fn(async () => ({ name: "torso.png" })) } as unknown as UxpFolder;
        const results = await runWrites(doc, folder, [write(["torso"], "torso.png")]);
        expect(results[0]?.ok).toBe(true);
        expect(workDoc.saveAs.png).toHaveBeenCalledOnce();
        expect(workDoc.closeWithoutSaving).toHaveBeenCalledOnce();
    });

    it("flattens a [merge] group before saving", async () => {
        const dup = { merge: vi.fn(async () => {}) };
        const layer = { name: "arm", duplicate: vi.fn(async () => dup) };
        const doc = { width: 10, height: 10, layers: [layer] } as unknown as PsDocument;
        vi.spyOn(app.documents, "add").mockResolvedValue(fakeWorkDoc() as never);
        const folder = { createFile: vi.fn(async () => ({ name: "arm.png" })) } as unknown as UxpFolder;
        await runWrites(doc, folder, [write(["arm"], "arm.png", true)]);
        expect(dup.merge).toHaveBeenCalledOnce();
    });

    it("creates intermediate folders for a nested output path", async () => {
        const layer = { name: "torso", duplicate: vi.fn(async () => ({ merge: vi.fn() })) };
        const doc = { width: 10, height: 10, layers: [layer] } as unknown as PsDocument;
        vi.spyOn(app.documents, "add").mockResolvedValue(fakeWorkDoc() as never);
        const sub: Record<string, unknown> = {
            createFile: vi.fn(async () => ({ name: "torso.png" })),
            getEntry: vi.fn(),
        };
        sub.createFolder = vi.fn(async () => sub);
        const createFolder = vi.fn(async () => sub);
        const folder = { createFolder, createFile: sub.createFile } as unknown as UxpFolder;
        await runWrites(doc, folder, [write(["torso"], "images/body/torso.png")]);
        expect(createFolder).toHaveBeenCalled();
    });
});
