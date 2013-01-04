from distutils.core import setup

setup(
    name='XBlockDebugger',
    version='0.1',
    description='XBlock Debugger',
    package_dir={'debugger': ''},
    packages=['debugger'],
    entry_points={
        'xblock.v1': [
            'debugchild = debugger.blocks:DebuggingChildBlock',
        ]
    }
)
