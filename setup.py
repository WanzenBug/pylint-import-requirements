import os

from setuptools import setup

README_PATH = os.path.join(os.path.dirname(__file__), "README.md")

setup(
    name="pylint-import-requirements",
    use_scm_version=True,
    author="Moritz 'WanzenBug' Wanzenböck",
    author_email="moritz@wanzenbug.xyz",
    description="A pylint plugin to check that all imports have matching requirements specified",
    license="GPL",
    keywords="pylint import requirements",
    url="http://github.com/WanzenBug/pylint-import-requirements",
    packages=["pylint_import_requirements"],
    long_description=open(README_PATH).read(),
    long_description_content_type="text/markdown",
    install_requires=[
        "pylint",
        "astroid",
        "importlib-metadata",
        "setuptools",
        "isort",
    ],
    tests_require=[
        "pytest"
    ],
    setup_requires=[
        "setuptools_scm"
    ],
    classifiers=[
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: GNU General Public License (GPL)",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Topic :: Software Development :: Debuggers",
        "Topic :: Software Development :: Quality Assurance",
        "Topic :: Software Development :: Testing",
    ],
)
