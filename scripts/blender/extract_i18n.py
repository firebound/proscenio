"""Extract translatable msgids from the Proscenio Blender addon (spec 072, A2).

A bpy-free ``ast`` walk over ``apps/blender/**`` that produces the
``(msgctxt, msgid)`` catalog backing the pt-BR table and its reverse-coverage
drift test, plus a worklist of raw dynamic strings still to be wrapped (the
A3 to-do).

Contexts follow the empirical Blender probe (``bl_rna.translation_context``):
operators translate their ``bl_label`` / ``bl_description`` under
``"Operator"``; panels, menus, properties and enum items translate under the
default ``"*"``; ``iface(msg, ctxt)`` carries its own context.

What lands in the catalog is what actually translates at runtime:
  - static strings Blender auto-translates: operator/panel ``bl_label`` +
    ``bl_description``, ``*Property(name=, description=)``, ``EnumProperty``
    item names + descriptions;
  - ``iface(...)`` calls (explicitly routed through the translation table).

Raw ``.label(text=...)`` / ``report_*(op, ...)`` string arguments do NOT
translate until wrapped in ``iface()``; they are reported as *unwrapped* (the
A3 worklist), not as catalog entries, so the catalog never lists a msgid that
would silently stay English.

CLI::

    uv run python scripts/blender/extract_i18n.py            # catalog summary
    uv run python scripts/blender/extract_i18n.py --unwrapped  # A3 worklist
    uv run python scripts/blender/extract_i18n.py --skeleton   # pt_br.py ROWS stub
"""

from __future__ import annotations

import argparse
import ast
from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field
from pathlib import Path

DEFAULT_CTX = "*"
OPERATOR_CTX = "Operator"

# bpy.props factory names whose ``name=`` / ``description=`` are translatable.
_PROPERTY_FUNCS = frozenset(
    {
        "StringProperty",
        "BoolProperty",
        "IntProperty",
        "FloatProperty",
        "EnumProperty",
        "PointerProperty",
        "CollectionProperty",
        "FloatVectorProperty",
        "IntVectorProperty",
        "BoolVectorProperty",
    }
)
_REPORT_FUNCS = frozenset(
    {"report_info", "report_warn", "report_error", "report_debug"}
)
_TRANSLATABLE_KWARGS = ("name", "description")


@dataclass(frozen=True)
class Unwrapped:
    """A dynamic string still routed around the translation table (A3 worklist)."""

    text: str
    kind: str  # "label" | "report"
    filename: str
    lineno: int
    is_fstring: bool


@dataclass
class ExtractResult:
    """Everything one source file (or the whole tree) yields."""

    catalog: list[tuple[str, str]] = field(default_factory=list)
    unwrapped: list[Unwrapped] = field(default_factory=list)


def _str_const(node: ast.expr | None) -> str | None:
    """The value of a string-literal node, else None."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _func_name(node: ast.Call) -> str | None:
    """The called function's short name (``iface``, ``StringProperty``, ...)."""
    func = node.func
    if isinstance(func, ast.Attribute):
        return func.attr
    if isinstance(func, ast.Name):
        return func.id
    return None


def _is_operator(cls: ast.ClassDef) -> bool:
    """True if the class is a Blender operator (translates under 'Operator').

    Matched by base class (``Operator`` / ``bpy.types.Operator``) or the
    ``_OT_`` id-name convention the addon follows.
    """
    if "_OT_" in cls.name:
        return True
    for base in cls.bases:
        if isinstance(base, ast.Name) and base.id == "Operator":
            return True
        if isinstance(base, ast.Attribute) and base.attr == "Operator":
            return True
    return False


def _fstring_template(node: ast.JoinedStr) -> str:
    """Render an f-string node back to a readable ``dynamic {expr}`` template."""
    parts: list[str] = []
    for value in node.values:
        if isinstance(value, ast.Constant) and isinstance(value.value, str):
            parts.append(value.value)
        elif isinstance(value, ast.FormattedValue):
            parts.append("{" + ast.unparse(value.value) + "}")
    return "".join(parts)


def _is_iface_call(node: ast.expr | None) -> bool:
    """True if the node is an ``iface(...)`` call (already wrapped)."""
    return isinstance(node, ast.Call) and _func_name(node) == "iface"


class _Visitor(ast.NodeVisitor):
    """Collect catalog entries + unwrapped dynamic strings from one module."""

    def __init__(self, filename: str) -> None:
        self.filename = filename
        self.result = ExtractResult()

    # -- static class strings ------------------------------------------------
    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        ctx = OPERATOR_CTX if _is_operator(node) else DEFAULT_CTX
        for stmt in node.body:
            targets: list[ast.expr] = []
            value: ast.expr | None = None
            if isinstance(stmt, ast.Assign):
                targets, value = stmt.targets, stmt.value
            elif isinstance(stmt, ast.AnnAssign) and stmt.target is not None:
                targets, value = [stmt.target], stmt.value
            name = _str_const(value)
            if not name:
                continue
            for target in targets:
                if isinstance(target, ast.Name) and target.id in (
                    "bl_label",
                    "bl_description",
                ):
                    self.result.catalog.append((ctx, name))
        self.generic_visit(node)

    # -- calls: properties, enum items, iface, label, report ----------------
    def visit_Call(self, node: ast.Call) -> None:
        name = _func_name(node)
        if name == "iface":
            self._collect_iface(node)
        elif name in _PROPERTY_FUNCS:
            self._collect_property(node)
        elif name == "label":
            self._collect_label(node)
        elif name in _REPORT_FUNCS:
            self._collect_report(node)
        self.generic_visit(node)

    def _collect_iface(self, node: ast.Call) -> None:
        msgid = _str_const(node.args[0]) if node.args else None
        if not msgid:
            return
        ctx = _str_const(node.args[1]) if len(node.args) > 1 else None
        self.result.catalog.append((ctx or DEFAULT_CTX, msgid))

    def _collect_property(self, node: ast.Call) -> None:
        for kw in node.keywords:
            if kw.arg in _TRANSLATABLE_KWARGS:
                msgid = _str_const(kw.value)
                if msgid:
                    self.result.catalog.append((DEFAULT_CTX, msgid))
            elif kw.arg == "items" and _func_name(node) == "EnumProperty":
                self._collect_enum_items(kw.value)

    def _collect_enum_items(self, items: ast.expr) -> None:
        if not isinstance(items, (ast.List, ast.Tuple)):
            return  # a callable or a referenced constant - not statically resolvable
        for elt in items.elts:
            if not isinstance(elt, (ast.Tuple, ast.List)) or len(elt.elts) < 3:
                continue  # None separator, or a malformed row
            for pos in (1, 2):  # (identifier, name, description[, icon, number])
                msgid = _str_const(elt.elts[pos])
                if msgid:
                    self.result.catalog.append((DEFAULT_CTX, msgid))

    def _collect_label(self, node: ast.Call) -> None:
        for kw in node.keywords:
            if kw.arg == "text":
                self._flag_dynamic(kw.value, "label")

    def _collect_report(self, node: ast.Call) -> None:
        # report.py routes every message through the injected translator, so a
        # fixed-literal report message is translatable (a catalog entry). An
        # f-string evaluates before report.py sees it, so it cannot match a
        # msgid - flagged unwrapped (the A3 f-string follow-on).
        if len(node.args) < 2:  # report_*(op, msg, ...)
            return
        msg = node.args[1]
        if _is_iface_call(msg):
            return  # an explicit iface template - caught by _collect_iface
        literal = _str_const(msg)
        if literal:
            self.result.catalog.append((DEFAULT_CTX, literal))
        elif isinstance(msg, ast.JoinedStr):
            self.result.unwrapped.append(
                Unwrapped(
                    _fstring_template(msg), "report", self.filename, msg.lineno, True
                )
            )

    def _flag_dynamic(self, value: ast.expr, kind: str) -> None:
        """Record a raw label/report string as unwrapped, unless already iface()."""
        if _is_iface_call(value):
            return
        literal = _str_const(value)
        if literal:
            self.result.unwrapped.append(
                Unwrapped(
                    literal, kind, self.filename, getattr(value, "lineno", 0), False
                )
            )
        elif isinstance(value, ast.JoinedStr):
            self.result.unwrapped.append(
                Unwrapped(
                    _fstring_template(value), kind, self.filename, value.lineno, True
                )
            )


def extract_from_source(source: str, filename: str = "<string>") -> ExtractResult:
    """Extract catalog + unwrapped entries from one module's source text."""
    visitor = _Visitor(filename)
    visitor.visit(ast.parse(source, filename=filename))
    result = visitor.result
    # Drop whitespace-only strings (e.g. a ``\xa0`` layout spacer label): they
    # are never translatable text and would only be catalog / worklist noise.
    result.catalog = [(ctx, msgid) for ctx, msgid in result.catalog if msgid.strip()]
    result.unwrapped = [u for u in result.unwrapped if u.text.strip()]
    return result


def iter_source_files(root: Path) -> Iterator[Path]:
    """Every addon ``.py`` worth scanning (skip tests + generated caches)."""
    for path in sorted(root.rglob("*.py")):
        parts = set(path.parts)
        if "tests" in parts or "__pycache__" in parts:
            continue
        yield path


def _merge(root: Path) -> ExtractResult:
    merged = ExtractResult()
    for path in iter_source_files(root):
        res = extract_from_source(
            path.read_text(encoding="utf-8"), str(path.relative_to(root))
        )
        merged.catalog.extend(res.catalog)
        merged.unwrapped.extend(res.unwrapped)
    return merged


def extract_catalog(root: Path) -> list[tuple[str, str]]:
    """The sorted, de-duplicated ``(msgctxt, msgid)`` catalog for the whole tree."""
    return sorted(set(_merge(root).catalog))


def find_unwrapped(root: Path) -> list[Unwrapped]:
    """Raw dynamic label/report strings not yet wrapped in ``iface()`` (A3 worklist)."""
    return _merge(root).unwrapped


def _addon_root() -> Path:
    return Path(__file__).resolve().parents[2] / "apps" / "blender"


def _skeleton(catalog: Iterable[tuple[str, str]]) -> str:
    """Emit ``ROWS`` stub lines for pt_br.py - empty msgstr slots to fill."""
    lines = ["ROWS: tuple[LocaleRow, ...] = ("]
    for ctx, msgid in catalog:
        lines.append(f"    (({ctx!r}, {msgid!r}), {''!r}),")
    lines.append(")")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Extract addon i18n msgids (spec 072)."
    )
    parser.add_argument(
        "--unwrapped", action="store_true", help="print the A3 worklist"
    )
    parser.add_argument(
        "--skeleton", action="store_true", help="print pt_br.py ROWS stub"
    )
    args = parser.parse_args()
    root = _addon_root()

    if args.unwrapped:
        for u in sorted(find_unwrapped(root), key=lambda u: (u.filename, u.lineno)):
            tag = "f-string" if u.is_fstring else "literal"
            print(f"{u.filename}:{u.lineno} [{u.kind}/{tag}] {u.text!r}")
        return 0

    catalog = extract_catalog(root)
    if args.skeleton:
        print(_skeleton(catalog))
        return 0

    by_ctx: dict[str, int] = {}
    for ctx, _ in catalog:
        by_ctx[ctx] = by_ctx.get(ctx, 0) + 1
    print(
        f"catalog: {len(catalog)} msgids "
        + ", ".join(f"{c}={n}" for c, n in sorted(by_ctx.items()))
    )
    print(f"unwrapped (A3 worklist): {len(find_unwrapped(root))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
