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
