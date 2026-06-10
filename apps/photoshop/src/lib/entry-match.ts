// Does a manifest entry's source(s) include this layer path? An entry
// matches either by its primary `layerPath` (polygon / mesh, or the
// sprite_frame host group) or by any of its per-frame `framePaths`
// (present on sprite_frame entries only).

import { elementsEqual } from "../utils/arrays";

import type { EntryRef } from "./planner";

export function entryMatchesPath(
    ref: EntryRef,
    layerPath: readonly string[],
): boolean {
    if (elementsEqual(ref.layerPath, layerPath)) return true;
    return ref.framePaths?.some((p) => elementsEqual(p, layerPath)) ?? false;
}
