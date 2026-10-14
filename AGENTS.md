## Context

- This repository builds the `biodivine-sys` native extension (`biodivine-py-sys/`) and the pure-Python
  `biodivine` package (`biodivine/`). `README.md` describes the layers and how to add a library; read
  it first.
- The bindings of a library are split between its own repository (the `_sys` crate: one thin PyO3
  wrapper per Rust item) and this one (the idiomatic Python submodule). A change to a library's
  Python interface usually touches both.

## Instructions

- `make verify` runs every check (fmt, clippy, cargo test, pytest, ruff, docs with warnings as
  errors, MSRV). Run it after every non-trivial change.
- `biodivine-py-sys` contains no bindings of its own; it only links the `_sys` crates together.
- The pure-Python layer never returns a `biodivine_sys` object: every value is a class of the
  `biodivine` package (the exception classes are the one exception, re-exported with the submodule
  as their `__module__`).
- No library logic is reimplemented in Python: a submodule converts arguments, adds Python
  protocols and conveniences, and delegates.
- Every public class, function and module has a docstring; the API reference in `biodivine/docs`
  is built from them with warnings denied.
- The versions of `biodivine-sys`, `biodivine` and the pin between them change together
  (`biodivine/tests/test_package.py` checks this).
