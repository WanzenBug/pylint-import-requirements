# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [2.0.1] - 2020-04-16
### Fixed
- Do not mark namespace packages as first party
  ( https://github.com/WanzenBug/pylint-import-requirements/pull/14 )
- Restored compatibility with python 3.4
  ( https://github.com/WanzenBug/pylint-import-requirements/pull/15 )

## [2.0.0] - 2020-02-20
### Add
- New lint: "unused-requirement": catches any requirement that is never
  imported in code
- New lint: "relative-import-across-packages": catches relative imports
  across namespace packages

## [1.0.3] - 2019-11-11
### Fix
- Fix namespace package detection for python versions < 3.7

## [1.0.2] - 2019-11-11
### Removed
- 'unresolved-import' message (covered by pylint 'import-error' already)

### Fix
- Detection of first vs third-party modules (now supports VCS deps)
- Packages with uppercase letters are detected correctly

## [1.0.1] - 2019-11-05
### Fix
-  Compatibility with Python 3.5

## [1.0.0] - 2019-10-31

[Unreleased]: https://github.com/WanzenBug/pylint-import-requirements/compare/v2.0.1...HEAD
[2.0.1]: https://github.com/WanzenBug/pylint-import-requirements/compare/v2.0.0...v2.0.1
[2.0.0]: https://github.com/WanzenBug/pylint-import-requirements/compare/v1.0.3...v2.0.0
[1.0.3]: https://github.com/WanzenBug/pylint-import-requirements/compare/v1.0.2...v1.0.3
[1.0.2]: https://github.com/WanzenBug/pylint-import-requirements/compare/v1.0.1...v1.0.2
[1.0.1]: https://github.com/WanzenBug/pylint-import-requirements/compare/v1.0.0...v1.0.1
[1.0.0]: https://github.com/WanzenBug/pylint-import-requirements/releases/tag/v1.0.0
