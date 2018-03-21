#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup
from setuptools import find_packages


VERSION = '0.0.2'
REQUIRES = ['requests>=2.12.3', 'fire>=0.1.3']


setup(
    name='fluxx_wrapper',
    packages=find_packages(),
    version=VERSION,
    description='A simple wrapper around Fluxx GMS\'s REST API.',
    author='Connor Sullivan',
    author_email='sully4792@gmail.com',
    install_requires=REQUIRES,
    python_requires='>=3',
    url='https://github.com/condad/fluxx-python-sdk',
    download_url='https://github.com/condad/fluxx-python-sdk/tarball/' + VERSION,
    keywords=['fluxx', 'gms', 'api', 'wrapper'],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    entry_points={
        'console_scripts': [
            'fluxx-cli = fluxx.cli:main',
        ],
    },
)
