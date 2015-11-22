"""Set up for XBlock"""
from setuptools import setup

setup(
    name='XBlock',
    version='0.4.4',
    description='XBlock Core Library',
    packages=[
        'xblock',
        'xblock.django',
        'xblock.reference',
        'xblock.test',
        'xblock.test.django',
    ],
    install_requires=[
        'lxml',
        'markupsafe',
        'python-dateutil',
        'pytz',
        'webob',
        'fs',
    ],
    extras_require={
        'django': ['django-pyfs']
    },
    license='Apache 2.0',
    classifiers=(
        "License :: OSI Approved :: Apache Software License 2.0",
    )
)
