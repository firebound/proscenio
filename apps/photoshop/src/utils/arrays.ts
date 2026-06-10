// Shallow element-wise equality for ordered collections: reference
// equality per element, in order. Used in memo bail-outs and tree-reuse
// detection.

export function elementsEqual<T>(a: readonly T[], b: readonly T[]): boolean {
    if (a === b) return true;
    if (a.length !== b.length) return false;
    for (let i = 0; i < a.length; i++) {
        if (a[i] !== b[i]) return false;
    }
    return true;
}
