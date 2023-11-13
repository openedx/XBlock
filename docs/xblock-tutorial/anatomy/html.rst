.. _The XBlock HTML File:

####################
The XBlock HTML File
####################

This section of the tutorial walks through the HTML file, `thumbs.html`_,  that
is part of the Thumbs XBlock in the XBlock SDK.

If you completed the steps in :ref:`Build an XBlock Quick Start`, you can find
this file locally at ``xblock_development/xblock-sdk/sample_xblocks/thumbs/static/html/thumbs.html``.

In the XBlock HTML file, you define the HTML content that is added to a
:ref:`fragment <XBlock Fragments>`. The HTML content can reference the XBlock
:ref:`fields <XBlock Fields>`. The fragment is returned by the :ref:`view
method <View Methods>`, to be displayed by the :ref:`runtime <XBlock
Runtimes>` application.

.. include:: ../reusable/code_thumbs_html.rst

Note the following details about the HTML file.

* The ``class`` values reference styles in the ``thumbs.css`` file. For more
  information, see :ref:`The XBlock Stylesheets`.

* The values ``self.upvotes`` and ``self.downvotes`` reference the fields in
  the XBlock Python class.

.. include:: ../../links.rst
