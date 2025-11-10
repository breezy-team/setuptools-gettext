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

import logging
import os
import re
import sys
from typing import List, Optional, Tuple

from setuptools import Command
from setuptools.dist import Distribution
from setuptools.modified import newer

__version__ = (0, 1, 16)
DEFAULT_SOURCE_DIR = "po"
DEFAULT_BUILD_DIR = "locale"
DEFAULT_LANGUAGE = "en"


def has_translate_toolkit() -> bool:
    try:
        import translate  # noqa
    except ImportError:
        return False
    return True


def has_msgfmt() -> bool:
    return find_executable("msgfmt") is not None


def lang_from_dir(source_dir: os.PathLike) -> List[str]:
    re_po = re.compile(r"^([a-zA-Z_]+)\.po$")
    lang = []
    for i in os.listdir(source_dir):
        mo = re_po.match(i)
        if mo:
            lang.append(mo.group(1))
    return lang


def parse_lang(lang: str) -> List[str]:
    return [i.strip() for i in lang.split(",") if i.strip()]


# Imported from distutils.util in Python 3.11:
def convert_path(pathname):
    """Return 'pathname' as a name that will work on the native filesystem.

    i.e. split it on '/' and put it back together again using the current
    directory separator.  Needed because filenames in the setup script are
    always supplied in Unix style, and have to be converted to the local
    convention before we can actually use them in the filesystem.  Raises
    ValueError on non-Unix-ish systems if 'pathname' either starts or
    ends with a slash.
    """
    if os.sep == "/":
        return pathname
    if not pathname:
        return pathname
    if pathname[0] == "/":
        raise ValueError(f"path '{pathname}' cannot be absolute")
    if pathname[-1] == "/":
        raise ValueError(f"path '{pathname}' cannot end with '/'")

    paths = pathname.split("/")
    while "." in paths:
        paths.remove(".")
    if not paths:
        return os.curdir
    return os.path.join(*paths)


class build_mo(Command):
    """Subcommand of build command: build_mo."""

    description = "compile po files to mo files"

    # List of options:
    #   - long name,
    #   - short name (None if no short name),
    #   - help string.
    user_options = [
        ("build-dir=", "d", "Directory to build locale files"),
        ("output-base=", "o", "mo-files base name"),
        ("force", "f", "Force creation of mo files"),
        ("translate-toolkit", "t", "Use translate-toolkit"),
        ("msgfmt", "m", "Use msgfmt program"),
        ("lang=", None, "Comma-separated list of languages to process"),
    ]

    boolean_options = ["force"]

    def initialize_options(self):
        self.build_dir = None
        self.output_base = None
        self.force = None
        self.msgfmt = None
        self.translate_toolkit = None
        self.lang = None
        self.outfiles = []

    def finalize_options(self):
        self.set_undefined_options("build", ("force", "force"))
        self.prj_name = self.distribution.get_name()
        if not self.output_base:
            self.output_base = self.prj_name or "messages"
        self.source_dir = self.distribution.gettext_source_dir  # type: ignore
        if self.build_dir is None:
            self.build_dir = (
                getattr(self.distribution, "gettext_build_dir", None)
                or DEFAULT_BUILD_DIR
            )
        if self.lang is None:
            self.lang = lang_from_dir(self.source_dir)
        else:
            self.lang = parse_lang(self.lang)

    def get_inputs(self):
        inputs = []
        for lang in self.lang:
            po = os.path.join(self.source_dir, lang + ".po")
            if not os.path.isfile(po):
                po = os.path.join(self.source_dir, lang + ".po")
            inputs.append(po)
        return inputs

    def run(self):
        """Run msgfmt for each language."""
        if not self.lang:
            return

        if self.msgfmt and self.translate_toolkit:
            logging.error("Cannot use both msgfmt and translate-toolkit!")
            return
        elif not self.msgfmt and not self.translate_toolkit:
            if has_msgfmt():
                self.msgfmt = True
            elif has_translate_toolkit():
                self.translate_toolkit = True
            else:
                logging.warning("No gettext tools found!")
                return

        if self.msgfmt and not has_msgfmt():
            logging.warning("GNU gettext msgfmt utility not found!")
            logging.warning("Skip compiling po files.")
            return

        if self.translate_toolkit and not has_translate_toolkit():
            logging.warning("Translate toolkit not found!")
            logging.warning("Skip compiling po files.")
            return

        default_lang = self.distribution.gettext_default_language

        if default_lang in self.lang:
            if find_executable("msginit") is None:
                logging.warning("GNU gettext msginit utility not found!")
                logging.warning("Skip creating English PO file.")
            else:
                logging.info("Creating English PO file...")
                pot = (self.prj_name or "messages") + ".pot"
                en_po = default_lang + ".po"
                self.spawn(
                    [
                        "msginit",
                        "--no-translator",
                        "-l",
                        default_lang,
                        "-i",
                        os.path.join(self.source_dir, pot),
                        "-o",
                        os.path.join(self.source_dir, en_po),
                    ]
                )

        basename = self.output_base
        if not basename.endswith(".mo"):
            basename += ".mo"

        for lang in self.lang:
            po = os.path.join(self.source_dir, lang + ".po")
            if not os.path.isfile(po):
                po = os.path.join(self.source_dir, lang + ".po")
            dir_ = os.path.join(self.build_dir, lang, "LC_MESSAGES")
            self.mkpath(dir_)
            mo = os.path.join(dir_, basename)
            if self.force or newer(po, mo):
                logging.info(f"Compile: {po} -> {mo}")
                self.compile_mo(po, mo)
                self.outfiles.append(mo)

    def compile_mo(self, po: str, mo: str):
        if self.msgfmt:
            self.spawn(["msgfmt", "-o", mo, po])
        elif self.translate_toolkit:
            from translate.tools.pocompile import convertmo

            with open(po, "rb") as pofile, open(mo, "wb") as mofile:
                convertmo(pofile, mofile, None)
        else:
            raise AssertionError("No gettext tools found!")

    def get_outputs(self):
        return self.outfiles


class clean_mo(Command):
    description = "clean .mo files"

    user_options = [("build-dir=", "d", "Directory to build locale files")]

    def initialize_options(self):
        self.build_dir = None

    def finalize_options(self):
        if self.build_dir is None:
            self.build_dir = (
                getattr(self.distribution, "gettext_build_dir", None)
                or DEFAULT_BUILD_DIR
            )

    def run(self):
        if not os.path.isdir(self.build_dir):
            return
        for root, dirs, files in os.walk(self.build_dir):
            for file_ in files:
                if file_.endswith(".mo"):
                    os.unlink(os.path.join(root, file_))


def gather_built_files(build_dir) -> List[str]:
    import glob

    return glob.glob(build_dir + "/*/LC_MESSAGES/*.mo")


class install_mo(Command):
    description: str = "install .mo files"

    user_options = [
        (
            "install-dir=",
            "d",
            "base directory for installing data files "
            "(default: installation base dir)",
        ),
        (
            "root=",
            None,
            "install everything relative to this alternate root directory",
        ),
        ("force", "f", "force installation (overwrite existing files)"),
    ]

    boolean_options = ["force"]

    build_dir: Optional[str]

    def initialize_options(self) -> None:
        self.data_files: List[str] = []
        self.build_dir = None
        self.install_dir = None
        self.outfiles: List[str] = []
        self.root = None
        self.force = 0

    def finalize_options(self) -> None:
        if self.build_dir is None:
            self.build_dir = self.distribution.gettext_build_dir  # type: ignore
        self.set_undefined_options(
            "install",
            ("install_data", "install_dir"),
            ("root", "root"),
            ("force", "force"),
        )

    def run(self) -> None:
        assert self.install_dir is not None
        self.mkpath(self.install_dir)
        assert self.build_dir is not None
        for filepath in gather_built_files(self.build_dir):
            langfile = filepath[len(self.build_dir.rstrip("/") + "/") :]
            install_dir = os.path.dirname(
                os.path.join("share/locale", langfile)
            )

            # it's a tuple with path to install to and a list of files
            dir = convert_path(install_dir)
            if not os.path.isabs(dir):
                dir = os.path.join(self.install_dir, dir)
            elif self.root:
                dir = change_root(self.root, dir)
            self.mkpath(dir)

            # Copy files, adding them to the list of output files.
            data = convert_path(filepath)
            (out, _) = self.copy_file(data, dir)
            self.outfiles.append(out)

    def get_inputs(self):
        return gather_built_files(self.build_dir)

    def get_outputs(self):
        return self.outfiles


class update_pot(Command):
    description: str = "update the .pot file"

    user_options: List[Tuple[str, str, str]] = []  # type: ignore

    def initialize_options(self) -> None:
        pass

    def finalize_options(self) -> None:
        pass

    def run(self) -> None:
        # TODO(jelmer): Support pygettext3 as well
        xgettext = find_executable("xgettext")
        if xgettext is None:
            logging.error("GNU gettext xgettext utility not found!")
            return
        args = [xgettext]
        args.extend(
            [
                "--package-name",
                self.distribution.get_name(),
                "--from-code",
                "UTF-8",
                "--sort-by-file",
                "--add-comments=i18n:",
                "-d",
                self.distribution.get_name(),
                "-p",
                self.distribution.gettext_source_dir,  # type: ignore
                "-o",
                f"{self.distribution.get_name()}.pot",
            ]
        )

        input_files = []
        for root, _dirs, files in os.walk("."):
            for file_ in files:
                if file_.endswith(".py"):
                    input_files.append(os.path.join(root, file_))
        args.extend(input_files)

        pot_path = os.path.join(
            self.distribution.gettext_source_dir,  # type: ignore
            self.distribution.get_name(),  # type: ignore
        )
        if os.path.exists(pot_path):
            args.append("--join")
        if self.distribution.get_contact():
            args += ["--msgid-bugs-address", self.distribution.get_contact()]

        self.spawn(args)


def has_gettext(command) -> bool:
    return os.path.isdir(command.distribution.gettext_source_dir)


def pyprojecttoml_config(dist: Distribution) -> None:
    build = dist.get_command_class("build")
    build.sub_commands.append(("build_mo", has_gettext))
    clean = dist.get_command_class("clean")
    clean.sub_commands.append(("clean_mo", has_gettext))
    install = dist.get_command_class("install")
    install.sub_commands.append(("install_mo", has_gettext))

    if sys.version_info[:2] >= (3, 11):
        from tomllib import load as toml_load
    else:
        from tomli import load as toml_load
    try:
        with open("pyproject.toml", "rb") as f:
            cfg = toml_load(f).get("tool", {}).get("setuptools-gettext")
    except FileNotFoundError:
        load_pyproject_config(dist, {})
    else:
        if cfg:
            load_pyproject_config(dist, cfg)
        else:
            load_pyproject_config(dist, {})


def load_pyproject_config(dist: Distribution, cfg) -> None:
    dist.gettext_source_dir = (  # type: ignore
        cfg.get("source_dir") or DEFAULT_SOURCE_DIR
    )
    dist.gettext_build_dir = (  # type: ignore
        cfg.get("build_dir") or DEFAULT_BUILD_DIR
    )
    dist.gettext_default_language = (  # type: ignore
        cfg.get("default_language") or DEFAULT_LANGUAGE
    )


def find_executable(executable):
    _, ext = os.path.splitext(executable)
    if sys.platform == "win32" and ext != ".exe":
        executable = executable + ".exe"

    if os.path.isfile(executable):
        return executable

    path = os.environ.get("PATH", os.defpath)

    # PATH='' doesn't match, whereas PATH=':' looks in the current directory
    if not path:
        return None

    paths = path.split(os.pathsep)
    for p in paths:
        f = os.path.join(p, executable)
        if os.path.isfile(f):
            return f
    return None


def change_root(new_root, pathname):
    if os.name == "posix":
        if not os.path.isabs(pathname):
            return os.path.join(new_root, pathname)
        else:
            return os.path.join(new_root, pathname[1:])
    elif os.name == "nt":
        (drive, path) = os.path.splitdrive(pathname)
        if path[0] == "\\":
            path = path[1:]
        return os.path.join(new_root, path)
    else:
        raise AssertionError(f"Unsupported OS: {os.name}")
