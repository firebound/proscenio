// Unit tests for the selection-bounds read. ps-selection-bounds imports
// { app } from "photoshop" at runtime, driven here through the host mock.

import { afterEach, describe, expect, it } from "vitest";

import { app } from "photoshop";

import { readSelectionCenter } from "../src/api/ps-selection-bounds";

type MutableApp = { activeDocument: unknown };

afterEach(() => {
    (app as MutableApp).activeDocument = null;
});

function withSelectionBounds(bounds: unknown): void {
    (app as MutableApp).activeDocument = { selection: { bounds } };
}

describe("readSelectionCenter", () => {
    it("returns null when no document is open", () => {
        (app as MutableApp).activeDocument = null;
        expect(readSelectionCenter()).toBeNull();
    });

    it("returns null when there is no active selection", () => {
        (app as MutableApp).activeDocument = { selection: {} };
        expect(readSelectionCenter()).toBeNull();
    });

    it("computes the rounded center of a numeric selection", () => {
        withSelectionBounds({ left: 10, top: 20, right: 30, bottom: 60 });
        expect(readSelectionCenter()).toEqual({
            x: 20,
            y: 40,
            bounds: { left: 10, top: 20, right: 30, bottom: 60 },
        });
    });

    it("reads PsUnitNumber bounds via _value", () => {
        withSelectionBounds({
            left: { _value: 0 },
            top: { _value: 0 },
            right: { _value: 10 },
            bottom: { _value: 4 },
        });
        expect(readSelectionCenter()?.x).toBe(5);
    });

    it("returns null for an inverted selection", () => {
        withSelectionBounds({ left: 30, top: 0, right: 10, bottom: 10 });
        expect(readSelectionCenter()).toBeNull();
    });

    it("returns null when a bound is non-numeric", () => {
        withSelectionBounds({ left: "x", top: 0, right: 10, bottom: 10 });
        expect(readSelectionCenter()).toBeNull();
    });
});
