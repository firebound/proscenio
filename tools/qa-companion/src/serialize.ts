/** Serialize the {@link Doc} model back to a canonical unified `.md`. */

import { type Doc, type Item } from "./format";

function scalar(key: string, value: string): string {
  const v = value.trim();
  return v ? `- ${key}: ${v}` : `- ${key}:`;
}

function noteLines(note: string): string[] {
  return note
    .split("\n")
    .map((l) => l.trim())
    .filter(Boolean);
}

export function serializeBlock(item: Item): string {
  const out: string[] = [`### ${item.id} · ${item.title.trim()}`];
  out.push(scalar("status", item.status));
  out.push(scalar("review", item.review));
  if (item.pre.trim()) out.push(scalar("pre", item.pre));

  const steps = item.steps.map((s) => s.trim()).filter(Boolean);
  if (steps.length) {
    out.push("- steps:");
    steps.forEach((step, i) => out.push(`  ${i + 1}. ${step}`));
  }

  out.push(scalar("observe", item.observe));
  if (item.intent.trim()) out.push(scalar("intent", item.intent));
  if (item.code.trim()) out.push(scalar("code", item.code));

  const note = noteLines(item.note);
  if (note.length === 1) {
    out.push(`- note: ${note[0]}`);
  } else if (note.length > 1) {
    out.push("- note:");
    note.forEach((l) => out.push(`  ${l}`));
  }

  const feedback = item.feedback
    .map((f) => ({ kind: f.kind.trim(), text: f.text.trim() }))
    .filter((f) => f.text);
  if (feedback.length) {
    out.push("- feedback:");
    feedback.forEach((f) => out.push(`  - ${f.kind || "note"}: ${f.text}`));
  }

  const shots = item.shots.map((s) => s.trim()).filter(Boolean);
  if (shots.length) {
    out.push("- shots:");
    shots.forEach((p) => out.push(`  - ${p}`));
  }

  if (item.reason.trim()) out.push(scalar("reason", item.reason));

  return out.join("\n");
}

export function serializeDoc(doc: Doc): string {
  const parts: string[] = [doc.preamble.replace(/\s+$/, "")];
  for (const group of doc.groups) {
    parts.push("");
    parts.push(`## ${group.name}`);
    for (const item of group.items) {
      parts.push("");
      parts.push(serializeBlock(item));
    }
  }
  return parts.join("\n") + "\n";
}
