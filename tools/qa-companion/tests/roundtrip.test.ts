import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";

import { describe, expect, it } from "vitest";

import { parseDoc } from "../src/parse";
import { serializeDoc } from "../src/serialize";
import { FILES, defaultStore, loadFlat } from "../src/store";

const norm = (text: string): string => serializeDoc(parseDoc(text));

describe("round-trip", () => {
  it("is idempotent on a hand-written sample (no data drift on a second cycle)", () => {
    const sample =
      "# T\n\nintro.\n\n## G\n\n### A-B-1 · t\n- status: pass\n- review: keep\n- steps:\n  1. do it\n- observe: it worked\n- note:\n  saw a glitch\n  then fine\n- feedback:\n  - ui: redundant control\n  - remove: drop the second search\n";
    expect(norm(norm(sample))).toBe(norm(sample));
  });

  it("preserves the full model through a serialize -> reparse cycle on the real checklists", () => {
    const store = defaultStore();
    for (const file of FILES) {
      const path = join(store.dir, file);
      if (!existsSync(path)) continue;
      const text = readFileSync(path, "utf8");
      const once = parseDoc(text);
      const twice = parseDoc(serializeDoc(once));
      expect(JSON.stringify(twice)).toBe(JSON.stringify(once));
    }
  });

  it("loads the migrated inventory from the real checklists", () => {
    const flat = loadFlat(defaultStore());
    // The audit seeded 452 items; the user prunes over time, so guard a floor
    // against a parser regression rather than pinning the exact count.
    expect(flat.length).toBeGreaterThan(400);
    expect(flat.some((it) => it.id === "PS-EXPORT-14")).toBe(true);
  });
});
