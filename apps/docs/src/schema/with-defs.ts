// Build a standalone schema for a single named `$def`, keeping the full `$defs`
// map alongside it so the JSON Schema viewer can still resolve nested `$ref`
// pointers (e.g. `#/$defs/Bone`). Shared by the per-feature schema pages.

type JsonSchema = Record<string, unknown> & {
  $defs?: Record<string, unknown>;
};

export function withDefs(schema: JsonSchema, name: string): JsonSchema {
  const def = (schema.$defs?.[name] ?? {}) as Record<string, unknown>;
  return {...def, $defs: schema.$defs};
}
