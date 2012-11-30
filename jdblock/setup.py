from distutils.core import setup

setup(
    name='JDBlocks',
    version='0.1',
    description='Static XBlocks from jasondavies.com',
    py_modules=['jdblocks'],
    entry_points={
        'xblock.v1': [
            'random-arboretum = jdblocks:RandomArboretum',
        ]
    }

)
