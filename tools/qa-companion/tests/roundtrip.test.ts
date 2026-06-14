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
      "# T\n\nintro.\n\n## G\n\n### A-B-1 · t\n- status: pass\n- review: keep\n- steps:\n  1. do it\n- observe: it worked\n- note:\n  saw a glitch\n  then fine\n";
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

  it("loads the curated inventory from the real checklists", () => {
    const flat = loadFlat(defaultStore());
    // The 2026-06 restructure condensed 452 items into ~205 (global chrome +
    // per-subpanel sweeps + flows); the user keeps pruning, so guard a floor
    // against a parser regression rather than pinning the exact count.
    expect(flat.length).toBeGreaterThan(150);
    expect(flat.some((it) => it.id === "FLOW-DOLL-01")).toBe(true);
  });
});
