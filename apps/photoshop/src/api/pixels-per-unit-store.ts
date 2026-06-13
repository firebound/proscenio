// Persists the exporter's pixels-per-unit across panel reloads in
// localStorage. A PSD import seeds this value from the imported
// manifest (see api/import-flow) so a re-export emits the imported PPU
// instead of whatever the numeric input last held - the 10x-scale
// waiver. The usePixelsPerUnit hook and the import flow both read and
// write through here. Mirrors api/folder-storage's localStorage owner.

import { DEFAULT_PIXELS_PER_UNIT } from "../lib/manifest";
import { log } from "../utils/log";

const KEY = "proscenio.pixelsPerUnit";

// Live subscribers (React hooks). A PSD import runs through the React-free
// import flow and calls `persistPixelsPerUnit`; without this notify, the
// open panel's numeric input + re-export kept the stale mount-time value
// until a manual reload (finding F-14). Persist now pushes the new value
// to every live hook.
type Listener = (value: number) => void;
const listeners = new Set<Listener>();

/** Subscribe to PPU changes written through `persistPixelsPerUnit`.
 *  Returns an unsubscribe function. */
export function subscribePixelsPerUnit(listener: Listener): () => void {
    listeners.add(listener);
    return () => { listeners.delete(listener); };
}

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
    // Isolate each listener: one throwing subscriber must not break the
    // notification chain for the rest (state would drift across components).
    for (const listener of listeners) {
        try {
            listener(normalised);
        } catch (err) {
            log.warn("pixels-per-unit", "subscriber threw; continuing", err);
        }
    }
    return normalised;
}

export { DEFAULT_PIXELS_PER_UNIT };
