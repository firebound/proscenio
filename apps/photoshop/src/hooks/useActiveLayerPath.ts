// Tracks the layer chain of the currently selected PS layer, so the
// Debug / Validate / Tags surfaces can highlight the manifest row
// matching the artist's current selection.
//
// `version` is the monotonic counter from `useDocumentChanges`; we
// re-read on every bump rather than subscribing here so all watchers
// share the same debounced trigger.

import React from "react";

import { readActiveLayerPath } from "../api/ps-selection";
import { elementsEqual } from "../utils/arrays";
import { log } from "../utils/log";

const POLL_MS = 300;

export function useActiveLayerPath(version: number): readonly string[] | null {
    const [path, setPath] = React.useState<readonly string[] | null>(null);

    // Bails on identical chains so polling does not flood the log.
    const updatePath = React.useCallback((next: readonly string[] | null) => {
        setPath((prev) => {
            if (pathsEqual(prev, next)) return prev;
            log.debug("useActiveLayerPath", "changed", next);
            return next;
        });
    }, []);

    React.useEffect(() => {
        // updatePath returns the previous reference unchanged when the
        // path did not move, so React skips the re-render despite the
        // synchronous setState in the effect.
        // eslint-disable-next-line react-hooks/set-state-in-effect
        updatePath(readActiveLayerPath());
    }, [version, updatePath]);

    // Polling fallback: on UXP builds where
    // `action.addNotificationListener` returns void, no `select` events
    // fire, so polling is the only way to learn the artist clicked a
    // different layer. Skip when the panel is hidden (document.hidden).
    React.useEffect(() => {
        const id = setInterval(() => {
            if (typeof document !== "undefined" && document.hidden) return;
            updatePath(readActiveLayerPath());
        }, POLL_MS);
        return () => { clearInterval(id); };
    }, [updatePath]);

    return path;
}

function pathsEqual(a: readonly string[] | null, b: readonly string[] | null): boolean {
    if (a === b) return true;
    if (a === null || b === null) return false;
    return elementsEqual(a, b);
}
