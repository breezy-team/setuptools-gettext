import os
import shutil
from tempfile import TemporaryDirectory

import pytest
from setuptools import Distribution

from setuptools_gettext import (
    build_mo,
    find_source_files,
    install_mo,
    load_pyproject_config,
    update_pot,
)


def test_example_build():
    with TemporaryDirectory() as td:
        shutil.copytree("example", td + "/example")

        old_cwd = os.getcwd()

        dist = Distribution()

        load_pyproject_config(dist, {})

        os.chdir(td + "/example")
        try:
            cmd = build_mo(dist)
            cmd.initialize_options()
            cmd.finalize_options()
            cmd.run()
        finally:
            os.chdir(old_cwd)


def test_example_install():
    with TemporaryDirectory() as td, TemporaryDirectory() as root:
        shutil.copytree("example", td + "/example")

        dist = Distribution()

        load_pyproject_config(dist, {})

        old_cwd = os.getcwd()

        os.chdir(td + "/example")
        try:
            cmd = install_mo(dist)
            cmd.initialize_options()
            cmd.root = root  # type: ignore
            cmd.finalize_options()
            cmd.run()
        finally:
            os.chdir(old_cwd)


def test_load_pyproject_config_default_compiler():
    dist = Distribution()

    load_pyproject_config(dist, {})

    assert getattr(dist, "gettext_compiler") == "auto"
    assert getattr(dist, "gettext_install_layout") == "share"


@pytest.mark.parametrize("compiler", ["auto", "msgfmt", "translate-toolkit"])
def test_load_pyproject_config_compiler(compiler):
    dist = Distribution()

    load_pyproject_config(dist, {"compiler": compiler})

    assert getattr(dist, "gettext_compiler") == compiler


def test_load_pyproject_config_rejects_invalid_compiler():
    dist = Distribution()

    with pytest.raises(ValueError, match="Unsupported setuptools-gettext"):
        load_pyproject_config(dist, {"compiler": "invalid"})


@pytest.mark.parametrize("install_layout", ["share", "package"])
def test_load_pyproject_config_install_layout(install_layout):
    dist = Distribution()

    load_pyproject_config(dist, {"install_layout": install_layout})

    assert getattr(dist, "gettext_install_layout") == install_layout


def test_load_pyproject_config_rejects_invalid_install_layout():
    dist = Distribution()

    with pytest.raises(ValueError, match="Unsupported setuptools-gettext"):
        load_pyproject_config(dist, {"install_layout": "invalid"})


def test_build_mo_uses_msgfmt_compiler_from_config():
    with TemporaryDirectory() as td:
        source_dir = os.path.join(td, "po")
        os.mkdir(source_dir)
        with open(os.path.join(source_dir, "nl.po"), "w") as f:
            f.write("")
        dist = Distribution(attrs={"name": "example"})

        load_pyproject_config(
            dist, {"source_dir": source_dir, "compiler": "msgfmt"}
        )
        cmd = build_mo(dist)
        cmd.initialize_options()
        cmd.finalize_options()

    assert cmd.msgfmt is True
    assert cmd.translate_toolkit is None


def test_build_mo_uses_translate_toolkit_compiler_from_config():
    with TemporaryDirectory() as td:
        source_dir = os.path.join(td, "po")
        os.mkdir(source_dir)
        with open(os.path.join(source_dir, "nl.po"), "w") as f:
            f.write("")
        dist = Distribution(attrs={"name": "example"})

        load_pyproject_config(
            dist, {"source_dir": source_dir, "compiler": "translate-toolkit"}
        )
        cmd = build_mo(dist)
        cmd.initialize_options()
        cmd.finalize_options()

    assert cmd.msgfmt is None
    assert cmd.translate_toolkit is True


@pytest.mark.parametrize(
    ("compiler", "flag", "expected_msgfmt", "expected_translate_toolkit"),
    [
        ("translate-toolkit", "msgfmt", True, None),
        ("msgfmt", "translate_toolkit", None, True),
    ],
)
def test_build_mo_cli_compiler_flags_override_config(
    compiler, flag, expected_msgfmt, expected_translate_toolkit
):
    with TemporaryDirectory() as td:
        source_dir = os.path.join(td, "po")
        os.mkdir(source_dir)
        with open(os.path.join(source_dir, "nl.po"), "w") as f:
            f.write("")
        dist = Distribution(attrs={"name": "example"})

        load_pyproject_config(
            dist, {"source_dir": source_dir, "compiler": compiler}
        )
        cmd = build_mo(dist)
        cmd.initialize_options()
        setattr(cmd, flag, True)
        cmd.finalize_options()

    assert cmd.msgfmt is expected_msgfmt
    assert cmd.translate_toolkit is expected_translate_toolkit


def test_find_source_files_example():
    found = find_source_files("example")
    rel = sorted(os.path.relpath(p, "example") for p in found)
    assert rel == [
        os.path.join("po", "hallowereld.pot"),
        os.path.join("po", "nl.po"),
    ]


def test_find_source_files_missing_dir():
    with TemporaryDirectory() as td:
        assert find_source_files(td) == []


def test_update_pot():
    # Skip this test if xgettext is not available
    if shutil.which("xgettext") is None:
        pytest.skip("xgettext not available")
    with TemporaryDirectory() as td:
        shutil.copytree("example", td + "/example")
        p = os.path.join(td, "example", "hallowereld", "example.py")
        with open(p, "w") as f:
            f.write('# Use the "_" shorthand for gettext\n')
            f.write("from gettext import gettext as _\n")
            f.write('print(_("Hello Example"))')

        dist = Distribution(
            attrs={
                "name": "hallowereld",
            }
        )

        load_pyproject_config(dist, {})

        old_cwd = os.getcwd()
        os.chdir(os.path.join(td, "example"))
        try:
            cmd = update_pot(dist)
            cmd.initialize_options()
            cmd.finalize_options()
            cmd.run()
        finally:
            os.chdir(old_cwd)
        with open(os.path.join(td, "example", "po", "hallowereld.pot")) as f:
            assert "Hello Example" in f.read()
