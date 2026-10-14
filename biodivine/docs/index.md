# biodivine

`biodivine` is the Python interface of the Biodivine libraries. Each library is a submodule of the
package, implemented in Rust and wrapped in idiomatic Python classes:

| module | what it does |
| --- | --- |
| {doc}`biodivine.xml_dom <xml_dom/index>` | build, parse, edit, validate and serialize XML documents, with full namespace support and thread-safe documents |

## Installation

```sh
pip install biodivine
```

or, with conda (the packages are in the `daemontus` channel and need `conda-forge`):

```sh
conda install -c conda-forge -c daemontus biodivine
```

The package works with CPython 3.9 and newer, including the free-threaded build (PyPI only). It
depends on `biodivine-sys`, a native extension that contains the Rust code of every library and is
installed automatically. To build both from a checkout of the `biodivine-py`
repository instead, run `make develop` there (it needs a Rust toolchain and creates a virtual
environment in `.venv`).

## Example

The following parses a small document, adds an element to it and serializes it again:

```python
import biodivine.xml_dom as xml

document = xml.Document.parse("<list><item>one</item></list>")
item = document.create_element("item")
item.append_child(document.create_text("two"))
document.root.append_child(item)

assert document.write() == "<list><item>one</item><item>two</item></list>"
```

## How the package is organized

* Every library is one submodule (`biodivine.xml_dom`, ...), and everything a user needs from that
  library is importable from the submodule itself. Larger submodules group their classes into
  documentation sections, but the classes are always importable from the submodule.
* The classes accept Python values in several convenient forms (a name can be a string or a tuple,
  a path can be any `os.PathLike`, ...), follow Python protocols where they make sense (`len`,
  iteration, indexing, equality, hashing, `copy`) and never return an object of the native
  extension.
* The native extension, `biodivine_sys`, has one submodule per library and mirrors the Rust APIs
  one to one. It is shared by all libraries, which is what lets the objects of one library be
  passed to another. It is an implementation detail: it is importable, but it is not documented
  here and its API may change in any release.
* `biodivine.__version__` is the version of the package (and of the extension it pins), while each
  submodule's `__version__` is the version of the Rust library it wraps.

The Biodivine book teaches the libraries with examples in both Python and Rust, and the Rust API
documentation of each library describes its design in depth.

```{toctree}
:maxdepth: 2
:caption: Libraries
xml_dom/index
```
