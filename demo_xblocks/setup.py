"""Set up for demo XBlocks"""
from setuptools import setup

setup(
    name='demo-xblocks',
    version='0.3',
    description='Sample XBlocks to demonstrate the core library',
    packages=['demo_xblocks'],
    install_requires=[
        'XBlock',
    ],
    entry_points={
        'xblock.v1': [
            'helloworld_demo = demo_xblocks.content:HelloWorldBlock',
            'html_demo = demo_xblocks.content:HtmlBlock',
            'sequence_demo = demo_xblocks.structure:Sequence',
            'vertical_demo = demo_xblocks.structure:VerticalBlock',
            'sidebar_demo = demo_xblocks.structure:SidebarBlock',
            'problem_demo = demo_xblocks.problem:ProblemBlock',
            'textinput_demo = demo_xblocks.problem:TextInputBlock',
            'equality_demo = demo_xblocks.problem:EqualityCheckerBlock',
            'attempts_scoreboard_demo = demo_xblocks.problem:AttemptsScoreboardBlock',
            'slider_demo = demo_xblocks.slider:Slider',
            'view_counter_demo = demo_xblocks.view_counter:ViewCounter',
        ]
    }
)
