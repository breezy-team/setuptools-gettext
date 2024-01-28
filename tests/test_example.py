import os
import shutil
import tempfile

from setuptools import Distribution

from setuptools_gettext import (
    build_mo,
    install_mo,
    load_pyproject_config,
    update_pot,
)


def test_example_build():
    td = tempfile.mkdtemp()
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
    td = tempfile.mkdtemp()
    shutil.copytree("example", td + "/example")
    root = tempfile.mkdtemp()

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


def test_update_pot():
    td = tempfile.mkdtemp()
    shutil.copytree("example", td + "/example")
    p = os.path.join(td, 'example', 'hallowereld', 'example.py')
    with open(p, 'w') as f:
        f.write("# Use the \"_\" shorthand for gettext\n")
        f.write("from gettext import gettext as _\n")
        f.write('print(_("Hello Example"))')

    dist = Distribution(attrs={
        "name": "hallowereld",
    })

    load_pyproject_config(dist, {})

    old_cwd = os.getcwd()
    os.chdir(os.path.join(td, 'example'))
    try:
        cmd = update_pot(dist)
        cmd.initialize_options()
        cmd.finalize_options()
        cmd.run()
    finally:
        os.chdir(old_cwd)
    with open(os.path.join(td, 'example', 'po', 'hallowereld.pot')) as f:
        assert 'Hello Example' in f.read()
