#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""

import os
from glob import glob
from os.path import abspath, basename, dirname, join, splitext

from setuptools import find_namespace_packages, find_packages, setup

with open("README.rst") as readme_file:
    readme = readme_file.read()

with open("HISTORY.rst") as history_file:
    history = history_file.read()

here = abspath(dirname(__file__))


def get_requirements(req_file):
    # We're using a pip8 style requirements file, which allows us to embed
    # hashes of the packages in it. However, setuptools doesn't support parsing
    # this type of file, so we need to strip those out before passing the
    # requirements along to it.
    requirements = []
    with open(join(here, "requirements", req_file)) as f:
        for line in f:
            line = line.strip()
            # Skip empty, comment lines, and line with hashes
            if not line or line.startswith("#") or line.startswith("--"):
                continue
            if line.startswith("-r "):
                req_file = line.split()[1]
                requirements.extend(get_requirements(req_file))
            else:
                requirements.extend(line.split(";")[0].rstrip("  \\").split())
    return requirements


setup_requirements = ["pytest-runner"]
test_requirements = ["pytest"]

# By default use public app requirements and name
packages = find_packages("src", include=["backend_common", "cli_common"]) + find_namespace_packages("src", include=["shipit_api.common", "shipit_api.public"])
name = "shipit_api-public"
req_file = "public.txt"

if os.environ.get("APP_TYPE") == "admin":
    packages.extend(find_namespace_packages("src", include=["shipit_api.admin"]))
    name = "shipit_api-admin"
    req_file = "base.txt"

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
    install_requires=get_requirements(req_file),
    license="MPL2.0",
    long_description=readme + "\n\n" + history,
    include_package_data=True,
    keywords="shipit_api",
    name=name,
    packages=packages,
    package_dir={"": "src"},
    py_modules=[splitext(basename(path))[0] for path in glob("src/*.py")],
    setup_requires=setup_requirements,
    test_suite="tests",
    tests_require=test_requirements,
    url="https://github.com/mozilla-releng/shipit",
    version="1.0.0",
    zip_safe=False,
)
