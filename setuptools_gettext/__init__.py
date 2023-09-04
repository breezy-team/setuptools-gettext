#
# Copyright (C) 2007, 2009, 2011 Canonical Ltd.
# Copyright (C) 2022-2023 Jelmer Vernooĳ <jelmer@jelmer.uk>
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

# This code is from bzr-explorer and modified for bzr.

"""build_mo command for setup.py."""

import os
import re
from distutils import log
from distutils.command.build import build
from distutils.command.clean import clean
from distutils.command.install import install
from distutils.core import Command
from distutils.dep_util import newer
from distutils.spawn import find_executable
from distutils.util import convert_path, change_root
from typing import List, Optional

from setuptools.dist import Distribution

__version__ = (0, 1, 5)

SOURCE_DIR = 'po'
DEFAULT_BUILD_DIR = 'locale'


def lang_from_dir(source_dir: os.PathLike) -> List[str]:
    re_po = re.compile(r'^([a-zA-Z_]+)\.po$')
    lang = []
    for i in os.listdir(source_dir):
        mo = re_po.match(i)
        if mo:
            lang.append(mo.group(1))
    return lang


def parse_lang(lang: str) -> List[str]:
    return [i.strip() for i in lang.split(',') if i.strip()]


class build_mo(Command):
    """Subcommand of build command: build_mo."""

    description = 'compile po files to mo files'

    # List of options:
    #   - long name,
    #   - short name (None if no short name),
    #   - help string.
    user_options = [('build-dir=', 'd', 'Directory to build locale files'),
                    ('output-base=', 'o', 'mo-files base name'),
                    ('source-dir=', None, 'Directory with sources po files'),
                    ('force', 'f', 'Force creation of mo files'),
                    ('lang=', None, 'Comma-separated list of languages '
                                    'to process'),
                    ]

    boolean_options = ['force']

    def initialize_options(self):
        self.build_dir = None
        self.output_base = None
        self.source_dir = None
        self.force = None
        self.lang = None
        self.outfiles = []

    def finalize_options(self):
        self.set_undefined_options('build', ('force', 'force'))
        self.prj_name = self.distribution.get_name()
        if not self.output_base:
            self.output_base = self.prj_name or 'messages'
        if self.source_dir is None:
            self.source_dir = SOURCE_DIR
        if self.build_dir is None:
            self.build_dir = DEFAULT_BUILD_DIR
        if self.lang is None:
            self.lang = lang_from_dir(self.source_dir)
        else:
            self.lang = parse_lang(self.lang)

    def get_inputs(self):
        inputs = []
        for lang in self.lang:
            po = os.path.join(SOURCE_DIR, lang + '.po')
            if not os.path.isfile(po):
                po = os.path.join(SOURCE_DIR, lang + '.po')
            inputs.append(po)
        return inputs

    def run(self):
        """Run msgfmt for each language."""
        if not self.lang:
            return

        if find_executable('msgfmt') is None:
            log.warn("GNU gettext msgfmt utility not found!")
            log.warn("Skip compiling po files.")
            return

        if 'en' in self.lang:
            if find_executable('msginit') is None:
                log.warn("GNU gettext msginit utility not found!")
                log.warn("Skip creating English PO file.")
            else:
                log.info('Creating English PO file...')
                pot = (self.prj_name or 'messages') + '.pot'
                en_po = 'en.po'
                self.spawn(['msginit',
                            '--no-translator',
                            '-l', 'en',
                            '-i', os.path.join(self.source_dir, pot),
                            '-o', os.path.join(self.source_dir, en_po),
                            ])

        basename = self.output_base
        if not basename.endswith('.mo'):
            basename += '.mo'

        for lang in self.lang:
            po = os.path.join(SOURCE_DIR, lang + '.po')
            if not os.path.isfile(po):
                po = os.path.join(SOURCE_DIR, lang + '.po')
            dir_ = os.path.join(self.build_dir, lang, 'LC_MESSAGES')
            self.mkpath(dir_)
            mo = os.path.join(dir_, basename)
            if self.force or newer(po, mo):
                log.info(f'Compile: {po} -> {mo}')
                self.spawn(['msgfmt', '-o', mo, po])
                self.outfiles.append(mo)

    def get_outputs(self):
        return self.outfiles


class clean_mo(Command):
    description = 'clean .mo files'

    user_options = [('build-dir=', 'd', 'Directory to build locale files')]

    def initialize_options(self):
        self.build_dir = None

    def finalize_options(self):
        if self.build_dir is None:
            self.build_dir = DEFAULT_BUILD_DIR

    def run(self):
        if not os.path.isdir(self.build_dir):
            return
        for root, dirs, files in os.walk(self.build_dir):
            for file_ in files:
                if file_.endswith('.mo'):
                    os.unlink(os.path.join(root, file_))


class install_mo(Command):

    description: str = "install .mo files"

    user_options = [
        (
            'install-dir=',
            'd',
            "base directory for installing data files "
            "(default: installation base dir)",
        ),
        ('root=', None,
         "install everything relative to this alternate root directory"),
        ('force', 'f', "force installation (overwrite existing files)"),
    ]

    boolean_options: List[str] = ['force']
    build_dir: Optional[str]
    install_dir: Optional[str]
    root: Optional[str]

    def initialize_options(self) -> None:
        self.install_dir = None
        self.outfiles: List[str] = []
        self.root = None
        self.force = 0
        self.build_dir = None

    def finalize_options(self) -> None:
        self.set_undefined_options(
            'install',
            ('install_data', 'install_dir'),
            ('root', 'root'),
            ('force', 'force'),
        )
        if self.build_dir is None:
            self.build_dir = DEFAULT_BUILD_DIR

    def run(self) -> None:
        assert self.install_dir is not None
        assert self.build_dir is not None
        self.mkpath(self.install_dir)
        import glob
        for filepath in glob.glob(self.build_dir + "/*/LC_MESSAGES/*.mo"):
            langfile = filepath[len(self.build_dir.rstrip('/')+'/'):]
            targetpath = os.path.join(
                self.install_dir,
                os.path.dirname(os.path.join("share/locale", langfile)))
            if self.root is not None:
                targetpath = change_root(self.root, targetpath)
            self.mkpath(targetpath)
            (out, _) = self.copy_file(convert_path(filepath), targetpath)
            self.outfiles.append(out)

    def get_inputs(self):
        import glob
        return glob.glob(self.build_dir + "/*/LC_MESSAGES/*.mo")

    def get_outputs(self):
        return self.outfiles


def has_gettext(_c) -> bool:
    return os.path.isdir(SOURCE_DIR)


def pyprojecttoml_config(dist: Distribution) -> None:
    pass


build.sub_commands.append(('build_mo', has_gettext))
clean.sub_commands.append(('clean_mo', has_gettext))
install.sub_commands.append(('install_mo', has_gettext))
