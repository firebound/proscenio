/**
 * Panel-level feedback model: `feedback.md`.
 *
 * Feedback is product feedback about a panel/control, not a test result, so it
 * lives apart from the test blocks - one section per area (a checklist group):
 *
 *     ## BL · Outliner panel
 *     - remove: the second (non-native) search field is redundant
 *     - ui: revisit the panel layout
 *
 * Each line is `kind: text`; a line with no kind defaults to `note`. The format
 * round-trips through parse -> edit -> serialize like the checklist blocks do.
 */

import { type Feedback } from "./format";

/** One area's feedback: an app code + group name (the panel) and its entries. */
export interface Area {
  app: string;
  group: string;
  feedback: Feedback[];
}

export interface FeedbackDoc {
  /** Everything before the first `## ` area header, kept verbatim. */
  preamble: string;
  areas: Area[];
}

export const FEEDBACK_PREAMBLE =
  "# Feature feedback\n\n" +
  "Panel-level product feedback gathered during the walk - not test results.\n" +
  "Each entry normalizes into a backlog file later (ui/remove -> ui-feedback,\n" +
  "bug -> bugs-found, code -> code-quality, perf -> perf, note -> general).\n";

const AREA_RE = /^##\s+(.+?)\s+·\s+(.*)$/;
const LINE_RE = /^-\s+(.*)$/;

function parseLine(raw: string): Feedback | null {
  const text = raw.trim();
  if (!text) return null;
  const colon = text.indexOf(":");
  if (colon < 0) return { kind: "note", text };
  const fb = { kind: text.slice(0, colon).trim(), text: text.slice(colon + 1).trim() };
  return fb.text ? fb : null;
}

export function parseFeedback(text: string): FeedbackDoc {
  // CRLF-tolerant: a stray \r would otherwise ride on the area header and the
  // entries, corrupting the middot split and the kind/text split.
  const lines = text.split(/\r?\n/);
  let firstArea = lines.findIndex((l) => l.startsWith("## "));
  if (firstArea < 0) firstArea = lines.length;
  const preamble = lines.slice(0, firstArea).join("\n");

  const areas: Area[] = [];
  let current: Area | null = null;
  for (let i = firstArea; i < lines.length; i += 1) {
    const line = lines[i] ?? "";
    const head = AREA_RE.exec(line);
    if (head) {
      current = { app: head[1]!.trim(), group: head[2]!.trim(), feedback: [] };
      areas.push(current);
      continue;
    }
    const entry = LINE_RE.exec(line);
    if (entry && current) {
      const fb = parseLine(entry[1]!);
      if (fb) current.feedback.push(fb);
    }
  }
  return { preamble, areas };
}

export function serializeFeedback(doc: FeedbackDoc): string {
  const parts: string[] = [doc.preamble.replace(/\s+$/, "")];
  for (const area of doc.areas) {
    const entries = area.feedback
      .map((f) => ({ kind: f.kind.trim() || "note", text: f.text.trim() }))
      .filter((f) => f.text);
    if (!entries.length) continue; // an emptied area drops out entirely
    parts.push("");
    parts.push(`## ${area.app} · ${area.group}`);
    entries.forEach((f) => parts.push(`- ${f.kind}: ${f.text}`));
  }
  return parts.join("\n") + "\n";
}
