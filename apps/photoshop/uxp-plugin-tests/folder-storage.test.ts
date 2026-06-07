// Unit tests for folder persistence. folder-storage reads/writes a token
// in localStorage and resolves it through uxp.storage. localStorage is
// stubbed for determinism; the storage calls are driven via vi.spyOn.

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { storage } from "uxp";

import { clearRememberedFolder, pickFolder, restoreFolder } from "../src/api/folder-storage";

const lfs = storage.localFileSystem;
const KEY = "proscenio.exporter.folderToken";

beforeEach(() => {
    const store = new Map<string, string>();
    vi.stubGlobal("localStorage", {
        getItem: (k: string) => store.get(k) ?? null,
        setItem: (k: string, v: string) => {
            store.set(k, v);
        },
        removeItem: (k: string) => {
            store.delete(k);
        },
    });
});

afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
});

describe("restoreFolder", () => {
    it("returns null when no token is stored", async () => {
        expect(await restoreFolder()).toBeNull();
    });

    it("resolves a stored token to a folder", async () => {
        localStorage.setItem(KEY, "tok-1");
        const folder = { isFolder: true };
        vi.spyOn(lfs, "getEntryForPersistentToken").mockResolvedValue(folder as never);
        expect(await restoreFolder()).toBe(folder);
    });

    it("clears a stale token and returns null when resolution rejects", async () => {
        localStorage.setItem(KEY, "tok-stale");
        vi.spyOn(lfs, "getEntryForPersistentToken").mockRejectedValue(new Error("gone"));
        expect(await restoreFolder()).toBeNull();
        expect(localStorage.getItem(KEY)).toBeNull();
    });

    it("returns null when the resolved entry is not a folder", async () => {
        localStorage.setItem(KEY, "tok-file");
        vi.spyOn(lfs, "getEntryForPersistentToken").mockResolvedValue({ isFolder: false } as never);
        expect(await restoreFolder()).toBeNull();
    });
});

describe("pickFolder", () => {
    it("picks a folder, persists its token, and returns it", async () => {
        const folder = { isFolder: true };
        vi.spyOn(lfs, "getFolder").mockResolvedValue(folder as never);
        vi.spyOn(lfs, "createPersistentToken").mockResolvedValue("tok-new" as never);
        expect(await pickFolder()).toBe(folder);
        expect(localStorage.getItem(KEY)).toBe("tok-new");
    });

    it("returns null when the picker is cancelled", async () => {
        vi.spyOn(lfs, "getFolder").mockRejectedValue(new Error("cancelled"));
        expect(await pickFolder()).toBeNull();
    });
});

describe("clearRememberedFolder", () => {
    it("removes the stored token", () => {
        localStorage.setItem(KEY, "tok");
        clearRememberedFolder();
        expect(localStorage.getItem(KEY)).toBeNull();
    });
});
