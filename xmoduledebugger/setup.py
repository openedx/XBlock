from distutils.core import setup

setup(
    name='XModuleDebugger',
    version='0.1',
    description='XModule Debugger',
    package_dir={'xmoduledebugger': ''},
    packages=['xmoduledebugger'],
    entry_points={
        'xmodule.v2': [
            'debugchild = xmoduledebugger.views:DebuggingChildModule',
        ]
    }
)