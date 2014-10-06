#!/usr/bin/env python
from setuptools import setup, find_packages

setup(
    name='auspost-apis',
    version=":versiontools:auspost:",
    url='https://github.com/elbaschid/auspost-apis',
    author="Sebastian Vetter",
    author_email="sebastian.vetter@tangentsnowball.com.au",
    description="A Python wrapper around Australia Post's APIs",
    long_description=open('README.rst').read(),
    keywords="wrapper, logistics, delivery, post, Australia",
    license='BSD',
    platforms=['linux'],
    packages=find_packages(exclude=["sandbox*", "tests*"]),
    include_package_data=True,
    install_requires=[
        'versiontools>=1.9.1',
        'requests>=1.0.2',
        'python-dateutil>=2.1',
        'pytz>=2012d',
    ],
    # See http://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
      'Environment :: Web Environment',
      'Intended Audience :: Developers',
      'License :: OSI Approved :: BSD License',
      'Operating System :: Unix',
      'Programming Language :: Python'
    ]
)
