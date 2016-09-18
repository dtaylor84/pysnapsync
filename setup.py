#!/usr/bin/env python
"""PySnapSync setup.py.

Setup script for PySnapSync application.
"""


from __future__ import absolute_import
from __future__ import print_function
from __future__ import division

from setuptools import setup, find_packages

from pypandoc import convert

setup(
    name='pysnapsync',
    version='0.1a1',
    description='Backup from LVM to btrfs, via rsync',
    long_description=convert('README.md', 'rst'),
    license='GPLv3+',
    author='David Taylor',
    author_email='davidt@yadt.uk',
    url='https://github.com/dtaylor84/pysnapsync',
    packages=find_packages(where='.'),
    package_data={
        'pysnapsync.client': [
            'snapsync.yaml',
            'config-schema.yaml',
        ],
    },
    entry_points={
        'console_scripts': [
            'snapsync=pysnapsync.client.snapsync:main',
            'snapsync_rsync=pysnapsync.server.snapsync_rsync:main',
        ],
    },
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Environment :: Console',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: System :: Archiving :: Backup',
    ],
    install_requires=[
        'ruamel.yaml',
        'pypandoc'
    ]
)
