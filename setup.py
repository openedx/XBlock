#!/usr/bin/env python

"""
Set up for XBlock
"""
import codecs
import os.path
from setuptools import setup

VERSION_FILE = os.path.join(os.path.dirname(__file__), 'xblock/VERSION.txt')
with codecs.open(VERSION_FILE, encoding='ascii') as f:
    VERSION = f.read().strip()

setup(
    name='XBlock',
    version=VERSION,
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
        'web-fragments',
    ],
    extras_require={
        'django': ['django-pyfs >= 1.0.5', 'lazy']
    },
    author='edX',
    author_email='oscm@edx.org',
    url='https://github.com/edx/XBlock',
    license='Apache 2.0',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Framework :: Django',
        'Framework :: Django :: 2.2',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.8",
    ]
)
