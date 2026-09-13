"""Check that the zh-CN translation covers every tr() string (C35).

Extracts every string passed to tr()/translate() (plus the keyboard/glossary/
intro constants that are translated at construction time) and compares it with
the keys of i18n/zh_CN.py. Missing keys fall back to English at runtime — this
tool reports them so the catalog stays complete.

    python tools/i18n_check.py
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

FILES = [*sorted((ROOT / "src" / "xvg_plotter" / "ui").glob("*.py")),
         ROOT / "src" / "xvg_plotter" / "app.py",
         ROOT / "src" / "xvg_plotter" / "i18n" / "__init__.py"]
# module-level constants whose contents are translated at construction time;
# KEYBOARD_ROWS rows are (shortcut, action) — only the action column is tr()'d
CONST_LISTS = {"KEYBOARD_ROWS", "GLOSSARY", "_INTRO", "COLS", "CLOUD_WARNING",
               "NORMALIZE_MODES", "LANGUAGES"}


def const_strs(node) -> list[str]:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return [node.value]
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        return const_strs(node.left) + const_strs(node.right)
    return []


def extract() -> set[str]:
    keys: set[str] = set()

    class V(ast.NodeVisitor):
        def visit_Call(self, node):
            fn = node.func
            name = (fn.attr if isinstance(fn, ast.Attribute)
                    else fn.id if isinstance(fn, ast.Name) else "")
            if name in ("tr", "qtr") and node.args:  # qtr = QCoreApplication.translate
                # translate-style: (context, source…); tr-style: (source, …)
                first = const_strs(node.args[0])
                second = const_strs(node.args[1]) if len(node.args) >= 2 else []
                if second and name == "qtr":
                    keys.update(second)
                else:
                    keys.update(first)
            elif name == "translate" and len(node.args) >= 2:
                keys.update(const_strs(node.args[1]))
            self.generic_visit(node)

        def visit_Assign(self, node):
            if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name) \
                    and node.targets[0].id in CONST_LISTS:
                name = node.targets[0].id
                if isinstance(node.value, (ast.List, ast.Tuple, ast.Dict)):
                    elts = (node.value.values if isinstance(node.value, ast.Dict)
                            else node.value.elts)
                    for el in elts:
                        inner = el.elts if isinstance(el, (ast.List, ast.Tuple)) \
                            else [el]
                        if name == "KEYBOARD_ROWS" and len(inner) == 2:
                            inner = inner[1:]  # shortcut column stays untranslated
                        for sub in inner:
                            keys.update(const_strs(sub))
                    return
                keys.update(const_strs(node.value))
                return
            self.generic_visit(node)

    v = V()
    for f in FILES:
        v.visit(ast.parse(f.read_text(encoding="utf-8")))
    return {k for k in keys if k.strip()}


def main() -> int:
    from xvg_plotter.i18n import zh_CN
    keys = extract()
    have = set(zh_CN.STRINGS)
    missing = sorted(keys - have)
    extra = sorted(have - keys)
    print(f"{len(keys)} translatable strings, "
          f"{len(keys & have)} translated, {len(missing)} missing")
    for k in missing:
        print("  MISSING:", k[:100].replace("\n", "\\n"))
    if extra:
        print(f"{len(extra)} dict keys no longer in the source (dead):")
        for k in extra:
            print("  dead:", k[:100].replace("\n", "\\n"))
    return 1 if missing else 0


if __name__ == "__main__":
    raise SystemExit(main())
