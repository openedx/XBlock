from distutils.core import setup

setup(
    name='XBlock',
    version='0.1',
    description='XBlock Core Library',
    package_dir={'xblock': ''},
    packages=['xblock'],
    entry_points={
        'xblock.v1': [
            'helloworld = xblock.content:HelloWorldBlock',
            'html = xblock.content:HtmlBlock',
            'sequence = xblock.structure:Sequence',
            'vertical = xblock.structure:VerticalBlock',
            'problem = xblock.problem:ProblemBlock',
            'textinput = xblock.problem:TextInputBlock',
            'equality = xblock.problem:EqualityCheckerBlock',
            'thumbs = xblock.thumbs:ThumbsBlock',
            'slider = xblock.slider:Slider',
            'progress_slider = xblock.slider:ProgressSlider',
        ]
    }
)
