/** Parse a unified checklist `.md` into the {@link Doc} model. */

import {
  type Doc,
  type Group,
  type Item,
  type Review,
  type Status,
  REVIEWS,
  STATUSES,
  emptyItem,
} from "./format";

const STATUS_SET = new Set<string>(STATUSES);
const REVIEW_SET = new Set<string>(REVIEWS);

const BLOCK_RE = /^###\s+(\S+)\s+·\s+(.*)$/;
const FIELD_RE = /^-\s+([a-z]+):\s?(.*)$/;

export function parseDoc(text: string): Doc {
  // Tolerate CRLF: a Windows editor or text-mode writer can introduce \r\n,
  // and a stray \r would otherwise ride on every line and break field matching.
  const lines = text.split(/\r?\n/);
  let firstStruct = lines.findIndex((l) => l.startsWith("## ") || l.startsWith("### "));
  if (firstStruct < 0) firstStruct = lines.length;
  const preamble = lines.slice(0, firstStruct).join("\n");

  const groups: Group[] = [];
  let current: Group | null = null;
  let i = firstStruct;

  while (i < lines.length) {
    const line = lines[i] ?? "";
    if (line.startsWith("## ")) {
      current = { name: line.slice(3).trim(), items: [] };
      groups.push(current);
      i += 1;
    } else if (line.startsWith("### ")) {
      const { item, next } = parseBlock(lines, i);
      if (!current) {
        current = { name: "", items: [] };
        groups.push(current);
      }
      current.items.push(item);
      i = next;
    } else {
      i += 1;
    }
  }

  return { preamble, groups };
}

function parseBlock(lines: string[], start: number): { item: Item; next: number } {
  const head = lines[start] ?? "";
  const match = BLOCK_RE.exec(head);
  const id = match ? match[1]! : head.slice(4).trim();
  const title = match ? match[2]!.trim() : "";
  const item = emptyItem(id, title);

  let i = start + 1;
  while (i < lines.length) {
    const line = lines[i] ?? "";
    if (line.startsWith("### ") || line.startsWith("## ")) break;
    if (line.trim() === "") {
      i += 1; // the blank line separating blocks ends this one
      break;
    }
    const field = FIELD_RE.exec(line);
    if (!field) {
      i += 1; // tolerate stray lines rather than dropping the block
      continue;
    }
    const key = field[1]!;
    const inline = field[2]!;
    i += 1;
    const cont: string[] = [];
    while (i < lines.length && lines[i]!.startsWith("  ")) {
      cont.push(lines[i]!.slice(2));
      i += 1;
    }
    applyField(item, key, inline, cont);
  }

  return { item, next: i };
}

function joinScalar(inline: string, cont: string[]): string {
  return [inline, ...cont]
    .map((s) => s.trim())
    .filter(Boolean)
    .join(" ");
}

function applyField(item: Item, key: string, inline: string, cont: string[]): void {
  switch (key) {
    case "status":
      item.status = STATUS_SET.has(inline) ? (inline as Status) : "pending";
      break;
    case "review":
      item.review = REVIEW_SET.has(inline) ? (inline as Review) : "keep";
      break;
    case "pre":
      item.pre = joinScalar(inline, cont);
      break;
    case "observe":
      item.observe = joinScalar(inline, cont);
      break;
    case "intent":
      item.intent = joinScalar(inline, cont);
      break;
    case "code":
      item.code = joinScalar(inline, cont);
      break;
    case "reason":
      item.reason = joinScalar(inline, cont);
      break;
    case "note": {
      const lines = [inline, ...cont].filter((l) => l.trim() !== "");
      item.note = lines.join("\n");
      break;
    }
    case "steps": {
      const steps = cont.map((l) => l.replace(/^\d+\.\s+/, "").trim()).filter(Boolean);
      if (inline.trim()) steps.unshift(inline.trim());
      item.steps = steps;
      break;
    }
    case "shots": {
      const shots = cont.map((l) => l.replace(/^-\s+/, "").trim()).filter(Boolean);
      if (inline.trim()) shots.unshift(inline.trim());
      item.shots = shots;
      break;
    }
    default:
      break;
  }
}
