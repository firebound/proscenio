// Tree shape the Tags tab renders. Hangs off the adapted Layer[] but
// pre-resolves the parsed display name + TagBag per node so the UI
// does not re-parse on every keystroke. Pure - no PS runtime touch.

import type { Layer } from "./layer";
import { parseLayerName, type TagBag } from "./tag-parser";

export interface TagTreeNode {
    /** Names from the document root down to this node, inclusive. */
    layerPath: string[];
    /** Same chain as `layerPath` but using stripped (tag-free) display
     *  names. Used as a stable key for UI state (collapsed / expanded
     *  rows) so editing a tag does not collapse the row whose ID would
     *  otherwise have shifted with its raw name. */
    displayPath: string[];
    /** Raw layer name as it appears in PS (with brackets). */
    rawName: string;
    /** Stripped name produced by `parseLayerName`. */
    displayName: string;
    tags: TagBag;
    /** `true` for LayerSets (`PsLayer` with `.layers`). */
    isGroup: boolean;
    visible: boolean;
    /** Depth in the tree, 0 for top-level layers. */
    depth: number;
    children: TagTreeNode[];
}

export function buildTagTree(layers: Layer[]): TagTreeNode[] {
    return layers.map((layer) => toNode(layer, [], [], 0));
}

/** Builds the tree while reusing previous node references when nothing
 *  about a node (rawName, visibility, parent chain) and its descendants
 *  has changed. Keeps `React.memo` happy: rows that did not change keep
 *  their `node` prop by reference, so the memo bail-out is a single
 *  pointer compare instead of a structural walk. */
export function buildTagTreeReusing(
    layers: Layer[],
    prev: TagTreeNode[] | null,
): TagTreeNode[] {
    return layers.map((layer, i) => reuseOrBuild(layer, prev?.[i] ?? null, [], [], 0));
}

function reuseOrBuild(
    layer: Layer,
    prev: TagTreeNode | null,
    parentLayerPath: string[],
    parentDisplayPath: string[],
    depth: number,
): TagTreeNode {
    const layerPath = [...parentLayerPath, layer.name];
    const parsed = parseLayerName(layer.name);
    const stable = parsed.displayName.length > 0 ? parsed.displayName : layer.name;
    const displayPath = [...parentDisplayPath, stable];
    const isGroup = layer.kind === "set";

    const children: TagTreeNode[] = isGroup
        ? layer.layers.map((child, i) => reuseOrBuild(
            child,
            prev?.children[i] ?? null,
            layerPath,
            displayPath,
            depth + 1,
        ))
        : [];

    if (
        prev !== null
        && prev.rawName === layer.name
        && prev.visible === layer.visible
        && prev.isGroup === isGroup
        && prev.depth === depth
        && stringArraysEqual(prev.layerPath, layerPath)
        && stringArraysEqual(prev.displayPath, displayPath)
        && childrenRefEqual(prev.children, children)
    ) {
        return prev;
    }
    return {
        layerPath,
        displayPath,
        rawName: layer.name,
        displayName: parsed.displayName,
        tags: parsed.tags,
        isGroup,
        visible: layer.visible,
        depth,
        children,
    };
}

function elementsEqual<T>(a: readonly T[], b: readonly T[]): boolean {
    if (a === b) return true;
    if (a.length !== b.length) return false;
    for (let i = 0; i < a.length; i++) {
        if (a[i] !== b[i]) return false;
    }
    return true;
}

const stringArraysEqual = elementsEqual<string>;
const childrenRefEqual = elementsEqual<TagTreeNode>;

function toNode(
    layer: Layer,
    parentLayerPath: string[],
    parentDisplayPath: string[],
    depth: number,
): TagTreeNode {
    const layerPath = [...parentLayerPath, layer.name];
    const parsed = parseLayerName(layer.name);
    const stable = parsed.displayName.length > 0 ? parsed.displayName : layer.name;
    const displayPath = [...parentDisplayPath, stable];
    const isGroup = layer.kind === "set";
    return {
        layerPath,
        displayPath,
        rawName: layer.name,
        displayName: parsed.displayName,
        tags: parsed.tags,
        isGroup,
        visible: layer.visible,
        depth,
        children: isGroup
            ? layer.layers.map((child) => toNode(child, layerPath, displayPath, depth + 1))
            : [],
    };
}

/** Flattens the tree depth-first for virtualised / sequential render. */
export function flattenTagTree(nodes: TagTreeNode[]): TagTreeNode[] {
    const out: TagTreeNode[] = [];
    for (const node of nodes) {
        out.push(node);
        if (node.children.length > 0) out.push(...flattenTagTree(node.children));
    }
    return out;
}
