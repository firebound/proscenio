import { existsSync, mkdtempSync, readFileSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

import { afterEach, describe, expect, it } from "vitest";

import {
  type Store,
  addItem,
  allocateId,
  loadFlat,
  removeItem,
  sanitizeId,
  saveScreenshot,
  upsertItem,
} from "../src/store";

const PNG_1PX =
  "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAAC0lEQVR4nGNgAAIAAAUAAen63NgAAAAASUVORK5CYII=";

const BLENDER_MD = `# Blender - manual-test checklist

intro.

## Outliner panel

### BL-OUTLN-01 · Outliner foldout
- status: pending
- review: keep
- observe: expands then collapses.
- code: outliner.py:1
`;

function freshStore(): Store {
  const dir = mkdtempSync(join(tmpdir(), "walk-store-"));
  writeFileSync(join(dir, "blender.md"), BLENDER_MD);
  return { dir, screenshotDir: join(dir, "walk-screenshots") };
}

let store: Store;
afterEach(() => {
  store = undefined as unknown as Store;
});

describe("store", () => {
  it("loads items flat with their file and group", () => {
    store = freshStore();
    const flat = loadFlat(store);
    expect(flat).toHaveLength(1);
    expect(flat[0]!.id).toBe("BL-OUTLN-01");
    expect(flat[0]!.file).toBe("blender.md");
    expect(flat[0]!.group).toBe("Outliner panel");
  });

  it("persists a status + note edit back to the .md", () => {
    store = freshStore();
    const item = loadFlat(store)[0]!;
    item.status = "fail";
    item.note = "panel did not expand";
    upsertItem(store, item.file, item.group, item);

    const reread = loadFlat(store)[0]!;
    expect(reread.status).toBe("fail");
    expect(reread.note).toBe("panel did not expand");
    expect(readFileSync(join(store.dir, "blender.md"), "utf8")).toContain("- status: fail");
  });

  it("allocates the next sequential id in a group's surface", () => {
    store = freshStore();
    expect(allocateId(store, "blender.md", "Outliner panel")).toBe("BL-OUTLN-02");
    const created = addItem(store, "blender.md", "Outliner panel", "brand new check");
    expect(created.id).toBe("BL-OUTLN-02");
    expect(loadFlat(store)).toHaveLength(2);
    // a second add steps past the one just written
    expect(allocateId(store, "blender.md", "Outliner panel")).toBe("BL-OUTLN-03");
  });

  it("archives a removed item to removed.md with its reason", () => {
    store = freshStore();
    expect(removeItem(store, "BL-OUTLN-01", "duplicate of BL-OUTLN-06")).toBe(true);
    expect(loadFlat(store)).toHaveLength(0);
    const removed = readFileSync(join(store.dir, "removed.md"), "utf8");
    expect(removed).toContain("### BL-OUTLN-01 · Outliner foldout");
    expect(removed).toContain("- reason: duplicate of BL-OUTLN-06");
  });

  it("returns false when removing an unknown id", () => {
    store = freshStore();
    expect(removeItem(store, "BL-NOPE-99", "x")).toBe(false);
    expect(loadFlat(store)).toHaveLength(1);
  });

  it("decodes and writes a pasted screenshot, returning its repo-relative path", () => {
    store = freshStore();
    const path = saveScreenshot(store, "BL-OUTLN-01", PNG_1PX);
    expect(path).toBe("walk-screenshots/BL-OUTLN-01-1.png");
    expect(existsSync(join(store.dir, path))).toBe(true);
    // a second paste does not clobber the first
    expect(saveScreenshot(store, "BL-OUTLN-01", PNG_1PX)).toBe("walk-screenshots/BL-OUTLN-01-2.png");
  });

  it("rejects a non-image / malformed data URL", () => {
    store = freshStore();
    expect(() => saveScreenshot(store, "BL-OUTLN-01", "data:text/plain;base64,QQ==")).toThrow();
    expect(() => saveScreenshot(store, "BL-OUTLN-01", "not a data url")).toThrow();
  });

  it("sanitizes ids against path traversal", () => {
    expect(sanitizeId("BL-OUTLN-01")).toBe("BL-OUTLN-01");
    expect(sanitizeId("../../weird/Name")).toBe("weirdName");
    expect(() => sanitizeId("///")).toThrow();
  });
});
