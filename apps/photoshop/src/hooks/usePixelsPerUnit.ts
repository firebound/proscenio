// Persists the manifest's pixels_per_unit across panel reloads via
// localStorage. The exporter sets the value via a numeric input;
// downstream tools (Blender, Godot) read it from the manifest to
// convert PSD pixel coordinates into engine units.

import React from "react";

const DEFAULT_PPU = 100;
const KEY = "proscenio.pixelsPerUnit";

function load(): number {
    try {
        const raw = window.localStorage.getItem(KEY);
        if (raw === null || raw === "") return DEFAULT_PPU;
        const parsed = Number.parseFloat(raw);
        return Number.isFinite(parsed) && parsed > 0 ? parsed : DEFAULT_PPU;
    } catch {
        return DEFAULT_PPU;
    }
}

function save(value: number): void {
    try {
        window.localStorage.setItem(KEY, String(value));
    } catch {
        // localStorage unavailable; in-memory only.
    }
}

export interface UsePixelsPerUnit {
    pixelsPerUnit: number;
    setPixelsPerUnit: (value: number) => void;
    reset: () => void;
    defaultValue: number;
}

export function usePixelsPerUnit(): UsePixelsPerUnit {
    const [pixelsPerUnit, setState] = React.useState<number>(load);

    const setPixelsPerUnit = React.useCallback((value: number) => {
        const normalised = Number.isFinite(value) && value > 0 ? value : DEFAULT_PPU;
        save(normalised);
        setState(normalised);
    }, []);

    const reset = React.useCallback(() => {
        save(DEFAULT_PPU);
        setState(DEFAULT_PPU);
    }, []);

    return { pixelsPerUnit, setPixelsPerUnit, reset, defaultValue: DEFAULT_PPU };
}
