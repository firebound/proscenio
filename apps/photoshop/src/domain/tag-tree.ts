// Tree shape the Tags tab renders. Pre-resolves the parsed display
// name + TagBag per node so the UI does not re-parse on every
// keystroke. Pure - no PS runtime touch.
//
// `buildTagTreeReusing` returns the prior node reference verbatim
// when nothing about a layer (rawName, visibility, parent chain) and
// its descendants has changed. That keeps `React.memo` happy: rows
// that did not change keep their `node` prop by reference, so the
// memo bail-out is a single pointer compare instead of a structural
// walk.

import type { Layer } from "./layer";
import { parseLayerName, type TagBag } from "./tag-parser";
import { elementsEqual } from "../util/arrays";

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
    const isGroup = layer.kind === "set";

    // Fast path: rawName + visibility + depth + parent chain all match.
    // Skip `parseLayerName` and reuse the prior tags/displayName.
    if (
        prev !== null
        && prev.rawName === layer.name
        && prev.visible === layer.visible
        && prev.isGroup === isGroup
        && prev.depth === depth
        && elementsEqual(prev.layerPath.slice(0, -1), parentLayerPath)
        && elementsEqual(prev.displayPath.slice(0, -1), parentDisplayPath)
    ) {
        if (!isGroup) return prev;
        const children = (layer as { layers: Layer[] }).layers.map((child, i) =>
            reuseOrBuild(child, prev.children[i] ?? null, prev.layerPath, prev.displayPath, depth + 1));
        if (elementsEqual(prev.children, children)) return prev;
        // Children changed; keep this node's own fields (rawName,
        // tags, displayName) but swap in the new children array.
        return {
            layerPath: prev.layerPath,
            displayPath: prev.displayPath,
            rawName: prev.rawName,
            displayName: prev.displayName,
            tags: prev.tags,
            isGroup: prev.isGroup,
            visible: prev.visible,
            depth: prev.depth,
            children,
        };
    }

    // Slow path: parse + build fresh node.
    const layerPath = [...parentLayerPath, layer.name];
    const parsed = parseLayerName(layer.name);
    const stable = parsed.displayName.length > 0 ? parsed.displayName : layer.name;
    const displayPath = [...parentDisplayPath, stable];

    const children: TagTreeNode[] = isGroup
        ? layer.layers.map((child, i) => reuseOrBuild(
            child,
            prev?.children[i] ?? null,
            layerPath,
            displayPath,
            depth + 1,
        ))
        : [];
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
