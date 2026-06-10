// Reads a snapshot of the active Photoshop document into React state,
// refreshed on demand because UXP does not auto-rerender on PS
// document changes. Live PS-event-driven refresh is handled separately
// by `useDocumentChanges`.

import React from "react";

import { readDocSnapshot, type DocSnapshot } from "../api/active-document";

export type { DocSnapshot } from "../api/active-document";

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
