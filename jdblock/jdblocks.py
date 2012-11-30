from xblock.core import StaticXBlock
print StaticXBlock

class RandomArboretum(StaticXBlock):
    view_names = ["student_view"]
    content = "random-arboretum.html"
    urls = [
        ('d3.v2.min.js', 'application/javascript'),
        ('arboretum.js', 'application/javascript'),
        ('random-arboretum.css', 'text/css'),
    ]
    initialize_js = 'start_arboretum'
