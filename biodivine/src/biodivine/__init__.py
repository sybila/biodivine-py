"""Python interface of the Biodivine libraries.

Each Biodivine library is a submodule of this package:

* :mod:`biodivine.xml_dom` - an XML DOM with safe namespace handling and thread-safe documents
  (the Rust crate ``biodivine-lib-xml-dom``).

The submodules are idiomatic Python wrappers around the native ``biodivine_sys`` extension, which
contains the Rust implementation of every library. All libraries share that one extension, so the
objects of one library can be passed to another one directly.

Example::

    import biodivine.xml_dom as xml

    document = xml.Document.parse("<root><child/></root>")
    print(document.root.children())   # [Element('child', id=1)]
"""

from biodivine_sys import __version__ as __version__

from . import xml_dom as xml_dom

__all__ = ["__version__", "xml_dom"]
