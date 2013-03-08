from distutils.core import setup

setup(
    name='XBlockWorkbench',
    version='0.1',
    description='XBlock Workbench',
    package_dir={'workbench': ''},
    packages=['workbench'],
    entry_points={
        'xblock.v1': [
            'debugchild = workbench.blocks:DebuggingChildBlock',
        ]
    }
)
