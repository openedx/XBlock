"""Set up for XBlock"""
from setuptools import setup

setup(
    name='XBlock',
    version="0.4.3",
    description='XBlock Core Library',
    packages=[
        'xblock',
        'xblock.django',
        'xblock.reference',
    ],
    install_requires=[
        'lxml',
        'markupsafe',
        'python-dateutil',
        'pytz',
        'webob',
    ],
    license='Apache 2.0',
    classifiers=(
        "License :: OSI Approved :: Apache Software License 2.0",
    )
)
