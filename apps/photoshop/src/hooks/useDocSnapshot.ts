// Reads a snapshot of the current Photoshop active document into
// React state. Refreshes on demand (the panel exposes a button)
// because UXP does not auto-rerender on PS document changes.
//
// The read funnels through `api/active-document`; live PS-event
// driven refresh is handled separately by `useDocumentChanges`, which
// bumps a version other hooks watch.

import React from "react";

import { readDocSnapshot, type DocSnapshot } from "../api/active-document";

export type { DocSnapshot };

export interface UseDocSnapshot {
    doc: DocSnapshot | null;
    refresh: () => Promise<void>;
}

export function useDocSnapshot(): UseDocSnapshot {
    const [doc, setDoc] = React.useState<DocSnapshot | null>(null);

    const refresh = React.useCallback((): Promise<void> => {
        setDoc(readDocSnapshot());
        return Promise.resolve();
    }, []);

    React.useEffect(() => {
        let cancelled = false;
        void Promise.resolve(readDocSnapshot()).then((snap) => {
            if (!cancelled) setDoc(snap);
        });
        return () => {
            cancelled = true;
        };
    }, []);

    return { doc, refresh };
}
