.. _fragment:

========
Fragment
========

When XBlock views are used to make a web page, each block produces just one
piece of the page, by returning a Fragment. A Fragment carries content (usually
HTML) and resources (for example, Javascript and CSS) needed by the content.
These allow for the composition of HTML, Javascript and CSS elements in a
predictable fashion.

Widgets have a number of attributes:

* Content: Content is most often HTML, but could also have an arbitrary
  mimetype. Each widget only has a single content value.

* Javascript: Javascript resources can include both external files to link to,
  and inline Javascript source code. When widgets are composed, external
  Javascript links will be uniqued, so that any individual page isn't loaded
  multiple times.

* CSS: Like Javascript, CSS can be both external and inline, and the external
  resources will be uniqued when widgets are composed.

* Javascript initializer: The Javascript specified for a widget can also
  specify a function to be called when that widget is rendered on the page.
  This function will be passed the DOM element containing all of the content
  from the widget, and is then expected to execute any code needed to make that
  widget operational. The Javascript view will also be passed a Javascript
  runtime object containing a set of functions that generate links back to the
  XBlocks handlers and views on the runtime server.

Since XBlocks nest hierarchically, a single XBlock view might require
collecting renderings from each of its children, and composing them together.
The parent will be responsible for deciding how the children's content composes
together to create the parent content. The widget system has utilities for
composing children's resources together into the parent.

Other information on widgets [[TODO: write this for realz]]:

    Caching information specifying how long a widget can be cached for. This
    can be specified at widget creation, or by using a decorator on the view
    function (if the cache duration is known ahead of time)


Fragment API
------------

.. module:: xblock.fragment
.. autoclass:: Fragment
    :members:
