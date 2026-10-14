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
The API reference of every release is published at
`https://biodivine.fi.muni.cz/docs/biodivine-py/<tag>/`, and that of the latest stable release also
at [`latest/`](https://biodivine.fi.muni.cz/docs/biodivine-py/latest/).

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

The `_sys` crates are git dependencies of [`biodivine-py-sys/Cargo.toml`](biodivine-py-sys/Cargo.toml),
pinned to release tags of their repositories. When this repository is checked out as part of the
`biodivine` workspace, where every library is a submodule next to it, they can be switched to `path`
dependencies while a library and its bindings change together. The Biodivine book, which must test
the checked-out libraries, does not edit this repository: its `make python-env` overrides the git
dependencies with Cargo `[patch]` entries during the build (described in the book's README).

### Continuous integration

[`build.yml`](.github/workflows/build.yml) runs on pushes and pull requests:

* `rust`: `cargo fmt`, `cargo clippy`, `cargo test` and rustdoc on a pinned toolchain, then
  `cargo test` on the minimum supported Rust version;
* `python`: builds the release wheel of `biodivine-sys` and runs `ruff` and `pytest` against it on
  Linux, macOS and Windows, with the oldest and the newest supported Python version and with the
  free-threaded build of the newest one;
* `docs`: builds the API reference with warnings denied.

### Adding a library

1. In the library's repository, add a `_sys` crate whose classes declare
   `module = "biodivine_sys.<name>"` and which exposes `pub fn register(module: &Bound<PyModule>)`.
   `<name>` is the library name without the `biodivine-lib-` prefix, in `snake_case`.
2. Add the crate to `biodivine-py-sys/Cargo.toml` and one `add_submodule` call to
   `biodivine-py-sys/src/lib.rs`.
3. Add the Python submodule `biodivine/src/biodivine/<name>/`, import it in
   `biodivine/src/biodivine/__init__.py`, and give it tests in `biodivine/tests/<name>/` and an API
   reference in `biodivine/docs/<name>/`.

## Releasing

Both distributions are released together, with the same version:

1. Pin every `_sys` crate to a release tag of its library.
2. Set the new version in `[workspace.package]` of [`Cargo.toml`](Cargo.toml) and, twice (the
   version and the pin of `biodivine-sys`), in [`biodivine/pyproject.toml`](biodivine/pyproject.toml).
   `make verify` checks that the three agree.
3. Push the tag `v<version>`. [`release.yml`](.github/workflows/release.yml) then:
   * checks that the tag matches the version, and runs every check of `build.yml`;
   * builds the wheels and the source distribution of `biodivine-sys` and the wheel and source
     distribution of `biodivine`, installs the built wheels on every architecture and runs the test
     suite against them;
   * publishes everything to PyPI;
   * deploys the API reference to `https://biodivine.fi.muni.cz/docs/biodivine-py/<tag>/` and, for
     a stable release (no pre-release suffix such as `-rc.1`), points `latest/` at it;
   * creates a draft GitHub release with the distributions, the documentation and release notes
     generated from the changes since the previous version (configured in
     [`.releasenotes.yml`](.releasenotes.yml); [`scripts/public_api.py`](scripts/public_api.py)
     lists the public API that is compared between the two versions).
4. Review the release notes and publish the GitHub release.

The `biodivine-sys` wheels are built against the stable ABI of Python 3.9, so there is one wheel per
platform: Linux (manylinux2014 and musllinux, x86-64 and ARM), macOS (ARM and x86-64) and Windows
(x86-64 and ARM). Free-threaded Python cannot use the stable ABI, so each platform also gets a wheel
for the free-threaded build of the newest Python version (on Linux for manylinux_2_28, which is
glibc 2.28). Anywhere else, pip builds the extension from the source distribution, which needs a
Rust toolchain.

The release workflow needs:

* PyPI trusted publishing: the `biodivine` and `biodivine-sys` projects on PyPI must both list this
  repository, the `release.yml` workflow and the `pypi` environment as a trusted publisher;
* the secrets `TS_OAUTH_CLIENT_ID` and `TS_OAUTH_SECRET` (a Tailscale OAuth client that reaches the
  documentation server) and `OPENROUTER_API_KEY` (the release-notes model).

## License

[MIT](LICENSE).
