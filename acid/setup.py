"""Set up for XBlock acid module"""

from setuptools import setup

setup(
    name='acid-xblock',
    version='0.1',
    description='Acid XBlock Test',
    py_modules=['acid'],
    install_requires=['XBlock'],
    entry_points={
        'xblock.v1': [
            'acid = acid:AcidBlock',
        ]
    },
    package_data={
        'acid': ['static/*'],
    },
)
