"""Set up for XBlock"""
from setuptools import setup

import versioneer
versioneer.VCS = 'git'
versioneer.versionfile_source = 'xblock/_version.py'
versioneer.versionfile_build = 'xblock/_version.py'
versioneer.tag_prefix = 'xblock-'  # tags are like 1.2.0
versioneer.parentdir_prefix = 'XBlock-'  # dirname like 'myproject-1.2.0'

setup(
    name='XBlock',
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
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
