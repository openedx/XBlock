from setuptools import setup

setup(
    name='chat-xblock',
    version='0.1',
    description='Chat XBlock Sample',
    py_modules=['chat'],
    install_requires=['XBlock'],
    entry_points={
        'xblock.v1': [
            'chat = chat:ChatBlock',
        ]
    }
)
