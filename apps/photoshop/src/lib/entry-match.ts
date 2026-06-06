// Pure predicate: does a manifest entry's source(s) include this layer
// path? Four UI / flow sites ask the same question - is the active or
// target layer the one a given `EntryRef` was emitted from? - so the
// comparison lives here once instead of being re-derived (twice with a
// local `samePath` clone) at each call site.
//
// An entry matches either by its primary `layerPath` (polygon / mesh,
// or the sprite_frame host group) or by any of its per-frame
// `framePaths` (present on sprite_frame entries only).

import { elementsEqual } from "../utils/arrays";

import type { EntryRef } from "./planner";

export function entryMatchesPath(
    ref: EntryRef,
    layerPath: readonly string[],
): boolean {
    if (elementsEqual(ref.layerPath, layerPath)) return true;
    return ref.framePaths?.some((p) => elementsEqual(p, layerPath)) ?? false;
}
