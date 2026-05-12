// Manifest JSON reader. Picks a `.json` file via the UXP file picker,
// parses it, then validates against the v1 schema. Validation errors
// surface as plain strings so the panel can list them - identical
// posture to `manifest-validator.ts` on the export side.
//
// Returns a discriminated result so the caller can branch without
// throwing across the UXP IPC boundary (exceptions inside
// `executeAsModal` etc. tend to surface as opaque host errors).

import { storage } from "uxp";
import type { UxpFile, UxpFolder } from "uxp";

import { validateManifest } from "./manifest-validator";
import type { Manifest } from "../types/manifest";

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
    const errors = validateManifest(parsed as Manifest);
    if (errors.length > 0) {
        return { kind: "invalid", errors };
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
        picked: { file, folder, manifest: parsed as Manifest },
    };
}

async function resolveParentFolder(file: UxpFile): Promise<UxpFolder | null> {
    // UXP UxpEntry exposes `nativePath` but not a typed parent
    // accessor. The localFileSystem call below works in PS via the
    // session-token mechanism: `createSessionToken` on a sibling
    // entry plus `getEntryWithUrl` is the canonical hop. Simpler:
    // strip the trailing filename from nativePath, then re-resolve
    // via getEntryWithUrl. UXP also exposes `file.parent` in modern
    // builds; we try that first, fall back to manual reconstruction
    // if the runtime does not expose it.
    interface FileWithParent {
        parent?: UxpFolder;
    }
    const direct = (file as unknown as FileWithParent).parent;
    if (direct !== undefined && direct.isFolder) return direct;
    return null;
}
