import os
from tempfile import TemporaryDirectory
from typing import NoReturn

import pytest
from setuptools import Distribution
from setuptools.errors import OptionError

import setuptools_gettext
import setuptools_gettext.install_layout
from setuptools_gettext import (
    build_mo,
    discover_catalogs,
    find_source_files,
    gather_built_files,
    install_mo,
    load_pyproject_config,
    parse_lang,
    pyprojecttoml_config,
)
from setuptools_gettext.catalog import lang_from_dir


def write_file(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write("foo")


def test_lang_from_dir():
    with TemporaryDirectory() as td:
        podir = os.path.join(td, "po")
        os.mkdir(podir)
        with open(os.path.join(podir, "de.po"), "w") as f:
            f.write("foo")
        with open(os.path.join(podir, "fr.po"), "w") as f:
            f.write("foo")
        with open(os.path.join(podir, "de_DE.po"), "w") as f:
            f.write("foo")
        with open(os.path.join(podir, "pt-BR.po"), "w") as f:
            f.write("foo")

        assert set(lang_from_dir(podir)) == {"de", "de_DE", "fr", "pt-BR"}


def test_parse_lang():
    assert parse_lang("de") == ["de"]
    assert parse_lang("de_DE,de") == ["de_DE", "de"]


def test_gather_built_files():
    with TemporaryDirectory() as td:
        builddir = os.path.join(td, "po")
        os.mkdir(builddir)
        dedir = os.path.join(builddir, "de")
        os.mkdir(dedir)
        de_lc_messages_dir = os.path.join(dedir, "LC_MESSAGES")
        os.mkdir(de_lc_messages_dir)
        with open(os.path.join(de_lc_messages_dir, "app.mo"), "w") as f:
            f.write("foo")
        with open(os.path.join(de_lc_messages_dir, "app2.mo"), "w") as f:
            f.write("foo")
        assert set(gather_built_files(builddir)) == {
            os.path.join(de_lc_messages_dir, "app.mo"),
            os.path.join(de_lc_messages_dir, "app2.mo"),
        }


def test_discover_catalogs_standard_layout():
    with TemporaryDirectory() as td:
        locale = os.path.join(td, "locale")
        po = os.path.join(locale, "pt-BR", "LC_MESSAGES", "django.po")
        write_file(po)

        catalogs = discover_catalogs(locale)

        assert catalogs[0].lang == "pt-BR"
        assert catalogs[0].domain == "django"
        assert catalogs[0].po == po
        assert not catalogs[0].uses_output_base


def run_build(cmd, monkeypatch):
    compiled = []

    def compile_mo(po, mo) -> None:
        compiled.append((po, mo))
        write_file(mo)

    monkeypatch.setattr(setuptools_gettext, "has_msgfmt", lambda: True)
    cmd.compile_mo = compile_mo
    cmd.run()
    return compiled


def test_build_standard_layout_uses_po_filename_domain(monkeypatch):
    with TemporaryDirectory() as td:
        locale = os.path.join(td, "locale")
        po = os.path.join(locale, "de", "LC_MESSAGES", "django.po")
        write_file(po)
        build_dir = os.path.join(td, "build")
        dist = Distribution(attrs={"name": "demo"})
        load_pyproject_config(
            dist, {"source_dir": locale, "build_dir": build_dir}
        )
        cmd = build_mo(dist)
        cmd.initialize_options()
        cmd.finalize_options()

        compiled = run_build(cmd, monkeypatch)

        mo = os.path.join(build_dir, "de", "LC_MESSAGES", "django.mo")
        assert compiled == [(po, mo)]
        assert cmd.get_outputs() == [mo]


def test_build_standard_layout_multiple_domains(monkeypatch):
    with TemporaryDirectory() as td:
        locale = os.path.join(td, "locale")
        django_po = os.path.join(locale, "de", "LC_MESSAGES", "django.po")
        djangojs_po = os.path.join(locale, "de", "LC_MESSAGES", "djangojs.po")
        write_file(django_po)
        write_file(djangojs_po)
        build_dir = os.path.join(td, "build")
        dist = Distribution(attrs={"name": "demo"})
        load_pyproject_config(
            dist, {"source_dir": locale, "build_dir": build_dir}
        )
        cmd = build_mo(dist)
        cmd.initialize_options()
        cmd.finalize_options()

        compiled = set(run_build(cmd, monkeypatch))

        assert compiled == {
            (
                django_po,
                os.path.join(build_dir, "de", "LC_MESSAGES", "django.mo"),
            ),
            (
                djangojs_po,
                os.path.join(build_dir, "de", "LC_MESSAGES", "djangojs.mo"),
            ),
        }


def test_build_standard_layout_output_base_overrides_domain(monkeypatch):
    with TemporaryDirectory() as td:
        locale = os.path.join(td, "locale")
        po = os.path.join(locale, "de", "LC_MESSAGES", "django.po")
        write_file(po)
        build_dir = os.path.join(td, "build")
        dist = Distribution(attrs={"name": "demo"})
        load_pyproject_config(
            dist, {"source_dir": locale, "build_dir": build_dir}
        )
        cmd = build_mo(dist)
        cmd.initialize_options()
        cmd.output_base = "custom"
        cmd.finalize_options()

        compiled = run_build(cmd, monkeypatch)

        mo = os.path.join(build_dir, "de", "LC_MESSAGES", "custom.mo")
        assert compiled == [(po, mo)]
        assert cmd.get_outputs() == [mo]


def test_build_mixed_layouts_without_output_collision(monkeypatch):
    with TemporaryDirectory() as td:
        source = os.path.join(td, "po")
        flat_po = os.path.join(source, "de.po")
        standard_po = os.path.join(source, "de", "LC_MESSAGES", "django.po")
        write_file(flat_po)
        write_file(standard_po)
        build_dir = os.path.join(td, "build")
        dist = Distribution(attrs={"name": "demo"})
        load_pyproject_config(
            dist, {"source_dir": source, "build_dir": build_dir}
        )
        cmd = build_mo(dist)
        cmd.initialize_options()
        cmd.finalize_options()

        compiled = set(run_build(cmd, monkeypatch))

        assert compiled == {
            (
                flat_po,
                os.path.join(build_dir, "de", "LC_MESSAGES", "demo.mo"),
            ),
            (
                standard_po,
                os.path.join(build_dir, "de", "LC_MESSAGES", "django.mo"),
            ),
        }


def test_package_layout_build_py_copies_generated_mo(monkeypatch):
    with TemporaryDirectory() as td:
        app_dir = os.path.join(td, "myapp")
        write_file(os.path.join(app_dir, "__init__.py"))
        locale = os.path.join(app_dir, "locale")
        po = os.path.join(locale, "de", "LC_MESSAGES", "django.po")
        write_file(po)
        dist = Distribution(
            attrs={
                "name": "demo",
                "packages": ["myapp"],
                "package_dir": {"myapp": app_dir},
            }
        )
        dist.script_name = "setup.py"
        load_pyproject_config(
            dist,
            {
                "source_dir": locale,
                "build_dir": locale,
                "install_layout": "package",
            },
        )
        old_cwd = os.getcwd()
        os.chdir(td)
        try:
            cmd = build_mo(dist)
            cmd.initialize_options()
            cmd.finalize_options()
            compiled = run_build(cmd, monkeypatch)

            build_py = dist.get_command_obj("build_py")
            build_py.ensure_finalized()
            build_py.build_lib = os.path.join(td, "build")
            build_py.run()
        finally:
            os.chdir(old_cwd)

        mo = os.path.join(locale, "de", "LC_MESSAGES", "django.mo")
        assert compiled == [(po, mo)]
        assert os.path.exists(
            os.path.join(
                td,
                "build",
                "myapp",
                "locale",
                "de",
                "LC_MESSAGES",
                "django.mo",
            )
        )


def test_install_mo_share_layout_keeps_legacy_destination():
    with TemporaryDirectory() as td:
        build_dir = os.path.join(td, "build")
        mo = os.path.join(build_dir, "de", "LC_MESSAGES", "django.mo")
        write_file(mo)
        install_dir = os.path.join(td, "install")
        dist = Distribution(attrs={"name": "demo"})
        load_pyproject_config(dist, {"build_dir": build_dir})
        cmd = install_mo(dist)
        cmd.initialize_options()
        cmd.install_dir = install_dir
        cmd.finalize_options()

        cmd.run()

        installed = os.path.join(
            install_dir,
            "share",
            "locale",
            "de",
            "LC_MESSAGES",
            "django.mo",
        )
        assert cmd.get_outputs() == [installed]
        assert os.path.exists(installed)


def test_install_mo_package_layout_installs_inside_package():
    with TemporaryDirectory() as td:
        app_dir = os.path.join(td, "myapp")
        write_file(os.path.join(app_dir, "__init__.py"))
        build_dir = os.path.join(app_dir, "locale")
        mo = os.path.join(build_dir, "de", "LC_MESSAGES", "django.mo")
        write_file(mo)
        install_dir = os.path.join(td, "install")
        dist = Distribution(
            attrs={
                "name": "demo",
                "packages": ["myapp"],
                "package_dir": {"myapp": app_dir},
            }
        )
        load_pyproject_config(
            dist, {"build_dir": build_dir, "install_layout": "package"}
        )
        cmd = install_mo(dist)
        cmd.initialize_options()
        cmd.install_dir = install_dir
        cmd.finalize_options()

        cmd.run()

        installed = os.path.join(
            install_dir,
            "myapp",
            "locale",
            "de",
            "LC_MESSAGES",
            "django.mo",
        )
        assert cmd.get_outputs() == [installed]
        assert os.path.exists(installed)


def test_install_mo_package_layout_installs_src_layout_package():
    with TemporaryDirectory() as td:
        app_dir = os.path.join(td, "src", "myapp")
        write_file(os.path.join(app_dir, "__init__.py"))
        build_dir = os.path.join(app_dir, "locale")
        write_file(os.path.join(build_dir, "de", "LC_MESSAGES", "django.mo"))
        install_dir = os.path.join(td, "install")
        dist = Distribution(
            attrs={
                "name": "demo",
                "packages": ["myapp"],
                "package_dir": {"": os.path.join(td, "src")},
            }
        )
        load_pyproject_config(
            dist, {"build_dir": build_dir, "install_layout": "package"}
        )
        cmd = install_mo(dist)
        cmd.initialize_options()
        cmd.install_dir = install_dir
        cmd.finalize_options()

        cmd.run()

        assert cmd.get_outputs() == [
            os.path.join(
                install_dir,
                "myapp",
                "locale",
                "de",
                "LC_MESSAGES",
                "django.mo",
            )
        ]


def test_package_layout_rejects_build_dir_outside_packages():
    with TemporaryDirectory() as td:
        build_dir = os.path.join(td, "locale")
        write_file(os.path.join(build_dir, "de", "LC_MESSAGES", "django.mo"))
        dist = Distribution(attrs={"name": "demo", "packages": ["myapp"]})
        load_pyproject_config(
            dist, {"build_dir": build_dir, "install_layout": "package"}
        )
        cmd = install_mo(dist)
        cmd.initialize_options()
        cmd.install_dir = os.path.join(td, "install")

        with pytest.raises(OptionError, match="inside a configured package"):
            cmd.finalize_options()


def test_package_layout_rejects_build_dir_on_different_mount(monkeypatch):
    with TemporaryDirectory() as td:
        build_dir = os.path.join(td, "locale")
        write_file(os.path.join(build_dir, "de", "LC_MESSAGES", "django.mo"))
        dist = Distribution(attrs={"name": "demo", "packages": ["myapp"]})
        load_pyproject_config(
            dist, {"build_dir": build_dir, "install_layout": "package"}
        )

        def raise_value_error(_path, _parent) -> NoReturn:
            raise ValueError("path is on mount 'c:', start on mount 'd:'")

        monkeypatch.setattr(
            setuptools_gettext.install_layout.os.path,
            "relpath",
            raise_value_error,
        )
        cmd = install_mo(dist)
        cmd.initialize_options()
        cmd.install_dir = os.path.join(td, "install")

        with pytest.raises(OptionError, match="inside a configured package"):
            cmd.finalize_options()


def test_pyproject_config_registers_build_mo_before_build_py():
    dist = Distribution()

    pyprojecttoml_config(dist)

    sub_commands = [
        sub_command[0]
        for sub_command in dist.get_command_class("build").sub_commands
    ]
    assert sub_commands.count("build_mo") == 1
    assert sub_commands.index("build_mo") < sub_commands.index("build_py")


def test_duplicate_output_paths_are_rejected():
    with TemporaryDirectory() as td:
        locale = os.path.join(td, "locale")
        write_file(os.path.join(locale, "de", "LC_MESSAGES", "django.po"))
        write_file(os.path.join(locale, "de", "LC_MESSAGES", "app.po"))
        dist = Distribution(attrs={"name": "demo"})
        build_dir = os.path.join(td, "build")
        load_pyproject_config(
            dist, {"source_dir": locale, "build_dir": build_dir}
        )
        cmd = build_mo(dist)
        cmd.initialize_options()
        cmd.output_base = "custom"

        with pytest.raises(OptionError, match="Multiple gettext catalogs"):
            cmd.finalize_options()


def test_load_pyproject_config_auto_detects_locale_without_po():
    with TemporaryDirectory() as td:
        write_file(
            os.path.join(td, "locale", "de", "LC_MESSAGES", "django.po")
        )
        old_cwd = os.getcwd()
        os.chdir(td)
        try:
            dist = Distribution(attrs={"name": "demo"})
            load_pyproject_config(dist, {})
        finally:
            os.chdir(old_cwd)

        assert dist.gettext_source_dir == "locale"


def test_find_source_files_auto_detects_locale():
    with TemporaryDirectory() as td:
        write_file(os.path.join(td, "locale", "django.pot"))
        write_file(
            os.path.join(td, "locale", "de", "LC_MESSAGES", "django.po")
        )

        found = find_source_files(td)

        assert sorted(os.path.relpath(path, td) for path in found) == [
            os.path.join("locale", "de", "LC_MESSAGES", "django.po"),
            os.path.join("locale", "django.pot"),
        ]
