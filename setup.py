#!/usr/bin/env python

"""
Set up for XBlock
"""
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
    long_description=open('README.rst').read(),
    long_description_content_type='text/x-rst',
    packages=[
        'xblock',
        'xblock.django',
        'xblock.reference',
        'xblock.utils',
        'xblock.test',
        'xblock.test.django',
        'xblock.test.utils',
    ],
    include_package_data=True,
    package_data={
        'xblock.utils': ['public/*', 'templates/*', 'templatetags/*'],
        'xblock.test.utils': ['data/*'],
    },
    install_requires=[
        'fs',
        'lxml',
        'mako',
        'markupsafe',
        'python-dateutil',
        'pytz',
        'pyyaml',
        'simplejson',
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
        'Framework :: Django :: 4.2',
        'Framework :: Django :: 5.2',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ]
)
