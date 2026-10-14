//! The native extension of the Biodivine Python bindings.
//!
//! This crate builds `biodivine_sys`, the one native module that every Biodivine library reaches
//! Python through. It contains no bindings of its own: each library keeps a thin PyO3 wrapper crate
//! (its `_sys` crate) next to its Rust code, and this crate links all of them into a single
//! extension, one submodule per library:
//!
//! | submodule | `_sys` crate | Rust library |
//! | --- | --- | --- |
//! | `biodivine_sys.xml_dom` | `biodivine-lib-xml-dom-py-sys` | `biodivine-lib-xml-dom` |
//!
//! # Why one extension
//!
//! A `#[pyclass]` type is registered with the interpreter by the extension module it is compiled
//! into. If two libraries were built as two extensions, the XML `Document` of one would be a
//! different Python class than the XML `Document` of the other, even though both come from the
//! same Rust type, and a binding that expects one would reject the other. Linking every `_sys`
//! crate into one module gives each Rust type exactly one Python class, so a library whose
//! bindings build on another library's types (say, a model format stored as XML) can accept and
//! return them directly.
//!
//! # What users see
//!
//! Nobody is expected to import this module directly. The `biodivine` package wraps it in
//! idiomatic, documented Python classes (`biodivine.xml_dom` for `biodivine_sys.xml_dom`, and so
//! on), and that package is the documented interface. This module is importable, but it has no
//! documentation of its own beyond the docstrings it inherits from the `_sys` crates.
//!
//! # Adding a library
//!
//! Add the library's `_sys` crate as a dependency, then add one [`add_submodule`] call to
//! [`biodivine_sys`] with the submodule name (the library name without the `biodivine-lib-`
//! prefix, in `snake_case`) and the crate's `register` function. The classes of the `_sys` crate
//! must declare `module = "biodivine_sys.<name>"`, so that the module path they report is the one
//! they can be imported from.
#![deny(rustdoc::broken_intra_doc_links, rustdoc::private_intra_doc_links)]

use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList};

/// The import name of the extension, which is the prefix of every submodule's import name.
///
/// It is spelled out rather than read from the module object, because the name of the module
/// object depends on how the extension is installed: a wheel installs it as `biodivine_sys`, while
/// `maturin develop` installs it as `biodivine_sys.biodivine_sys` inside a generated package that
/// re-exports everything listed in `__all__`.
pub const PACKAGE: &str = "biodivine_sys";

#[cfg(test)]
mod tests;

/// The `biodivine_sys` module: one submodule per Biodivine library.
#[pymodule]
pub fn biodivine_sys(module: &Bound<'_, PyModule>) -> PyResult<()> {
    module.add(
        "__doc__",
        "Native extension of the Biodivine Python bindings. Use the `biodivine` package instead.",
    )?;
    // The version of the extension (and of the `biodivine` package that pins it). Each submodule
    // reports the version of the library it wraps as its own `__version__`.
    module.add("__version__", env!("CARGO_PKG_VERSION"))?;
    module.add("__all__", PyList::new(module.py(), ["__version__"])?)?;

    add_submodule(module, "xml_dom", biodivine_lib_xml_dom_sys::register)?;

    Ok(())
}

/// Creates the submodule `name` of `parent` and lets `register` fill it.
///
/// A native submodule is an attribute of its parent, but Python's import system does not know about
/// it: `import biodivine_sys.xml_dom` only works if the submodule is in `sys.modules`. This function
/// therefore also registers the submodule there, under its full dotted name (see [`PACKAGE`]), sets
/// `__name__` to that name so that the module path printed by Python is the one it can be imported
/// from, and lists `name` in the parent's `__all__`.
///
/// # Errors
///
/// Fails with the exception raised by `register`, or by the interpreter when the module cannot be
/// created or registered.
pub fn add_submodule(
    parent: &Bound<'_, PyModule>,
    name: &str,
    register: impl FnOnce(&Bound<'_, PyModule>) -> PyResult<()>,
) -> PyResult<()> {
    let py = parent.py();
    let full_name = format!("{PACKAGE}.{name}");
    let submodule = PyModule::new(py, name)?;
    register(&submodule)?;
    submodule.setattr("__name__", full_name.as_str())?;
    // Also appends `name` to the parent's `__all__`.
    parent.add_submodule(&submodule)?;
    let modules = py
        .import("sys")?
        .getattr("modules")?
        .cast_into::<PyDict>()?;
    modules.set_item(full_name, submodule)?;
    Ok(())
}
