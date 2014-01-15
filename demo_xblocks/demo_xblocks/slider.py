"""Simple XBlock with a slider interface.

WARNING: This is an experimental module, subject to future change or removal.
"""

import json
from webob import Response

from xblock.core import XBlock
from xblock.fields import Scope, Integer
from xblock.fragment import Fragment


class Slider(XBlock):
    """Base XBlock with a slider interface."""
    min_value = Integer(help="Minimum value", default=0, scope=Scope.content)
    max_value = Integer(help="Maximum value", default=100, scope=Scope.content)
    value = Integer(help="Student value", default=0, scope=Scope.user_state)

    def student_view(self, context):  # pylint: disable=W0613
        """Provide the default student view."""
        html = SLIDER_TEMPLATE.format(min=self.min_value,
                                      max=self.max_value,
                                      val=self.value)
        frag = Fragment(html)
        frag.add_css("input[type=range] { width=100px; }")
        frag.add_javascript(SLIDER_JS)
        frag.initialize_js('Slider')

        return frag

    def update(self, request):
        """Update upon request."""
        data = json.loads(request.body)
        self.value = int(data['value'])
        return Response()


SLIDER_TEMPLATE = u"""
<input type="range" min="{min}" max="{max}" value="{val}"/> <span> {val} </span>
"""

SLIDER_JS = """
function Slider(runtime, element) {
  if (!(this instanceof Slider)) {
    return new Slider(runtime, element);
  }

  this.handlerUrl = runtime.handlerUrl(element, 'update');

  this.input = $(element).children('input[type="range"]');
  this.output = $(element).children('span');

  var self = this;

  self.input.on('change', function () {
    self.output.html(this.value);
  });

  self.input.on('mouseup', function () {
    $.post(self.handlerUrl, JSON.stringify({value: this.value}));
  });
};

Slider.prototype.submit = function() {
  return this.input.val();
};

Slider.prototype.handleSubmit = function(result) {
};
"""
