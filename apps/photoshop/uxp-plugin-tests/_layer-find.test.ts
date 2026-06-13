// Unit tests for the shared layer-tree walk. _layer-find imports only
// types from "photoshop" (erased at runtime), so it runs under plain
// vitest against duck-typed fakes - no host mock needed.

import { describe, expect, it } from "vitest";

import { findLayerById, findLayerByPath } from "../src/api/_layer-find";
import type { PsDocument, PsLayer } from "photoshop";

function layer(name: string, children?: PsLayer[]): PsLayer {
    return (children === undefined ? { name } : { name, layers: children }) as unknown as PsLayer;
}

function doc(layers: PsLayer[]): PsDocument {
    return { layers } as unknown as PsDocument;
}

describe("findLayerByPath", () => {
    it("returns null for an empty path", () => {
        expect(findLayerByPath(doc([layer("a")]), [])).toBeNull();
    });

    it("finds a top-level layer by name", () => {
        const target = layer("torso");
        expect(findLayerByPath(doc([layer("bg"), target]), ["torso"])).toBe(target);
    });

    it("walks into nested groups", () => {
        const hand = layer("hand");
        const arm = layer("arm", [hand]);
        expect(findLayerByPath(doc([arm]), ["arm", "hand"])).toBe(hand);
    });

    it("returns null when a path segment does not match", () => {
        const tree = doc([layer("arm", [layer("hand")])]);
        expect(findLayerByPath(tree, ["arm", "ghost"])).toBeNull();
    });

    it("returns null when descending past a leaf layer", () => {
        const tree = doc([layer("arm")]);
        expect(findLayerByPath(tree, ["arm", "hand"])).toBeNull();
    });

    it("does not crash when a matched leaf reports `.layers` as null", () => {
        // Regression: some UXP builds expose an art layer's `.layers` as
        // `null`, and the old `toArray` only guarded `undefined`, so
        // `Array.from(null)` threw "object null is not iterable" on every
        // rename + export write while the adapted tree still rendered.
        const leaf = { name: "eye.L", layers: null } as unknown as PsLayer;
        expect(findLayerByPath(doc([leaf]), ["eye.L"])).toBe(leaf);
    });

    it("does not crash when the document layer collection is null", () => {
        const tree = { layers: null } as unknown as PsDocument;
        expect(findLayerByPath(tree, ["eye.L"])).toBeNull();
    });

    it("does not crash when an intermediate group reports `.layers` as null", () => {
        const arm = { name: "arm", layers: null } as unknown as PsLayer;
        expect(findLayerByPath(doc([arm]), ["arm", "hand"])).toBeNull();
    });
});

describe("findLayerById", () => {
    const withId = (name: string, id: number, children?: PsLayer[]): PsLayer =>
        ({ name, id, ...(children === undefined ? {} : { layers: children }) }) as unknown as PsLayer;

    it("finds a top-level layer by id regardless of name", () => {
        const target = withId("eye.R", 99);
        expect(findLayerById(doc([withId("bg", 1), target]), 99)).toBe(target);
    });

    it("finds a nested layer by id even when its parent group was renamed", () => {
        const target = withId("eye.R", 99);
        // Parent group is "eyes" now, not the cached "Agrupar 1".
        const tree = doc([withId("eyes", 5, [target])]);
        expect(findLayerById(tree, 99)).toBe(target);
    });

    it("returns null when no layer carries the id", () => {
        expect(findLayerById(doc([withId("a", 1), withId("b", 2)]), 999)).toBeNull();
    });

    it("does not crash when a branch reports null children", () => {
        const tree = doc([{ name: "grp", id: 1, layers: null } as unknown as PsLayer]);
        expect(findLayerById(tree, 42)).toBeNull();
    });
});
