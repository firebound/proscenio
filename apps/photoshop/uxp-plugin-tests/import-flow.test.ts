// Unit tests for the import orchestrator. Drives the host mock's
// documents.add + open (via png-placer) and a fake folder tree to cover
// mesh stamping, the missing-PNG skip, sprite-group stamping, and the
// modal-failure path.

import { afterEach, describe, expect, it, vi } from "vitest";

import { app } from "photoshop";

import { runImport } from "../src/api/import-flow";
import type { Manifest } from "../src/lib/manifest";
import type { UxpFolder } from "uxp";

function meshManifest(): Manifest {
    return {
        format_version: 1,
        doc: "hero.psd",
        size: [64, 64],
        pixels_per_unit: 100,
        layers: [
            {
                kind: "mesh",
                name: "torso",
                path: "images/torso.png",
                position: [10, 20],
                size: [32, 32],
                z_order: 0,
            },
        ],
    } as unknown as Manifest;
}

function spriteManifest(): Manifest {
    return {
        format_version: 1,
        doc: "hero.psd",
        size: [64, 64],
        pixels_per_unit: 100,
        layers: [
            {
                kind: "sprite",
                name: "blink",
                position: [0, 0],
                size: [32, 32],
                z_order: 0,
                frames: [{ index: 0, path: "images/blink/0.png" }],
            },
        ],
    } as unknown as Manifest;
}

function folderResolving(file: unknown): UxpFolder {
    // Dotted names resolve to the leaf file; bare names resolve to a
    // nested folder, so any "images/.../leaf.png" depth walks cleanly.
    const makeFolder = (): Record<string, unknown> => ({
        isFolder: true,
        getEntry: vi.fn(async (name: string) => (name.includes(".") ? file : makeFolder())),
    });
    return makeFolder() as unknown as UxpFolder;
}

function stubDocAdd(): void {
    const doc = {
        createLayerGroup: vi.fn(async () => ({ delete: vi.fn(async () => {}) })),
    };
    vi.spyOn(app.documents, "add").mockResolvedValue(doc as never);
}

function stubSourceLayer(): void {
    const duped = { translate: vi.fn(async () => {}), move: vi.fn(async () => {}), name: "" };
    const srcLayer = {
        bounds: { left: 0, top: 0, right: 32, bottom: 32 },
        duplicate: vi.fn(async () => duped),
    };
    vi.spyOn(app, "open").mockResolvedValue({
        layers: [srcLayer],
        closeWithoutSaving: vi.fn(async () => {}),
    } as never);
}

afterEach(() => {
    vi.restoreAllMocks();
});

describe("runImport", () => {
    it("stamps a mesh entry and returns ok", async () => {
        stubDocAdd();
        stubSourceLayer();
        const result = await runImport(meshManifest(), folderResolving({ isFile: true, name: "torso.png" }));
        expect(result.kind).toBe("ok");
        expect(result.stamped).toBe(1);
        expect(result.skipped).toBe(0);
    });

    it("skips a mesh entry whose PNG is missing", async () => {
        stubDocAdd();
        stubSourceLayer();
        const folder = {
            getEntry: vi.fn(async () => {
                throw new Error("not found");
            }),
        } as unknown as UxpFolder;
        const result = await runImport(meshManifest(), folder);
        expect(result.kind).toBe("ok");
        expect(result.stamped).toBe(0);
        expect(result.skipped).toBe(1);
        expect(result.warnings?.[0]).toContain("missing PNG");
    });

    it("stamps a sprite entry's frames into a group", async () => {
        stubDocAdd();
        stubSourceLayer();
        const result = await runImport(spriteManifest(), folderResolving({ isFile: true, name: "0.png" }));
        expect(result.kind).toBe("ok");
        expect(result.stamped).toBe(1);
    });

    it("returns failed when the modal throws", async () => {
        vi.spyOn(app.documents, "add").mockRejectedValue(new Error("doc add failed"));
        const result = await runImport(meshManifest(), {} as unknown as UxpFolder);
        expect(result.kind).toBe("failed");
        expect(result.errors?.[0]).toContain("doc add failed");
    });
});
