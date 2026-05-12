// Manifest JSON writer. Stringifies a v1 manifest with two-space
// indent so output is diff-friendly against the JSX exporter baseline,
// then writes it through the UXP local file system.
//
// Validation runs at the call site (`controllers/export-flow.ts`) so
// the panel can surface ajv errors before any disk writes happen.

import type { UxpFolder } from "uxp";

import type { Manifest } from "../types/manifest";

export async function writeManifest(
    folder: UxpFolder,
    manifest: Manifest,
    fileName: string,
): Promise<void> {
    const file = await folder.createFile(fileName, { overwrite: true });
    const body = JSON.stringify(manifest, null, 2);
    await file.write(body, { format: "utf8" });
}
