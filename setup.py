"""Set up for XBlock"""
from setuptools import setup

setup(
    name='XBlock',
    version='0.2',
    description='XBlock Core Library',
    packages=['xblock'],
    install_requires=[
        'webob',
    ],
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
            'slider = xblock.slider:Slider',
            'progress_slider = xblock.slider:ProgressSlider',
            'view_counter = xblock.view_counter:ViewCounter'
        ]
    }
)
