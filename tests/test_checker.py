import contextlib
import copy
import os
import sys
import typing

import astroid
import pylint.testutils
import pytest

from pylint_import_requirements import ImportRequirementsLinter


@contextlib.contextmanager
def expect_messages(expected_messages: typing.List[pylint.testutils.Message]) \
        -> typing.Iterator[ImportRequirementsLinter]:
    linter = pylint.testutils.UnittestLinter()
    yield ImportRequirementsLinter(linter)
    issued_messages = linter.release_messages()
    assert expected_messages == issued_messages


@pytest.fixture(autouse=True)
def mock_package(tmpdir) -> typing.Iterator[None]:
    tmpdir.join('setup.py').write_text(
        "import setuptools\n"
        "setuptools.setup(install_requires=['astroid', 'pylint'])\n",
        encoding='utf-8',
    )
    tmpdir.join('_test_module.py').write_text(
        "def hello():\n"
        "   pass\n",
        encoding='utf-8',
    )
    old_cwd = os.getcwd()
    os.chdir(tmpdir.strpath)
    old_path = copy.copy(sys.path)
    sys.path.insert(0, tmpdir.strpath)
    try:
        yield
    finally:
        os.chdir(old_cwd)
        sys.path = old_path


@pytest.mark.parametrize('code', [
    'import astroid',
    'import pylint',
    'import astroid as hypocycloid',
    'import pylint.testutils',
    'import _test_module',
])
def test_clean_import(code):
    import_node = astroid.extract_node(code)
    with expect_messages([]) as checker:
        checker.visit_import(import_node)


@pytest.mark.parametrize('code', [
    'from astroid import extract_node',
    'from astroid import extract_node as astroid_extract_node',
    'from pylint.testutils import Message, UnittestLinter',
    'from _test_module import hello',
])
def test_clean_importfrom(code):
    importfrom_node = astroid.extract_node(code)
    with expect_messages([]) as checker:
        checker.visit_importfrom(importfrom_node)


@pytest.mark.parametrize(('code', 'expected_msg_args'), [
    ('import setuptools', ('setuptools', 'setuptools')),
    ('import importlib_metadata', ('importlib_metadata', 'importlib-metadata')),
    ('import setuptools.monkey', ('setuptools.monkey', 'setuptools')),
    ('import setuptools.monkey as simian', ('setuptools.monkey', 'setuptools')),
])
def test_missing_requirement_import(code, expected_msg_args):
    import_node = astroid.extract_node(code)
    expected_msg = pylint.testutils.Message(
        msg_id='missing-requirement',
        args=expected_msg_args,
        node=import_node,
    )
    with expect_messages([expected_msg]) as checker:
        checker.visit_import(import_node)


@pytest.mark.parametrize(('code', 'expected_msg_args'), [
    ('from importlib_metadata import Distribution',
     ('importlib_metadata', 'importlib-metadata')),
    ('from importlib_metadata import *',
     ('importlib_metadata', 'importlib-metadata')),
    ('from setuptools import monkey as simian',
     ('setuptools', 'setuptools')),
    ('from setuptools.monkey import patch_all as make_great_again',
     ('setuptools.monkey', 'setuptools')),
])
def test_missing_requirement_importfrom(code, expected_msg_args):
    importfrom_node = astroid.extract_node(code)
    expected_msg = pylint.testutils.Message(
        msg_id='missing-requirement',
        args=expected_msg_args,
        node=importfrom_node,
    )
    with expect_messages([expected_msg]) as checker:
        checker.visit_importfrom(importfrom_node)


def test_unresolved_import():
    import_node = astroid.extract_node('import none_existing_module')
    expected_msg = pylint.testutils.Message(
        msg_id='unresolved-import',
        args='none_existing_module',
        node=import_node,
    )
    with expect_messages([expected_msg]) as checker:
        checker.visit_import(import_node)


def test_unresolved_importfrom():
    import_nodefrom = astroid.extract_node('from none_existing_module import func')
    expected_msg = pylint.testutils.Message(
        msg_id='unresolved-import',
        args='none_existing_module',
        node=import_nodefrom,
    )
    with expect_messages([expected_msg]) as checker:
        checker.visit_importfrom(import_nodefrom)
