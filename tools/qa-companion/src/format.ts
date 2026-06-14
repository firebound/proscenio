/**
 * The unified checklist block model.
 *
 * Every manual-test item is one Markdown block:
 *
 *     ### <id> · <title>
 *     - status: pending
 *     - review: keep
 *     - pre: <one line>            (optional)
 *     - steps:                     (optional; numbered sublist)
 *       1. <step>
 *     - observe: <one line>        (the "observe Y")
 *     - intent: <one line>         (optional; the documented intent oracle)
 *     - code: <path:lines>         (optional)
 *     - note: <free text>          (optional; single line, or indented multiline)
 *     - shots:                     (optional; dash sublist of screenshot paths)
 *       - walk-screenshots/<id>-1.png
 *     - reason: <why dropped>      (only in removed.md)
 *
 * Scalar fields are single-line; `steps` / `shots` are sublists; `note` is free
 * multiline. There are no tables, so no pipe-escaping - the format round-trips
 * cleanly through parse -> edit -> serialize.
 */

export const STATUSES = ["pending", "pass", "fail", "blocked", "n/a", "regressed"] as const;
export type Status = (typeof STATUSES)[number];

export const REVIEWS = ["keep", "rephrase", "drop", "todo"] as const;
export type Review = (typeof REVIEWS)[number];

export interface Item {
  id: string;
  title: string;
  /** Did the feature pass the manual check. */
  status: Status;
  /** Verdict on the test itself (curation): keep / rephrase / drop / todo. */
  review: Review;
  pre: string;
  steps: string[];
  /** The expected observation - the "observe Y". */
  observe: string;
  intent: string;
  code: string;
  /** Free-text observation recorded during the walk. */
  note: string;
  /** Screenshot paths, repo-relative (e.g. walk-screenshots/PS-EXPORT-14-1.png). */
  shots: string[];
  /** Why the test was dropped (only set for items archived in removed.md). */
  reason: string;
}

export interface Group {
  name: string;
  items: Item[];
}

export interface Doc {
  /** Everything before the first `## ` group (header + intro), kept verbatim. */
  preamble: string;
  groups: Group[];
}

export function emptyItem(id: string, title: string): Item {
  return {
    id,
    title,
    status: "pending",
    review: "keep",
    pre: "",
    steps: [],
    observe: "",
    intent: "",
    code: "",
    note: "",
    shots: [],
    reason: "",
  };
}

export interface IdParts {
  app: string;
  surface: string;
  seq: string;
}

/** `BL-OUTLN-01` -> `{ app: "BL", surface: "OUTLN", seq: "01" }`. */
export function splitId(id: string): IdParts {
  const parts = id.split("-");
  return { app: parts[0] ?? id, surface: parts[1] ?? "", seq: parts[2] ?? "" };
}
