# biodivine-sys

The native extension of the Biodivine Python bindings. It links the low-level PyO3 wrappers of
every Biodivine Rust library into one module, `biodivine_sys`, with one submodule per library
(`biodivine_sys.xml_dom`, ...).

This package is an implementation detail of [`biodivine`](https://pypi.org/project/biodivine/),
which wraps it in idiomatic, documented Python classes and is what you should install and import.
The API of `biodivine_sys` mirrors the Rust crates one to one and may change in any release.
