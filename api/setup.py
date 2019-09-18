#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""

from glob import glob
from os.path import abspath, basename, dirname, join, splitext

from setuptools import setup, find_packages

with open("README.rst") as readme_file:
    readme = readme_file.read()

with open("HISTORY.rst") as history_file:
    history = history_file.read()

here = abspath(dirname(__file__))
# We're using a pip8 style requirements file, which allows us to embed hashes
# of the packages in it. However, setuptools doesn't support parsing this type
# of file, so we need to strip those out before passing the requirements along
# to it.
with open(join(here, "requirements", "base.txt")) as f:
    requirements = []
    for line in f:
        # Skip empty and comment lines
        if not line.strip() or line.strip().startswith("#"):
            continue
        # Skip lines with hash values
        if not line.strip().startswith("--"):
            requirements.append(line.split(";")[0].split()[0])
            requirement_without_python_filter = line.split(";")[0]
            requirement_without_trailing_characters = requirement_without_python_filter.split()[0]

setup_requirements = ["pytest-runner"]

test_requirements = ["pytest"]

setup(
    author="Mozilla Release Engineering",
    author_email="release@mozilla.com",
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)" "Natural Language :: English",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
    ],
    description="Ship It API",
    install_requires=requirements,
    license="MPL2.0",
    long_description=readme + "\n\n" + history,
    include_package_data=True,
    keywords="shipit_api",
    name="shipit_api",
    packages=find_packages("src"),
    package_dir={"": "src"},
    py_modules=[splitext(basename(path))[0] for path in glob("src/*.py")],
    setup_requires=setup_requirements,
    test_suite="tests",
    tests_require=test_requirements,
    url="https://github.com/mozilla-releng/shipit",
    version="1.0.0",
    zip_safe=False,
)
