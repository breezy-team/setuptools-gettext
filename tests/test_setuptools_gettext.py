import os
from tempfile import TemporaryDirectory

import pytest
from setuptools import Distribution
from setuptools.errors import OptionError

import setuptools_gettext
from setuptools_gettext import (
    build_mo,
    discover_catalogs,
    find_source_files,
    gather_built_files,
    load_pyproject_config,
    parse_lang,
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
