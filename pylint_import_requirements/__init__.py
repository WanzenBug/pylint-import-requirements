"""
pylint_import_requirements
==========================
Pylint plugin that checks that all imports can be resolved from the package requirements

Usage
-----
Run pylint with
```
pylint --load-plugins=pylint_import_requirements <your-files-to-lint>
```

The plugin expects a `setup.py` file to exist in the working directory
"""
import importlib.util
import pathlib
from collections import namedtuple
from distutils.core import run_setup
from typing import Dict, List, Optional, Set

import astroid
import importlib_metadata
from importlib_metadata import Distribution
from isort import isort
from pkg_resources import get_distribution
from pylint.checkers import BaseChecker
from pylint.interfaces import IAstroidChecker

_FileInfo = namedtuple("_FileInfo", ("path", "source", "allowed",))


class ImportRequirementsLinter(BaseChecker):
    """Check that all import statements are covered by `install_requires` statements"""

    # This class variable defines the type of checker that we are implementing.
    # In this case, we are implementing an AST checker.
    __implements__ = IAstroidChecker

    # The name defines a custom section of the config for this checker.
    name = "import-in-requirements"
    # The priority indicates the order that pylint will run the checkers.
    priority = -1
    # This class variable declares the messages (ie the warnings and errors)
    # that the checker can emit.
    msgs = {
        "W6667": (
            "import '%s' not covered by 'install_requires', from distribution: '%s'",
            "missing-requirement",
            "all import statements should be directly provided by packages which are first order "
            "dependencies",
        )
    }

    def __init__(self, linter):
        """Initialize the linter by loading all 'allowed' imports from package requirements"""
        super(ImportRequirementsLinter, self).__init__(linter)

        self.known_files = {}  # type: Dict[pathlib.PurePath, _FileInfo]
        self.isort_obj = isort.SortImports(file_contents="")
        all_loadable_distributions = set(
            importlib_metadata.distributions()
        )  # type: Set[Distribution]

        allowed_distributions = {
            get_distribution(x).project_name for x in run_setup("setup.py").install_requires
        }

        for dist in all_loadable_distributions:
            dist_name = dist.metadata["Name"]
            allowed = dist_name in allowed_distributions
            # Get a list of files created by the distribution
            distribution_files = dist.files
            # Resolve the (relative) paths to absolute paths
            resolved_filepaths = {x.locate() for x in distribution_files}

            distribution_file_info = {
                p: _FileInfo(p, dist, allowed) for p in resolved_filepaths
            }
            # Add them to the whitelist
            self.known_files.update(distribution_file_info)

    def visit_import(self, node: astroid.node_classes.Import):
        """Called when an `import foo` statement is visited"""

        # Loop, because we get all imports from a single line
        # i.e. `import csv, json -> names=('csv', 'json',)
        for modname, _alias in node.names:
            self.check_import(node, modname)

    def visit_importfrom(self, node):
        """Called when a `from foo import bar` statement is visited"""

        modname = node.modname
        if node.level:
            # Handle relative imports
            root = node.root()
            parent_level = node.level
            if not root.package:
                # We are not in a package (`__init__.py`)
                # so all relative imports are scoped to the parent package
                parent_level += 1
            relative_path = ("." * parent_level) + modname
            current_package = root.name
            modname = importlib.util.resolve_name(relative_path, current_package)

        names = [name for name, _alias in node.names]
        self.check_import(node, modname, names)

    def check_import(self, node, modname: str, names: Optional[List[str]] = None):
        """Run the actual check

        It works like this:
        1. If its in the stdlib or same package we return immediately, nothing to fix there
        2. we try to find the spec (=metadata) of the import, using `importlib.util.find_spec`
            2a. If we cannot import, then there should be an import-error anyways
        3. We check the `origin` field of the spec. This normally points to the file to be imported
            3a. If we cannot access the origin path, it must be a namespace module (since we already
                filtered stdlib modules)
            3b. If we import names (i.e. the foo in `from bla import foo`) we try to import the
                `full` module name (`bla.foo`) and run our checks on that
            3c. We allow partial matches. This means we get the namespace module search path and
                verify that at least one package adds something to the module
        4. We verify that the imported file is installed from one of the allowed distributions
        """
        # Step 1
        if self._is_stdlib_or_first_party_module(modname):
            return

        # Step 2
        spec = importlib.util.find_spec(modname, package=node.frame().name)
        if not spec:
            return

        # Step 3
        origin_path = spec.origin
        if not origin_path:
            # Must be namespace package
            self.check_namespace_module(node, spec, names)
            return

        # Step 4
        resolved_origin = pathlib.Path(origin_path).resolve()
        known_info = self.known_files.get(resolved_origin)
        if known_info and not known_info.allowed:
            candidate_name = known_info.source.metadata["Name"]
            self.add_message("missing-requirement", node=node, args=(modname, candidate_name))
        if not known_info:
            self.add_message("missing-requirement", node=node, args=(modname, "<unknown>"))

    def check_namespace_module(self, node, spec, names: Optional[List[str]]):
        """Try to check a module spec of a namespace module"""
        # If we import any names, try to resolve them instead
        if names:
            for name in names:
                self.check_import(node, modname="{}.{}".format(spec.name, name), names=None)
            return

        # We tried our best, but we can only verify that some part of the namespace is installed
        submodule_path = str(next(iter(spec.submodule_search_locations)))
        other_candidates = set()
        for path, info in self.known_files.items():
            if not str(path).startswith(submodule_path):
                continue

            if info.allowed:
                return

            other_candidates.add(info.source)

        alternative_dist_msg = ",".join((str(o.metadata["Name"]) for o in other_candidates))
        self.add_message("missing-requirement", node=node, args=(spec.name, alternative_dist_msg))
        return

    def _is_stdlib_or_first_party_module(self, package):
        """Check if the given path is from a built-in module or not"""

        # Approach taken from https://github.com/PyCQA/pylint/blob/master/pylint/checkers/imports.py
        import_category = self.isort_obj.place_module(package)
        return import_category in {"FUTURE", "STDLIB", "FIRSTPARTY"}


def register(linter):
    """This required method auto registers the checker.

    :param linter: The linter to register the checker to.
    :type linter: pylint.lint.PyLinter
    """
    linter.register_checker(ImportRequirementsLinter(linter))
