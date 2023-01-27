#!/usr/bin/env python

"""
Set up for XBlock
"""
import codecs
import os
import os.path
import re

from setuptools import setup


def get_version(*file_paths):
    """
    Extract the version string from the file at the given relative path fragments.
    """
    filename = os.path.join(os.path.dirname(__file__), *file_paths)
    with open(filename, encoding='utf-8') as opened_file:
        version_file = opened_file.read()
        version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]",
                                  version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError('Unable to find version string.')


VERSION = get_version("xblock", "__init__.py")


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
        'webob',
        'web-fragments',
    ],
    extras_require={
        'django': ['openedx-django-pyfs >= 1.0.5', 'lazy']
    },
    author='edX',
    author_email='oscm@edx.org',
    url='https://github.com/openedx/XBlock',
    license='Apache 2.0',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Framework :: Django',
        'Framework :: Django :: 3.2',
        'Framework :: Django :: 4.0',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
    ]
)
