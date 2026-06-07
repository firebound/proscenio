// Unit tests for the XMP tag mirror. Drives the host mock's XMPMeta to
// confirm the bag is stamped under the proscenio namespace, and that any
// failure degrades to a false return without throwing.

import { afterEach, describe, expect, it, vi } from "vitest";

import { xmp as uxpXmp } from "uxp";

import { PROSCENIO_XMP_NAMESPACE_URI, writeLayerTagsToXmp } from "../src/api/xmp";
import type { PsLayer } from "photoshop";
import type { TagBag } from "../src/lib/tag-parser";

const tags = { kind: "mesh", folder: "body" } as TagBag;

afterEach(() => {
    vi.restoreAllMocks();
});

describe("writeLayerTagsToXmp", () => {
    it("stamps the tag bag into the layer XMP and returns true", () => {
        const setProperty = vi.spyOn(uxpXmp.XMPMeta.prototype, "setProperty");
        const layer = { xmpMetadata: "" } as unknown as PsLayer;

        const ok = writeLayerTagsToXmp(layer, ["arm", "hand"], tags);

        expect(ok).toBe(true);
        expect(setProperty).toHaveBeenCalledOnce();
        const [namespace, key, value] = setProperty.mock.calls[0] as [string, string, string];
        expect(namespace).toBe(PROSCENIO_XMP_NAMESPACE_URI);
        expect(key).toBe("tag_arm__hand");
        expect(JSON.parse(value)).toMatchObject({ kind: "mesh", folder: "body" });
        expect((layer as unknown as { xmpMetadata: string }).xmpMetadata).toBe("<xmp/>");
    });

    it("returns false without throwing when the metadata read fails", () => {
        const layer = {
            get xmpMetadata(): string {
                throw new Error("no metadata");
            },
        } as unknown as PsLayer;
        expect(writeLayerTagsToXmp(layer, ["x"], tags)).toBe(false);
    });
});
