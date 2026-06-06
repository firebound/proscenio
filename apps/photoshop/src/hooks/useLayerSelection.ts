// Click-to-select seam for the panel sections. Sections route their
// "reveal this layer in PS" intent through here instead of importing
// `api/ps-selection` directly, keeping the layering
// `panels -> hooks -> api`. Fire-and-forget: selection is a UI
// affordance, so failures are logged inside the api layer, not awaited.

import React from "react";

import { selectLayerByPath } from "../api/ps-selection";

export function useLayerSelection(): (layerPath: readonly string[]) => void {
    return React.useCallback((layerPath: readonly string[]) => {
        void selectLayerByPath(layerPath);
    }, []);
}
