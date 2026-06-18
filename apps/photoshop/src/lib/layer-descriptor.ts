// Flat-descriptor -> nested Layer tree rebuild for the spec-048 batchPlay
// multiGet read path.
//
// A `action.batchPlay` multiGet over the whole layer stack (`count: -1`)
// returns a FLAT array of layer descriptors; group structure is encoded by
// a per-descriptor `layerSection` marker rather than by nesting. This module
// folds that flat array back into the nested `Layer[]` tree the exporter and
// the tag UI consume.
//
// Two responsibilities are kept deliberately separate:
//
//   - `parseDescriptor` is the thin, SWAPPABLE field mapper: it reads one raw
//     descriptor's fields (name / visible / id / bounds / section) into a
//     typed `ParsedEntry`. The exact key names and the section-marker field
//     vary across UXP / PS builds and will be confirmed against a real PSD in
//     a live session, so this is the only function that should need editing
//     when the live descriptor differs from the EXPECTED shape below.
//
//   - `rebuildLayerTree` is the pure fold: it consumes parsed entries and
//     builds the tree. This is the logic under test and should not need to
//     change when the field names are confirmed.
//
// This module is pure data transform - no Photoshop / UXP APIs - so it is
// fully unit-testable under plain vitest. It is intentionally NOT wired into
// adapt-document.ts yet; the wiring and the live descriptor validation happen
// later on the main thread.

import type { Layer, LayerBounds } from "./layer";

// A single raw multiGet descriptor. Loose by design: the real shape is only
// confirmable against a live PSD, so the mapper validates fields defensively.
export type RawDescriptor = unknown;

// Photoshop's `layerSection` marker, normalised to a small internal enum:
//   - "start"   opens a group (LayerSet);
//   - "end"     closes a group (a hidden divider layer);
//   - "content" a normal art layer (leaf).
export type LayerSectionKind = "start" | "end" | "content";

// One parsed descriptor: the section marker plus the fields a Layer needs.
// `bounds` follows the same semantics as adapt-document's `toBounds`
// (null when the rectangle has zero or negative area). End dividers carry a
// `name` / `visible` too, but the fold discards everything but `section` for
// them, so the extra fields are harmless.
export interface ParsedEntry {
    section: LayerSectionKind;
    name: string;
    visible: boolean;
    id: number | undefined;
    bounds: LayerBounds | null;
}

// EXPECTED multiGet descriptor key names. Centralised here so the live
// session only has to edit this block (and `mapSection` / `readBounds`)
// when the real descriptor differs from the documented standard.
const KEYS = {
    name: "name",
    visible: "visible",
    id: "layerID",
    section: "layerSection",
    bounds: "bounds",
} as const;

// Photoshop's `layerSection` string values, mapped onto LayerSectionKind.
const SECTION_VALUES: Readonly<Record<string, LayerSectionKind>> = {
    layerSectionStart: "start",
    layerSectionEnd: "end",
    layerSectionContent: "content",
};

// Reads one raw descriptor's fields into a ParsedEntry. Returns null when the
// value is not a usable descriptor (not an object, no string name, or an
// unrecognised section marker) so the fold can skip it safely. SWAPPABLE:
// adjust KEYS / SECTION_VALUES / readBounds to match the live descriptor.
export function parseDescriptor(raw: RawDescriptor): ParsedEntry | null {
    if (typeof raw !== "object" || raw === null) return null;
    const record = raw as Record<string, unknown>;

    const section = mapSection(record[KEYS.section]);
    if (section === null) return null;

    const name = record[KEYS.name];
    if (typeof name !== "string") return null;

    const rawVisible = record[KEYS.visible];
    const visible = typeof rawVisible === "boolean" ? rawVisible : true;

    return {
        section,
        name,
        visible,
        id: readId(record[KEYS.id]),
        bounds: readBounds(record[KEYS.bounds]),
    };
}

// Rebuilds the nested Layer[] tree from a flat multiGet descriptor array.
//
// Ordering assumption (CENTRALISED - one flip to correct in the live
// session): Photoshop enumerates layers BOTTOM-UP, so index 0 is the
// bottom-most layer. The fold walks the raw array as given and PREPENDS each
// finished layer to its parent's child list, which reverses bottom-up into
// the TOP-DOWN visual order the DOM-walk adapter produces (top layer first).
// In that bottom-up order a group appears as: its END divider, then its
// children, then its START marker; so the fold opens a group on "end" and
// closes it on "start".
//
// If the live descriptor turns out to enumerate TOP-DOWN instead, flip this
// single `LAYER_ENUMERATION` constant to "top-down": that swaps the
// start/end roles and the prepend/append so the rest of the fold is
// unchanged. Compared (not a bare boolean literal) so both branches stay
// live code rather than being statically pruned by narrowing.
type LayerEnumeration = "bottom-up" | "top-down";
const LAYER_ENUMERATION = "bottom-up" as LayerEnumeration;
const BOTTOM_UP = LAYER_ENUMERATION === "bottom-up";

export function rebuildLayerTree(raw: readonly RawDescriptor[]): Layer[] {
    const root: Layer[] = [];
    // Stack of in-progress groups. Each frame holds the LayerSet being built
    // and the sibling list it will be added to when it closes.
    const stack: { set: Extract<Layer, { kind: "set" }>; siblings: Layer[] }[] = [];

    const currentSiblings = (): Layer[] => {
        const top = stack[stack.length - 1];
        return top === undefined ? root : top.set.layers;
    };

    const addLayer = (siblings: Layer[], layer: Layer): void => {
        // Prepend in bottom-up mode so the result lands top-down; append in
        // top-down mode so the result keeps the source order.
        if (BOTTOM_UP) siblings.unshift(layer);
        else siblings.push(layer);
    };

    // In bottom-up order a group OPENS on its end divider and CLOSES on its
    // start marker; top-down order swaps those roles.
    const openMarker: LayerSectionKind = BOTTOM_UP ? "end" : "start";
    const closeMarker: LayerSectionKind = BOTTOM_UP ? "start" : "end";

    for (const item of raw) {
        const entry = parseDescriptor(item);
        if (entry === null) continue;

        if (entry.section === openMarker) {
            const set: Extract<Layer, { kind: "set" }> = {
                kind: "set",
                name: "", // backfilled by the matching close marker (it carries the name)
                visible: true,
                layers: [],
            };
            stack.push({ set, siblings: currentSiblings() });
            continue;
        }

        if (entry.section === closeMarker) {
            const frame = stack.pop();
            if (frame === undefined) continue; // unbalanced close; skip defensively
            frame.set.name = entry.name;
            frame.set.visible = entry.visible;
            if (entry.id !== undefined) frame.set.id = entry.id;
            addLayer(frame.siblings, frame.set);
            continue;
        }

        // A content leaf -> art layer.
        const art: Layer = {
            kind: "art",
            name: entry.name,
            visible: entry.visible,
            ...(entry.id === undefined ? {} : { id: entry.id }),
            bounds: entry.bounds,
        };
        addLayer(currentSiblings(), art);
    }

    return root;
}

// Maps a raw `layerSection` value onto LayerSectionKind; null for anything
// unrecognised so the caller can reject the descriptor. The live multiGet
// (confirmed against a real PSD) wraps the value in an `{ _enum, _value }`
// action-descriptor envelope; a bare string is also accepted so the shape
// stays robust across UXP / PS builds.
function mapSection(value: unknown): LayerSectionKind | null {
    const raw = typeof value === "string"
        ? value
        : typeof value === "object" && value !== null
            ? (value as Record<string, unknown>)["_value"]
            : undefined;
    if (typeof raw !== "string") return null;
    return SECTION_VALUES[raw] ?? null;
}

// Keeps only a real number; everything else (string, undefined, NaN) becomes
// undefined so the Layer's optional `id` is omitted.
function readId(value: unknown): number | undefined {
    return typeof value === "number" && Number.isFinite(value) ? value : undefined;
}

// Mirrors adapt-document's `toBounds` exactly: w = right - left,
// h = bottom - top, null when w <= 0 || h <= 0 or the rectangle is missing.
// The descriptor may carry each side directly or wrapped in a `{ _value }`
// action-descriptor envelope, so each side is read defensively. SWAPPABLE:
// adjust this when the live bounds nesting is confirmed.
function readBounds(value: unknown): LayerBounds | null {
    if (typeof value !== "object" || value === null) return null;
    const record = value as Record<string, unknown>;
    const left = readNumber(record["left"]);
    const top = readNumber(record["top"]);
    const right = readNumber(record["right"]);
    const bottom = readNumber(record["bottom"]);
    if (left === null || top === null || right === null || bottom === null) return null;
    const w = right - left;
    const h = bottom - top;
    if (w <= 0 || h <= 0) return null;
    return { x: left, y: top, w, h };
}

// Reads a bounds side, unwrapping the `{ _value, _unit }` action-descriptor
// envelope when present; null when no finite number is recoverable.
function readNumber(value: unknown): number | null {
    if (typeof value === "number") return Number.isFinite(value) ? value : null;
    if (typeof value === "object" && value !== null) {
        const inner = (value as Record<string, unknown>)["_value"];
        if (typeof inner === "number" && Number.isFinite(inner)) return inner;
    }
    return null;
}
