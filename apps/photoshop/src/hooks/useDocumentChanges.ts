// Subscribes to Photoshop notification events that mutate the layer
// tree or selection, exposing a monotonically-increasing version
// number other hooks watch so they re-run when the user edits the PSD.
//
// PS fires `set` aggressively (one per attribute mutation), so a 150ms
// debounce keeps downstream effects from thrashing while the user drags
// a value slider or types a layer name. The UXP subscription boundary
// lives in `api/ps-notifications`; this hook owns only debounce +
// version state.

import React from "react";

import { subscribeToEvents, type NotificationEvent } from "../api/ps-notifications";
import { log } from "../utils/log";

const WATCHED_EVENTS: NotificationEvent[] = [
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
        let pending: ReturnType<typeof setTimeout> | null = null;

        const fire = (): void => {
            pending = null;
            if (cancelled) return;
            log.debug("useDocumentChanges", "version bump");
            setVersion((v) => v + 1);
        };
        const bump = (event?: NotificationEvent): void => {
            log.trace("useDocumentChanges", "event", event?.event);
            if (pending !== null) clearTimeout(pending);
            pending = setTimeout(fire, DEBOUNCE_MS);
        };

        const unsubscribe = subscribeToEvents(WATCHED_EVENTS, bump);

        return () => {
            cancelled = true;
            if (pending !== null) clearTimeout(pending);
            unsubscribe();
        };
    }, []);

    return version;
}
