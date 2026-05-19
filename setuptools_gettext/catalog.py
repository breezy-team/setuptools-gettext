#
# Copyright (C) 2007, 2009, 2011 Canonical Ltd.
# Copyright (C) 2022-2023 Jelmer Vernooĳ <jelmer@jelmer.uk>
# Copyright (C) 2026 Michal Čihař <michal@weblate.org>
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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA

"""Gettext catalog discovery helpers."""

import os
from dataclasses import dataclass
from glob import glob
from typing import List, Optional

LC_MESSAGES = "LC_MESSAGES"


@dataclass(frozen=True)
class Catalog:
    lang: str
    domain: str
    po: str
    uses_output_base: bool


def lang_from_dir(source_dir: os.PathLike) -> List[str]:
    lang: List[str] = []
    if not os.path.isdir(source_dir):
        return lang
    for i in os.listdir(source_dir):
        if i.endswith(".po") and not i.startswith("."):
            lang.append(i[:-3])
    return lang


def parse_lang(lang: str) -> List[str]:
    return [i.strip() for i in lang.split(",") if i.strip()]


def _flat_catalogs_from_dir(source_dir: os.PathLike) -> List[Catalog]:
    return [
        Catalog(
            lang=lang,
            domain=lang,
            po=os.path.join(source_dir, f"{lang}.po"),
            uses_output_base=True,
        )
        for lang in lang_from_dir(source_dir)
    ]


def _standard_catalogs_from_dir(source_dir: os.PathLike) -> List[Catalog]:
    catalogs = []
    pattern = os.path.join(source_dir, "*", LC_MESSAGES, "*.po")
    for po in glob(pattern):
        lang = os.path.basename(os.path.dirname(os.path.dirname(po)))
        domain = os.path.splitext(os.path.basename(po))[0]
        catalogs.append(
            Catalog(
                lang=lang,
                domain=domain,
                po=po,
                uses_output_base=False,
            )
        )
    return catalogs


def discover_catalogs(
    source_dir: os.PathLike, lang: Optional[List[str]] = None
) -> List[Catalog]:
    if lang is None:
        catalogs = _flat_catalogs_from_dir(source_dir)
        catalogs.extend(_standard_catalogs_from_dir(source_dir))
        return sorted(catalogs, key=lambda catalog: catalog.po)

    catalogs = []
    for language in lang:
        found = False
        flat_po = os.path.join(source_dir, f"{language}.po")
        if os.path.isfile(flat_po):
            found = True
            catalogs.append(
                Catalog(
                    lang=language,
                    domain=language,
                    po=flat_po,
                    uses_output_base=True,
                )
            )

        pattern = os.path.join(source_dir, language, LC_MESSAGES, "*.po")
        for po in sorted(glob(pattern)):
            found = True
            catalogs.append(
                Catalog(
                    lang=language,
                    domain=os.path.splitext(os.path.basename(po))[0],
                    po=po,
                    uses_output_base=False,
                )
            )

        if not found:
            catalogs.append(
                Catalog(
                    lang=language,
                    domain=language,
                    po=flat_po,
                    uses_output_base=True,
                )
            )
    return catalogs


def has_standard_catalogs(source_dir: str) -> bool:
    pattern = os.path.join(source_dir, "*", LC_MESSAGES, "*.po")
    return bool(glob(pattern))


def mo_basename(name: str) -> str:
    if name.endswith(".mo"):
        return name
    return f"{name}.mo"
