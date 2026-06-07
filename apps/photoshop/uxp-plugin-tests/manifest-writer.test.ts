// Unit tests for the manifest JSON writer. manifest-writer imports only
// a type from "uxp" (erased at runtime); it operates on the folder it is
// handed, so a fake folder/file pair drives it - no host mock needed.

import { describe, expect, it, vi } from "vitest";

import { writeManifest } from "../src/api/manifest-writer";
import type { Manifest } from "../src/lib/manifest";
import type { UxpFolder } from "uxp";

function fakeManifest(): Manifest {
    return {
        format_version: 1,
        doc: "hero.psd",
        size: [256, 128],
        pixels_per_unit: 100,
        layers: [],
    };
}

describe("writeManifest", () => {
    it("creates the file with overwrite and writes two-space-indented JSON", async () => {
        const write = vi.fn(async () => {});
        const createFile = vi.fn(async () => ({ write }));
        const folder = { createFile } as unknown as UxpFolder;
        const manifest = fakeManifest();

        await writeManifest(folder, manifest, "manifest.json");

        expect(createFile).toHaveBeenCalledWith("manifest.json", { overwrite: true });
        expect(write).toHaveBeenCalledOnce();
        const body = write.mock.calls[0]?.[0] as string;
        expect(JSON.parse(body)).toEqual(manifest);
        expect(body).toContain('\n  "doc"'); // two-space indent
    });
});
