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

import { log } from "../util/log";

const WATCHED_EVENTS = [
    { event: "select" },
    { event: "make" },
    { event: "delete" },
    { event: "set" },
    { event: "open" },
    { event: "close" },
];

const DEBOUNCE_MS = 150;

type ListenerHandle = { remove(): void };

function isHandle(value: unknown): value is ListenerHandle {
    return (
        typeof value === "object"
        && value !== null
        && typeof (value as { remove?: unknown }).remove === "function"
    );
}

function isPromiseLike<T>(value: unknown): value is Promise<T> {
    return (
        typeof value === "object"
        && value !== null
        && typeof (value as { then?: unknown }).then === "function"
    );
}

export function useDocumentChanges(): number {
    const [version, setVersion] = React.useState(0);

    React.useEffect(() => {
        let cancelled = false;
        let listenerHandle: { remove(): void } | null = null;
        let pending: ReturnType<typeof setTimeout> | null = null;

        const fire = (): void => {
            pending = null;
            if (cancelled) return;
            log.debug("useDocumentChanges", "version bump");
            setVersion((v) => v + 1);
        };
        const bump = (event?: { event: string }): void => {
            log.trace("useDocumentChanges", "event", event?.event);
            if (pending !== null) clearTimeout(pending);
            pending = setTimeout(fire, DEBOUNCE_MS);
        };

        // UXP changed `addNotificationListener` over time. Older PS /
        // UXP builds return `void` (no teardown handle), the next
        // generation returns the handle synchronously, recent builds
        // return `Promise<handle>`. Probe the shape at runtime so the
        // hook works across versions without forcing a host bump.
        const adopt = (handle: unknown): void => {
            if (!isHandle(handle)) return;
            if (cancelled) handle.remove();
            else listenerHandle = handle;
        };
        try {
            const result = action.addNotificationListener(WATCHED_EVENTS, bump) as unknown;
            if (isPromiseLike<unknown>(result)) {
                result.then(adopt).catch((err) => {
                    log.warn("useDocumentChanges", "subscription rejected", err);
                });
            } else if (isHandle(result)) {
                listenerHandle = result;
            } else {
                log.debug("useDocumentChanges", "subscribed (no teardown handle)");
            }
        } catch (err) {
            log.warn("useDocumentChanges", "addNotificationListener threw", err);
        }

        return () => {
            cancelled = true;
            if (pending !== null) clearTimeout(pending);
            if (listenerHandle !== null) listenerHandle.remove();
        };
    }, []);

    return version;
}
