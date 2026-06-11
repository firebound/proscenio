// Tests for the pure Tags advanced-fields model. Covers the draft <->
// TagBag mapping and the baseline diff, with emphasis on the value
// validation shared with the bracket-tag parser (invalid input must be
// left alone rather than written) and on clearing a set field - the diff
// carries cleared keys in `clear` so the writer can delete the tag.

import { describe, expect, it } from "vitest";

import { computeChanges, formFromTags, formsEqual, type DetailForm } from "../src/lib/tag-form";
import { applyTagChanges } from "../src/lib/tag-writer";
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

describe("computeChanges sets", () => {
    it("returns empty set and clear when the form matches the baseline", () => {
        expect(computeChanges(form({ folder: "body" }), form({ folder: "body" }))).toEqual({
            set: {},
            clear: [],
        });
    });

    it("sets a newly-typed folder, trimming whitespace", () => {
        expect(computeChanges(form({ folder: "  body  " }), EMPTY)).toEqual({
            set: { folder: "body" },
            clear: [],
        });
    });

    it("sets a valid path", () => {
        expect(computeChanges(form({ path: "hero" }), EMPTY)).toEqual({ set: { path: "hero" }, clear: [] });
    });

    it("ignores a path with separators (parser rule reuse)", () => {
        expect(computeChanges(form({ path: "a/b" }), EMPTY)).toEqual({ set: {}, clear: [] });
        expect(computeChanges(form({ path: ".." }), EMPTY)).toEqual({ set: {}, clear: [] });
    });

    it("sets a valid scale as a number", () => {
        expect(computeChanges(form({ scale: "2" }), EMPTY)).toEqual({ set: { scale: 2 }, clear: [] });
    });

    it("ignores non-numeric or non-positive scale (parser rule reuse)", () => {
        expect(computeChanges(form({ scale: "1abc" }), EMPTY)).toEqual({ set: {}, clear: [] });
        expect(computeChanges(form({ scale: "0" }), EMPTY)).toEqual({ set: {}, clear: [] });
    });

    it("sets origin from the x / y pair", () => {
        expect(computeChanges(form({ originX: "1", originY: "2" }), EMPTY)).toEqual({
            set: { origin: [1, 2] },
            clear: [],
        });
    });

    it("ignores a non-numeric origin", () => {
        expect(computeChanges(form({ originX: "x", originY: "2" }), EMPTY)).toEqual({ set: {}, clear: [] });
    });

    it("sets a name pattern only when it carries the * wildcard (parser rule reuse)", () => {
        expect(computeChanges(form({ namePattern: "arm_*" }), EMPTY)).toEqual({
            set: { namePattern: "arm_*" },
            clear: [],
        });
        expect(computeChanges(form({ namePattern: "literal" }), EMPTY)).toEqual({ set: {}, clear: [] });
    });

    it("enables the origin marker", () => {
        expect(computeChanges(form({ originMarker: true }), EMPTY)).toEqual({
            set: { originMarker: true },
            clear: [],
        });
    });
});

describe("computeChanges clears", () => {
    it("clears a folder emptied against a set baseline", () => {
        expect(computeChanges(EMPTY, form({ folder: "body" }))).toEqual({ set: {}, clear: ["folder"] });
    });

    it("clears a path emptied against a set baseline", () => {
        expect(computeChanges(EMPTY, form({ path: "hero" }))).toEqual({ set: {}, clear: ["path"] });
    });

    it("clears a scale emptied against a set baseline", () => {
        expect(computeChanges(EMPTY, form({ scale: "2" }))).toEqual({ set: {}, clear: ["scale"] });
    });

    it("clears an origin emptied against a set baseline", () => {
        expect(computeChanges(EMPTY, form({ originX: "1", originY: "2" }))).toEqual({
            set: {},
            clear: ["origin"],
        });
    });

    it("clears a name pattern emptied against a set baseline", () => {
        expect(computeChanges(EMPTY, form({ namePattern: "arm_*" }))).toEqual({
            set: {},
            clear: ["namePattern"],
        });
    });

    it("clears the origin marker when unchecked against a set baseline", () => {
        expect(computeChanges(EMPTY, form({ originMarker: true }))).toEqual({
            set: {},
            clear: ["originMarker"],
        });
    });
});

describe("computeChanges round-trip through the writer", () => {
    it("removes the bracket from the layer name when a field is cleared", () => {
        const baseline = formFromTags({ folder: "body" });
        const changes = computeChanges(EMPTY, baseline);
        const name = applyTagChanges("hero", { folder: "body" }, changes);
        expect(name).toBe("hero");
        expect(name).not.toContain("[folder");
    });

    it("still writes the bracket when a field is set", () => {
        const changes = computeChanges(form({ folder: "body" }), EMPTY);
        expect(applyTagChanges("hero", {}, changes)).toBe("hero [folder:body]");
    });
});
