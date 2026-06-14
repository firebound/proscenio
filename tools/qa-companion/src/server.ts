/**
 * Local-only HTTP server: serves the walk UI and the round-trip API.
 *
 * The UI POSTs every change straight back to the checklist `.md` files, so the
 * walk + curation persists synchronously into the repo (git-reviewable, no
 * separate export). Bound to 127.0.0.1.
 *
 *     pnpm walk            # then open http://127.0.0.1:8040
 */

import { type IncomingMessage, type ServerResponse, createServer } from "node:http";
import { existsSync, readFileSync } from "node:fs";
import { extname, join, normalize, resolve } from "node:path";
import { dirname } from "node:path";
import { fileURLToPath } from "node:url";

import { FEEDBACK_KINDS, REVIEWS, STATUSES, type Item, emptyItem } from "./format";
import {
  type Store,
  addItem,
  defaultStore,
  loadFlat,
  removeItem,
  saveScreenshot,
  upsertItem,
} from "./store";

const HERE = dirname(fileURLToPath(import.meta.url));
const PUBLIC_DIR = resolve(HERE, "../public");
const PORT = Number.parseInt(process.env["PORT"] ?? "8040", 10);

const CONTENT_TYPES: Record<string, string> = {
  ".html": "text/html; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".png": "image/png",
  ".jpg": "image/jpeg",
  ".jpeg": "image/jpeg",
  ".webp": "image/webp",
};

function sendJson(res: ServerResponse, code: number, body: unknown): void {
  const data = JSON.stringify(body);
  res.writeHead(code, { "Content-Type": "application/json; charset=utf-8" });
  res.end(data);
}

function readBody(req: IncomingMessage): Promise<unknown> {
  return new Promise((resolveBody, rejectBody) => {
    const chunks: Buffer[] = [];
    req.on("data", (c: Buffer) => chunks.push(c));
    req.on("end", () => {
      const raw = Buffer.concat(chunks).toString("utf8");
      if (!raw) {
        resolveBody({});
        return;
      }
      try {
        resolveBody(JSON.parse(raw));
      } catch (err) {
        rejectBody(err instanceof Error ? err : new Error(String(err)));
      }
    });
    req.on("error", rejectBody);
  });
}

/** Coerce an untrusted payload into a valid Item (defaults via emptyItem). */
function coerceItem(raw: Record<string, unknown>): Item {
  const id = typeof raw["id"] === "string" ? raw["id"] : "";
  const item = emptyItem(id, typeof raw["title"] === "string" ? raw["title"] : "");
  const status = raw["status"];
  if (typeof status === "string" && (STATUSES as readonly string[]).includes(status)) {
    item.status = status as Item["status"];
  }
  const review = raw["review"];
  if (typeof review === "string" && (REVIEWS as readonly string[]).includes(review)) {
    item.review = review as Item["review"];
  }
  for (const key of ["pre", "observe", "intent", "code", "note", "reason"] as const) {
    const v = raw[key];
    if (typeof v === "string") item[key] = v;
  }
  if (Array.isArray(raw["steps"])) item.steps = raw["steps"].filter((s) => typeof s === "string");
  if (Array.isArray(raw["shots"])) item.shots = raw["shots"].filter((s) => typeof s === "string");
  if (Array.isArray(raw["feedback"])) {
    item.feedback = raw["feedback"]
      .filter((f): f is Record<string, unknown> => typeof f === "object" && f !== null)
      .map((f) => ({
        kind: typeof f["kind"] === "string" ? f["kind"] : "note",
        text: typeof f["text"] === "string" ? f["text"] : "",
      }))
      .filter((f) => f.text);
  }
  return item;
}

function serveStatic(res: ServerResponse, baseDir: string, urlPath: string): void {
  const rel = normalize(decodeURIComponent(urlPath)).replace(/^(\.\.[/\\])+/, "");
  const filePath = join(baseDir, rel);
  if (!filePath.startsWith(baseDir) || !existsSync(filePath)) {
    res.writeHead(404).end("not found");
    return;
  }
  const type = CONTENT_TYPES[extname(filePath).toLowerCase()] ?? "application/octet-stream";
  res.writeHead(200, { "Content-Type": type });
  res.end(readFileSync(filePath));
}

function handleApi(store: Store, req: IncomingMessage, res: ServerResponse, path: string): void {
  if (req.method === "GET" && path === "/api/state") {
    const items = loadFlat(store);
    const groupsByFile: Record<string, string[]> = {};
    for (const it of items) {
      (groupsByFile[it.file] ??= []).push(it.group);
    }
    for (const file of Object.keys(groupsByFile)) {
      groupsByFile[file] = [...new Set(groupsByFile[file])];
    }
    sendJson(res, 200, { items, statuses: STATUSES, reviews: REVIEWS, feedbackKinds: FEEDBACK_KINDS, groupsByFile });
    return;
  }

  if (req.method === "POST") {
    void readBody(req)
      .then((body) => {
        const raw = (body ?? {}) as Record<string, unknown>;
        if (path === "/api/item") {
          const file = String(raw["file"] ?? "");
          const group = String(raw["group"] ?? "");
          const item = coerceItem((raw["item"] ?? {}) as Record<string, unknown>);
          if (!item.id) {
            const created = addItem(store, file, group, item.title);
            sendJson(res, 200, { ok: true, item: created });
            return;
          }
          upsertItem(store, file, group, item);
          sendJson(res, 200, { ok: true, item });
          return;
        }
        if (path === "/api/remove") {
          const ok = removeItem(store, String(raw["id"] ?? ""), String(raw["reason"] ?? ""));
          sendJson(res, ok ? 200 : 404, { ok });
          return;
        }
        if (path === "/api/screenshot") {
          const result = saveScreenshot(store, String(raw["id"] ?? ""), String(raw["dataUrl"] ?? ""));
          sendJson(res, 200, { ok: true, path: result });
          return;
        }
        sendJson(res, 404, { ok: false, error: "unknown endpoint" });
      })
      .catch((err: unknown) => {
        sendJson(res, 400, { ok: false, error: err instanceof Error ? err.message : String(err) });
      });
    return;
  }

  sendJson(res, 405, { ok: false, error: "method not allowed" });
}

function main(): void {
  const store = defaultStore();
  const server = createServer((req, res) => {
    const path = (req.url ?? "/").split("?")[0] ?? "/";
    if (path.startsWith("/api/")) {
      handleApi(store, req, res, path);
      return;
    }
    if (path.startsWith("/walk-screenshots/")) {
      serveStatic(res, store.screenshotDir, path.slice("/walk-screenshots/".length));
      return;
    }
    serveStatic(res, PUBLIC_DIR, path === "/" ? "index.html" : path);
  });

  server.listen(PORT, "127.0.0.1", () => {
    console.log(`[walk] QA Companion at http://127.0.0.1:${PORT}`);
    console.log("[walk] changes persist straight into the checklist .md files");
    console.log("[walk] Ctrl+C to stop");
  });
}

main();
