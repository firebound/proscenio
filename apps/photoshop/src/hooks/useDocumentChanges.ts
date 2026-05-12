// Subscribes to Photoshop notification events that mutate the layer
// tree or selection. Exposes a monotonically-increasing version number
// other hooks (`useDocSnapshot`, `useExportPreview`) depend on so they
// re-run automatically when the user edits the PSD.
//
// Events watched:
// - `select`  active layer changed
// - `make`    new layer / group created
// - `delete`  layer / group removed
// - `set`     layer property changed (rename, visibility toggle, ...)
// - `open`    document opened (switches the active doc)
// - `close`   document closed
//
// PS fires `set` aggressively (one per attribute mutation); a 150ms
// debounce keeps the downstream effects from thrashing while the user
// drags a value slider or types a layer name.

import React from "react";
import { action } from "photoshop";

const WATCHED_EVENTS = [
    { event: "select" },
    { event: "make" },
    { event: "delete" },
    { event: "set" },
    { event: "open" },
    { event: "close" },
];

const DEBOUNCE_MS = 150;

export function useDocumentChanges(): number {
    const [version, setVersion] = React.useState(0);

    React.useEffect(() => {
        let cancelled = false;
        let listenerHandle: { remove(): void } | null = null;
        let pending: ReturnType<typeof setTimeout> | null = null;

        const bump = (): void => {
            if (pending !== null) clearTimeout(pending);
            pending = setTimeout(() => {
                pending = null;
                if (!cancelled) setVersion((v) => v + 1);
            }, DEBOUNCE_MS);
        };

        void action
            .addNotificationListener(WATCHED_EVENTS, bump)
            .then((handle) => {
                if (cancelled) handle.remove();
                else listenerHandle = handle;
            })
            .catch(() => {
                // UXP build without notification support; degrade
                // gracefully - the manual Refresh buttons still work.
            });

        return () => {
            cancelled = true;
            if (pending !== null) clearTimeout(pending);
            if (listenerHandle !== null) listenerHandle.remove();
        };
    }, []);

    return version;
}
