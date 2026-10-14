"""The ``biodivine`` package as a whole: its submodules and its version."""

from __future__ import annotations

import re
from pathlib import Path
from types import ModuleType

import biodivine_sys

import biodivine

REPOSITORY = Path(__file__).resolve().parents[2]


def _workspace_version() -> str:
    manifest = (REPOSITORY / "Cargo.toml").read_text(encoding="utf-8")
    workspace = manifest[manifest.index("[workspace.package]") :]
    found = re.search(r'^version = "([^"]+)"', workspace, flags=re.MULTILINE)
    assert found is not None
    return found.group(1)


def test_every_library_is_a_submodule() -> None:
    assert biodivine.__all__ == ["__version__", "xml_dom"]
    assert biodivine_sys.__all__ == ["__version__", "xml_dom"]
    assert isinstance(biodivine.xml_dom, ModuleType)


def test_the_versions_agree() -> None:
    """The extension, the package and its pin of the extension are released together."""
    version = _workspace_version()
    assert biodivine_sys.__version__ == version
    assert biodivine.__version__ == version
    pyproject = (REPOSITORY / "biodivine" / "pyproject.toml").read_text(encoding="utf-8")
    assert f'version = "{version}"' in pyproject
    assert f'"biodivine-sys=={version}"' in pyproject


def test_native_submodules_are_importable_by_name() -> None:
    import biodivine_sys.xml_dom

    assert biodivine_sys.xml_dom.Document.__module__ == "biodivine_sys.xml_dom"
