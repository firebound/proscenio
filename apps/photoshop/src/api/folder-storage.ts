// Folder persistence across plugin reloads.
//
// UXP's `storage.localFileSystem.createPersistentToken` serialises a
// folder reference to an opaque string that we stash in localStorage.
// On the next plugin session, `getEntryForPersistentToken` resolves it
// back without prompting the user.
//
// If the user moves or deletes the folder between sessions, the
// resolution call rejects; we treat that as "no folder" and let the
// panel show the picker again.

import { storage } from "uxp";
import type { UxpFolder } from "uxp";

const STORAGE_KEY = "proscenio.exporter.folderToken";

export async function restoreFolder(): Promise<UxpFolder | null> {
    const token = readToken();
    if (token === null) return null;
    try {
        const entry = await storage.localFileSystem.getEntryForPersistentToken(token);
        if (!entry.isFolder) return null;
        return entry as UxpFolder;
    } catch {
        // Stale token (folder moved / deleted); clear it.
        clearToken();
        return null;
    }
}

export async function pickFolder(): Promise<UxpFolder | null> {
    try {
        const folder = await storage.localFileSystem.getFolder();
        const token = await storage.localFileSystem.createPersistentToken(folder);
        writeToken(token);
        return folder;
    } catch {
        return null;
    }
}

export function clearRememberedFolder(): void {
    clearToken();
}

function readToken(): string | null {
    try {
        return localStorage.getItem(STORAGE_KEY);
    } catch {
        return null;
    }
}

function writeToken(token: string): void {
    try {
        localStorage.setItem(STORAGE_KEY, token);
    } catch {
        // localStorage unavailable in this UXP build; the folder still
        // works for this session, just not the next one.
    }
}

function clearToken(): void {
    try {
        localStorage.removeItem(STORAGE_KEY);
    } catch {
        // ignore
    }
}
