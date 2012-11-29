from distutils.core import setup

setup(
    name='JDModules',
    version='0.1',
    description='Static XModules from jasondavies.com',
    py_modules=['jdmodules'],
    entry_points={
        'xmodule.v2': [
            'random-arboretum = jdmodules:RandomArboretum',
        ]
    }

)