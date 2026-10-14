//! In-process tests of the aggregate module (`cargo test` starts an interpreter, see the
//! `auto-initialize` dev-dependency).

use pyo3::prelude::*;

/// Builds the extension module the way the interpreter would, and registers it in `sys.modules`.
fn initialize(py: Python<'_>) -> Bound<'_, PyModule> {
    let module = PyModule::new(py, "biodivine_sys").unwrap();
    crate::biodivine_sys(&module).unwrap();
    py.import("sys")
        .unwrap()
        .getattr("modules")
        .unwrap()
        .set_item("biodivine_sys", &module)
        .unwrap();
    module
}

#[test]
fn every_library_is_a_submodule() {
    Python::attach(|py| {
        let module = initialize(py);
        let version: String = module.getattr("__version__").unwrap().extract().unwrap();
        assert_eq!(version, env!("CARGO_PKG_VERSION"));
        let all: Vec<String> = module.getattr("__all__").unwrap().extract().unwrap();
        assert_eq!(all, ["__version__", "xml_dom"]);

        let xml_dom = module.getattr("xml_dom").unwrap();
        let name: String = xml_dom.getattr("__name__").unwrap().extract().unwrap();
        assert_eq!(name, "biodivine_sys.xml_dom");
        assert!(xml_dom.hasattr("Document").unwrap());
    });
}

#[test]
fn submodules_are_importable_by_their_dotted_name() {
    Python::attach(|py| {
        let module = initialize(py);
        let imported = py.import("biodivine_sys.xml_dom").unwrap();
        assert!(imported.is(module.getattr("xml_dom").unwrap()));

        // The classes report the module they can be imported from.
        let document = imported.getattr("Document").unwrap();
        let owner: String = document.getattr("__module__").unwrap().extract().unwrap();
        assert_eq!(owner, "biodivine_sys.xml_dom");
    });
}
