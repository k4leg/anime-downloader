#!/usr/bin/env python

from setuptools import setup, find_packages

with open('README.md') as f:
    README = f.read()

setup(
    name='anime-downloader',
    version='1',
    url='https://github.com/k4leg/anime-downloader',
    author='k4leg',
    author_email='python.bogdan@gmail.com',
    classifiers=[
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: 3.8',
        'Environment :: Console',
        'Development Status :: 4 - Beta',
    ],
    license='GPL-3.0-or-later',
    description='Simple anime downloader',
    long_description=README,
    long_description_content_type='text/markdown',
    keywords='anime',
    python_requires='>=3.8',
    requires=['beautifulsoup4', 'requests', 'rich'],
    packages=find_packages(),
    scripts=['anime-downloader']
)
