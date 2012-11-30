from distutils.core import setup

setup(
    name='XModuleDebugger',
    version='0.1',
    description='XModule Debugger',
    package_dir={'debugger': ''},
    packages=['debugger'],
    entry_points={
        'xmodule.v2': [
            'debugchild = debugger.views:DebuggingChildModule',
        ]
    }
)
