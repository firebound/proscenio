// Vitest host mock for the UXP "uxp" module, wired in through
// vitest.config.ts test.alias. Surface for the storage / xmp imports in
// the file-IO api modules; tests configure behavior with vi.spyOn.

import { vi } from "vitest";

export const storage = {
    localFileSystem: {
        getFolder: vi.fn(),
        getFileForOpening: vi.fn(),
        createSessionToken: vi.fn(),
        createPersistentToken: vi.fn(),
        getEntryForPersistentToken: vi.fn(),
        getEntryWithUrl: vi.fn(),
    },
    formats: { utf8: "utf8" },
};

class XMPMeta {
    raw: string;

    constructor(raw = "") {
        this.raw = raw;
    }

    setProperty(_namespace: string, _key: string, _value: string): void {}

    serialize(): string {
        return "<xmp/>";
    }

    static registerNamespace = vi.fn();
}

export const xmp = { XMPMeta };
