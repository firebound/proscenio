// Photoshop-agnostic layer view consumed by the exporter recursion.
// The UXP adapter maps Photoshop's `LayerSet` / `ArtLayer` onto this
// shape; unit tests pass plain object trees.
//
// `bounds` is the source-document pixel rectangle of the layer's
// visible content (Photoshop's `layer.bounds`, already trimmed to
// non-transparent pixels). It is null only for layers with no visible
// pixels, which the exporter drops.

export interface LayerBounds {
    x: number;
    y: number;
    w: number;
    h: number;
}

export interface BaseLayer {
    name: string;
    visible: boolean;
    /** Photoshop's stable per-layer id (`PsLayer.id`). Survives renames,
     *  so the UI keys rows on it to avoid remounting a subtree every time
     *  a tag edit rewrites a layer name. Optional: unit-test fixtures and
     *  any host build that does not expose it fall back to the path key. */
    id?: number;
}

export interface ArtLayer extends BaseLayer {
    kind: "art";
    bounds: LayerBounds | null;
}

export interface LayerSet extends BaseLayer {
    kind: "set";
    layers: Layer[];
}

export type Layer = ArtLayer | LayerSet;
