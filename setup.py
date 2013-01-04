from distutils.core import setup

setup(
    name='XBlock',
    version='0.1',
    description='XBlock Core Library',
    packages=['xblock', 'xblock_debugger'],
    entry_points={
        'xblock.v1': [
            'helloworld = xblock.content:HelloWorldBlock',
            'html = xblock.content:HtmlBlock',
            'sequence = xblock.structure:Sequence',
            'vertical = xblock.structure:VerticalBlock',
            'sidebar = xblock.structure:SidebarBlock',
            'problem = xblock.problem:ProblemBlock',
            'textinput = xblock.problem:TextInputBlock',
            'equality = xblock.problem:EqualityCheckerBlock',
            'attempts_scoreboard = xblock.problem:AttemptsScoreboardBlock',
            'thumbs = xblock.thumbs:ThumbsBlock',
            'slider = xblock.slider:Slider',
            'progress_slider = xblock.slider:ProgressSlider',
            'debugchild = xblock_debugger.blocks:DebuggingChildBlock',
        ]
    }
)
