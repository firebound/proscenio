// Photoshop -> exporter Layer adapter.
//
// The pure planner (`src/domain/planner.ts`) consumes the
// runtime-agnostic `Layer` shape from `src/domain/layer.ts`. This
// module bridges the live Photoshop document into that shape so the
// planner can run identically against synthetic test data and a real
// PSD. Nothing in here touches the file system or schedules an
// export; it only reads.
//
// Group detection uses the duck-typed shape (presence of a `.layers`
// array) rather than `layer.kind === constants.LayerKind.group`. The
// enum value differs across UXP / PS versions (some return numbers,
// some return strings, some swap the casing); the `.layers` array is
// the universal signal that a layer is a LayerSet.

import { type PsDocument, type PsLayer, type PsBounds } from "photoshop";

import type { DocumentInfo } from "../domain/planner";
import type { Layer, LayerBounds } from "../domain/layer";

export interface AdaptedDocument {
    info: DocumentInfo;
    layers: Layer[];
}

export function adaptDocument(doc: PsDocument): AdaptedDocument {
    return {
        info: {
            name: doc.name,
            width: doc.width,
            height: doc.height,
        },
        layers: doc.layers.map(adaptLayer),
    };
}

export function adaptLayer(layer: PsLayer): Layer {
    if (isGroup(layer)) {
        return {
            kind: "set",
            name: layer.name,
            visible: layer.visible,
            layers: (layer.layers ?? []).map(adaptLayer),
        };
    }
    return {
        kind: "art",
        name: layer.name,
        visible: layer.visible,
        bounds: toBounds(layer.bounds),
    };
}

function isGroup(layer: PsLayer): boolean {
    return Array.isArray(layer.layers);
}

function toBounds(raw: PsBounds | null | undefined): LayerBounds | null {
    if (raw === null || raw === undefined) return null;
    const w = raw.right - raw.left;
    const h = raw.bottom - raw.top;
    if (w <= 0 || h <= 0) return null;
    return { x: raw.left, y: raw.top, w, h };
}
