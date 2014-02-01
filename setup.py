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
    ]
)
