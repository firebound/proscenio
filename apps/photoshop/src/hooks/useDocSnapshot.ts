// Reads a snapshot of the current Photoshop active document into
// React state. Refreshes on demand (the panel exposes a button)
// because UXP does not auto-rerender on PS document changes.
//
// Wave 10.4 stopped here intentionally. Subscribing to PS notification
// events (`action.addNotificationListener` for `select`, `open`,
// `close`, ...) is parked for SPEC 011 when the tag inspector needs
// the live tree to drive its UI.

import React from "react";
import { app } from "photoshop";

export interface DocSnapshot {
    name: string;
    width: number;
    height: number;
}

export interface UseDocSnapshot {
    doc: DocSnapshot | null;
    refresh: () => Promise<void>;
}

export function useDocSnapshot(): UseDocSnapshot {
    const [doc, setDoc] = React.useState<DocSnapshot | null>(null);

    const refresh = React.useCallback(async () => {
        setDoc(readActiveDocument());
    }, []);

    React.useEffect(() => {
        let cancelled = false;
        Promise.resolve(readActiveDocument()).then((snap) => {
            if (!cancelled) setDoc(snap);
        });
        return () => {
            cancelled = true;
        };
    }, []);

    return { doc, refresh };
}

function readActiveDocument(): DocSnapshot | null {
    const d = app.activeDocument;
    if (d === null) return null;
    return { name: d.name, width: d.width, height: d.height };
}
