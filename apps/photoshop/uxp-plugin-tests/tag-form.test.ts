// Tests for the pure Tags advanced-fields model. Covers the draft <->
// TagBag mapping and the baseline diff, with emphasis on the value
// validation shared with the bracket-tag parser (invalid input must be
// left alone rather than written).

import { describe, expect, it } from "vitest";

import { computeChanges, formFromTags, formsEqual, type DetailForm } from "../src/lib/tag-form";
import type { TagBag } from "../src/lib/tag-parser";

const EMPTY: DetailForm = {
    folder: "",
    path: "",
    scale: "",
    originX: "",
    originY: "",
    originMarker: false,
    namePattern: "",
};

function form(over: Partial<DetailForm>): DetailForm {
    return { ...EMPTY, ...over };
}

describe("formFromTags", () => {
    it("maps an empty bag to the empty form", () => {
        expect(formFromTags({})).toEqual(EMPTY);
    });

    it("stringifies scale and splits origin into x / y", () => {
        const tags: TagBag = { scale: 1.5, origin: [12, -3] };
        const f = formFromTags(tags);
        expect(f.scale).toBe("1.5");
        expect(f.originX).toBe("12");
        expect(f.originY).toBe("-3");
    });

    it("carries string fields and the origin-marker flag", () => {
        const f = formFromTags({ folder: "body", path: "hero", originMarker: true, namePattern: "p*" });
        expect(f).toMatchObject({ folder: "body", path: "hero", originMarker: true, namePattern: "p*" });
    });
});

describe("formsEqual", () => {
    it("is true for identical forms", () => {
        expect(formsEqual(form({ folder: "a" }), form({ folder: "a" }))).toBe(true);
    });

    it("is false when any field differs", () => {
        expect(formsEqual(form({ scale: "1" }), form({ scale: "2" }))).toBe(false);
    });
});

describe("computeChanges", () => {
    it("returns no changes when the form matches the baseline", () => {
        expect(computeChanges(form({ folder: "body" }), form({ folder: "body" }))).toEqual({});
    });

    it("sets a newly-typed folder, trimming whitespace", () => {
        expect(computeChanges(form({ folder: "  body  " }), EMPTY)).toEqual({ folder: "body" });
    });

    it("sets a valid path", () => {
        expect(computeChanges(form({ path: "hero" }), EMPTY)).toEqual({ path: "hero" });
    });

    it("ignores a path with separators (parser rule reuse)", () => {
        expect(computeChanges(form({ path: "a/b" }), EMPTY)).toEqual({});
        expect(computeChanges(form({ path: ".." }), EMPTY)).toEqual({});
    });

    it("sets a valid scale as a number", () => {
        expect(computeChanges(form({ scale: "2" }), EMPTY)).toEqual({ scale: 2 });
    });

    it("ignores non-numeric or non-positive scale (parser rule reuse)", () => {
        expect(computeChanges(form({ scale: "1abc" }), EMPTY)).toEqual({});
        expect(computeChanges(form({ scale: "0" }), EMPTY)).toEqual({});
    });

    it("sets origin from the x / y pair", () => {
        expect(computeChanges(form({ originX: "1", originY: "2" }), EMPTY)).toEqual({ origin: [1, 2] });
    });

    it("ignores a non-numeric origin", () => {
        expect(computeChanges(form({ originX: "x", originY: "2" }), EMPTY)).toEqual({});
    });

    it("sets a name pattern only when it carries the * wildcard (parser rule reuse)", () => {
        expect(computeChanges(form({ namePattern: "arm_*" }), EMPTY)).toEqual({ namePattern: "arm_*" });
        expect(computeChanges(form({ namePattern: "literal" }), EMPTY)).toEqual({});
    });

    it("enables the origin marker", () => {
        expect(computeChanges(form({ originMarker: true }), EMPTY)).toEqual({ originMarker: true });
    });
});
