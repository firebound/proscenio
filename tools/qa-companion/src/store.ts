/**
 * Filesystem store: the checklist `.md` files are the source of truth.
 *
 * Every mutation re-serializes the whole owning file atomically, so the `.md`
 * on disk is always the canonical render of the model - reviewable in git.
 */

import { Buffer } from "node:buffer";
import { existsSync, mkdirSync, readFileSync, renameSync, writeFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import { type Doc, type Feedback, type Item, emptyItem, splitId } from "./format";
import { type Area, FEEDBACK_PREAMBLE, parseFeedback, serializeFeedback } from "./feedback";
import { parseDoc } from "./parse";
import { serializeDoc } from "./serialize";

export const FILES = ["blender.md", "photoshop.md", "godot.md", "flows.md"] as const;
export const REMOVED_FILE = "removed.md";
export const FEEDBACK_FILE = "feedback.md";

const APP_BY_FILE: Record<string, string> = {
  "blender.md": "BL",
  "photoshop.md": "PS",
  "godot.md": "GD",
  "flows.md": "FLOW",
};

const FILE_BY_APP: Record<string, string> = Object.fromEntries(
  Object.entries(APP_BY_FILE).map(([file, app]) => [app, file]),
);

/** Stable key for an area/panel, matching the client's `file||group`. */
export function areaKey(file: string, group: string): string {
  return `${file}||${group}`;
}

export interface FlatItem extends Item {
  file: string;
  group: string;
}

export interface Store {
  /** Directory holding the checklist `.md` files. */
  dir: string;
  /** Directory for pasted screenshots. */
  screenshotDir: string;
}

export function defaultStore(): Store {
  // The companion owns its data: the checklist surface and screenshots live in
  // this package (next to src/), not in a numbered spec folder.
  const here = dirname(fileURLToPath(import.meta.url));
  const pkgRoot = resolve(here, "..");
  return { dir: join(pkgRoot, "checklist"), screenshotDir: join(pkgRoot, "walk-screenshots") };
}

function atomicWrite(path: string, data: string | Buffer): void {
  mkdirSync(dirname(path), { recursive: true });
  const tmp = `${path}.tmp`;
  writeFileSync(tmp, data);
  renameSync(tmp, path);
}

function readDoc(dir: string, file: string): Doc {
  return parseDoc(readFileSync(join(dir, file), "utf8"));
}

export function loadFlat(store: Store): FlatItem[] {
  const out: FlatItem[] = [];
  for (const file of FILES) {
    if (!existsSync(join(store.dir, file))) continue;
    const doc = readDoc(store.dir, file);
    for (const group of doc.groups) {
      for (const item of group.items) {
        out.push({ ...item, file, group: group.name });
      }
    }
  }
  return out;
}

/** Load all panel feedback, keyed by `file||group` (the client's area key). */
export function loadFeedback(store: Store): Record<string, Feedback[]> {
  const path = join(store.dir, FEEDBACK_FILE);
  if (!existsSync(path)) return {};
  const doc = parseFeedback(readFileSync(path, "utf8"));
  const out: Record<string, Feedback[]> = {};
  for (const area of doc.areas) {
    const file = FILE_BY_APP[area.app];
    if (!file) continue; // unknown app code: skip rather than mis-key
    out[areaKey(file, area.group)] = area.feedback;
  }
  return out;
}

/** Replace one area's feedback list, then persist feedback.md (empty = remove). */
export function upsertFeedback(store: Store, file: string, group: string, feedback: Feedback[]): void {
  const app = APP_BY_FILE[file];
  if (!app) throw new Error(`unknown checklist file: ${file}`);

  const path = join(store.dir, FEEDBACK_FILE);
  const doc = existsSync(path)
    ? parseFeedback(readFileSync(path, "utf8"))
    : { preamble: FEEDBACK_PREAMBLE, areas: [] as Area[] };

  const clean = feedback
    .map((f) => ({ kind: f.kind.trim() || "note", text: f.text.trim() }))
    .filter((f) => f.text);

  const idx = doc.areas.findIndex((a) => a.app === app && a.group === group);
  if (clean.length === 0) {
    if (idx >= 0) doc.areas.splice(idx, 1);
  } else if (idx >= 0) {
    doc.areas[idx]!.feedback = clean;
  } else {
    doc.areas.push({ app, group, feedback: clean });
  }
  atomicWrite(path, serializeFeedback(doc));
}

/** Insert or replace an item in `file`/`group`, then persist that file. */
export function upsertItem(store: Store, file: string, group: string, item: Item): void {
  const doc = readDoc(store.dir, file);
  for (const g of doc.groups) {
    const idx = g.items.findIndex((x) => x.id === item.id);
    if (idx >= 0) {
      g.items[idx] = item;
      atomicWrite(join(store.dir, file), serializeDoc(doc));
      return;
    }
  }
  let target = doc.groups.find((g) => g.name === group);
  if (!target) {
    target = { name: group, items: [] };
    doc.groups.push(target);
  }
  target.items.push(item);
  atomicWrite(join(store.dir, file), serializeDoc(doc));
}

/** Move an item out of its checklist into removed.md with a reason. */
export function removeItem(store: Store, id: string, reason: string): boolean {
  let moved: Item | null = null;
  for (const file of FILES) {
    if (!existsSync(join(store.dir, file))) continue;
    const doc = readDoc(store.dir, file);
    let changed = false;
    for (const g of doc.groups) {
      const idx = g.items.findIndex((x) => x.id === id);
      if (idx >= 0) {
        moved = { ...g.items[idx]!, reason: reason.trim() };
        g.items.splice(idx, 1);
        changed = true;
        break;
      }
    }
    if (changed) {
      atomicWrite(join(store.dir, file), serializeDoc(doc));
      break;
    }
  }
  if (!moved) return false;

  const removedPath = join(store.dir, REMOVED_FILE);
  const doc: Doc = existsSync(removedPath)
    ? parseDoc(readFileSync(removedPath, "utf8"))
    : { preamble: "# Removed tests\n", groups: [] };
  let group = doc.groups.find((g) => g.name === "Removed");
  if (!group) {
    group = { name: "Removed", items: [] };
    doc.groups.push(group);
  }
  group.items.push(moved);
  atomicWrite(removedPath, serializeDoc(doc));
  return true;
}

/** Allocate the next free `<APP>-<SURFACE>-<NN>` id for a new item in a group. */
export function allocateId(store: Store, file: string, group: string): string {
  const app = APP_BY_FILE[file] ?? "XX";
  const flat = loadFlat(store);

  const surfaceCount = new Map<string, number>();
  for (const it of flat) {
    if (it.file === file && it.group === group) {
      const surface = splitId(it.id).surface;
      if (surface) surfaceCount.set(surface, (surfaceCount.get(surface) ?? 0) + 1);
    }
  }
  const surface =
    [...surfaceCount.entries()].sort((a, b) => b[1] - a[1])[0]?.[0] ?? "NEW";

  let max = 0;
  for (const it of flat) {
    const parts = splitId(it.id);
    if (parts.app === app && parts.surface === surface) {
      const n = Number.parseInt(parts.seq, 10);
      if (!Number.isNaN(n)) max = Math.max(max, n);
    }
  }
  return `${app}-${surface}-${String(max + 1).padStart(2, "0")}`;
}

/** Create an empty item with an allocated id, persisted into file/group. */
export function addItem(store: Store, file: string, group: string, title: string): Item {
  const item = emptyItem(allocateId(store, file, group), title.trim() || "new test");
  upsertItem(store, file, group, item);
  return item;
}

export function sanitizeId(id: string): string {
  const safe = id.replace(/[^A-Za-z0-9_-]/g, "");
  if (!safe) throw new Error("id has no filename-safe characters");
  return safe;
}

const DATA_URL_RE = /^data:image\/(png|jpe?g|webp);base64,(.+)$/s;

/** Decode a base64 image data URL, write it under screenshotDir, return its path. */
export function saveScreenshot(store: Store, id: string, dataUrl: string): string {
  const match = DATA_URL_RE.exec(dataUrl.trim());
  if (!match) throw new Error("not a base64 image data URL");
  let ext = match[1]!.toLowerCase();
  if (ext === "jpeg") ext = "jpg";
  const raw = Buffer.from(match[2]!, "base64");
  if (raw.length === 0) throw new Error("empty image payload");

  const safe = sanitizeId(id);
  mkdirSync(store.screenshotDir, { recursive: true });
  let n = 1;
  let dest = join(store.screenshotDir, `${safe}-${n}.${ext}`);
  while (existsSync(dest)) {
    n += 1;
    dest = join(store.screenshotDir, `${safe}-${n}.${ext}`);
  }
  atomicWrite(dest, raw);
  return `walk-screenshots/${safe}-${n}.${ext}`;
}
