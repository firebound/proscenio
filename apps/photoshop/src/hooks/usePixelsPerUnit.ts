// Persists the manifest's pixels_per_unit across panel reloads via
// localStorage. The exporter sets the value via a numeric input; a PSD
// import seeds it from the imported manifest. Downstream tools (Blender,
// Godot) read it from the manifest to convert PSD pixel coordinates into
// engine units. The localStorage owner lives in api/pixels-per-unit-store
// so the React-free import flow can seed the same key.

import React from "react";

import {
    DEFAULT_PIXELS_PER_UNIT,
    loadPixelsPerUnit,
    persistPixelsPerUnit,
    subscribePixelsPerUnit,
} from "../api/pixels-per-unit-store";

export interface UsePixelsPerUnit {
    pixelsPerUnit: number;
    setPixelsPerUnit: (value: number) => void;
    reset: () => void;
    defaultValue: number;
}

export function usePixelsPerUnit(): UsePixelsPerUnit {
    const [pixelsPerUnit, setState] = React.useState<number>(loadPixelsPerUnit);

    // A PSD import seeds the PPU through the React-free import flow; subscribe
    // so the live input + re-export pick up the imported value immediately
    // instead of staying on the stale mount-time read until a reload (F-14).
    React.useEffect(() => subscribePixelsPerUnit(setState), []);

    const setPixelsPerUnit = React.useCallback((value: number) => {
        setState(persistPixelsPerUnit(value));
    }, []);

    const reset = React.useCallback(() => {
        setState(persistPixelsPerUnit(DEFAULT_PIXELS_PER_UNIT));
    }, []);

    return { pixelsPerUnit, setPixelsPerUnit, reset, defaultValue: DEFAULT_PIXELS_PER_UNIT };
}
