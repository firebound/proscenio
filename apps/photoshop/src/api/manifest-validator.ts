// ajv-backed validation gate for the v2 PSD manifest, against the
// shared schema at `packages/models/schemas/psd_manifest.schema.json`.
//
// Two surfaces:
//
// - `validateManifest(manifest)`: export side; caller already holds a
//   `Manifest`-typed value and wants the string error list. Empty == valid.
// - `parseManifest(raw)`: read side; takes an `unknown` payload, runs
//   ajv's type-narrowing predicate, and returns a discriminated result.
//   On `kind: "ok"`, `value` is statically typed as `Manifest` (no cast).

// `Ajv` (the default export from `"ajv"`) targets draft-07. The PSD
// manifest schema declares draft 2020-12, so use the dedicated
// `Ajv2020` build that bundles the 2020-12 meta-schemas.
import Ajv2020 from "ajv/dist/2020";
import type { ErrorObject } from "ajv";

import schema from "../../../../packages/models/schemas/psd_manifest.schema.json";
import type { Manifest } from "../lib/manifest";

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
