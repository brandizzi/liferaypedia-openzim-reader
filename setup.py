#!/usr/bin/env python
from setuptools import setup, find_packages

setup(
    name="liferaypedia-openzim-reader",
    version="0.0.1.dev1",
    author='Adam Victor Brandizzi',
    author_email='adam@brandizzi.com.br',
    description='liferaypedia-openzim-reader',
    license='LGPLv3',
    url='https://github.com/brandizzi/liferaypedia-openzim-reader',

    packages=find_packages(),
    test_suite='liferaypedia-openzim-reader.tests',
    test_loader='unittest:TestLoader',
)
