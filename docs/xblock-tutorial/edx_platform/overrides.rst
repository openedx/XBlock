.. _Replace a Preinstalled XBlock With a Custom Implementation:

##########################################################
Replace a Preinstalled XBlock With a Custom Implementation
##########################################################

In XBlock ``v5.1.0``, the ability was introduced to override an XBlock with a custom
implementation.

This can be done by:

1. Creating an XBlock in a new or existing package installed into ``edx-platform``.

2. Adding the ``xblock.v1.overrides`` entry point in ``setup.py``, pointing to your
   custom XBlock.

This works with updated logic in ``load_class``'s ``default_select``, which gives
load priority to a class with the ``.overrides`` suffix.

This can be disabled by providing a different ``select`` kwarg to ``load_class`` which
ignores or otherwise changes override logic.

*******
Example
*******

Imagine there is an XBlock installed ``edx-platform``:

.. code:: python

    # edx-platform/xblocks/video_block.py
    class VideoBlock(XBlock):
    ...

    # edx-platform/setup.py
    setup(
        # ...

        entry_points={
            "xblock.v1": [
                "video = xblocks.video_block::VideoBlock"
                # ...
            ]
        }
    )

If you then create your own Python package with a custom version of that XBlock...

.. code:: python

    # your_plugin/xblocks/video_block.py
    class YourVideoBlock(XBlock):
    ...

    # your_plugin/setup.py
    setup(
        # ...
        entry_points={
            "xblock.v1.overrides": [
                "video = your_plugin.xblocks.video_block::YourVideoBlock"
                # ...
            ],
        }
    )

And install that package into your virtual environment, then your block should be
loaded instead of the existing implementation.

.. note::

    The ``load_class`` code will throw an error in the following cases:

    1. There are multiple classes attempting to override one XBlock implementation.

    2. There is an override provided where an existing XBlock implementation is not found.
