import contextlib
import copy
import os
import sys
import tokenize
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
    assert issued_messages == expected_messages


@pytest.fixture()
def mock_only_uppercase(tmpdir) -> typing.Iterator[None]:
    tmpdir.join('setup.py').write_text(
        "import setuptools\n"
        "setuptools.setup(\n"
        "   packages=['_test_module'],\n"
        "   install_requires=['astroid', 'pylint', 'UppercaSe'],\n"
        ")\n",
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


@pytest.fixture()
def mock_only_namespace(tmpdir) -> typing.Iterator[None]:
    tmpdir.join('setup.py').write_text(
        "import setuptools\n"
        "setuptools.setup(\n"
        "   packages=['name', 'name.foo'],\n"
        "   install_requires=['astroid', 'pylint', 'namespace'],\n"
        ")\n",
        encoding='utf-8',
    )
    namespace_dir = tmpdir.join("name", "foo")
    namespace_dir.ensure(dir=True)
    namespace_dir.join('__init__.py').write_text(
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
    'import uppercase',
])
def test_clean_import(mock_only_uppercase, code):
    import_node = astroid.extract_node(code)
    with expect_messages([]) as checker:
        checker.visit_import(import_node)


@pytest.mark.parametrize('code', [
    'import astroid',
    'import pylint',
    'import astroid as hypocycloid',
    'import pylint.testutils',
    'import name.foo',
])
def test_clean_import_ns(mock_only_namespace, code):
    import_node = astroid.extract_node(code)
    with expect_messages([]) as checker:
        checker.visit_import(import_node)


@pytest.mark.parametrize('code', [
    'from astroid import extract_node',
    'from astroid import extract_node as astroid_extract_node',
    'from pylint.testutils import Message, UnittestLinter',
    'from _test_module import hello',
    'from uppercase import bla',
])
def test_clean_importfrom(mock_only_uppercase, code):
    importfrom_node = astroid.extract_node(code)
    with expect_messages([]) as checker:
        checker.visit_importfrom(importfrom_node)


@pytest.mark.parametrize('code', [
    'from astroid import extract_node',
    'from astroid import extract_node as astroid_extract_node',
    'from pylint.testutils import Message, UnittestLinter',
    'from _test_module import hello',
    'from name import foo',
])
def test_clean_importfrom_ns(mock_only_namespace, code):
    importfrom_node = astroid.extract_node(code)
    with expect_messages([]) as checker:
        checker.visit_importfrom(importfrom_node)


@pytest.mark.parametrize(('code', 'expected_msg_args'), [
    ('import setuptools', ('setuptools', 'setuptools')),
    ('import importlib_metadata', ('importlib_metadata', 'importlib-metadata')),
    ('import setuptools.monkey', ('setuptools.monkey', 'setuptools')),
    ('import setuptools.monkey as simian', ('setuptools.monkey', 'setuptools')),
    ('import name', ('name', 'namespace')),
    ('import name.space', ('name.space', 'namespace')),
])
def test_missing_requirement_import(mock_only_uppercase, code,
                                    expected_msg_args):
    import_node = astroid.extract_node(code)
    expected_msg = pylint.testutils.Message(
        msg_id='missing-requirement',
        args=expected_msg_args,
        node=import_node,
    )
    with expect_messages([expected_msg]) as checker:
        checker.visit_import(import_node)


@pytest.mark.parametrize(('code', 'expected_msg_args'), [
    ('import setuptools', ('setuptools', 'setuptools')),
    ('import importlib_metadata', ('importlib_metadata', 'importlib-metadata')),
    ('import setuptools.monkey', ('setuptools.monkey', 'setuptools')),
    ('import setuptools.monkey as simian', ('setuptools.monkey', 'setuptools')),
    ('import uppercase', ('uppercase', 'UppercaSe')),
])
def test_missing_requirement_import_ns(mock_only_namespace, code,
                                       expected_msg_args):
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
    ('from name import space', ('name.space', 'namespace')),
    ('from name.space import hello_world', ('name.space', 'namespace')),
])
def test_missing_requirement_importfrom(mock_only_uppercase, code,
                                        expected_msg_args):
    importfrom_node = astroid.extract_node(code)
    expected_msg = pylint.testutils.Message(
        msg_id='missing-requirement',
        args=expected_msg_args,
        node=importfrom_node,
    )
    with expect_messages([expected_msg]) as checker:
        checker.visit_importfrom(importfrom_node)


@pytest.mark.parametrize(('code', 'expected_msg_args'), [
    ('from importlib_metadata import Distribution',
     ('importlib_metadata', 'importlib-metadata')),
    ('from importlib_metadata import *',
     ('importlib_metadata', 'importlib-metadata')),
    ('from setuptools import monkey as simian',
     ('setuptools', 'setuptools')),
    ('from setuptools.monkey import patch_all as make_great_again',
     ('setuptools.monkey', 'setuptools')),
    ('from uppercase import bla', ('uppercase', 'UppercaSe')),
])
def test_missing_requirement_importfrom_ns(mock_only_namespace, code,
                                           expected_msg_args):
    importfrom_node = astroid.extract_node(code)
    expected_msg = pylint.testutils.Message(
        msg_id='missing-requirement',
        args=expected_msg_args,
        node=importfrom_node,
    )
    with expect_messages([expected_msg]) as checker:
        checker.visit_importfrom(importfrom_node)


@pytest.mark.parametrize(('codelines', 'expected_msgs_args'), [
    (
            [
                'import astroid',
                'import pylint',
                'import astroid as hypocycloid',
                'import pylint.testutils',
                'import _test_module',
                'import uppercase',
            ], [],
    ),
    (
            [
                'import astroid',
                'import pylint',
                'import astroid as hypocycloid',
                'import pylint.testutils',
                'import _test_module',
            ], [
                ('UppercaSe',),
            ]
    ),
    (
            [
                'import pylint',
                'import pylint.testutils',
                'import _test_module',
            ], [
                ('UppercaSe',),
                ('astroid',),
            ]
    ),
])
def test_unused_requirements(mock_only_uppercase, codelines,
                             expected_msgs_args):
    expected_msgs = []
    for msg_args in expected_msgs_args:
        expected_msgs.append(pylint.testutils.Message(
            msg_id='unused-requirement',
            args=msg_args,
            line=0,
        ))
    with expect_messages(expected_msgs) as checker:
        checker.open()
        for line in codelines:
            node = astroid.extract_node(line)
            if isinstance(node, astroid.Import):
                checker.visit_import(node)
            else:
                checker.visit_importfrom(node)
        checker.close()


@pytest.mark.parametrize(('comments', 'expected_msgs_args'), [
    (
            [
                b'# pylint-import-requirements: imports=astroid,pylint,astroid,pylint,UppercaSe',
            ], [],
    ),
    (
            [
                b'# pylint-import-requirements: imports=astroid',
                b'# pylint-import-requirements: imports=pylint',
                b'# pylint-import-requirements: imports=pylint',
                b'# pylint-import-requirements: imports=_test_module',
                b'# pylint-import-requirements: imports=UppercaSe'
            ], []
    ),
    (
            [
                b'# pylint-import-requirements: imports=pylint',
                b'# pylint-import-requirements: imports=_test_module',
            ], [
                ('UppercaSe',),
                ('astroid',),
            ]
    ),
    (
            [
                b'# pylint-import-requirements: imports=pylint,_test_module',
            ], [
                ('UppercaSe',),
                ('astroid',),
            ]
    ),
])
def test_comment_control(mock_only_uppercase, comments, expected_msgs_args):
    expected_msgs = []
    for msg_args in expected_msgs_args:
        expected_msgs.append(pylint.testutils.Message(
            msg_id='unused-requirement',
            args=msg_args,
            line=0,
        ))
    with expect_messages(expected_msgs) as checker:
        checker.open()
        checker.process_tokens(tokenize.tokenize(iter(comments).__next__))
        checker.close()


@pytest.mark.parametrize(('codelines', 'expected_msgs_args'), [
    (
            [
                'import astroid',
                'import pylint',
                'import astroid as hypocycloid',
                'import pylint.testutils',
                'import name.space',
            ], [],
    ),
    (
            [
                'import astroid',
                'import pylint',
                'import astroid as hypocycloid',
                'import pylint.testutils',
                'from name import space',
            ], [],
    ),
    (
            [
                'import astroid',
                'import pylint',
                'import astroid as hypocycloid',
                'import pylint.testutils',
                'import name.foo',
            ], [
                ('namespace',),
            ]
    ),
    (
            [
                'import astroid',
                'import pylint',
                'import astroid as hypocycloid',
                'import pylint.testutils',
                'from name import foo',
            ], [
                ('namespace',),
            ]
    ),
    (
            [
                'import pylint',
                'import pylint.testutils',
                'from name import foo',
            ], [
                ('astroid',),
                ('namespace',),
            ]
    ),
])
def test_unused_requirements_ns(mock_only_namespace, codelines,
                                expected_msgs_args):
    expected_msgs = []
    for msg_args in expected_msgs_args:
        expected_msgs.append(pylint.testutils.Message(
            msg_id='unused-requirement',
            args=msg_args,
            line=0,
        ))
    with expect_messages(expected_msgs) as checker:
        checker.open()
        for line in codelines:
            node = astroid.extract_node(line)
            if isinstance(node, astroid.Import):
                checker.visit_import(node)
            else:
                checker.visit_importfrom(node)
        checker.close()


@pytest.mark.parametrize(('comments', 'expected_msgs'), [
    (
            [
                b'# pylint-import-requirements: imports=astroid,pylint,astroid,pylint,UppercaSe',
            ], [],
    ),
    (
            [
                b'# pylint-import-requirements: importss=astroid',
            ], [
                pylint.testutils.Message(
                    msg_id='unrecognized-inline-option',
                    args=('importss',),
                    line=1,
                ),
                pylint.testutils.Message(
                    msg_id='unused-requirement',
                    args=('UppercaSe',),
                    line=0,
                ),
                pylint.testutils.Message(
                    msg_id='unused-requirement',
                    args=('astroid',),
                    line=0,
                ),
                pylint.testutils.Message(
                    msg_id='unused-requirement',
                    args=('pylint',),
                    line=0,
                ),
            ],
    ),
    (
            [
                b'# pylint-import-requirements:'
            ], [
                pylint.testutils.Message(
                    msg_id='unrecognized-inline-option',
                    args=('',),
                    line=1,
                ),
                pylint.testutils.Message(
                    msg_id='unused-requirement',
                    args=('UppercaSe',),
                    line=0,
                ),
                pylint.testutils.Message(
                    msg_id='unused-requirement',
                    args=('astroid',),
                    line=0,
                ),
                pylint.testutils.Message(
                    msg_id='unused-requirement',
                    args=('pylint',),
                    line=0,
                ),
            ],
    ),
    (
            [
                b'# pylint-import-requirements: imports_test_module',
            ], [
                pylint.testutils.Message(
                    msg_id='unrecognized-inline-option',
                    args=('imports_test_module',),
                    line=1,
                ),
                pylint.testutils.Message(
                    msg_id='unused-requirement',
                    args=('UppercaSe',),
                    line=0,
                ),
                pylint.testutils.Message(
                    msg_id='unused-requirement',
                    args=('astroid',),
                    line=0,
                ),
                pylint.testutils.Message(
                    msg_id='unused-requirement',
                    args=('pylint',),
                    line=0,
                ),
            ],
    ),
])
def test_comment_control_parsing(mock_only_uppercase, comments, expected_msgs):
    with expect_messages(expected_msgs) as checker:
        checker.open()
        checker.process_tokens(tokenize.tokenize(iter(comments).__next__))
        checker.close()
