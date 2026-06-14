import { describe, expect, it } from "vitest";

import { emptyItem } from "../src/format";
import { serializeBlock } from "../src/serialize";

describe("serializeBlock", () => {
  it("renders a full item with numbered steps, multiline note and shots", () => {
    const item = emptyItem("BL-OUTLN-01", "Outliner foldout");
    item.status = "pass";
    item.review = "rephrase";
    item.pre = "panel visible";
    item.steps = ["Click the header.", "Click again."];
    item.observe = "expands then collapses.";
    item.intent = "flat list.";
    item.code = "outliner.py:127-139";
    item.note = "line one\nline two";
    item.shots = ["walk-screenshots/BL-OUTLN-01-1.png"];

    expect(serializeBlock(item)).toBe(
      [
        "### BL-OUTLN-01 · Outliner foldout",
        "- status: pass",
        "- review: rephrase",
        "- pre: panel visible",
        "- steps:",
        "  1. Click the header.",
        "  2. Click again.",
        "- observe: expands then collapses.",
        "- intent: flat list.",
        "- code: outliner.py:127-139",
        "- note:",
        "  line one",
        "  line two",
        "- shots:",
        "  - walk-screenshots/BL-OUTLN-01-1.png",
      ].join("\n"),
    );
  });

  it("omits empty optionals and never leaves a trailing space", () => {
    const item = emptyItem("PS-EXPORT-26", "empty doc export");
    const out = serializeBlock(item);
    expect(out).toBe(
      ["### PS-EXPORT-26 · empty doc export", "- status: pending", "- review: keep", "- observe:"].join("\n"),
    );
    expect(out.split("\n").some((l) => l.endsWith(" "))).toBe(false);
  });

  it("inlines a single-line note", () => {
    const item = emptyItem("X-Y-1", "t");
    item.note = "one liner";
    expect(serializeBlock(item)).toContain("- note: one liner");
  });
});
