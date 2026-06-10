// Manifest picker/reader. Drives uxp.storage's file picker with a fake file.

import { afterEach, describe, expect, it, vi } from "vitest";

import { storage } from "uxp";

import { readManifestFromPicker } from "../src/api/manifest-reader";

const lfs = storage.localFileSystem;

const validManifest = {
    format_version: 1,
    doc: "x.psd",
    size: [10, 10],
    pixels_per_unit: 100,
    layers: [
        {
            kind: "sprite",
            name: "blink",
            position: [0, 0],
            size: [10, 10],
            z_order: 0,
            frames: [{ index: 0, path: "images/blink/0.png" }],
        },
    ],
};

afterEach(() => {
    vi.restoreAllMocks();
});

function fakeFile(text: string, parent: unknown): unknown {
    return { read: async () => text, parent, nativePath: "/proj/x.json" };
}

describe("readManifestFromPicker", () => {
    it("returns cancelled when the picker is dismissed", async () => {
        vi.spyOn(lfs, "getFileForOpening").mockRejectedValue(new Error("cancel"));
        expect(await readManifestFromPicker()).toEqual({ kind: "cancelled" });
    });

    it("returns invalid for non-JSON content", async () => {
        vi.spyOn(lfs, "getFileForOpening").mockResolvedValue(
            fakeFile("{not json", { isFolder: true }) as never,
        );
        expect((await readManifestFromPicker()).kind).toBe("invalid");
    });

    it("returns invalid when the manifest fails schema validation", async () => {
        vi.spyOn(lfs, "getFileForOpening").mockResolvedValue(
            fakeFile(JSON.stringify({ format_version: 99 }), { isFolder: true }) as never,
        );
        expect((await readManifestFromPicker()).kind).toBe("invalid");
    });

    it("returns ok with the parsed manifest, file, and parent folder", async () => {
        const folder = { isFolder: true };
        vi.spyOn(lfs, "getFileForOpening").mockResolvedValue(
            fakeFile(JSON.stringify(validManifest), folder) as never,
        );
        const result = await readManifestFromPicker();
        expect(result.kind).toBe("ok");
        if (result.kind === "ok") {
            expect(result.picked.manifest).toEqual(validManifest);
            expect(result.picked.folder).toBe(folder);
        }
    });

    it("rebuilds the parent folder from nativePath when file.parent is absent", async () => {
        const parentFolder = { isFolder: true };
        vi.spyOn(lfs, "getFileForOpening").mockResolvedValue(
            fakeFile(JSON.stringify(validManifest), undefined) as never,
        );
        vi.spyOn(lfs, "getEntryWithUrl").mockResolvedValue(parentFolder as never);
        const result = await readManifestFromPicker();
        expect(result.kind).toBe("ok");
        if (result.kind === "ok") expect(result.picked.folder).toBe(parentFolder);
    });
});
