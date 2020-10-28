#!/usr/bin/env python

# Copyright (C) 2020 k4leg <python.bogdan@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

from setuptools import find_packages, setup

with open('README.md') as f:
    README = f.read()

setup(
    name='anime-downloader',
    version='0.1',
    url='https://github.com/k4leg/anime-downloader',
    author='k4leg',
    author_email='python.bogdan@gmail.com',
    classifiers=[
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Environment :: Console',
        'Development Status :: 4 - Beta',
    ],
    license='GPL-3.0-or-later',
    description='Simple anime downloader',
    long_description=README,
    long_description_content_type='text/markdown',
    keywords='anime',
    python_requires='>=3.8',
    requires=['beautifulsoup4', 'click', 'requests', 'rich'],
    packages=find_packages(),
    scripts=['anime-downloader'],
)
