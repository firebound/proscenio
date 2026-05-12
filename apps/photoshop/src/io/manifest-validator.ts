// ajv-backed validation gate for the v1 PSD manifest.
//
// Schema source of truth lives at the repo root (`schemas/psd_manifest.schema.json`)
// so the Blender importer and this exporter share one definition. The
// TypeScript build pulls it in via a relative import widened in
// tsconfig include; webpack inlines the JSON at bundle time.
//
// `validateManifest` returns the list of ajv errors as plain strings.
// Empty array == valid. The export flow refuses to write the manifest
// or any PNG until the array is empty - failing fast keeps a broken
// manifest from leaving the panel and breaking the importer
// downstream.

// `Ajv` (the default export from `"ajv"`) targets draft-07. The PSD
// manifest schema declares draft 2020-12, so use the dedicated
// `Ajv2020` build that bundles the 2020-12 meta-schemas.
import Ajv2020 from "ajv/dist/2020";
import type { ErrorObject } from "ajv";

import schema from "../../../../schemas/psd_manifest.schema.json";
import type { Manifest } from "../types/manifest";

const ajv = new Ajv2020({ allErrors: true, strict: false });
const validate = ajv.compile(schema);

export function validateManifest(manifest: Manifest): string[] {
    const ok = validate(manifest);
    if (ok) return [];
    return (validate.errors ?? []).map(formatError);
}

function formatError(err: ErrorObject): string {
    const at = err.instancePath === "" ? "(root)" : err.instancePath;
    return `${at} ${err.message ?? "invalid"}`;
}
