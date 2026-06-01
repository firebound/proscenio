// ajv-backed validation gate for the v2 PSD manifest.
//
// Schema source of truth lives at the repo root
// (`packages/models/schemas/psd_manifest.schema.json`) and is shared by every
// consumer / downstream importer of the manifest. The TypeScript
// build pulls it in via a relative import widened in tsconfig
// include; webpack inlines the JSON at bundle time.
//
// Two surfaces:
//
// - `validateManifest(manifest)`: legacy shape used on the export side,
//   where the caller already holds a `Manifest`-typed value (constructed
//   from the panel state) and only wants the string-formatted error
//   list. Empty array == valid.
//
// - `parseManifest(raw)`: the read-side entry point. Takes an `unknown`
//   payload (e.g. `JSON.parse` output), runs ajv's type-narrowing
//   predicate, and returns a discriminated `ParseManifestResult`. The
//   caller never has to cast - on `kind: "ok"`, `value` is statically
//   typed as `Manifest`. Mirrors the model-first contract on the Blender
//   side where the importer trusts the parsed pydantic record.

// `Ajv` (the default export from `"ajv"`) targets draft-07. The PSD
// manifest schema declares draft 2020-12, so use the dedicated
// `Ajv2020` build that bundles the 2020-12 meta-schemas.
import Ajv2020 from "ajv/dist/2020";
import type { ErrorObject } from "ajv";

import schema from "../../../../packages/models/schemas/psd_manifest.schema.json";
import type { Manifest } from "../domain/manifest";

const ajv = new Ajv2020({ allErrors: true, strict: false });
const validate = ajv.compile<Manifest>(schema);

export type ParseManifestResult =
    | { kind: "ok"; value: Manifest }
    | { kind: "invalid"; errors: string[] };

export function validateManifest(manifest: Manifest): string[] {
    const ok = validate(manifest);
    if (ok) return [];
    return (validate.errors ?? []).map(formatError);
}

export function parseManifest(raw: unknown): ParseManifestResult {
    if (validate(raw)) {
        return { kind: "ok", value: raw };
    }
    return {
        kind: "invalid",
        errors: (validate.errors ?? []).map(formatError),
    };
}

function formatError(err: ErrorObject): string {
    const at = err.instancePath === "" ? "(root)" : err.instancePath;
    return `${at} ${err.message ?? "invalid"}`;
}
