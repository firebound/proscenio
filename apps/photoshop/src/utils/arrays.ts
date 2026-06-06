// Generic element-wise equality for ordered collections. Used in
// memo bail-outs (TagRow, useActiveLayerPath) and in tree-reuse
// detection (buildTagTreeReusing). Reference-equal arrays short-
// circuit; length mismatches fail fast; otherwise pointer-equal
// elements in order.

export function elementsEqual<T>(a: readonly T[], b: readonly T[]): boolean {
    if (a === b) return true;
    if (a.length !== b.length) return false;
    for (let i = 0; i < a.length; i++) {
        if (a[i] !== b[i]) return false;
    }
    return true;
}
