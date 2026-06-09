"""AST-based duplication scanner for apps/blender.

Goes beyond token copy-paste (PMD CPD) to surface semantic / type-4 clones:
functions that perform the same operation through different syntax. Two signals
are emitted per function so clones can be clustered three ways:

  - skeleton: the AST node-type sequence with identifier and constant values
    abstracted away. Identical skeletons are type-1/2/3 clones (renames,
    reordered locals, swapped literals) that CPD may still miss.
  - call multiset: the dotted call targets the function invokes (bpy.data...,
    helper names, ...). High overlap with a *different* skeleton is the
    type-4 signal - same operation, different control flow.
  - returns / arg shape: coarse intent grouping.

Usage:
    python specs/025-code-duplication/tools/ast_scan.py > specs/025-code-duplication/raw/ast-report.txt
    python specs/025-code-duplication/tools/ast_scan.py --json specs/025-code-duplication/raw/ast-inventory.json
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import sys
from dataclasses import dataclass, field
from itertools import combinations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3] / "apps" / "blender"
SKIP_DIRS = {
    "__pycache__", ".mypy_cache", ".pytest_cache", ".ruff_cache", "wheels",
}


def dotted(node: ast.expr) -> str:
    """Best-effort dotted path for a call target (a.b.c.method)."""
    parts: list[str] = []
    cur: ast.expr | None = node
    while isinstance(cur, ast.Attribute):
        parts.append(cur.attr)
        cur = cur.value
    if isinstance(cur, ast.Name):
        parts.append(cur.id)
    elif isinstance(cur, ast.Call):
        parts.append("()")
    parts.reverse()
    return ".".join(parts) if parts else "<expr>"


class FuncVisitor(ast.NodeVisitor):
    """Collects skeleton tokens and call targets for one function body."""

    def __init__(self) -> None:
        self.skeleton: list[str] = []
        self.calls: list[str] = []

    def generic_visit(self, node: ast.AST) -> None:
        t = type(node).__name__
        if isinstance(node, ast.Name):
            self.skeleton.append("Name")
        elif isinstance(node, ast.Constant):
            self.skeleton.append("Const")
        elif isinstance(node, ast.arg):
            self.skeleton.append("arg")
        else:
            self.skeleton.append(t)
        if isinstance(node, ast.Call):
            self.calls.append(dotted(node.func))
        super().generic_visit(node)


@dataclass
class FuncInfo:
    file: str
    qual: str
    lineno: int
    end: int
    nargs: int
    nstmt: int
    is_test: bool
    skel_hash: str
    skel_len: int
    calls: tuple[str, ...]
    call_set: frozenset[str] = field(default_factory=frozenset)


def walk_functions(tree: ast.Module, relpath: str, is_test: bool) -> list[FuncInfo]:
    out: list[FuncInfo] = []

    class Top(ast.NodeVisitor):
        def __init__(self) -> None:
            self.stack: list[str] = []

        def _emit(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
            v = FuncVisitor()
            for child in node.body:
                v.visit(child)
            skel = ",".join(v.skeleton)
            h = hashlib.sha1(skel.encode()).hexdigest()[:12]
            qual = ".".join([*self.stack, node.name])
            calls = tuple(v.calls)
            out.append(
                FuncInfo(
                    file=relpath,
                    qual=qual,
                    lineno=node.lineno,
                    end=getattr(node, "end_lineno", node.lineno) or node.lineno,
                    nargs=len(node.args.args) + len(node.args.kwonlyargs),
                    nstmt=len(node.body),
                    is_test=is_test,
                    skel_hash=h,
                    skel_len=len(v.skeleton),
                    calls=calls,
                    call_set=frozenset(c for c in calls if c != "<expr>"),
                )
            )

        def visit_ClassDef(self, node: ast.ClassDef) -> None:
            self.stack.append(node.name)
            self.generic_visit(node)
            self.stack.pop()

        def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
            self._emit(node)
            self.stack.append(node.name)
            self.generic_visit(node)
            self.stack.pop()

        def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
            self.visit_FunctionDef(node)  # type: ignore[arg-type]

    Top().visit(tree)
    return out


def collect() -> list[FuncInfo]:
    funcs: list[FuncInfo] = []
    for path in sorted(ROOT.rglob("*.py")):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        rel = path.relative_to(ROOT).as_posix()
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError as exc:  # pragma: no cover
            print(f"# parse error {rel}: {exc}", file=sys.stderr)
            continue
        is_test = rel.startswith("tests/")
        funcs.extend(walk_functions(tree, rel, is_test))
    return funcs


def jaccard(a: frozenset[str], b: frozenset[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def report(funcs: list[FuncInfo]) -> None:
    prod = [f for f in funcs if not f.is_test]
    print(f"# AST inventory: {len(funcs)} functions ({len(prod)} production, "
          f"{len(funcs) - len(prod)} test)\n")

    # --- 1. exact skeleton clusters (type-1/2/3) ---
    by_skel: dict[str, list[FuncInfo]] = {}
    for f in prod:
        if f.skel_len >= 12:  # skip trivial stubs
            by_skel.setdefault(f.skel_hash, []).append(f)
    skel_groups = sorted(
        (g for g in by_skel.values() if len(g) > 1),
        key=lambda g: (-g[0].skel_len, -len(g)),
    )
    print(f"## Structural clones (identical AST skeleton, production, >=12 nodes): "
          f"{len(skel_groups)} groups\n")
    for g in skel_groups:
        locs = ", ".join(f"{f.file}:{f.lineno} {f.qual}" for f in g)
        print(f"- [{len(g)}x, {g[0].skel_len} nodes] {locs}")
    print()

    # --- 2. type-4 candidates: high call-set overlap, different skeleton ---
    # Only compare functions with a meaningful call set; skip identical skeletons
    # (already covered above). Pairwise within production.
    rich = [f for f in prod if len(f.call_set) >= 4]
    rich.sort(key=lambda f: f.file)
    pairs: list[tuple[float, FuncInfo, FuncInfo]] = []
    for a, b in combinations(rich, 2):
        if a.skel_hash == b.skel_hash:
            continue
        j = jaccard(a.call_set, b.call_set)
        if j >= 0.6:
            pairs.append((j, a, b))
    pairs.sort(key=lambda p: -p[0])
    print(f"## Type-4 candidates (call-set overlap >=0.6, different skeleton): "
          f"{len(pairs)} pairs\n")
    for j, a, b in pairs:
        shared = ", ".join(sorted(a.call_set & b.call_set))
        print(f"- [{j:.2f}] {a.file}:{a.lineno} {a.qual}  <->  "
              f"{b.file}:{b.lineno} {b.qual}")
        print(f"    shared calls: {shared}")
    print()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", type=Path, default=None)
    args = ap.parse_args()
    funcs = collect()
    if args.json:
        args.json.write_text(
            json.dumps(
                [
                    {
                        "file": f.file, "qual": f.qual, "lineno": f.lineno,
                        "end": f.end, "nargs": f.nargs, "nstmt": f.nstmt,
                        "is_test": f.is_test, "skel_hash": f.skel_hash,
                        "skel_len": f.skel_len, "calls": list(f.calls),
                    }
                    for f in funcs
                ],
                indent=1,
            ),
            encoding="utf-8",
        )
        print(f"wrote {args.json} ({len(funcs)} functions)", file=sys.stderr)
    report(funcs)


if __name__ == "__main__":
    main()
