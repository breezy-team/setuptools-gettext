#
# Copyright (C) 2026 Michal Cihar <michal@weblate.org>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
# MA 02110-1301 USA

"""Install layout helpers for compiled gettext catalogs."""

import os
from typing import List, Tuple

from setuptools.dist import Distribution
from setuptools.errors import OptionError

from .catalog import LC_MESSAGES

DEFAULT_INSTALL_LAYOUT = "share"
VALID_INSTALL_LAYOUTS = ("share", "package")


def normalize_install_layout(install_layout) -> str:
    if install_layout is None:
        return DEFAULT_INSTALL_LAYOUT
    if not isinstance(install_layout, str):
        raise ValueError(
            "Unsupported setuptools-gettext install_layout "
            f"{install_layout!r}; expected one of: "
            f"{', '.join(VALID_INSTALL_LAYOUTS)}"
        )
    install_layout = install_layout.strip().lower()
    if install_layout not in VALID_INSTALL_LAYOUTS:
        raise ValueError(
            "Unsupported setuptools-gettext install_layout "
            f"{install_layout!r}; expected one of: "
            f"{', '.join(VALID_INSTALL_LAYOUTS)}"
        )
    return install_layout


def package_locale_info(
    dist: Distribution, build_dir: str
) -> Tuple[str, str, str]:
    matches = []
    for package in getattr(dist, "packages", None) or []:
        package_dir = _get_package_dir(dist, package)
        if _is_inside_path(build_dir, package_dir):
            relative = os.path.relpath(
                os.path.abspath(build_dir), os.path.abspath(package_dir)
            )
            matches.append(
                (
                    len(os.path.abspath(package_dir)),
                    package,
                    package_dir,
                    "" if relative == os.curdir else relative,
                )
            )

    if not matches:
        raise OptionError(
            "setuptools-gettext install_layout='package' requires "
            "build_dir to be inside a configured package"
        )

    _length, package, package_dir, relative = max(matches)
    return package, package_dir, relative


def add_package_data_for_build_dir(dist: Distribution, build_dir: str) -> None:
    package, _package_dir, relative_build_dir = package_locale_info(
        dist, build_dir
    )
    pattern = _package_data_pattern(relative_build_dir)

    package_data = getattr(dist, "package_data", None) or {}
    patterns = list(package_data.get(package, []))
    if pattern not in patterns:
        patterns.append(pattern)
    package_data[package] = patterns
    dist.package_data = package_data


def package_install_dir(
    package: str, relative_build_dir: str, langfile: str
) -> str:
    parts = package.split(".")
    if relative_build_dir:
        parts.append(relative_build_dir)
    parts.append(langfile)
    return os.path.dirname(os.path.join(*parts))


def _get_package_dir(dist: Distribution, package: str) -> str:
    path = package.split(".")
    package_dir = getattr(dist, "package_dir", None) or {}
    if not package_dir:
        result = os.path.join(*path) if path else ""
    else:
        tail: List[str] = []
        while path:
            package_name = ".".join(path)
            if package_name in package_dir:
                tail.insert(0, package_dir[package_name])
                result = os.path.join(*tail)
                break
            tail.insert(0, path[-1])
            del path[-1]
        else:
            default_dir = package_dir.get("")
            if default_dir is not None:
                tail.insert(0, default_dir)
            result = os.path.join(*tail) if tail else ""

    src_root = getattr(dist, "src_root", None)
    if src_root is not None:
        return os.path.join(src_root, result)
    return result


def _is_inside_path(path: str, parent: str) -> bool:
    path = os.path.normcase(os.path.abspath(path))
    parent = os.path.normcase(os.path.abspath(parent))
    try:
        relative = os.path.relpath(path, parent)
    except ValueError:
        return False
    return relative == os.curdir or (
        relative != os.pardir and not relative.startswith(os.pardir + os.sep)
    )


def _package_data_pattern(relative_build_dir: str) -> str:
    relative_build_dir = relative_build_dir.replace(os.sep, "/")
    return "/".join(
        part
        for part in (
            relative_build_dir,
            "*",
            LC_MESSAGES,
            "*.mo",
        )
        if part
    )
