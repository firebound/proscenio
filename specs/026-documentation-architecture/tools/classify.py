"""Wave 0: triage every extracted comment into the 8-destination taxonomy.

Regex buckets the confident destinations; the why/design residual is tagged
route-by-reading because separating tighten-inline / to-module-docstring /
to-architecture / delete-padding genuinely needs reading the surrounding code.
The split is the owner-sign-off artifact gating Wave 2.

Destinations (STUDY B.1): keep-directive, keep-contract, keep-apifact,
delete, to-test-link, to-architecture, route-by-reading.
(tighten-inline / to-assert / to-module-docstring are resolved inside
route-by-reading during the cleanup wave.)
"""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
recs = [json.loads(l) for l in (HERE / "comments.jsonl").read_text(encoding="utf-8").splitlines()]

DIRECTIVE = re.compile(
    r"(type:\s*ignore|noqa|pragma|fmt:\s*(on|off)|mypy:|"                           # py
    r"gdlint:|warning[-_]ignore|@warning_ignore|"                                    # gd
    r"eslint-disable|prettier-ignore|@ts-(ignore|expect-error|nocheck)|//\s*@ts)",  # ts
    re.IGNORECASE)
SPEC = re.compile(r"(specs?/|backlog|\bPR\s*#?\d|#\d{2,4}\b|\bT-REV\d|see\b[^.]*\.md)", re.IGNORECASE)
ARCH_HIST = re.compile(r"\b(formerly|lifted from|moved (from|to|out)|renamed|deduped|"
                       r"both copies|split out|pulled out|factored out|used to (be|live|bubble))\b",
                       re.IGNORECASE)
REGRESSION = re.compile(r"\b(regression|caused a bug|post-?mortem|the bug:|\bB\d fix|"
                        r"caught (in|by).*review|user caught|would (re-?introduce|reintroduce))\b",
                        re.IGNORECASE)
APIFACT = re.compile(r"(bpy\.|np\.|numpy|Blender 4|Blender \d|bottom-up|top-down|flat RGBA|"
                     r"isinstance|EEVEE|BMesh|depsgraph|StructRNA|_RestrictData|foreach_set|"
                     r"matrix_world|find_child|Node\.|batchPlay|UXP|executeAsModal|"
                     r"Godot's|Godot-shaped)", re.IGNORECASE)
CROSS_CUT = re.compile(r"(XZ|picture[- ]plane|golden|exclude_unset|model_dump|format_version|"
                       r"front ortho)", re.IGNORECASE)
DIVIDER = re.compile(r"[-=*_]{4,}")


def strip(text: str, lang: str) -> str:
    t = text.strip()
    for p in ("///", "//", "/**", "/*", "*/", "##", "#"):
        if t.startswith(p):
            t = t[len(p):]
    return t.strip(" *").strip()


def classify(r: dict) -> str:
    text, kind, lang = r["text"], r["kind"], r["lang"]
    body = strip(text, lang)
    if DIRECTIVE.search(text):
        return "keep-directive"
    # contract family: docstrings / doc-comments / jsdoc default to keep-contract
    if kind in ("docstring", "doc-comment", "jsdoc"):
        if SPEC.search(body):
            return "delete"            # spec-ref in a docstring -> strip the ref
        if ARCH_HIST.search(body):
            return "route-by-reading"  # trim history clause
        return "keep-contract"
    if DIVIDER.search(body):
        return "delete"
    if SPEC.search(body):
        return "delete"
    if ARCH_HIST.search(body):
        return "delete"
    if REGRESSION.search(body):
        return "to-test-link"
    if CROSS_CUT.search(body):
        return "to-architecture"
    if APIFACT.search(body):
        return "keep-apifact"
    return "route-by-reading"


for r in recs:
    r["dest"] = classify(r)

(HERE / "classified.jsonl").write_text(
    "\n".join(json.dumps(r, ensure_ascii=False) for r in recs), encoding="utf-8")

overall = Counter(r["dest"] for r in recs)
print("=== split by destination ===")
for dest, c in overall.most_common():
    print(f"  {dest:18} {c:5}")
print(f"  {'TOTAL':18} {len(recs):5}")
print("\n=== by language x destination ===")
lx = Counter((r["lang"], r["dest"]) for r in recs)
for (lang, dest), c in sorted(lx.items()):
    print(f"  {lang:3} {dest:18} {c:5}")
