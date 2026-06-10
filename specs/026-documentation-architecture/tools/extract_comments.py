"""Wave 0: extract every comment and docstring from hand-authored source.

Languages: Python (.py), GDScript (.gd), TypeScript (.ts/.tsx). Generated files
are excluded by path and by an AUTO-GENERATED header in the first 3 lines, so the
codegen emitters (which carry that string mid-file, as a template) stay in scope.

Output: comments.jsonl, one record per comment/docstring:
  {file, line, lang, kind, text}
kind in {comment, docstring, doc-comment, block, jsdoc}.
"""

from __future__ import annotations

import ast
import io
import json
import subprocess
import tokenize
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]

EXCLUDE_PREFIXES = (
    "apps/godot/addons/proscenio/schema_bindings/",
    "apps/photoshop/src/schema_bindings/",
    "examples/generated/",
    "docs/content/",
    "packages/models/schemas/",
)


def tracked(*globs: str) -> list[str]:
    out = subprocess.check_output(["git", "ls-files", *globs], cwd=REPO, text=True)
    return [l for l in out.splitlines() if l.strip()]


def is_generated(rel: str, text: str) -> bool:
    if any(rel.startswith(p) for p in EXCLUDE_PREFIXES):
        return True
    head = "\n".join(text.splitlines()[:3])
    return "AUTO-GENERATED" in head


# ---------------- Python ----------------

def extract_py(rel: str, src: str, rec: list[dict]) -> None:
    try:
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                if ast.get_docstring(node, clean=False) is not None:
                    body0 = node.body[0]
                    if isinstance(body0, ast.Expr) and hasattr(body0, "lineno"):
                        rec.append({"file": rel, "line": body0.lineno, "lang": "py",
                                    "kind": "docstring", "text": ast.get_docstring(node, clean=False)[:400]})
    except SyntaxError:
        # Unparseable file: skip docstrings; the tokenizer pass below still runs.
        pass
    try:
        for tok in tokenize.generate_tokens(io.StringIO(src).readline):
            if tok.type == tokenize.COMMENT:
                rec.append({"file": rel, "line": tok.start[0], "lang": "py",
                            "kind": "comment", "text": tok.string})
    except (tokenize.TokenError, IndentationError):
        # Best-effort: a malformed file yields no comments rather than aborting the run.
        pass


# ---------------- GDScript ----------------

def extract_gd(rel: str, src: str, rec: list[dict]) -> None:
    """Line scan that skips `#` inside string literals.

    Tracks triple-quoted strings across lines; single/double strings within a
    line. Finds the first `#` that is not inside a string and treats the rest of
    the line as a comment (`##` is a GDScript doc-comment).
    """
    in_triple: str | None = None
    for n, line in enumerate(src.splitlines(), 1):
        i, hash_at, in_str = 0, -1, None
        while i < len(line):
            three = line[i:i + 3]
            if in_triple:
                if three == in_triple:
                    in_triple = None
                    i += 3
                    continue
                i += 1
                continue
            if in_str:
                if line[i] == "\\":
                    i += 2
                    continue
                if line[i] == in_str:
                    in_str = None
                i += 1
                continue
            if three in ('"""', "'''"):
                in_triple = three
                i += 3
                continue
            c = line[i]
            if c in ('"', "'"):
                in_str = c
            elif c == "#":
                hash_at = i
                break
            i += 1
        if hash_at >= 0:
            body = line[hash_at:]
            kind = "doc-comment" if body.startswith("##") else "comment"
            rec.append({"file": rel, "line": n, "lang": "gd", "kind": kind, "text": body.rstrip()})


# ---------------- TypeScript ----------------

def extract_ts(rel: str, src: str, rec: list[dict]) -> None:
    """Char state machine: strings (', \", `), // line, /* */ block, /** jsdoc."""
    i, n, line = 0, len(src), 1
    state = "code"
    buf_start = 0
    buf_line = 1
    while i < n:
        c = src[i]
        nxt = src[i + 1] if i + 1 < n else ""
        if c == "\n":
            line += 1
        if state == "code":
            if c in ("'", '"', "`"):
                state = ("str", c)
            elif c == "/" and nxt == "/":
                state, buf_start, buf_line = "line", i, line
                i += 2
                continue
            elif c == "/" and nxt == "*":
                state = "jsdoc" if (i + 2 < n and src[i + 2] == "*") else "block"
                buf_start, buf_line = i, line
                i += 2
                continue
        elif isinstance(state, tuple):  # in string
            q = state[1]
            if c == "\\":
                i += 2
                continue
            if c == q:
                state = "code"
        elif state == "line":
            if c == "\n":
                rec.append({"file": rel, "line": buf_line, "lang": "ts", "kind": "comment",
                            "text": src[buf_start:i].rstrip()})
                state = "code"
        elif state in ("block", "jsdoc"):
            if c == "*" and nxt == "/":
                kind = "jsdoc" if state == "jsdoc" else "block"
                rec.append({"file": rel, "line": buf_line, "lang": "ts", "kind": kind,
                            "text": src[buf_start:i + 2][:400]})
                state = "code"
                i += 2
                continue
        i += 1
    if state == "line":
        rec.append({"file": rel, "line": buf_line, "lang": "ts", "kind": "comment",
                    "text": src[buf_start:].rstrip()})


def main() -> None:
    rec: list[dict] = []
    files = tracked("*.py", "*.gd", "*.ts", "*.tsx")
    n_files, n_excluded = 0, 0
    for rel in files:
        path = REPO / rel
        try:
            src = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, FileNotFoundError):
            continue
        if is_generated(rel, src):
            n_excluded += 1
            continue
        n_files += 1
        ext = path.suffix
        if ext == ".py":
            extract_py(rel, src, rec)
        elif ext == ".gd":
            extract_gd(rel, src, rec)
        else:
            extract_ts(rel, src, rec)

    out = Path(__file__).resolve().parent / "comments.jsonl"
    with out.open("w", encoding="utf-8") as fh:
        for r in rec:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")

    from collections import Counter
    by_lang = Counter((r["lang"], r["kind"]) for r in rec)
    print(f"scanned {n_files} files, excluded {n_excluded} generated")
    for (lang, kind), c in sorted(by_lang.items()):
        print(f"  {lang:3} {kind:12} {c}")
    print(f"total records: {len(rec)} -> {out}")


if __name__ == "__main__":
    main()
