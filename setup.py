#!/usr/bin/env python

"""
Set up for XBlock
"""

import os.path
from setuptools import setup

version_file = os.path.join(os.path.dirname(__file__), 'xblock/VERSION.txt')

setup(
    name='XBlock',
    version=open(version_file).read().strip(),
    description='XBlock Core Library',
    packages=[
        'xblock',
        'xblock.django',
        'xblock.reference',
        'xblock.test',
        'xblock.test.django',
    ],
    include_package_data=True,
    install_requires=[
        'fs',
        'lxml',
        'markupsafe',
        'python-dateutil',
        'pytz',
        'pyyaml',
        'six',
        'webob',
    ],
    extras_require={
        'django': ['django-pyfs']
    },
    license='Apache 2.0',
    classifiers=(
        "License :: OSI Approved :: Apache Software License 2.0",
    )
)
