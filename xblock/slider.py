import json
from webob import Response

from xblock.core import XBlock, Scope, Integer
from xblock.widget import Widget

class Slider(XBlock):
    min_value = Integer(help="Minimum value", default=0, scope=Scope.content)
    max_value = Integer(help="Maximum value", default=100, scope=Scope.content)
    value = Integer(help="Student value", default=0, scope=Scope.student_state)

    @XBlock.view('student_view')
    def render_student(self, context):
        html = SLIDER_TEMPLATE.format(min=self.min_value,
                                      max=self.max_value,
                                      val=self.value)
        widget = Widget(html)
        widget.add_css("input[type=range] { width=100px; }")
        widget.add_javascript(SLIDER_JS);
        widget.initialize_js('Slider')

        return widget

    @XBlock.handler('update')
    def handle_update(self, request):
        data = json.loads(request.body)
        self.value = int(data['value'])
        return Response()


class ProgressSlider(Slider):
    @XBlock.view('student_view')
    def render_student(self, context):
        widget = super(ProgressSlider, self).render_student(context)

        # TODO: [rocha] non-wrapped ccs will make this global
        #               not what we want
        #
        # widget.add_css("input[type=range] + span { color: red; }")

        # TODO: [rocha] initial progress - could on in constructor or initializer
        self.runtime.publish('progress', (self.value, self.max_value))

        widget.add_javascript(P_SLIDER_JS)
        widget.initialize_js('ProgressSlider')
        return widget

    @XBlock.handler('update')
    def handle_progress(self, request):
        response = super(ProgressSlider, self).handle_update(request)
        self.runtime.publish('progress', (self.value, self.max_value))
        return response

SLIDER_TEMPLATE = """
<input type="range" min="{min}" max="{max}" value="{val}"/> <span> {val} </span>
"""

SLIDER_JS = """
function Slider(runtime, element) {
  if (!(this instanceof Slider)) {
    return new Slider(runtime, element);
  }

  this.handler_url = runtime.handler_url('update');
  this.input = $(element).children('input[type="range"]');
  this.output = $(element).children('span');

  var self = this;

  self.input.on('change', function () {
    self.output.html(this.value);
  });

  self.input.on('mouseup', function () {
    $.post(self.handler_url, JSON.stringify({value: this.value}));
  });
};

Slider.prototype.submit = function() {
  return this.input.val();
};

Slider.prototype.handle_submit = function(result) {
};
"""

P_SLIDER_JS = """
function ProgressSlider(runtime, element) {
  if (!(this instanceof ProgressSlider)) {
    return new ProgressSlider(runtime, element);
  }

  Slider.call(this, runtime, element);

  $(element).css('color','red');

  this.input.on('mouseup', function() {
    console.log('updating progress');
  });
}

ProgressSlider.prototype = Object.create(Slider.prototype);
"""
