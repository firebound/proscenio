// Regression coverage for the `TagRow` React.memo comparator. Pure -
// exercises `tagRowEqual` only; no React render.
//
// Locks the spec 048 fix: the comparator must skip a re-render
// (return true) whenever a row's own data is unchanged, even across a
// fresh props object. Re-renders are only triggered by this row's own
// node/selection/collapse data. Notably there is no per-row `busy`
// flag anymore - one rename used to flip a shared `busy` boolean and
// force every row to re-render twice.

import { describe, expect, it } from "vitest";

import type { TagBag } from "../src/lib/tag-parser";
import type { TagTreeNode } from "../src/lib/tag-tree";
import { tagRowEqual, type TagRowProps } from "../src/panels/sections/tags/Row";

function node(overrides: Partial<TagTreeNode> = {}): TagTreeNode {
    return {
        id: 1,
        layerPath: ["torso"],
        displayPath: ["torso"],
        rawName: "torso",
        displayName: "torso",
        tags: {} as TagBag,
        isGroup: false,
        visible: true,
        depth: 0,
        children: [],
        ...overrides,
    };
}

function props(overrides: Partial<TagRowProps> = {}): TagRowProps {
    return {
        node: node(),
        selected: false,
        collapsed: false,
        onRename: () => undefined,
        onToggleCollapse: () => undefined,
        ...overrides,
    };
}

describe("tagRowEqual", () => {
    it("skips re-render when the same node ref and callbacks are reused", () => {
        const shared = props();
        const next: TagRowProps = { ...shared };
        expect(tagRowEqual(shared, next)).toBe(true);
    });

    it("skips re-render when a fresh node carries identical row data", () => {
        const onRename = (): void => undefined;
        const onToggleCollapse = (): void => undefined;
        const prev = props({ onRename, onToggleCollapse });
        // New node object, same fields - the structural path must match.
        const next = props({ node: node(), onRename, onToggleCollapse });
        expect(tagRowEqual(prev, next)).toBe(true);
    });

    it("re-renders when this row becomes selected", () => {
        const onRename = (): void => undefined;
        const onToggleCollapse = (): void => undefined;
        const prev = props({ onRename, onToggleCollapse });
        const next = props({ selected: true, onRename, onToggleCollapse });
        expect(tagRowEqual(prev, next)).toBe(false);
    });

    it("re-renders when the row's own tags change", () => {
        const onRename = (): void => undefined;
        const onToggleCollapse = (): void => undefined;
        const prev = props({ onRename, onToggleCollapse });
        const next = props({
            node: node({ tags: { ignore: true } as TagBag }),
            onRename,
            onToggleCollapse,
        });
        expect(tagRowEqual(prev, next)).toBe(false);
    });

    it("re-renders when the rename callback identity changes", () => {
        const onToggleCollapse = (): void => undefined;
        const prev = props({ onRename: () => undefined, onToggleCollapse });
        const next = props({ onRename: () => undefined, onToggleCollapse });
        expect(tagRowEqual(prev, next)).toBe(false);
    });
});
