// Manifest JSON reader. Picks a `.json` file via the UXP file picker,
// parses it, then validates against the v2 schema. Validation errors
// surface as plain strings so the panel can list them - identical
// posture to `manifest-validator.ts` on the export side.
//
// Returns a discriminated result so the caller can branch without
// throwing across the UXP IPC boundary (exceptions inside
// `executeAsModal` etc. tend to surface as opaque host errors).
//
// The Manifest type flows from ajv's type-narrowing predicate (see
// `parseManifest` in `manifest-validator.ts`), not from a cast. A
// document that survives ajv is statically typed as `Manifest`.

import { storage } from "uxp";
import type { UxpFile, UxpFolder } from "uxp";

import { parseManifest } from "./manifest-validator";
import type { Manifest } from "../domain/manifest";

export interface PickedManifest {
    file: UxpFile;
    folder: UxpFolder;
    manifest: Manifest;
}

export type ReadManifestResult =
    | { kind: "ok"; picked: PickedManifest }
    | { kind: "cancelled" }
    | { kind: "invalid"; errors: string[] };

export async function readManifestFromPicker(): Promise<ReadManifestResult> {
    const file = await storage.localFileSystem
        .getFileForOpening({ types: ["json"] })
        .catch(() => null);
    if (file === null) return { kind: "cancelled" };

    const raw = await file.read();
    const text = typeof raw === "string" ? raw : new TextDecoder("utf-8").decode(raw);
    let parsed: unknown;
    try {
        parsed = JSON.parse(text);
    } catch (err) {
        return {
            kind: "invalid",
            errors: [`manifest is not valid JSON: ${err instanceof Error ? err.message : String(err)}`],
        };
    }
    const result = parseManifest(parsed);
    if (result.kind === "invalid") {
        return result;
    }
    const folder = await resolveParentFolder(file);
    if (folder === null) {
        return {
            kind: "invalid",
            errors: ["could not resolve manifest's parent folder"],
        };
    }
    return {
        kind: "ok",
        picked: { file, folder, manifest: result.value },
    };
}

async function resolveParentFolder(file: UxpFile): Promise<UxpFolder | null> {
    // Modern UXP exposes `file.parent` directly on the picked entry.
    // Older builds (and a few host-version regressions) drop it; fall
    // back to reconstructing the parent path from `nativePath` and
    // re-resolving via `getEntryWithUrl`.
    if (file.parent?.isFolder === true) return file.parent;

    const native = file.nativePath;
    if (native.length === 0) return null;
    const parentPath = native.replace(/[\\/][^\\/]+$/, "");
    if (parentPath.length === 0 || parentPath === native) return null;
    try {
        const entry = await storage.localFileSystem.getEntryWithUrl(parentPath);
        return entry.isFolder ? (entry as UxpFolder) : null;
    } catch {
        return null;
    }
}
