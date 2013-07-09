"""Script execution for script fragments in content."""

import textwrap


def run_script(pycode):
    """Run the Python in `pycode`, and return a dict of the resulting globals."""
    # Fix up the whitespace in pycode.
    if pycode[0] == "\n":
        pycode = pycode[1:]
    pycode.rstrip()
    pycode = textwrap.dedent(pycode)

    # execute it.
    globs = {}
    exec pycode in globs, globs  # pylint: disable=W0122

    return globs
