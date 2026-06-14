import { describe, expect, it } from "vitest";

import { parseDoc } from "../src/parse";

const SAMPLE = `# Title - manual-test checklist

intro paragraph.

## Group A

### BL-OUTLN-01 · Outliner foldout
- status: pass
- review: keep
- pre: panel visible
- steps:
  1. Click the header.
  2. Click again.
- observe: expands then collapses.
- intent: flat list.
- code: outliner.py:127-139
- note: looked fine
- shots:
  - walk-screenshots/BL-OUTLN-01-1.png

### PS-EXPORT-14 · Run export
- status: pending
- review: rephrase
- observe: green Wrote N
- note:
  line one
  line two
`;

describe("parseDoc", () => {
  it("captures groups, item count, and the preamble", () => {
    const doc = parseDoc(SAMPLE);
    expect(doc.preamble).toContain("# Title");
    expect(doc.groups).toHaveLength(1);
    expect(doc.groups[0]!.name).toBe("Group A");
    expect(doc.groups[0]!.items).toHaveLength(2);
  });

  it("parses every field shape on a full block", () => {
    const it0 = parseDoc(SAMPLE).groups[0]!.items[0]!;
    expect(it0.id).toBe("BL-OUTLN-01");
    expect(it0.title).toBe("Outliner foldout");
    expect(it0.status).toBe("pass");
    expect(it0.review).toBe("keep");
    expect(it0.pre).toBe("panel visible");
    expect(it0.steps).toEqual(["Click the header.", "Click again."]);
    expect(it0.observe).toBe("expands then collapses.");
    expect(it0.intent).toBe("flat list.");
    expect(it0.code).toBe("outliner.py:127-139");
    expect(it0.note).toBe("looked fine");
    expect(it0.shots).toEqual(["walk-screenshots/BL-OUTLN-01-1.png"]);
  });

  it("parses a multiline note and an empty steps list", () => {
    const it1 = parseDoc(SAMPLE).groups[0]!.items[1]!;
    expect(it1.note).toBe("line one\nline two");
    expect(it1.steps).toEqual([]);
    expect(it1.review).toBe("rephrase");
  });

  it("coerces an unknown status/review to the safe default", () => {
    const doc = parseDoc("## G\n\n### X-Y-1 · t\n- status: bogus\n- review: nope\n- observe: x\n");
    const item = doc.groups[0]!.items[0]!;
    expect(item.status).toBe("pending");
    expect(item.review).toBe("keep");
  });

  it("keeps an item that appears before any group header", () => {
    const doc = parseDoc("### A-B-1 · loose\n- status: pass\n- observe: y\n");
    expect(doc.groups).toHaveLength(1);
    expect(doc.groups[0]!.items[0]!.id).toBe("A-B-1");
  });

  it("parses a feedback sublist into kind/text pairs", () => {
    const doc = parseDoc(
      "## G\n\n### X-Y-1 · t\n- status: pass\n- observe: ok\n- feedback:\n  - ui: panel wastes width\n  - remove: redundant second search\n",
    );
    expect(doc.groups[0]!.items[0]!.feedback).toEqual([
      { kind: "ui", text: "panel wastes width" },
      { kind: "remove", text: "redundant second search" },
    ]);
  });

  it("defaults a feedback line with no kind to 'note'", () => {
    const doc = parseDoc("## G\n\n### X-Y-1 · t\n- observe: ok\n- feedback:\n  - just a loose thought\n");
    expect(doc.groups[0]!.items[0]!.feedback).toEqual([{ kind: "note", text: "just a loose thought" }]);
  });

  it("tolerates CRLF line endings (id/title not corrupted by a trailing \\r)", () => {
    const crlf = "## G\r\n\r\n### BL-X-1 · A title\r\n- status: pass\r\n- observe: ok here\r\n";
    const item = parseDoc(crlf).groups[0]!.items[0]!;
    expect(item.id).toBe("BL-X-1");
    expect(item.title).toBe("A title");
    expect(item.status).toBe("pass");
    expect(item.observe).toBe("ok here");
  });
});
