from xmodule.core import StaticXModule
print StaticXModule

class RandomArboretum(StaticXModule):
    view_names = ["student_view"]
    content = "random-arboretum.html"
    urls = [
        ('d3.v2.min.js', 'application/javascript'),
        ('arboretum.js', 'application/javascript'),
        ('random-arboretum.css', 'text/css'),
    ]
    initialize_js = 'start_arboretum'
