# Biodivine Python bindings

This repository builds the Python interface of the Biodivine libraries. It produces two Python
distributions:

| distribution | import name | what it is |
| --- | --- | --- |
| [`biodivine`](biodivine) | `biodivine` | the package users install and import: one idiomatic, documented submodule per library (`biodivine.xml_dom`, ...) |
| [`biodivine-sys`](biodivine-py-sys) | `biodivine_sys` | the native extension behind it: the Rust code of every library, linked into one module; an implementation detail of `biodivine` |

```python
import biodivine.xml_dom as xml

document = xml.Document.parse('<root xmlns="http://example.com"><item/></root>')
assert document.is_valid()
print(document.root.children())   # [Element('item', id=1)]
```

The [package README](biodivine/README.md) is the user-facing introduction (it is also the package's
PyPI page), and the API reference is built from [`biodivine/docs`](biodivine/docs) by `make docs`.

## Libraries

| Python module | native module | `_sys` crate | Rust library |
| --- | --- | --- | --- |
| `biodivine.xml_dom` | `biodivine_sys.xml_dom` | `biodivine-lib-xml-dom-py-sys` | [`biodivine-lib-xml-dom`](https://github.com/sybila/biodivine-lib-xml-dom) |

## How the layers fit together

Every Biodivine library reaches Python through four layers, of which the last two live here:

1. **The Rust library** (e.g. `biodivine-lib-xml-dom`), published on crates.io. It contains no PyO3
   code.
2. **The library's `_sys` crate** (e.g. `biodivine-lib-xml-dom-py-sys`), in the same repository as
   the library and kept in sync with it: one thin PyO3 wrapper per public Rust item, with no policy
   of its own. It is a plain Rust library exposing a `register(module)` function, and it is never
   published; it is consumed through git, pinned to a commit or release tag.
3. **`biodivine-sys`** ([`biodivine-py-sys`](biodivine-py-sys)): one PyO3 extension module that
   depends on every `_sys` crate and gives each one a submodule (`biodivine_sys.xml_dom`, ...).
4. **`biodivine`** ([`biodivine`](biodivine)): pure Python. Each library is a submodule that wraps
   the corresponding native submodule in classes that accept convenient argument types, follow
   Python protocols and never return a native object.

Layer 3 exists because PyO3 registers a Rust type with the interpreter once per extension module.
If every library shipped its own extension, a library whose bindings build on another library's
types (an SBML model is an XML document, for example) would see a *different* Python class for the
same Rust type, and the two could not be mixed. With a single extension, each Rust type has exactly
one Python class, so the `_sys` crate of one library can take and return the types of another.

The trade-off is that the native extension is released as one unit: a change to any library's
bindings means a new `biodivine-sys` release, and `biodivine` pins the exact `biodivine-sys`
version it was written against.

## Development

The `Makefile` wraps everything, using a virtual environment in `.venv`:

```sh
make venv       # create .venv with maturin, pytest, ruff and the documentation toolchain
make develop    # build biodivine-sys into .venv, install biodivine in editable mode
make test       # cargo test, then pytest
make lint       # cargo fmt --check, cargo clippy -D warnings, ruff
make docs       # API reference of biodivine (biodivine/docs/_build/index.html)
make verify     # all of the above, plus rustdoc and the minimum supported Rust version
```

The `_sys` crates are git dependencies of [`biodivine-py-sys/Cargo.toml`](biodivine-py-sys/Cargo.toml).
When this repository is checked out as part of the `biodivine` workspace, where every library is a
submodule next to it, they can be switched to `path` dependencies while a library and its bindings
change together.

### Adding a library

1. In the library's repository, add a `_sys` crate whose classes declare
   `module = "biodivine_sys.<name>"` and which exposes `pub fn register(module: &Bound<PyModule>)`.
   `<name>` is the library name without the `biodivine-lib-` prefix, in `snake_case`.
2. Add the crate to `biodivine-py-sys/Cargo.toml` and one `add_submodule` call to
   `biodivine-py-sys/src/lib.rs`.
3. Add the Python submodule `biodivine/src/biodivine/<name>/`, import it in
   `biodivine/src/biodivine/__init__.py`, and give it tests in `biodivine/tests/<name>/` and an API
   reference in `biodivine/docs/<name>/`.

## License

[MIT](LICENSE).
