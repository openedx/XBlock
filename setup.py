"""Set up for XBlock"""
from setuptools import setup

setup(
    name='XBlock',
    version='0.4a1',
    author='edX',
    description='XBlock Core Library',
    packages=[
        'xblock',
        'xblock.django',
    ],
    install_requires=[
        'lxml',
        'webob',
        'pytz',
        'python-dateutil',
    ],
    license='AGPL',
    classifiers=[
        "Topic :: Education",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU Affero General Public License v3",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
    ]
)
