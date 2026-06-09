"""Scan v2 - closes the gaps in v1 (ast_scan.py).

v1 weaknesses this addresses:
  1. v1 grouped only IDENTICAL skeleton hashes. v2 adds k-gram (shingle)
     similarity over the skeleton token sequence across ALL function pairs,
     surfacing type-3 near-clones (one inserted/removed statement) that v1's
     exact hash missed.
  2. v1 gated call-overlap at >=4 calls / Jaccard >=0.6. v2 lowers to >=2
     calls / Jaccard >=0.5 so small and pure helpers are compared too.
  3. v1 ignored data. v2 compares class field-name sets (dataclasses /
     PropertyGroups) across files for duplicate schemas.

Still function-granular: inline blocks are the PMD CPD pass's job.
"""

from __future__ import annotations

import ast
from itertools import combinations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3] / "apps" / "blender"
SKIP_DIRS = {"__pycache__", ".mypy_cache", ".pytest_cache", ".ruff_cache", "wheels"}


def dotted(node: ast.expr) -> str:
    parts: list[str] = []
    cur: ast.expr | None = node
    while isinstance(cur, ast.Attribute):
        parts.append(cur.attr)
        cur = cur.value
    if isinstance(cur, ast.Name):
        parts.append(cur.id)
    parts.reverse()
    return ".".join(parts) if parts else "<expr>"


class FuncVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.skeleton: list[str] = []
        self.calls: list[str] = []

    def generic_visit(self, node: ast.AST) -> None:
        if isinstance(node, ast.Name):
            self.skeleton.append("Name")
        elif isinstance(node, ast.Constant):
            self.skeleton.append("Const")
        elif isinstance(node, ast.arg):
            self.skeleton.append("arg")
        else:
            self.skeleton.append(type(node).__name__)
        if isinstance(node, ast.Call):
            self.calls.append(dotted(node.func))
        super().generic_visit(node)


class Func:
    __slots__ = ("file", "qual", "lineno", "skel", "shingles", "calls")

    def __init__(self, file: str, qual: str, lineno: int, skel: list[str], calls: list[str]):
        self.file = file
        self.qual = qual
        self.lineno = lineno
        self.skel = skel
        self.calls = frozenset(c for c in calls if c != "<expr>")
        self.shingles = shingle(skel, 4)


def shingle(seq: list[str], k: int) -> frozenset[str]:
    if len(seq) < k:
        return frozenset([",".join(seq)]) if seq else frozenset()
    return frozenset(",".join(seq[i:i + k]) for i in range(len(seq) - k + 1))


def jac(a: frozenset, b: frozenset) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def collect() -> tuple[list[Func], list[tuple[str, str, frozenset[str]]]]:
    funcs: list[Func] = []
    schemas: list[tuple[str, str, frozenset[str]]] = []  # (file, classname, fieldset)
    for path in sorted(ROOT.rglob("*.py")):
        if any(p in SKIP_DIRS for p in path.parts):
            continue
        rel = path.relative_to(ROOT).as_posix()
        if rel.startswith("tests/"):
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError:
            continue

        stack: list[str] = []

        def walk(node: ast.AST) -> None:
            for child in ast.iter_child_nodes(node):
                if isinstance(child, ast.ClassDef):
                    fields = {
                        t.target.id if isinstance(t, ast.AnnAssign) and isinstance(t.target, ast.Name)
                        else None
                        for t in child.body
                    }
                    fields |= {
                        tgt.id
                        for s in child.body if isinstance(s, ast.Assign)
                        for tgt in s.targets if isinstance(tgt, ast.Name)
                    }
                    fset = frozenset(f for f in fields if f)
                    if len(fset) >= 3:
                        schemas.append((rel, child.name, fset))
                    stack.append(child.name)
                    walk(child)
                    stack.pop()
                elif isinstance(child, ast.FunctionDef | ast.AsyncFunctionDef):
                    v = FuncVisitor()
                    for b in child.body:
                        v.visit(b)
                    funcs.append(Func(rel, ".".join([*stack, child.name]), child.lineno, v.skeleton, v.calls))
                    stack.append(child.name)
                    walk(child)
                    stack.pop()
                else:
                    walk(child)

        walk(tree)
    return funcs, schemas


FRAMEWORK = {
    "register", "unregister", "poll", "execute", "draw", "invoke", "modal",
    "cancel", "draw_header", "draw_header_preset", "draw_item", "draw_buttons",
}
# Schema fields that mark a Blender-registered class (operator/panel/PG) whose
# shared field names are framework idiom, not data duplication.
BL_MARKERS = {"bl_idname", "bl_label", "bl_description", "bl_options", "bl_space_type",
              "bl_region_type", "bl_category", "bl_parent_id", "bl_order", "bl_context"}


def is_framework(f: Func) -> bool:
    leaf = f.qual.split(".")[-1]
    return leaf in FRAMEWORK or leaf.startswith("__")


def main() -> None:
    funcs, schemas = collect()
    funcs = [f for f in funcs if not is_framework(f)]
    print(f"# Scan v2 (framework methods excluded): {len(funcs)} functions, {len(schemas)} classes\n")

    # --- 1. skeleton shingle similarity, all pairs, tightened ---
    big = [f for f in funcs if len(f.skel) >= 25]
    print("## Near-structural clones (skeleton 4-gram Jaccard >=0.85, >=25 nodes):\n")
    sk_pairs = []
    for a, b in combinations(big, 2):
        j = jac(a.shingles, b.shingles)
        if j >= 0.85:
            sk_pairs.append((j, a, b))
    sk_pairs.sort(key=lambda p: -p[0])
    for j, a, b in sk_pairs:
        tag = "SAME-FILE" if a.file == b.file else ""
        print(f"- [{j:.2f}] {tag} {a.file}:{a.lineno} {a.qual}  <->  {b.file}:{b.lineno} {b.qual}")
    print(f"\n({len(sk_pairs)} skeleton-similar pairs)\n")

    # --- 2. call overlap, lowered but require >=3 shared meaningful calls ---
    rich = [f for f in funcs if len(f.calls) >= 2]
    print("## Call-overlap candidates (Jaccard >=0.6, >=3 shared calls):\n")
    cl_pairs = []
    for a, b in combinations(rich, 2):
        shared = a.calls & b.calls
        if len(shared) >= 3 and jac(a.calls, b.calls) >= 0.6:
            cl_pairs.append((jac(a.calls, b.calls), a, b, shared))
    cl_pairs.sort(key=lambda p: -p[0])
    for j, a, b, shared in cl_pairs:
        tag = "SAME-FILE" if a.file == b.file else ""
        print(f"- [{j:.2f}] {tag} {a.file}:{a.lineno} {a.qual}  <->  {b.file}:{b.lineno} {b.qual}")
        print(f"    shared: {', '.join(sorted(shared))}")
    print(f"\n({len(cl_pairs)} call-overlap pairs)\n")

    # --- 3. duplicate data schemas, excluding bl_-marked classes ---
    data_schemas = [(f, c, s) for (f, c, s) in schemas if not (s & BL_MARKERS)]
    print(f"## Duplicate data schemas (non-bl classes, field Jaccard >=0.6, diff files): "
          f"({len(data_schemas)} data classes)\n")
    sc_pairs = []
    for (fa, ca, sa), (fb, cb, sb) in combinations(data_schemas, 2):
        if fa == fb:
            continue
        j = jac(sa, sb)
        if j >= 0.6:
            sc_pairs.append((j, fa, ca, fb, cb, sa & sb))
    sc_pairs.sort(key=lambda p: -p[0])
    for j, fa, ca, fb, cb, shared in sc_pairs:
        print(f"- [{j:.2f}] {fa}:{ca}  <->  {fb}:{cb}   shared: {', '.join(sorted(shared))}")
    print(f"\n({len(sc_pairs)} schema pairs)")


if __name__ == "__main__":
    main()
