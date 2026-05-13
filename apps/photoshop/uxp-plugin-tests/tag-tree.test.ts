// Coverage for the Tags-tab tree shape. Pure - exercises the
// Layer[] -> TagTreeNode[] adapter only; no PS runtime.

import { describe, expect, it } from "vitest";

import type { ArtLayer, Layer, LayerSet } from "../src/domain/layer";
import { buildTagTree, flattenTagTree } from "../src/domain/tag-tree";

function art(name: string, visible = true): ArtLayer {
    return { kind: "art", name, visible, bounds: { x: 0, y: 0, w: 10, h: 10 } };
}

function set(name: string, layers: Layer[], visible = true): LayerSet {
    return { kind: "set", name, visible, layers };
}

describe("buildTagTree", () => {
    it("parses tags on leaf layers", () => {
        const tree = buildTagTree([art("torso [ignore]")]);
        expect(tree[0]).toMatchObject({
            displayName: "torso",
            tags: { ignore: true },
            isGroup: false,
            depth: 0,
            children: [],
        });
        expect(tree[0].layerPath).toEqual(["torso [ignore]"]);
    });

    it("recurses into groups, advancing depth + path", () => {
        const layers: Layer[] = [
            set("body [merge]", [art("torso"), art("head")]),
        ];
        const tree = buildTagTree(layers);
        expect(tree[0].isGroup).toBe(true);
        expect(tree[0].tags.merge).toBe(true);
        expect(tree[0].children).toHaveLength(2);
        expect(tree[0].children[0].depth).toBe(1);
        expect(tree[0].children[0].layerPath).toEqual(["body [merge]", "torso"]);
    });

    it("propagates visibility", () => {
        const tree = buildTagTree([art("hidden", false)]);
        expect(tree[0].visible).toBe(false);
    });
});

describe("flattenTagTree", () => {
    it("emits nodes depth-first", () => {
        const layers: Layer[] = [
            set("body", [art("torso"), set("head", [art("hair")])]),
            art("ground"),
        ];
        const flat = flattenTagTree(buildTagTree(layers));
        expect(flat.map((n) => n.rawName)).toEqual([
            "body",
            "torso",
            "head",
            "hair",
            "ground",
        ]);
    });
});
