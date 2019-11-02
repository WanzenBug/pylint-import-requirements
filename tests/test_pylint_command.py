import pathlib
import subprocess


def _run_pylint(package_dir_path: pathlib.Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        ('pylint', '--score=n', '--load-plugins=pylint_import_requirements', 'module.py'),
        cwd=package_dir_path,
        stdout=subprocess.PIPE,
        check=False,
    )

def test_clean(test_packages_dir_path: pathlib.Path):
    process = _run_pylint(test_packages_dir_path.joinpath('clean'))
    assert process.returncode == 0

def test_missing_requirement(test_packages_dir_path: pathlib.Path):
    process = _run_pylint(test_packages_dir_path.joinpath('missing-requirement'))
    assert process.returncode != 0
    assert process.stdout == b"************* Module module\n" \
        b"module.py:4:0: W6667: import 'isort' not covered by 'install_requires', " \
        b"from distribution: 'isort' (missing-requirement)\n" \
        b"module.py:5:0: W6667: import 'setuptools.monkey' not covered by 'install_requires', " \
        b"from distribution: 'setuptools' (missing-requirement)\n" \
        b"module.py:6:0: W6667: import 'importlib_metadata' not covered by 'install_requires', " \
        b"from distribution: 'importlib-metadata' (missing-requirement)\n"

def test_unresolved_import(test_packages_dir_path: pathlib.Path):
    process = _run_pylint(test_packages_dir_path.joinpath('unresolved-import'))
    assert process.returncode != 0
    assert process.stdout == b"************* Module module\n" \
        b"module.py:1:0: E0611: No name 'pancake' in module 'abc' (no-name-in-module)\n" \
        b"module.py:5:0: E6666: import '_ham_with_eggs' does not resolve to a location " \
        b"(unresolved-import)\n" \
        b"module.py:5:0: E0401: Unable to import '_ham_with_eggs' (import-error)\n"
