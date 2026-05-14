// Persists the polygon / sprite_frame filename templates across
// panel reloads via localStorage. Both the exporter and the debug
// preview read from this hook so a value tweaked in the exporter
// panel is reflected in the dry-run.
//
// Tokens recognised by the planner: `{name}` (sanitised manifest
// entry name) and either `{kind}` (polygon path template) or
// `{index}` (sprite_frame frame template). The `images/` prefix
// and any `[folder:...]` subfolder are added by the planner; the
// template only controls the file portion.

import React from "react";

const DEFAULT_POLYGON = "{name}.png";
const DEFAULT_FRAMES = "{name}/{index}.png";
const KEY_POLYGON = "proscenio.template.polygon";
const KEY_FRAMES = "proscenio.template.frames";

function load(key: string, fallback: string): string {
    try {
        const v = window.localStorage.getItem(key);
        return v === null || v === "" ? fallback : v;
    } catch {
        return fallback;
    }
}

function save(key: string, value: string): void {
    try {
        window.localStorage.setItem(key, value);
    } catch {
        // localStorage not available (UXP variants, tests) - keep
        // in-memory state only.
    }
}

export interface UseFilenameTemplate {
    polygonTemplate: string;
    framesTemplate: string;
    setPolygonTemplate: (value: string) => void;
    setFramesTemplate: (value: string) => void;
    reset: () => void;
    defaults: { polygon: string; frames: string };
}

export function useFilenameTemplate(): UseFilenameTemplate {
    const [polygonTemplate, setPolygonState] = React.useState(() => load(KEY_POLYGON, DEFAULT_POLYGON));
    const [framesTemplate, setFramesState] = React.useState(() => load(KEY_FRAMES, DEFAULT_FRAMES));

    const setPolygonTemplate = React.useCallback((value: string) => {
        const normalised = value === "" ? DEFAULT_POLYGON : value;
        save(KEY_POLYGON, normalised);
        setPolygonState(normalised);
    }, []);

    const setFramesTemplate = React.useCallback((value: string) => {
        const normalised = value === "" ? DEFAULT_FRAMES : value;
        save(KEY_FRAMES, normalised);
        setFramesState(normalised);
    }, []);

    const reset = React.useCallback(() => {
        save(KEY_POLYGON, DEFAULT_POLYGON);
        save(KEY_FRAMES, DEFAULT_FRAMES);
        setPolygonState(DEFAULT_POLYGON);
        setFramesState(DEFAULT_FRAMES);
    }, []);

    return {
        polygonTemplate,
        framesTemplate,
        setPolygonTemplate,
        setFramesTemplate,
        reset,
        defaults: { polygon: DEFAULT_POLYGON, frames: DEFAULT_FRAMES },
    };
}
