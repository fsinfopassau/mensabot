#!/usr/bin/env python3

from codecs import open
from os import path

from setuptools import setup

here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

version = '0.5.0'

setup(
    name='stwno-cmds',
    version=version,
    description='API for the canteens and cafeterias of the `Studentenwerk Niederbayern-Oberpfalz`',
    long_description=long_description,
    url='https://github.com/N-Coder/mensabot',
    author='Niko Fink',
    license='MIT',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.6',
    ],
    entry_points={
        "console_scripts": [
            "mensa = stwno_cmds.main:mensa",
            "cafete = stwno_cmds.main:cafete",
            "mensa-diff = stwno_cmds.main:diff"
        ]
    },
    packages=["data", "stwno_cmds"],
    package_dir={"data": "stwno_cmds/translations/dateparser", "stwno_cmds": "stwno_cmds"},
    package_data={
        'stwno_cmds': ['templates/*', 'templates/*/*', 'templates/*/*/*', 'translations/*',
                       'translations/dateparser*'],
        'data': ['*.yaml']
    },
    install_requires=[
        'stwno-api==%s' % version,
        'dateparser',
        'jinja2',
        'babel',
        'pyyaml',
    ]
)
