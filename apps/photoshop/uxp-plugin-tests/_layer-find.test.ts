// Unit tests for the shared layer-tree walk. _layer-find imports only
// types from "photoshop" (erased at runtime), so it runs under plain
// vitest against duck-typed fakes - no host mock needed.

import { describe, expect, it } from "vitest";

import { findLayerByPath } from "../src/api/_layer-find";
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
});
