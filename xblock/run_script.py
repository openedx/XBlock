"""
Script execution for script fragments in content.
"""
import typing as t

import textwrap


def run_script(pycode: str) -> dict[str, t.Any]:
    """Run the Python in `pycode`, and return a dict of the resulting globals."""
    # Fix up the whitespace in pycode.
    if pycode[0] == "\n":
        pycode = pycode[1:]
    pycode.rstrip()
    pycode = textwrap.dedent(pycode)

    # execute it.
    globs: dict[str, t.Any] = {}
    exec(pycode, globs, globs)  # pylint: disable=W0122

    return globs
