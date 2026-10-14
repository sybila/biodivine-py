"""Interrupting long operations from Python.

On the main thread, a Python signal handler (the one behind Ctrl+C, or one installed with
``signal.signal``) can interrupt a whole-document operation: the operation stops early and the
exception the handler raised is propagated unchanged. The handler runs while no document lock is
held, so it may even use the document that the interrupted operation was working on.
"""

from __future__ import annotations

import signal
import subprocess
import sys
import textwrap
import time
from pathlib import Path

import pytest

import biodivine.xml_dom as xml

pytestmark = pytest.mark.skipif(
    not hasattr(signal, "setitimer"), reason="needs signal.setitimer (Unix)"
)

#: Large enough that every operation below takes far longer than the timer delay. Not larger: the
#: test holds several copies of the document at once (about 1 GB in total), and on a CI runner
#: with little memory, a larger document made every operation, interrupted or not, unpredictably
#: slow.
SOURCE = "<root>" + "<item a='1'>text</item>" * 400_000 + "</root>"


class Interrupted(Exception):
    """Raised by the test signal handler."""


def _raise_interrupted(signum: int, frame: object) -> None:
    raise Interrupted()


def _interrupt(action, between=None) -> None:
    """Runs ``action`` twice: once to time it, then with a timer that raises `Interrupted` a tenth
    of the way in, and checks that the second run raises it. ``between`` runs between the two (to
    clean up after the first run).

    This does not check *when* the exception surfaces, or whether the operation stopped early: the
    timing of a CI runner varies too much for either (even a timer at a tenth of the first run can
    fire after the second run has finished), and an operation that finished would still raise the
    exception right after returning. What it checks is that the handler's exception reaches the
    caller unchanged, and the tests below check that an interrupted operation leaves a consistent
    state behind.
    """
    started = time.perf_counter()
    action()
    duration = time.perf_counter() - started
    if between is not None:
        between()
    previous = signal.signal(signal.SIGALRM, _raise_interrupted)
    signal.setitimer(signal.ITIMER_REAL, duration / 10)
    try:
        with pytest.raises(Interrupted):
            action()
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)


def test_a_signal_handler_exception_interrupts_every_long_operation() -> None:
    document = xml.Document.parse(SOURCE)
    actions = {
        "parse(str)": lambda: xml.Document.parse(SOURCE),
        "parse(bytes)": lambda: xml.Document.parse(SOURCE.encode()),
        "write": document.write,
        "validate": document.validate,
        "is_valid": document.is_valid,
        "validation_errors": document.validation_errors,
    }
    for name, action in actions.items():
        try:
            _interrupt(action)
        except BaseException as error:
            raise AssertionError(name) from error


def test_an_interrupted_copy_leaves_the_documents_intact() -> None:
    document = xml.Document.parse(SOURCE)
    target = xml.Document()
    nodes = document.node_count
    # Whether the copy stopped in the middle (and freed what it had copied) or the signal came only
    # after it finished (leaving the copy as garbage), nothing is left once garbage is collected.
    _interrupt(document.root.deep_clone, between=document.collect_garbage)
    document.collect_garbage()
    assert document.node_count == nodes
    assert document.is_valid()
    _interrupt(lambda: document.root.deep_clone_into(target), between=target.collect_garbage)
    target.collect_garbage()
    assert target.node_count == 0


def test_an_interrupted_write_file_can_be_repeated(tmp_path: Path) -> None:
    document = xml.Document.parse(SOURCE)
    path = tmp_path / "document.xml"
    _interrupt(lambda: document.write_file(path))
    # The file may hold part of the document; writing it again replaces it with all of it.
    document.write_file(path)
    assert path.read_text(encoding="utf-8") == document.write()


def test_a_handler_may_use_the_interrupted_document() -> None:
    # Run in a subprocess, so that a regression (a deadlock) fails the test instead of hanging it.
    script = textwrap.dedent(
        """
        import signal
        import biodivine.xml_dom as xml

        document = xml.Document.parse("<root>" + "<item/>" * 400_000 + "</root>")
        def handler(signum, frame):
            document.root.append_child(document.create_element("late"))
        signal.signal(signal.SIGALRM, handler)
        signal.setitimer(signal.ITIMER_REAL, 0.01, 0.01)
        for _ in range(5):
            document.validate()
            document.collect_garbage()
        signal.setitimer(signal.ITIMER_REAL, 0)
        print("done")
        """
    )
    result = subprocess.run(
        [sys.executable, "-c", script], capture_output=True, text=True, timeout=120
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "done"
