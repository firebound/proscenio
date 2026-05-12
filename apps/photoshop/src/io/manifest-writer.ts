// Manifest JSON writer. Stringifies a v1 manifest with two-space
// indent so output is diff-friendly against the JSX exporter baseline,
// then writes it through the UXP local file system.
//
// Validation runs at the call site (`controllers/export-flow.ts`) so
// the panel can surface ajv errors before any disk writes happen.

import type { UxpFolder } from "uxp";

import type { Manifest } from "../domain/manifest";

export async function writeManifest(
    folder: UxpFolder,
    manifest: Manifest,
    fileName: string,
): Promise<void> {
    const file = await folder.createFile(fileName, { overwrite: true });
    const body = JSON.stringify(manifest, null, 2);
    // No `{ format: "utf8" }` here - UXP's storage API rejects a bare
    // string and wants `storage.formats.utf8`. The default for string
    // content already is utf8, so omitting the option is the safe path.
    await file.write(body);
}
