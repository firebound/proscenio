import { describe, expect, it } from "vitest";

import { parseFeedback, serializeFeedback } from "../src/feedback";

const SAMPLE = `# Feature feedback

intro line.

## BL · Outliner panel
- remove: the second (non-native) search field is redundant
- ui: revisit the panel layout

## PS · Exporter panel
- bug: filename template ignores trailing slash
`;

describe("parseFeedback", () => {
  it("captures the preamble, areas, and kind/text entries", () => {
    const doc = parseFeedback(SAMPLE);
    expect(doc.preamble).toContain("# Feature feedback");
    expect(doc.areas).toHaveLength(2);
    expect(doc.areas[0]).toEqual({
      app: "BL",
      group: "Outliner panel",
      feedback: [
        { kind: "remove", text: "the second (non-native) search field is redundant" },
        { kind: "ui", text: "revisit the panel layout" },
      ],
    });
    expect(doc.areas[1]!.app).toBe("PS");
    expect(doc.areas[1]!.feedback[0]!.kind).toBe("bug");
  });

  it("defaults an entry with no kind to 'note'", () => {
    const doc = parseFeedback("## BL · X\n- a loose thought\n");
    expect(doc.areas[0]!.feedback).toEqual([{ kind: "note", text: "a loose thought" }]);
  });

  it("tolerates CRLF (the middot split and kind split survive a trailing \\r)", () => {
    const doc = parseFeedback("## BL · Outliner panel\r\n- ui: ok here\r\n");
    expect(doc.areas[0]!.app).toBe("BL");
    expect(doc.areas[0]!.group).toBe("Outliner panel");
    expect(doc.areas[0]!.feedback[0]).toEqual({ kind: "ui", text: "ok here" });
  });
});

describe("serializeFeedback round-trip", () => {
  it("is idempotent on a second cycle", () => {
    const norm = (t: string): string => serializeFeedback(parseFeedback(t));
    expect(norm(norm(SAMPLE))).toBe(norm(SAMPLE));
  });

  it("omits an area whose entries are all empty", () => {
    const out = serializeFeedback({
      preamble: "# Feature feedback\n",
      areas: [
        { app: "BL", group: "Empty", feedback: [{ kind: "ui", text: "  " }] },
        { app: "BL", group: "Kept", feedback: [{ kind: "ui", text: "real" }] },
      ],
    });
    expect(out).not.toContain("## BL · Empty");
    expect(out).toContain("## BL · Kept");
  });
});
