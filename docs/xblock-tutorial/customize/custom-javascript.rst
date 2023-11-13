.. _Customize myxblock.js:

#######################
Customize myxblock.js
#######################

This section describes how to modify the JavaScript file of the XBlock you
created, ``myxblock.js``, to provide the functionality in the Thumbs XBlock
example in the XBlock SDK.

In ``myxblock.js``, you will define code that manages user interaction
with the XBlock. The code is added to a :ref:`fragment <XBlock
Fragments>`. 

.. contents::
 :local:
 :depth: 1 

***********************************
The Default XBlock JavaScript File
***********************************

When you :ref:`create a new XBlock <Create Your First XBlock>`, the default
JavaScript file is created automatically, with skeletal functionality defined.
In the ``xblock_development/myxblock/myxblock/static/js/source`` directory, see
the file ``myxblock.js``.

.. include:: ../reusable/code_myxblock_js.rst

The file contains JavaScript code to increment the ``count`` field that was
added by default to the XBlock. Delete this code.

********************
Add JavaScript Code
********************

JavaScript code implements the browser-side functionality you need for your
XBlock. The Thumbs XBlock uses clicks on the up and down vote buttons to call
the handler to record votes.

Follow the guidelines below to implement JavaScript code.

* Add the function ``MyXBlock`` to initialize the XBlock. 

  The ``MyXBlock`` function maps to the constructor in the :ref:`XBlock
  Python file <The XBlock Python File>` and provides access to its methods and
  fields.

* Add the URL to the vote handler to the ``MyXBlock`` function.
  
  .. code-block:: javascript

    var handlerUrl = runtime.handlerUrl(element, 'vote');
  
* Add ``Post`` commands in the ``MyXBlock`` function to increase the up and
  down votes in the XBlock.

  .. note:: Do not change the main function name, ``MyXBlock``.

*******************************************
Check JavaScript Against the Thumbs XBlock
*******************************************

After you have defined the JavaScript code, check your work against the code in
the Thumbs XBlock, in the file ``xblock_development/xblock-sdk/sample_xblocks/thumbs/static/js/source/thumbs.js``.

.. include:: ../reusable/code_thumbs_javascript.rst

If necessary, make corrections to the code in your XBlock so that it
matches the code in the Thumbs XBlock.

**********************************
Next Step
**********************************

After you complete your customizations to the JavaScript file, you continue on
and :ref:`customize the XBlock CSS file<Customize myxblock.css>`.

.. include:: ../../links.rst
