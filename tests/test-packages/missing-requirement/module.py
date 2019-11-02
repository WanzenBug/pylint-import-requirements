import abc

import astroid as hypocycloid
import isort
import setuptools.monkey as simian
from importlib_metadata import Distribution


def main():
    print(abc, isort, hypocycloid, simian, Distribution)


if __name__ == '__main__':
    main()
