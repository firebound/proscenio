// Persists the exporter's pixels-per-unit across panel reloads in
// localStorage. A PSD import seeds this value from the imported
// manifest (see api/import-flow) so a re-export emits the imported PPU
// instead of whatever the numeric input last held - the 10x-scale
// waiver. The usePixelsPerUnit hook and the import flow both read and
// write through here. Mirrors api/folder-storage's localStorage owner.

import { DEFAULT_PIXELS_PER_UNIT } from "../lib/manifest";

const KEY = "proscenio.pixelsPerUnit";

function normalise(value: number): number {
    return Number.isFinite(value) && value > 0 ? value : DEFAULT_PIXELS_PER_UNIT;
}

export function loadPixelsPerUnit(): number {
    try {
        const raw = globalThis.localStorage.getItem(KEY);
        if (raw === null || raw === "") return DEFAULT_PIXELS_PER_UNIT;
        return normalise(Number.parseFloat(raw));
    } catch {
        return DEFAULT_PIXELS_PER_UNIT;
    }
}

// Returns the normalised value actually stored so callers can mirror
// it into React state without re-deriving the guard.
export function persistPixelsPerUnit(value: number): number {
    const normalised = normalise(value);
    try {
        globalThis.localStorage.setItem(KEY, String(normalised));
    } catch {
        // localStorage unavailable; in-memory only.
    }
    return normalised;
}

export { DEFAULT_PIXELS_PER_UNIT };
