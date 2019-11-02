import copy
import os
import subprocess
import sys
import typing

import pytest


@pytest.fixture(autouse=True)
def mock_package(tmpdir) -> typing.Iterator[None]:
    tmpdir.join('_test_module.py').write_text(
        "import astroid\n"
        "def hello():\n"
        "    print(astroid)\n",
        encoding='utf-8',
    )
    old_cwd = os.getcwd()
    os.chdir(tmpdir)
    old_path = copy.copy(sys.path)
    sys.path.insert(0, tmpdir.strpath)
    try:
        yield
    finally:
        os.chdir(old_cwd)
        sys.path = old_path

def _run_pylint() -> subprocess.CompletedProcess:
    return subprocess.run(
        ('pylint', '--score=n', '--load-plugins=pylint_import_requirements', '_test_module.py'),
        check=False,
    )

def test_clean(tmpdir):
    tmpdir.join('setup.py').write_text(
        "import setuptools\n"
        "setuptools.setup(install_requires=['astroid'])\n",
        encoding='utf-8',
    )
    assert _run_pylint().returncode == 0

def test_missing_requirement(tmpdir):
    tmpdir.join('setup.py').write_text(
        "import setuptools\n"
        "setuptools.setup(install_requires=['pylint'])\n",
        encoding='utf-8',
    )
    assert _run_pylint().returncode != 0
