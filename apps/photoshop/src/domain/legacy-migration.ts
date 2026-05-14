// SPEC 011 D3: the legacy `_<name>` skip convention is gone, replaced
// by `[ignore]`. Old PSDs authored under SPEC 010 routinely use the
// underscore prefix to opt layers out of the export. This module walks
// the adapted layer tree and produces a list of rename candidates so
// the artist can convert in bulk from the Tags tab.
//
// Rules:
//   - any layer name with a leading underscore is a candidate;
//   - all leading underscores are stripped (`__foo` and `_foo` both
//     produce `foo`);
//   - if the stripped name already carries `[ignore]`, the rename only
//     drops the prefix; otherwise ` [ignore]` is appended;
//   - empty name after stripping (`_` alone) becomes `[ignore]`.
//
// Pure module; the matching UXP applier lives in
// `src/io/legacy-migration.ts`.

import type { Layer } from "./layer";

export interface UnderscoreMigrationCandidate {
    layerPath: string[];
    oldName: string;
    newName: string;
}

export function planUnderscoreMigration(layers: Layer[]): UnderscoreMigrationCandidate[] {
    const out: UnderscoreMigrationCandidate[] = [];
    walk(layers, [], out);
    return out;
}

function walk(
    layers: Layer[],
    parentPath: string[],
    out: UnderscoreMigrationCandidate[],
): void {
    for (const layer of layers) {
        const layerPath = [...parentPath, layer.name];
        if (layer.name.startsWith("_")) {
            const stripped = layer.name.replace(/^_+/, "").trim();
            const newName = nextName(stripped);
            if (newName !== layer.name) {
                out.push({ layerPath, oldName: layer.name, newName });
            }
        }
        if (layer.kind === "set") {
            walk(layer.layers, layerPath, out);
        }
    }
}

function nextName(stripped: string): string {
    if (stripped.length === 0) return "[ignore]";
    if (/\[ignore\]/.test(stripped)) return stripped;
    return `${stripped} [ignore]`;
}
