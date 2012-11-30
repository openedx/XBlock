from distutils.core import setup

setup(
    name='XModule',
    version='0.1',
    description='XModule Core Library',
    package_dir={'xmodule': ''},
    packages=['xmodule'],
    entry_points={
        'xmodule.v2': [
            'thumbs = xmodule.core:ThumbsModule',
            'helloworld = xmodule.core:HelloWorldModule',
            'vertical = xmodule.core:VerticalModule',
            'problem = xmodule.problem:ProblemModule',
            'textinput = xmodule.problem:TextInputModule',
        ]
    }
)