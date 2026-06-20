// Unit tests for the document color-profile guard. The classification is the
// real logic (which named profiles warn); readDocColorProfile is the thin DOM
// read, exercised against the shapes a live document actually produces -
// including the builds that omit the property or return the "None" marker.

import { describe, expect, it } from "vitest";

import type { PsDocument } from "photoshop";

import { classifyColorProfile, readDocColorProfile } from "../src/api/doc-color-profile";

describe("classifyColorProfile", () => {
    it("treats the standard sRGB profile as sRGB", () => {
        expect(classifyColorProfile("sRGB IEC61966-2.1")).toEqual({
            kind: "srgb",
            profile: "sRGB IEC61966-2.1",
        });
    });

    it("flags Adobe RGB (1998) as non-sRGB", () => {
        expect(classifyColorProfile("Adobe RGB (1998)")).toEqual({
            kind: "non-srgb",
            profile: "Adobe RGB (1998)",
        });
    });

    it("flags other wide-gamut profiles as non-sRGB", () => {
        expect(classifyColorProfile("Display P3").kind).toBe("non-srgb");
        expect(classifyColorProfile("ProPhoto RGB").kind).toBe("non-srgb");
    });

    it("treats the UXP 'None' marker as unknown, not a warning", () => {
        // UXP returns the literal "None" for an un-color-managed document; the
        // working space governs export so we must not warn.
        expect(classifyColorProfile("None")).toEqual({ kind: "unknown" });
        expect(classifyColorProfile("none")).toEqual({ kind: "unknown" });
    });

    it("treats empty / missing values as unknown", () => {
        expect(classifyColorProfile("")).toEqual({ kind: "unknown" });
        expect(classifyColorProfile("   ")).toEqual({ kind: "unknown" });
        expect(classifyColorProfile(null)).toEqual({ kind: "unknown" });
        expect(classifyColorProfile(undefined)).toEqual({ kind: "unknown" });
    });

    it("tolerates surrounding whitespace on a real name", () => {
        expect(classifyColorProfile("  sRGB IEC61966-2.1  ")).toEqual({
            kind: "srgb",
            profile: "sRGB IEC61966-2.1",
        });
    });
});

describe("readDocColorProfile", () => {
    const docWith = (colorProfileName: unknown): PsDocument =>
        ({ colorProfileName }) as unknown as PsDocument;

    it("classifies the document's assigned profile", () => {
        expect(readDocColorProfile(docWith("Adobe RGB (1998)")).kind).toBe("non-srgb");
        expect(readDocColorProfile(docWith("sRGB IEC61966-2.1")).kind).toBe("srgb");
    });

    it("returns unknown for an un-color-managed document", () => {
        expect(readDocColorProfile(docWith("None"))).toEqual({ kind: "unknown" });
    });

    it("returns unknown when the build omits colorProfileName", () => {
        expect(readDocColorProfile({} as unknown as PsDocument)).toEqual({ kind: "unknown" });
    });

    it("returns unknown when the property is not a string", () => {
        expect(readDocColorProfile(docWith(42))).toEqual({ kind: "unknown" });
    });
});
