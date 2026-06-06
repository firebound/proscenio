// PS notification subscription wrapper. Keeps the UXP boundary in
// `api/`: hooks ask for "tell me when the document changes" and get a
// plain teardown function back, without touching `action` or knowing
// how `addNotificationListener` drifts across builds.
//
// UXP changed `addNotificationListener` over time. Older PS / UXP
// builds return `void` (no teardown handle), the next generation
// returns the handle synchronously, recent builds return
// `Promise<handle>`. We probe the shape at runtime so callers work
// across versions without forcing a host bump.

import { action } from "photoshop";

import { log } from "../utils/log";

export interface NotificationEvent {
    event: string;
}

interface ListenerHandle {
    remove(): void;
}

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

/** Subscribe to PS notification events. Returns a teardown function
 *  that is safe to call even if the underlying handle never resolved
 *  (the cancel flag swallows a late-arriving Promise<handle>). */
export function subscribeToEvents(
    events: readonly NotificationEvent[],
    callback: (event?: NotificationEvent) => void,
): () => void {
    let cancelled = false;
    let handle: ListenerHandle | null = null;

    const adopt = (h: unknown): void => {
        if (!isHandle(h)) return;
        if (cancelled) h.remove();
        else handle = h;
    };

    try {
        // `addNotificationListener` is typed as a union of three
        // possible return shapes; the union is wider than what any
        // single Photoshop build returns, so the runtime probe is
        // what actually picks the shape.
        const result = action.addNotificationListener(events, callback);
        if (isPromiseLike<unknown>(result)) {
            result.then(adopt).catch((err: unknown) => {
                log.warn("ps-notifications", "subscription rejected", err);
            });
        } else if (isHandle(result)) {
            handle = result;
        } else {
            log.debug("ps-notifications", "subscribed (no teardown handle)");
        }
    } catch (err) {
        log.warn("ps-notifications", "addNotificationListener threw", err);
    }

    return () => {
        cancelled = true;
        if (handle !== null) handle.remove();
    };
}
