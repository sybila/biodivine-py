"""Prints the public API of the `biodivine` package, one line per item, in a stable order.

The release notes are generated from the difference between the output of this script at two
versions, so it reads the sources (with `ast`) instead of importing the package: it must work on
any checkout without building the native extension, and its output should change only when the
API does.

The public API consists of every module, class, function, method, property and module or class
attribute whose name does not start with an underscore, the dunder methods (such as `__len__`, which
define the Python protocols a class supports), and every name a module re-exports through
`__all__`.

Usage: `python3 scripts/public_api.py [package directory]`, by default `biodivine/src/biodivine`.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path
from typing import Iterator, Optional, Union

REPOSITORY = Path(__file__).resolve().parents[1]
FunctionDef = Union[ast.FunctionDef, ast.AsyncFunctionDef]


def _is_public(name: str) -> bool:
    return not name.startswith("_") or (name.startswith("__") and name.endswith("__"))


def _signature(function: FunctionDef) -> str:
    returns = f" -> {ast.unparse(function.returns)}" if function.returns else ""
    prefix = "async def" if isinstance(function, ast.AsyncFunctionDef) else "def"
    return f"{prefix} {function.name}({ast.unparse(function.args)}){returns}"


def _decorators(function: FunctionDef) -> set[str]:
    return {ast.unparse(decorator) for decorator in function.decorator_list}


def _assigned_names(statement: ast.stmt) -> list[str]:
    if isinstance(statement, ast.Assign):
        return [target.id for target in statement.targets if isinstance(target, ast.Name)]
    if isinstance(statement, ast.AnnAssign) and isinstance(statement.target, ast.Name):
        return [statement.target.id]
    return []


def _assigned_value(statement: ast.stmt) -> str:
    """The annotation and the value of an assignment, as `: annotation = value`."""
    annotation = getattr(statement, "annotation", None)
    value = getattr(statement, "value", None)
    return (f": {ast.unparse(annotation)}" if annotation else "") + (
        f" = {ast.unparse(value)}" if value else ""
    )


def _declared_all(tree: ast.Module) -> Optional[list[str]]:
    for statement in tree.body:
        if "__all__" in _assigned_names(statement):
            assert statement.value is not None
            return list(ast.literal_eval(statement.value))
    return None


def _class_members(path: str, cls: ast.ClassDef) -> Iterator[str]:
    for statement in cls.body:
        if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if not _is_public(statement.name):
                continue
            decorators = _decorators(statement)
            if "property" in decorators:
                returns = f": {ast.unparse(statement.returns)}" if statement.returns else ""
                yield f"{path}.{statement.name}{returns} (property)"
            elif any(decorator.endswith((".setter", ".deleter")) for decorator in decorators):
                # Part of a property listed above; a setter makes it writable.
                yield f"{path}.{statement.name} (property setter)"
            else:
                kind = next(
                    (f" ({name})" for name in ("staticmethod", "classmethod") if name in decorators),
                    "",
                )
                yield f"{path}: {_signature(statement)}{kind}"
        elif isinstance(statement, ast.ClassDef) and _is_public(statement.name):
            yield from _class(f"{path}.{statement.name}", statement)
        else:
            for name in _assigned_names(statement):
                if not name.startswith("_"):
                    yield f"{path}.{name}{_assigned_value(statement)}"


def _class(path: str, cls: ast.ClassDef) -> Iterator[str]:
    bases = ", ".join(ast.unparse(base) for base in cls.bases)
    yield f"{path}: class {cls.name}({bases})" if bases else f"{path}: class {cls.name}"
    yield from _class_members(path, cls)


def _module(module: str, tree: ast.Module) -> Iterator[str]:
    yield f"{module}: module"
    exported = _declared_all(tree)
    defined: set[str] = set()
    for statement in tree.body:
        if isinstance(statement, ast.ClassDef):
            defined.add(statement.name)
            if _is_public(statement.name) and (exported is None or statement.name in exported):
                yield from _class(f"{module}.{statement.name}", statement)
        elif isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef)):
            defined.add(statement.name)
            if _is_public(statement.name) and (exported is None or statement.name in exported):
                yield f"{module}: {_signature(statement)}"
        else:
            for name in _assigned_names(statement):
                defined.add(name)
                if not name.startswith("_") and (exported is None or name in exported):
                    yield f"{module}.{name}{_assigned_value(statement)}"
    # Names that a module exports but does not define are re-exports (of a submodule's class, or
    # of a native class or exception).
    for statement in tree.body:
        if isinstance(statement, ast.ImportFrom):
            source = "." * statement.level + (statement.module or "")
            for alias in statement.names:
                name = alias.asname or alias.name
                if name not in defined and exported is not None and name in exported:
                    yield f"{module}.{name} (re-exported from {source})"


def public_api(package: Path) -> list[str]:
    """Returns the public API of the package in `package`, sorted."""
    lines: list[str] = []
    for file in package.rglob("*.py"):
        parts = file.relative_to(package.parent).with_suffix("").parts
        if parts[-1] == "__init__":
            parts = parts[:-1]
        if not all(_is_public(part) for part in parts):
            continue
        tree = ast.parse(file.read_text(encoding="utf-8"), filename=str(file))
        lines.extend(_module(".".join(parts), tree))
    return sorted(lines)


def main() -> None:
    package = Path(sys.argv[1]) if len(sys.argv) > 1 else REPOSITORY / "biodivine/src/biodivine"
    for line in public_api(package):
        print(line)


if __name__ == "__main__":
    main()
