#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import io

from setuptools import setup
from setuptools import find_packages

if sys.argv[-1] == 'test':
    os.system('python -sm unittest discover tests "*_test.py"')
    sys.exit(0)

if sys.argv[-1] == 'publish':
    os.system('python setup.py sdist')
    os.system('twine upload dist/*')
    sys.exit()

with io.open('README.md', 'rt', encoding='utf8') as f:
    README = f.read()


VERSION = '0.0.7'
REQUIRES = ['requests>=2.12.3', 'fire>=0.1.3']


setup(
    name='fluxx_wrapper',
    packages=find_packages(),
    version=VERSION,
    description='A simple wrapper around Fluxx GMS\'s REST API.',
    long_description=README,
    long_description_content_type='text/markdown',
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
