// Reads the active document, adapts it to the Layer[] shape, and
// builds the Tags tab tree. Refresh paths:
//
//   1. On every PS notification bump (via `version`).
//   2. After a layer rename runs through this hook.
//   3. Polled as a fallback - some UXP builds never fire notification
//      callbacks, so the timer is the only way the panel learns about
//      external edits. The cadence adapts to document visibility:
//      ACTIVE_POLL_MS while the panel is visible, IDLE_POLL_MS while
//      hidden, since the polling has no work to do off-screen.
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
import { buildTagTreeReusing, type TagTreeNode } from "../domain/tag-tree";
import { renameLayer, type RenameResult } from "../io/layer-rename";
import { elementsEqual } from "../util/arrays";

const ACTIVE_POLL_MS = 1500;
const IDLE_POLL_MS = 4000;

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
    const treeRef = React.useRef<TagTreeNode[]>([]);
    const noDocRef = React.useRef<boolean>(true);

    const syncOnce = React.useCallback(() => {
        if (typeof document !== "undefined" && document.hidden === true) return;
        const snap = readTree(treeRef.current);
        // `buildTagTreeReusing` preserves node refs for unchanged
        // subtrees, so a top-level element-wise compare is enough
        // to bail when nothing structural moved - O(top-level
        // count) instead of walking the whole tree.
        if (
            snap.noDocument === noDocRef.current
            && elementsEqual(treeRef.current, snap.tree)
        ) return;
        noDocRef.current = snap.noDocument;
        treeRef.current = snap.tree;
        setTree(snap.tree);
        setNoDocument(snap.noDocument);
    }, []);

    React.useEffect(() => {
        syncOnce();
    }, [version, tick, syncOnce]);

    React.useEffect(() => {
        let id: ReturnType<typeof setInterval> | null = null;
        const start = (): void => {
            const hidden = typeof document !== "undefined" && document.hidden === true;
            const interval = hidden ? IDLE_POLL_MS : ACTIVE_POLL_MS;
            id = setInterval(syncOnce, interval);
        };
        const stop = (): void => {
            if (id !== null) {
                clearInterval(id);
                id = null;
            }
        };
        const onVisibility = (): void => {
            stop();
            start();
        };
        start();
        if (typeof document !== "undefined") {
            document.addEventListener("visibilitychange", onVisibility);
        }
        return () => {
            stop();
            if (typeof document !== "undefined") {
                document.removeEventListener("visibilitychange", onVisibility);
            }
        };
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

function readTree(prev: TagTreeNode[]): { tree: TagTreeNode[]; noDocument: boolean } {
    const doc = app.activeDocument;
    if (doc === null) return { tree: [], noDocument: true };
    const adapted = adaptDocument(doc);
    return { tree: buildTagTreeReusing(adapted.layers, prev), noDocument: false };
}
