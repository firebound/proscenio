// Coverage for the Tags-tab tree shape. Pure - exercises the
// Layer[] -> TagTreeNode[] adapter only; no PS runtime.

import { describe, expect, it } from "vitest";

import type { ArtLayer, Layer, LayerSet } from "../src/lib/layer";
import { buildTagTreeReusing, tagNodeIdentity, type TagTreeNode } from "../src/lib/tag-tree";

function art(name: string, visible = true): ArtLayer {
    return { kind: "art", name, visible, bounds: { x: 0, y: 0, w: 10, h: 10 } };
}

function set(name: string, layers: Layer[], visible = true): LayerSet {
    return { kind: "set", name, visible, layers };
}

function build(layers: Layer[]): TagTreeNode[] {
    return buildTagTreeReusing(layers, null);
}

describe("tagNodeIdentity", () => {
    it("uses the layer id when present", () => {
        expect(tagNodeIdentity({ id: 7, displayPath: ["body", "arm"] })).toBe("id:7");
    });

    it("falls back to the display path when there is no id", () => {
        expect(tagNodeIdentity({ displayPath: ["body", "arm"] })).toBe('path:["body","arm"]');
    });

    it("distinguishes two same-named siblings by their distinct ids", () => {
        const a = tagNodeIdentity({ id: 1, displayPath: ["dup"] });
        const b = tagNodeIdentity({ id: 2, displayPath: ["dup"] });
        expect(a).not.toBe(b);
    });

    it("does not collide two hierarchies that share a slash-joined path", () => {
        // Without JSON encoding, both join("/") to "a/b/c".
        const a = tagNodeIdentity({ displayPath: ["a/b", "c"] });
        const b = tagNodeIdentity({ displayPath: ["a", "b/c"] });
        expect(a).not.toBe(b);
    });
});

describe("buildTagTreeReusing - fresh build", () => {
    it("parses tags on leaf layers", () => {
        const tree = build([art("torso [ignore]")]);
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
        const tree = build(layers);
        expect(tree[0].isGroup).toBe(true);
        expect(tree[0].tags.merge).toBe(true);
        expect(tree[0].children).toHaveLength(2);
        expect(tree[0].children[0].depth).toBe(1);
        expect(tree[0].children[0].layerPath).toEqual(["body [merge]", "torso"]);
    });

    it("propagates visibility", () => {
        const tree = build([art("hidden", false)]);
        expect(tree[0].visible).toBe(false);
    });

    it("carries the layer id onto the node", () => {
        const tree = build([{ kind: "art", name: "torso", visible: true, id: 42, bounds: null }]);
        expect(tree[0].id).toBe(42);
    });

    it("preserves the id across a rename so the React key stays stable", () => {
        // The remount-on-rename bug: a tag edit renames the layer, which
        // changed the old layerPath-based key and tore the row down. The
        // id survives the rename, so a key built from it does not change.
        const before: Layer[] = [{ kind: "art", name: "torso", visible: true, id: 7, bounds: null }];
        const first = build(before);
        const after: Layer[] = [{ kind: "art", name: "torso [ignore]", visible: true, id: 7, bounds: null }];
        const second = buildTagTreeReusing(after, first);
        expect(second[0].id).toBe(7);
        expect(second[0].id).toBe(first[0].id);
        expect(second[0].tags.ignore).toBe(true);
    });
});

describe("buildTagTreeReusing - reuse", () => {
    it("returns the same node reference when nothing changed", () => {
        const layers: Layer[] = [art("torso"), art("head")];
        const first = build(layers);
        const second = buildTagTreeReusing(layers, first);
        expect(second[0]).toBe(first[0]);
        expect(second[1]).toBe(first[1]);
    });

    it("returns the same group reference when its subtree is intact", () => {
        const layers: Layer[] = [
            set("body", [art("torso"), art("head")]),
        ];
        const first = build(layers);
        const second = buildTagTreeReusing(layers, first);
        expect(second[0]).toBe(first[0]);
        expect(second[0].children[0]).toBe(first[0].children[0]);
    });

    it("rebuilds only the changed branch", () => {
        const first = build([
            set("body", [art("torso"), art("head")]),
            art("ground"),
        ]);
        const second = buildTagTreeReusing(
            [
                set("body", [art("torso [ignore]"), art("head")]),
                art("ground"),
            ],
            first,
        );
        // ground stayed identical
        expect(second[1]).toBe(first[1]);
        // body group needs a new wrapper (one child changed)...
        expect(second[0]).not.toBe(first[0]);
        // ...but the unchanged sibling head keeps its reference.
        expect(second[0].children[1]).toBe(first[0].children[1]);
        // and the renamed child got fresh tags.
        expect(second[0].children[0].tags.ignore).toBe(true);
    });
});
