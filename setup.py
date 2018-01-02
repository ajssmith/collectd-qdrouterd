#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""

from setuptools import setup, find_packages

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

requirements = [
    # TODO: put package requirements here
]

setup_requirements = [
    # TODO(ajssmith): put setup requirements (distutils extensions, etc.) here
]

test_requirements = [
    # TODO: put package test requirements here
]

setup(
    name='collectd-qdrouterd',
    version='0.1.0',
    description="A collectd plugin, written in python, to collect statistics from Qpid Dispatch Router",
    long_description=readme + '\n\n' + history,
    author="Andy Smith",
    author_email='ansmith@redhat.com',
    url='https://github.com/ajssmith/collectd-qdrouterd',
    packages=find_packages(include=['collectd_qdrouterd']),
    include_package_data=True,
    install_requires=requirements,
    license="Apache Software License 2.0",
    zip_safe=False,
    keywords='collectd-qdrouterd',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
    test_suite='tests',
    tests_require=test_requirements,
    setup_requires=setup_requirements,
)
