import os

from setuptools import setup


# Utility function to read the README file.
# Used for the long_description.  It"s nice, because now 1) we have a top level
# README file and 2) it"s easier to type in the README file than to put a raw
# string in below ...
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    name="pylint-import-requirements",
    use_scm_version=True,
    author="Moritz 'WanzenBug' Wanzenböck",
    author_email="moritz.wanzenboeck@catalysts.cc",
    description="A pylint plugin to check that all imports have matching requirements specified",
    license="GPL",
    keywords="pylint import requirements",
    url="http://github.com/Catalysts/pylint-import-requirements",
    packages=["pylint_import_requirements"],
    long_description=read("README.md"),
    install_requires=[
        "pylint",
        "astroid",
        "importlib-metadata",
        "setuptools",
    ],
    tests_require=[
        "pytest"
    ],
    setup_requires=[
        "setuptools_scm"
    ],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Topic :: Software Development :: Debuggers",
        "Topic :: Software Development :: Testing",
        "Topic :: Software Development :: Quality Assurance",
        "License :: OSI Approved :: GNU General Public License (GPL)",
    ],
)
