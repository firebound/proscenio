/**
 * One-shot: rewrite every checklist file through parse -> serialize so the `.md`
 * on disk matches the canonical TS serializer exactly. Run once after the Python
 * migration seeds the unified blocks; thereafter the round-trip is a no-op.
 */

import { existsSync, readFileSync, renameSync, writeFileSync } from "node:fs";
import { join } from "node:path";

import { parseDoc } from "./parse";
import { serializeDoc } from "./serialize";
import { FILES, REMOVED_FILE, defaultStore } from "./store";

function main(): void {
  const store = defaultStore();
  let total = 0;
  for (const file of [...FILES, REMOVED_FILE]) {
    const path = join(store.dir, file);
    if (!existsSync(path)) continue;
    const doc = parseDoc(readFileSync(path, "utf8"));
    const out = serializeDoc(doc);
    const tmp = `${path}.tmp`;
    writeFileSync(tmp, out);
    renameSync(tmp, path);
    const n = doc.groups.reduce((acc, g) => acc + g.items.length, 0);
    total += n;
    console.log(`[normalize] ${file}: ${n} items`);
  }
  console.log(`[normalize] ${total} items canonicalized`);
}

main();
