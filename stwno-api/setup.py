#!/usr/bin/env python3

from codecs import open
from os import path

from setuptools import find_packages, setup

here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

version = '0.5.0'

setup(
    name='stwno-api',
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
    packages=find_packages(),
    install_requires=[
        'requests',
        'beautifulsoup4',
        'cached_property',
        'fuzzywuzzy'
    ]
)
