##############################################################################
#
# Copyright (c) 2008 Agendaless Consulting and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the BSD-like license at
# http://www.repoze.org/LICENSE.txt.  A copy of the license should accompany
# this distribution.  THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL
# EXPRESS OR IMPLIED WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO,
# THE IMPLIED WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND
# FITNESS FOR A PARTICULAR PURPOSE
#
##############################################################################

__version__ = '0.6.1'

import os

from ez_setup import use_setuptools
use_setuptools()

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.txt')).read()
CHANGES = open(os.path.join(here, 'CHANGES.txt')).read()

requires = [
    'setuptools',
    'repoze.zcml',
    'zope.component',
    'zope.interface',
    'zope.configuration>=3.8.0',
    ]

tests_requires = requires + [
    'zope.testing',
    'repoze.sphinx.autointerface',
    ]

testing_extras = tests_requires + ['nose', 'coverage']

setup(
    name='repoze.workflow',
    version=__version__,
    description='Content workflow for repoze.bfg',
    long_description=README + '\n\n' +  CHANGES,
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
    ],
    keywords='web repoze workflow',
    author="Agendaless Consulting",
    author_email="repoze-dev@lists.repoze.org",
    url="http://www.repoze.org",
    license="BSD-derived (http://www.repoze.org/LICENSE.txt)",
    packages=find_packages(),
    include_package_data=True,
    namespace_packages=['repoze'],
    zip_safe=False,
    tests_require = tests_requires,
    install_requires= requires,
    test_suite="repoze.workflow",
    entry_points = """
    """,
    extras_require={
        'testing': testing_extras,
    },
)
