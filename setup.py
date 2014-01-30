"""Set up for XBlock"""
from setuptools import setup

setup(
    name='XBlock',
    version='0.4a0',
    description='XBlock Core Library',
    packages=['xblock', 'workbench', 'demo_xblocks'],
    install_requires=[
        'webob',
    ]
)
