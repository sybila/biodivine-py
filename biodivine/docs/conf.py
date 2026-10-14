"""Sphinx configuration for the API reference of the `biodivine` Python package.

Build with ``make docs`` from the repository root, or by hand::

    .venv/bin/python -m sphinx -b html biodivine/docs biodivine/docs/_build

The package must be importable, which means the native extension has to be built first
(``make develop``); autodoc imports the modules it documents.
"""

import biodivine

project = "biodivine"
copyright = "2026, Sybila"
author = "Sybila"
# Read from the installed package, so the documentation cannot advertise a different version than
# the code.
version = biodivine.__version__
release = version

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.intersphinx",
    "myst_parser",
    "sphinx_design",
]

autodoc_default_options = {
    "members": True,
    "undoc-members": False,
    "show-inheritance": True,
    "member-order": "alphabetical",
}
autodoc_typehints = "description"
napoleon_google_docstring = True
napoleon_numpy_docstring = False

myst_enable_extensions = ["colon_fence", "deflist"]
source_suffix = {".md": "markdown", ".rst": "restructuredtext"}
master_doc = "index"

html_theme = "shibuya"
html_title = "biodivine"
html_theme_options = {
    "accent_color": "violet",
    "color_mode": "auto",
    "show_ai_links": False,
    "github_url": "https://github.com/sybila/biodivine-py",
}
exclude_patterns = ["_build"]

intersphinx_mapping = {"python": ("https://docs.python.org/3", None)}
