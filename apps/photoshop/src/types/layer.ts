// Photoshop-agnostic layer view consumed by the exporter recursion.
// The real adapter (Wave 10.3) maps Photoshop's `LayerSet` / `ArtLayer`
// onto this shape; unit tests pass plain object trees.
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
