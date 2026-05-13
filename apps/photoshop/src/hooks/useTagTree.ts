// Reads the active document, adapts it to the Layer[] shape, and
// builds the Tags tab tree. Refresh paths:
//
//   1. On every PS notification bump (via `version`).
//   2. After a layer rename runs through this hook.
//   3. Polled every 1.5s as a fallback - some UXP builds never fire
//      notification callbacks, so the timer is the only way the
//      panel learns about external edits.
//
// All three paths fold into the same read + hash-compare step. A
// fresh tree is only pushed to state when the structural hash
// (rawName + visibility, depth-first) differs from the prior one.
// Identical snapshots short-circuit to a no-op so React.memo on
// `TagRow` actually saves work and the user's open dropdowns are
// not torn down by polling.

import React from "react";
import { app } from "photoshop";

import { adaptDocument } from "../adapters/photoshop-layer";
import { buildTagTree, type TagTreeNode } from "../domain/tag-tree";
import { renameLayer, type RenameResult } from "../io/layer-rename";

const POLL_MS = 1500;

export interface UseTagTree {
    tree: TagTreeNode[];
    noDocument: boolean;
    busy: boolean;
    lastError: string | null;
    rename: (layerPath: readonly string[], newName: string) => Promise<void>;
    refresh: () => void;
}

export function useTagTree(version: number): UseTagTree {
    const [tree, setTree] = React.useState<TagTreeNode[]>([]);
    const [noDocument, setNoDocument] = React.useState(true);
    const [busy, setBusy] = React.useState(false);
    const [lastError, setLastError] = React.useState<string | null>(null);
    const [tick, setTick] = React.useState(0);
    const lastHashRef = React.useRef<string>("__init__");

    const syncOnce = React.useCallback(() => {
        const snap = readTree();
        const hash = hashTree(snap.tree, snap.noDocument);
        if (hash === lastHashRef.current) return;
        lastHashRef.current = hash;
        setTree(snap.tree);
        setNoDocument(snap.noDocument);
    }, []);

    React.useEffect(() => {
        syncOnce();
    }, [version, tick, syncOnce]);

    React.useEffect(() => {
        const id = setInterval(syncOnce, POLL_MS);
        return () => clearInterval(id);
    }, [syncOnce]);

    const refresh = React.useCallback(() => setTick((t) => t + 1), []);

    const rename = React.useCallback(
        async (layerPath: readonly string[], newName: string) => {
            setBusy(true);
            setLastError(null);
            try {
                const result: RenameResult = await renameLayer(layerPath, newName);
                if (!result.ok) setLastError(result.reason ?? "rename failed");
            } finally {
                setBusy(false);
                refresh();
            }
        },
        [refresh],
    );

    return { tree, noDocument, busy, lastError, rename, refresh };
}

function readTree(): { tree: TagTreeNode[]; noDocument: boolean } {
    const doc = app.activeDocument;
    if (doc === null) return { tree: [], noDocument: true };
    const adapted = adaptDocument(doc);
    return { tree: buildTagTree(adapted.layers), noDocument: false };
}

function hashTree(nodes: TagTreeNode[], noDocument: boolean): string {
    if (noDocument) return "no-doc";
    const parts: string[] = [];
    walkHash(nodes, parts);
    return parts.join("|");
}

function walkHash(nodes: TagTreeNode[], out: string[]): void {
    for (const n of nodes) {
        out.push(n.rawName, n.visible ? "1" : "0");
        if (n.children.length > 0) {
            out.push("[");
            walkHash(n.children, out);
            out.push("]");
        }
    }
}
