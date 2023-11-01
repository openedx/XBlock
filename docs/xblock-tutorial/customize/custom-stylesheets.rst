.. _Customize myxblock.css:

#######################
Customize myxblock.css
#######################

This section describes how to modify the static CSS file of the XBlock you
created, ``myxblock.css``, to provide the functionality in the Thumbs XBlock
example in the XBlock SDK.

In ``myxblock.css``, you define the styles that are added to the
fragment that is returned by the view method to be displayed by the runtime
application.

.. contents::
 :local:
 :depth: 1 

*******************************
The Default XBlock CSS File
*******************************

When you :ref:`create a new XBlock <Create Your First XBlock>`, the default
static CSS file is created automatically, with skeletal functionality defined.
In the ``xblock_development/myxblock/myxblock/static/css`` directory, see the
file ``myxblock.css``.

.. include:: ../reusable/code_myxblock_css.rst

The file contains CSS code to format the ``count`` field that was added by
default to the XBlock. Delete this code.

********************
Add CSS Code
********************

You must add CSS code to format the XBlock content. Follow the guidelines
below.

* Create a single class that defines formatting for ``.upvote`` and
  ``.downvote``.

* The cursor type is pointer.
  
* The border is 1px, solid, and with the color #888.
  
* The padding is ``0.5em``;
  
* The color for ``.upvote`` is green and for ``downvote`` is red.

****************************************
Check CSS Against the Thumbs XBlock
****************************************

After you have defined the CSS code, check your work against the CSS in the
Thumbs XBlock, in the file ``xblock_development/xblock-sdk/sample_xblocks/thumbs/static/css/thumbs.css``.

.. include:: ../reusable/code_thumbs_css.rst

If necessary, make corrections to the CSS code in your XBlock so that it
matches the code in the Thumbs XBlock.

The styles in ``thumbs.css`` are referenced in the :ref:`XBlock HTML file <The
XBlock HTML File>`.

.. include:: ../../links.rst
