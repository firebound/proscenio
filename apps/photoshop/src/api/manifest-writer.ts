// Manifest JSON writer. Stringifies a v2 manifest with two-space
// indent (diff-friendly) and writes it through the UXP file system.
// Validation runs at the call site, before any disk write.

import type { UxpFolder } from "uxp";

import type { Manifest } from "../lib/manifest";

export async function writeManifest(
    folder: UxpFolder,
    manifest: Manifest,
    fileName: string,
): Promise<void> {
    const file = await folder.createFile(fileName, { overwrite: true });
    // Trailing newline so the committed manifest matches the repo's
    // end-of-file convention (the parity-oracle fixture is committed; a
    // newline-less export would be rewritten by the pre-commit hook on
    // every re-export).
    const body = `${JSON.stringify(manifest, null, 2)}\n`;
    // Pass no format option: UXP rejects a bare `"utf8"` string (it
    // wants `storage.formats.utf8`), and string content defaults to utf8.
    await file.write(body);
}
