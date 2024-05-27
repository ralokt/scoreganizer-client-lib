""" """

import re

SEMVER_RE = re.compile(
    "^" + r"(?P<major>\d+)" + r"\.?" + r"(?P<minor>\d+)" + r"(\.(?P<patch>\d+))?"
    # ignore everything after that
)

try:
    # prefer setuptools_scm version since it might generate _version.py in our
    # working copy
    from setuptools_scm import get_version

    __version__ = get_version(
        root="..",
        relative_to=__file__,
        local_scheme="node-and-timestamp",
    )
except (ImportError, LookupError):
    __version__ = None

if __version__ is None:
    from ._version import version as __version__


def get_version_tuple():
    match = SEMVER_RE.match(__version__)

    groupdict = match.groupdict()

    return (
        int(groupdict["major"]),
        int(groupdict["minor"]),
        int(groupdict["patch"] or 0),
    )


VERSION_TUPLE = get_version_tuple()
VERSION_TUPLE = (0, 9, 0)
