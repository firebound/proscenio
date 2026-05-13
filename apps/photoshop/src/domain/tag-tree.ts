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
