// Photoshop -> exporter Layer adapter.
//
// The pure planner (`src/controllers/exporter.ts`) consumes the
// runtime-agnostic `Layer` shape from `src/types/layer.ts`. This
// module bridges the live Photoshop document into that shape so the
// planner can run identically against synthetic test data and a real
// PSD. Nothing in here touches the file system or schedules an
// export; it only reads.
//
// The mapping is intentionally narrow: only the fields the planner
// reads (`name`, `visible`, `bounds`, children, set vs art) cross the
// boundary. The Photoshop layer kind enum is exposed via
// `constants.LayerKind`; group layers (LayerSet) report
// `LayerKind.group` and surface their children via `layer.layers`.

import { constants, type PsBounds, type PsDocument, type PsLayer } from "photoshop";

import type { DocumentInfo } from "../controllers/exporter";
import type { Layer, LayerBounds } from "../types/layer";

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
        const children = layer.layers ?? [];
        return {
            kind: "set",
            name: layer.name,
            visible: layer.visible,
            layers: children.map(adaptLayer),
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
    return layer.kind === constants.LayerKind.group;
}

function toBounds(raw: PsBounds | null | undefined): LayerBounds | null {
    if (raw === null || raw === undefined) return null;
    const w = raw.right - raw.left;
    const h = raw.bottom - raw.top;
    if (w <= 0 || h <= 0) return null;
    return { x: raw.left, y: raw.top, w, h };
}
