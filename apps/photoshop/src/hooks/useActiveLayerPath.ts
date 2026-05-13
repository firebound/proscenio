// Tracks the layer chain of the currently selected PS layer. Combined
// with the planner's `entryRefs` it lets the Debug / Validate / Tags
// surfaces highlight the manifest row matching the artist's current
// selection ("reveal-output").
//
// The `version` argument is the monotonic counter from
// `useDocumentChanges` - bumped when PS fires a select / make /
// delete / set / open / close notification. We re-read on every bump
// rather than subscribing inside this hook so all watchers share the
// same debounced trigger.

import React from "react";

import { readActiveLayerPath } from "../io/ps-selection";
import { log } from "../util/log";

const POLL_MS = 300;

export function useActiveLayerPath(version: number): readonly string[] | null {
    const [path, setPath] = React.useState<readonly string[] | null>(null);

    // Centralised setter: bails on identical chains and only logs
    // when the path actually changes - avoids polling-induced log
    // floods at trace level.
    const updatePath = React.useCallback((next: readonly string[] | null) => {
        setPath((prev) => {
            if (pathsEqual(prev, next)) return prev;
            log.debug("useActiveLayerPath", "changed", next);
            return next;
        });
    }, []);

    // Read on every PS notification bump.
    React.useEffect(() => {
        updatePath(readActiveLayerPath());
    }, [version, updatePath]);

    // Polling fallback. On UXP builds where
    // `action.addNotificationListener` returns void, no `select` events
    // ever fire - we never learn that the artist clicked a different
    // layer. Polling at 300ms catches selection changes cheaply.
    React.useEffect(() => {
        const id = setInterval(() => {
            updatePath(readActiveLayerPath());
        }, POLL_MS);
        return () => clearInterval(id);
    }, [updatePath]);

    return path;
}

function pathsEqual(a: readonly string[] | null, b: readonly string[] | null): boolean {
    if (a === b) return true;
    if (a === null || b === null) return false;
    if (a.length !== b.length) return false;
    for (let i = 0; i < a.length; i++) {
        if (a[i] !== b[i]) return false;
    }
    return true;
}
