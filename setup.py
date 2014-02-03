"""Set up for XBlock"""
from setuptools import setup

setup(
    name='XBlock',
    version='0.4a0',
    description='XBlock Core Library',
    packages=[
        'xblock',
        'xblock.django',
    ],
    install_requires=[
        'lxml',
        'webob',
    ]
)
