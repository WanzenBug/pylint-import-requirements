import pytest

from pylint_import_requirements import _isort_place_module


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
