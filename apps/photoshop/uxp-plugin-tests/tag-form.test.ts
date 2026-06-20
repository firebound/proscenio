// Tests for the pure Tags advanced-fields model. Covers the draft <->
// TagBag mapping and the baseline diff, with emphasis on the value
// validation shared with the bracket-tag parser (invalid input must be
// left alone rather than written) and on clearing a set field - the diff
// carries cleared keys in `clear` so the writer can delete the tag.

import { describe, expect, it } from "vitest";

import {
    computeChanges,
    detailFormErrors,
    formFromTags,
    formsEqual,
    type DetailForm,
} from "../src/lib/tag-form";
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

describe("detailFormErrors surfaces rejected input", () => {
    it("reports no errors for an empty form", () => {
        expect(detailFormErrors(EMPTY)).toEqual({});
    });

    it("reports no errors for a fully valid form", () => {
        const f = form({ path: "hero", scale: "1.5", originX: "1", originY: "2", namePattern: "p*" });
        expect(detailFormErrors(f)).toEqual({});
    });

    it("flags a path with separators (the value the parser silently drops)", () => {
        expect(detailFormErrors(form({ path: "a/b" })).path).toBeDefined();
        expect(detailFormErrors(form({ path: ".." })).path).toBeDefined();
    });

    it("flags a non-numeric or non-positive scale", () => {
        expect(detailFormErrors(form({ scale: "1abc" })).scale).toBeDefined();
        expect(detailFormErrors(form({ scale: "0" })).scale).toBeDefined();
    });

    it("flags a half-filled origin pair", () => {
        expect(detailFormErrors(form({ originX: "1" })).origin).toBeDefined();
        expect(detailFormErrors(form({ originY: "2" })).origin).toBeDefined();
    });

    it("flags a non-numeric origin", () => {
        expect(detailFormErrors(form({ originX: "x", originY: "2" })).origin).toBeDefined();
    });

    it("flags a partly-numeric origin like 1abc (strict parse, not parseFloat)", () => {
        expect(detailFormErrors(form({ originX: "1abc", originY: "2" })).origin).toBeDefined();
        expect(detailFormErrors(form({ originX: "1", originY: "2px" })).origin).toBeDefined();
    });

    it("flags a name pattern missing the * wildcard", () => {
        expect(detailFormErrors(form({ namePattern: "literal" })).namePattern).toBeDefined();
    });

    it("does not flag a valid name pattern, scale, path, or origin", () => {
        expect(detailFormErrors(form({ namePattern: "arm_*" }))).toEqual({});
        expect(detailFormErrors(form({ scale: "0.5" }))).toEqual({});
        expect(detailFormErrors(form({ path: "hero-01" }))).toEqual({});
        expect(detailFormErrors(form({ originX: "0", originY: "0" }))).toEqual({});
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
