.. _The XBlock JavaScript File:

##########################
The XBlock JavaScript File
##########################

This section of the tutorial walks through the JavaScript file, `thumbs.js`_,
that is part of the Thumbs XBlock in the XBlock SDK.

If you completed the steps in :ref:`Build an XBlock Quick Start`, you can find
this file locally at ``xblock_development/xblock-sdk/sample_xblocks/thumbs/static/js/src/thumbs.js``.

In the XBlock JavaScript file, you define code that manages user interaction
with the XBlock. The code is added to a :ref:`fragment <XBlock
Fragments>`. 

The XBlock's JavaScript uses the runtime handler, and can use the ``children``
and ``childMap`` functions as needed.

The JavaScript references the XBlock :ref:`fields <XBlock Fields>`
and :ref:`methods <XBlock Methods>`. The fragment is returned by the :ref:`view
method <View Methods>`, to be displayed by the :ref:`runtime <XBlock Runtimes>`
application.

.. include:: ../reusable/code_thumbs_javascript.rst

Note the following details about the JavaScript file.

* The function ``ThumbsBlock`` initializes the XBlock. A JavaScript function to
  initialize the XBlock is required.

* The ``ThumbsBlock`` function maps to the constructor in the :ref:`XBlock
  Python file <The XBlock Python File>` and provides access to its methods and
  fields.

* The ``ThumbsBlock`` function uses the runtime handler.
  
  .. code-block:: javascript

    var handlerUrl = runtime.handlerUrl(element, 'vote');
  
* The ``ThumbsBlock`` function includes the ``POST`` commands to increase the up
  and down votes in the XBlock.
  
The XBlock JavaScript code can also use the ``children`` and ``childMap``
functions as needed. For more information, see :ref:`XBlock Children`.

.. include:: ../../links.rst
