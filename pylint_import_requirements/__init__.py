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
import sys
from collections import namedtuple, defaultdict
from distutils.core import run_setup
from tokenize import TokenInfo, COMMENT
from typing import Dict, List, Optional, Set

import astroid
import importlib_metadata
from importlib_metadata import Distribution
from isort import isort
from pkg_resources import get_distribution
from pylint.checkers import BaseChecker
from pylint.interfaces import IAstroidChecker, ITokenChecker

_DistInfo = namedtuple("_DistInfo", ("source", "allowed",))
_REQUIRES_INSTALL_PREFIX = "pylint-import-requirements:"


def _is_namespace_spec(spec) -> bool:
    """Check whether the given spec is from a namespace module or not"""
    if sys.version_info < (3, 7, 0):
        # https://github.com/python/cpython/blob/86c17c06c9420040c79c29ecf924741f37975342/Lib/importlib/_bootstrap_external.py#L1165
        return spec.origin == "namespace"
    # https://github.com/python/cpython/blob/917dbe350a762ed6d75b7d074f3fb87975ba717b/Lib/importlib/_bootstrap_external.py#L1288
    # https://github.com/python/cpython/pull/5481
    return spec.origin is None


def _filter_non_namespace_packages(package_names: List[str]) -> List[str]:
    """Given a list of packages, only return those names that are NOT a namespace package"""
    result = []
    for name in package_names:
        spec = importlib.util.find_spec(name)
        if not spec:
            # Could not load module, so its probably not a package
            continue
        if _is_namespace_spec(spec) and len(spec.submodule_search_locations) >= 2:
            # Its a namespace package with more than 2 search locations
            continue
        # The package is directly importable, or a namespace package with only 1
        # search locations, i.e. not really a namespace at all
        result.append(name)
    return result


class ImportRequirementsLinter(BaseChecker):
    """Check that all import statements are covered by `install_requires` statements"""

    # This class variable defines the type of checker that we are implementing.
    # In this case, we are implementing an AST checker.
    __implements__ = (IAstroidChecker, ITokenChecker,)

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
            {
                "scope": "node"
            }
        ),
        "W6668": (
            "install_requires: '%s' does not seem to be used",
            "unused-requirement",
            "All requirements should be used in code at least once.\n"
            "If there are imports that are required because they are lazy loaded as a transitive "
            "dependency, consider using a control comment:\n"
            "```# {} imports=<distribution-name>```".format(_REQUIRES_INSTALL_PREFIX),
            {
                "scope": "package"
            }
        ),
        "W6669": (
            "import from a different package with relative imports: '%s'",
            "relative-import-across-packages",
            "all imports from another package should be absolute",
            {
                "scope": "node"
            }
        ),
    }

    def __init__(self, linter):
        """Initialize the linter by loading all 'allowed' imports from package requirements"""
        super(ImportRequirementsLinter, self).__init__(linter)

        self.known_files = {}  # type: Dict[pathlib.PurePath, _DistInfo]
        self.known_modules = defaultdict(set)  # type: defaultdict[str, Set[_DistInfo]]
        self.isort_obj = isort.SortImports(file_contents="")
        all_loadable_distributions = set(
            importlib_metadata.distributions()
        )  # type: Set[Distribution]

        setup_result = run_setup("setup.py")
        self.first_party_packages = _filter_non_namespace_packages(setup_result.packages or [])
        self.allowed_distributions = {
            get_distribution(x).project_name for x in setup_result.install_requires
        }
        self.visited_distributions = set()

        for dist in all_loadable_distributions:
            dist_name = dist.metadata["Name"]
            allowed = dist_name in self.allowed_distributions
            # Get a list of files created by the distribution
            distribution_files = dist.files
            # Resolve the (relative) paths to absolute paths
            resolved_filepaths = {x.locate() for x in distribution_files}

            distribution_file_info = {
                p: _DistInfo(dist, allowed) for p in resolved_filepaths
            }

            # Add them to the whitelist
            self.known_files.update(distribution_file_info)

            # Add source distributions to backup list
            if not dist.read_text("SOURCES.txt"):
                continue
            dist_modules_text = dist.read_text("top_level.txt") or ""
            dist_modules = dist_modules_text.split()

            for mod in dist_modules:
                self.known_modules[mod].add(_DistInfo(dist, allowed))

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
            if root.package:
                parent_level -= 1

            if root.name.count(".") < parent_level:
                self.add_message("relative-import-across-packages", node=node, args=(modname,))
            # We can just return here, relative imports are always first party modules
            return

        names = [name for name, _alias in node.names]
        self.check_import(node, modname, names)

    def open(self):
        self.visited_distributions = set()

    def close(self):
        superfluous_distributions = self.allowed_distributions - self.visited_distributions
        for name in sorted(superfluous_distributions):
            self.add_message("unused-requirement", line=0, args=(name,))

    def check_import(self, node, modname: str, names: Optional[List[str]] = None):
        """Run the actual check

        It works like this:
        1. If the module name is in the known first party modules, there is nothing to check
        2. If its in the stdlib, nothing to check here
        3. we try to find the spec (=metadata) of the import, using `importlib.util.find_spec`
            3a. If we cannot import, then there should be an import-error anyways
        4. We check the `origin` field of the spec. This normally points to the file to be imported
            4a. If we cannot access the origin path, it must be a namespace module (since we already
                filtered stdlib modules)
            4b. If we import names (i.e. the foo in `from bla import foo`) we try to import the
                `full` module name (`bla.foo`) and run our checks on that
            4c. We allow partial matches. This means we get the namespace module search path and
                verify that at least one package adds something to the module
        5. We verify that the imported file is installed from one of the allowed distributions
        """
        # Step 1
        if self._is_first_party_module(modname):
            return

        # Step 2
        if self._is_stdlib_module(modname):
            return

        # Step 3
        spec = importlib.util.find_spec(modname, package=node.frame().name)
        if not spec:
            return

        # Step 4
        if _is_namespace_spec(spec):
            # Must be namespace package
            self.check_namespace_module(node, spec, names)
            return

        # Step 5
        resolved_origin = pathlib.Path(spec.origin).resolve()
        known_info = self.known_files.get(resolved_origin)
        if known_info:
            self.visited_distributions.add(known_info.source.metadata["Name"])

        if known_info and not known_info.allowed:
            candidate_name = known_info.source.metadata["Name"]
            self.add_message("missing-requirement", node=node, args=(modname, candidate_name))
        if not known_info:
            mod_candidates = self._from_known_mod(modname) or set()

            allowed_candidate = None
            for mod in mod_candidates:
                self.visited_distributions.add(mod.source.metadata["Name"])
                if mod.allowed:
                    allowed_candidate = mod
            if allowed_candidate:
                return

            dist_names = [x.source.metadata['Name'] for x in mod_candidates] or ["<unknown>"]
            self.add_message(
                "missing-requirement", node=node, args=(modname, ", ".join(dist_names))
            )

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

    def _from_known_mod(self, modname: str) -> Optional[Set[_DistInfo]]:
        """Resolve the modname based on all modnames provided by distributions

        This can be useful in case a loaded file is for some reason or another not listed in the
        distribution files.

        This for example happens with native extensions that are installed as
        editable. In such a case, the distribution files only contain the 'source' files, not the
        build extension
        """
        toplevel, _, _ = modname.partition(".")
        return self.known_modules.get(toplevel)

    def _is_stdlib_module(self, module) -> bool:
        """Check if the given path is from a built-in module or not"""

        # Approach taken from https://github.com/PyCQA/pylint/blob/master/pylint/checkers/imports.py
        import_category = self.isort_obj.place_module(module)
        return import_category in {"FUTURE", "STDLIB"}

    def _is_first_party_module(self, module) -> bool:
        """Check if the given module is from a first party package

        In order to match up module names with package names it may be necessary to strip the
        trailing segment. Generally, if there is a directory structure like:

        foo:
            __init__.py
            bar.py
        setup.py

        In this case, package names would be ['foo'], while the module in bar.py would be referenced
        by 'foo.bar'. In this case __init__.py would be named just 'foo'.

        Because of this, there is a 2 stage lookup:
        1. if the module name matches one of the known first party names, it is a first party module
        2. split the name at the last '.'. If everything before the last '.' is in the first party
           names, it is also accepted as first party module
        """
        if module in self.first_party_packages:
            return True
        package_name = module.rpartition(".")[0]  # rpartition always returns 3 items
        return package_name in self.first_party_packages

    def process_tokens(self, tokens: List[TokenInfo]):
        """Scan tokens to respond to control comments.

        An example of a control comment:
        ```
        import pandas as pd

        pd.read_feather('file.feather')  # pylint-import-requirements: imports=pyarrow
        ```
        """
        for token in tokens:
            if token.type != COMMENT:
                continue

            content = token.string.lstrip("# ")
            if not content.startswith(_REQUIRES_INSTALL_PREFIX):
                continue

            stripped_content = content[len(_REQUIRES_INSTALL_PREFIX):].strip()
            option_name, _, option_values = stripped_content.partition("=")

            if option_name != "imports":
                self.add_message(
                    "unrecognized-inline-option", line=token.start[0], args=(option_name,)
                )
                continue

            for val in option_values.split(","):
                self.visited_distributions.add(val)


def register(linter):
    """This required method auto registers the checker.

    :param linter: The linter to register the checker to.
    :type linter: pylint.lint.PyLinter
    """
    linter.register_checker(ImportRequirementsLinter(linter))
