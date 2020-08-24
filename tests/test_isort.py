import pytest

from pylint_import_requirements import _isort_place_module, _is_stdlib_module


@pytest.mark.parametrize(
    ("module_name", "category"),
    [
        ("astroid", "THIRDPARTY"),
        ("io", "STDLIB"),
        ("pylint_import_requirements", "FIRSTPARTY"),
        ("subprocess", "STDLIB"),
    ],
)
def test__isort_place_module(module_name, category):
    assert _isort_place_module(module_name) == category


@pytest.mark.parametrize(
    ("module_name", "is_stdlib_module"),
    [
        ("astroid", False),
        ("io", True),
        ("pylint_import_requirements", False),
        ("subprocess", True),
    ],
)
def test__is_stdlib_module(module_name, is_stdlib_module):
    assert _is_stdlib_module(module_name) == is_stdlib_module
