"""Set up for XBlock"""
from setuptools import setup

setup(
    name='XBlock',
    version='0.3',
    description='XBlock Core Library',
    packages=['xblock'],
    install_requires=[
        'webob',
    ],
    entry_points={
        'xblock.v1': [
            'helloworld_demo = xblock.content:HelloWorldBlock',
            'html_demo = xblock.content:HtmlBlock',
            'sequence_demo = xblock.structure:Sequence',
            'vertical_demo = xblock.structure:VerticalBlock',
            'sidebar_demo = xblock.structure:SidebarBlock',
            'problem_demo = xblock.problem:ProblemBlock',
            'textinput_demo = xblock.problem:TextInputBlock',
            'equality_demo = xblock.problem:EqualityCheckerBlock',
            'attempts_scoreboard_demo = xblock.problem:AttemptsScoreboardBlock',
            'slider_demo = xblock.slider:Slider',
            'view_counter_demo = xblock.view_counter:ViewCounter',
        ]
    }
)
