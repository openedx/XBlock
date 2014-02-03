"""Set up for XBlock"""
from setuptools import setup

setup(
    name='XBlock',
    version='0.4a0',
    description='XBlock Core Library',
    packages=[
        'xblock',
        'workbench',
        'acid',
        'demo_xblocks',
        'thumbs',
    ],
    package_dir={
        'acid': 'acid/acid',
        'demo_xblocks': 'demo_xblocks/demo_xblocks',
        'thumbs': 'thumbs/thumbs'
    },
    install_requires=[
        'Django >= 1.4, < 1.5',
        'lxml',
        'requests',
        'webob',
        'WSGIProxy',
        'simplejson'
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
