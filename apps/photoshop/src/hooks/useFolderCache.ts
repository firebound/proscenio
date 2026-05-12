// Manages the chosen output folder for the panel: restores the
// persisted folder on mount, exposes pick / clear actions. UXP-side
// persistence lives in `infrastructure`-flavoured `io/folder-storage`.

import React from "react";
import type { UxpFolder } from "uxp";

import { clearRememberedFolder, pickFolder, restoreFolder } from "../io/folder-storage";

export interface UseFolderCache {
    folder: UxpFolder | null;
    pick: () => Promise<void>;
    clear: () => void;
}

export function useFolderCache(): UseFolderCache {
    const [folder, setFolder] = React.useState<UxpFolder | null>(null);

    React.useEffect(() => {
        let cancelled = false;
        void restoreFolder().then((restored) => {
            if (!cancelled) setFolder(restored);
        });
        return () => {
            cancelled = true;
        };
    }, []);

    const pick = React.useCallback(async () => {
        const picked = await pickFolder();
        if (picked !== null) setFolder(picked);
    }, []);

    const clear = React.useCallback(() => {
        clearRememberedFolder();
        setFolder(null);
    }, []);

    return { folder, pick, clear };
}
