#!/usr/bin/env python
"""
Use cookiecutter to create a new XBlock project.
"""

import os
import textwrap

from cookiecutter.main import cookiecutter


EXPLANATION = """\
This script will create a new XBlock project.

You will be prompted for two pieces of information:

* short_name: a single word, all lower-case, for directory and file names.
  For a hologram 3-D XBlock, you might choose "holo3d".

* class_name: a valid Python class name.  It's best if this ends with "XBlock",
  so for our hologram XBlock, you might choose "Hologram3dXBlock".

Once you specify those two words, a directory will be created in the current
directory containing the new project.

If you don't want to create the project here, or you enter a name incorrectly,
just type Ctrl-C to stop this script.  If you don't want the resulting project,
just delete the directory it created.

"""


def main():
    print EXPLANATION

    # Find the prototype.
    proto_dir = os.path.abspath(os.path.join(__file__, "../../prototype"))

    cookiecutter(proto_dir)


if __name__ == "__main__":
    main()
