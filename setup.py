from codecs import open
from os import path

from setuptools import find_packages, setup

here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='mensabot',
    version='0.2.1',
    description='telegram bot for uni passau mensa',
    long_description=long_description,
    url='https://github.com/N-Coder/mensabot',
    author='Niko Fink',
    license='MIT',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.5',
    ],
    entry_points={
        "console_scripts": [
            "mensabot = mensabot.bot:main"
        ]
    },
    packages=find_packages(),
    package_data={
        'mensabot': ['templates', 'languages'],
    },
    install_requires=[
        'dateparser',
        'requests',
        'beautifulsoup4',
        'jinja2',
        'regex',
        'babel',
        'python-telegram-bot',
        'sqlalchemy',
    ]
)
