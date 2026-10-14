# biodivine

The Python interface of the Biodivine libraries. Every library is a submodule of the `biodivine`
package, and every submodule is an idiomatic Python layer over a Rust implementation:

| submodule | what it does | Rust crate |
| --- | --- | --- |
| `biodivine.xml_dom` | build, parse, edit, validate and serialize XML documents, with full namespace support and thread-safe documents | [`biodivine-lib-xml-dom`](https://github.com/sybila/biodivine-lib-xml-dom) |

```sh
pip install biodivine
# or
conda install -c conda-forge -c daemontus biodivine
```

## Example

The following builds a small namespaced document, checks that it is valid, and serializes it:

```python
import biodivine.xml_dom as xml

document = xml.Document()
ex = xml.Namespace("http://example.com", "ex")

root = document.create_element(("root", ex))
root.declare_namespace(ex)
document.set_root(root)

child = document.create_element(("child", ex))
child.append_child(document.create_text("Hello, World!"))
root.append_child(child)

assert document.is_valid()
assert document.write() == (
    '<ex:root xmlns:ex="http://example.com"><ex:child>Hello, World!</ex:child></ex:root>'
)
```

## How it fits together

The Rust code of all libraries is compiled into one native extension, distributed as the
[`biodivine-sys`](https://pypi.org/project/biodivine-sys/) package and installed automatically as
a dependency. Because every library shares that extension, the objects of one library (say, an XML
document) can be handed to another library directly. You never need to import `biodivine_sys`
yourself: the classes of `biodivine` accept Python values in several convenient forms, follow
Python protocols (`len`, iteration, indexing, equality, hashing) and never return a native object.

## Documentation

* The [API reference](https://biodivine.fi.muni.cz/docs/biodivine-py/latest/) documents every
  submodule, class and function, with examples. It describes the latest release; the reference of
  an earlier version `X.Y.Z` is at `https://biodivine.fi.muni.cz/docs/biodivine-py/vX.Y.Z/`.
* The Biodivine book teaches every library with examples in both Python and Rust.
* The source code, the issue tracker and the development workflow are in the
  [`biodivine-py`](https://github.com/sybila/biodivine-py) repository.
