// Reads the active document, adapts it to the Layer[] shape, and
// builds the Tags tab tree. Refresh paths:
//
//   1. On every PS notification bump (via `version`).
//   2. After a layer rename runs through this hook.
//   3. Polled as a fallback - some UXP builds never fire notification
//      callbacks, so the timer is the only way the panel learns about
//      external edits. Cadence adapts to visibility: ACTIVE_POLL_MS
//      while visible, IDLE_POLL_MS while hidden.
//
// All three paths fold into the same read + compare step. A fresh tree
// is pushed to state only when it differs structurally from the prior
// one, so polling does not tear down the user's open dropdowns and
// React.memo on `TagRow` keeps saving work.

import React from "react";

import { readActiveLayerTreeAsync } from "../api/active-document";
import { buildTagTreeReusing, type TagTreeNode } from "../lib/tag-tree";
import { renameLayer, type RenameResult } from "../api/layer-rename";
import { elementsEqual } from "../utils/arrays";

// Fallback poll cadence. Before we have proof that PS notifications fire
// (some UXP builds never call the listener), poll aggressively. Once a
// single `version` bump proves events work, relax to a rare safety net so
// an idle panel is not paying a full IPC tree walk every 1.5s forever.
const ACTIVE_POLL_MS = 1500;
const IDLE_POLL_MS = 4000;
const SAFETY_POLL_MS = 15000;
const HIDDEN_SAFETY_POLL_MS = 60000;

export interface UseTagTree {
    tree: TagTreeNode[];
    noDocument: boolean;
    lastError: string | null;
    rename: (layerPath: readonly string[], newName: string, id?: number) => Promise<void>;
    refresh: () => void;
}

export function useTagTree(version: number): UseTagTree {
    const [tree, setTree] = React.useState<TagTreeNode[]>([]);
    const [noDocument, setNoDocument] = React.useState(true);
    const [lastError, setLastError] = React.useState<string | null>(null);
    const [tick, setTick] = React.useState(0);
    // Derived, not state: `version` starts at 0 and bumps on every PS
    // notification, so `version > 0` is proof events fire - no setState in
    // an effect. The boolean is stable once true, so the poll effect below
    // re-runs only on the single false->true transition.
    const eventsConfirmed = version > 0;
    const treeRef = React.useRef<TagTreeNode[]>([]);
    const noDocRef = React.useRef<boolean>(true);
    const lastSyncAtRef = React.useRef<number>(0);
    // The read is now async (spec-048 multiGet), so guard the classic
    // stale-async hazards. `inFlightRef` stops a second read starting
    // before the current one resolves - on a deep PSD two overlapping
    // batchPlay walks would double the IPC load. `pendingRef` records that
    // a trigger (version bump / poll) arrived mid-flight so the loop does
    // exactly one more read afterwards rather than dropping the update.
    // `mountedRef` drops a resolved write after unmount.
    const inFlightRef = React.useRef<boolean>(false);
    const pendingRef = React.useRef<boolean>(false);
    const mountedRef = React.useRef<boolean>(true);
    React.useEffect(() => () => { mountedRef.current = false; }, []);

    const runLoop = React.useCallback(async () => {
        inFlightRef.current = true;
        try {
            do {
                pendingRef.current = false;
                if (typeof document !== "undefined" && document.hidden) break;
                // Stamp the time of the actual IPC read so the poll can skip a
                // tick when an event-driven sync already covered this interval.
                lastSyncAtRef.current = Date.now();
                const snap = await readTree(treeRef.current);
                if (!mountedRef.current) return;
                // buildTagTreeReusing preserves node refs for unchanged
                // subtrees, so a top-level element-wise compare suffices to
                // bail when nothing structural moved.
                if (
                    snap.noDocument === noDocRef.current
                    && elementsEqual(treeRef.current, snap.tree)
                ) continue;
                noDocRef.current = snap.noDocument;
                treeRef.current = snap.tree;
                setTree(snap.tree);
                setNoDocument(snap.noDocument);
                // pendingRef is set true by `syncOnce` from outside this
                // closure (a trigger that arrived mid-flight) and mountedRef
                // by the unmount cleanup; eslint cannot see those cross-
                // closure mutations and wrongly flags the condition.
                // eslint-disable-next-line @typescript-eslint/no-unnecessary-condition
            } while (pendingRef.current && mountedRef.current);
        } finally {
            inFlightRef.current = false;
        }
    }, []);

    const syncOnce = React.useCallback(() => {
        if (typeof document !== "undefined" && document.hidden) return;
        // A read is already running: record the request so the loop reads
        // once more when it finishes, instead of starting a second walk.
        if (inFlightRef.current) {
            pendingRef.current = true;
            return;
        }
        // Fire-and-forget: a transient read failure is ignored on purpose
        // (the next poll tick / version bump retries), so swallow the
        // rejection rather than leaving the promise floating.
        runLoop().catch(() => undefined);
    }, [runLoop]);

    React.useEffect(() => {
        syncOnce();
    }, [version, tick, syncOnce]);

    React.useEffect(() => {
        let id: ReturnType<typeof setInterval> | null = null;
        const pollIntervalMs = (hidden: boolean): number => {
            if (eventsConfirmed) return hidden ? HIDDEN_SAFETY_POLL_MS : SAFETY_POLL_MS;
            return hidden ? IDLE_POLL_MS : ACTIVE_POLL_MS;
        };
        const start = (): void => {
            const hidden = typeof document !== "undefined" && document.hidden;
            const interval = pollIntervalMs(hidden);
            id = setInterval(() => {
                // Skip the IPC walk when an event-driven (or prior) sync
                // already ran within this interval - no redundant walk right
                // after an edit, and none at all while events keep us fresh.
                if (Date.now() - lastSyncAtRef.current < interval) return;
                syncOnce();
            }, interval);
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
    }, [syncOnce, eventsConfirmed]);

    const refresh = React.useCallback(() => { setTick((t) => t + 1); }, []);

    const rename = React.useCallback(
        async (layerPath: readonly string[], newName: string, id?: number) => {
            setLastError(null);
            try {
                const result: RenameResult = await renameLayer(layerPath, newName, id);
                if (!result.ok) setLastError(result.reason ?? "rename failed");
            } catch (err) {
                setLastError(err instanceof Error ? err.message : "rename threw exception");
            } finally {
                refresh();
            }
        },
        [refresh],
    );

    return { tree, noDocument, lastError, rename, refresh };
}

async function readTree(
    prev: TagTreeNode[],
): Promise<{ tree: TagTreeNode[]; noDocument: boolean }> {
    const adapted = await readActiveLayerTreeAsync();
    if (adapted === null) return { tree: [], noDocument: true };
    return { tree: buildTagTreeReusing(adapted.layers, prev), noDocument: false };
}
