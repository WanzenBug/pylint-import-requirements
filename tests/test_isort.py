import pylint.testutils
import pytest

import pylint_import_requirements

# pylint: disable=redefined-outer-name,protected-access


@pytest.fixture(scope="module")
def checker():
    return pylint_import_requirements.ImportRequirementsLinter(
        linter=pylint.testutils.UnittestLinter()
    )


@pytest.mark.parametrize(
    ("module_name", "category"),
    [
        ("astroid", "THIRDPARTY"),
        ("io", "STDLIB"),
        ("pylint_import_requirements", "FIRSTPARTY"),
        ("subprocess", "STDLIB"),
    ],
)
def test__isort_place_module(checker, module_name, category):
    assert checker._isort_place_module(module_name) == category


@pytest.mark.parametrize(
    ("module_name", "is_stdlib_module"),
    [
        ("astroid", False),
        ("io", True),
        ("pylint_import_requirements", False),
        ("subprocess", True),
    ],
)
def test__is_stdlib_module(checker, module_name, is_stdlib_module):
    assert checker._is_stdlib_module(module_name) == is_stdlib_module
