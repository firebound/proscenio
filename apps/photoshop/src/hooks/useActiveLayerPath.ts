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
import { elementsEqual } from "../util/arrays";
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
    // layer. Polling at 300ms catches selection changes cheaply. Skips
    // when the host hides the panel (document.hidden) so background
    // panels do not burn cycles.
    React.useEffect(() => {
        const id = setInterval(() => {
            if (typeof document !== "undefined" && document.hidden === true) return;
            updatePath(readActiveLayerPath());
        }, POLL_MS);
        return () => clearInterval(id);
    }, [updatePath]);

    return path;
}

function pathsEqual(a: readonly string[] | null, b: readonly string[] | null): boolean {
    if (a === b) return true;
    if (a === null || b === null) return false;
    return elementsEqual(a, b);
}
