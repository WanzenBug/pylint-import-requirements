import pathlib

import pytest


@pytest.fixture
def test_packages_dir_path() -> pathlib.Path:
    return pathlib.Path(__file__).parent.joinpath('test-packages')
