#!/usr/bin/env python

import os
from setuptools import setup, Command, find_packages

from pypandoc import convert

class CleanCommand(Command):
    """Custom clean command to tidy up the project root."""

    user_options = [
        ('all', None, '(Compatibility with original clean command)')
    ]
    def initialize_options(self):
        self.all = False
    def finalize_options(self):
        pass
    def run(self):
        os.system('rm -Rf ./*.egg-info')

setup(
    name='pysnapsync',
    version='0.1a0',
    description='Backup from LVM to btrfs, via rsync',
    long_description=convert('README.md', 'rst'),
    license='GPLv3+',
    author='David Taylor',
    author_email='davidt@yadt.uk',
    url='https://github.com/dtaylor84/pysnapsync',
    packages=find_packages(where='.'),
    package_data={
        'pysnapsync': ['pysnapsync.yaml'],
    },
    entry_points={
        'console_scripts': [
            'pysnapsync-client=pysnapsync.client:main',
            'pysnapsync-server=pysnapsync.server:main',
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
    cmdclass={
        'clean': CleanCommand,
    },
    install_requires=[
        'pyyaml',
        'pypandoc'
    ]
)
