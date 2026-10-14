"""Runs the Python examples of the READMEs and of the API reference pages.

The code blocks of one page run in order and share one namespace, so a page can introduce a name
in one block and use it in the next one, exactly as a reader would.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPOSITORY = Path(__file__).resolve().parents[2]
PAGES = [
    REPOSITORY / "README.md",
    REPOSITORY / "biodivine" / "README.md",
    *sorted((REPOSITORY / "biodivine" / "docs").rglob("*.md")),
]
PAGES = [page for page in PAGES if "_build" not in page.parts]


def _python_blocks(page: Path) -> list[str]:
    return re.findall(r"```python\n(.*?)```", page.read_text(encoding="utf-8"), flags=re.DOTALL)


def test_the_documentation_has_examples() -> None:
    """A mis-globbed directory would silently run nothing, so the pages are checked by name."""
    names = {page.relative_to(REPOSITORY).as_posix() for page in PAGES if _python_blocks(page)}
    assert {
        "README.md",
        "biodivine/README.md",
        "biodivine/docs/index.md",
        "biodivine/docs/xml_dom/index.md",
    } <= names


@pytest.mark.parametrize(
    "page", PAGES, ids=lambda page: page.relative_to(REPOSITORY).as_posix()
)
def test_page_examples_run(page: Path) -> None:
    namespace: dict[str, object] = {"__name__": "__main__"}
    for index, block in enumerate(_python_blocks(page)):
        exec(compile(block, f"{page.name}[{index}]", "exec"), namespace)
