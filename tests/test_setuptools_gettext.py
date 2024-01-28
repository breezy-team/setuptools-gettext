import os
import tempfile

from setuptools_gettext import gather_built_files, lang_from_dir, parse_lang


def test_lang_from_dir():
    td = tempfile.mkdtemp()
    podir = os.path.join(td, 'po')
    os.mkdir(podir)
    with open(os.path.join(podir, 'de.po'), 'w') as f:
        f.write('foo')
    with open(os.path.join(podir, 'fr.po'), 'w') as f:
        f.write('foo')
    with open(os.path.join(podir, 'de_DE.po'), 'w') as f:
        f.write('foo')

    assert set(lang_from_dir(podir)) == set(['de', 'de_DE', 'fr'])


def test_parse_lang():
    assert parse_lang('de') == ['de']
    assert parse_lang('de_DE,de') == ['de_DE', 'de']


def test_gather_built_files():
    td = tempfile.mkdtemp()
    builddir = os.path.join(td, 'po')
    os.mkdir(builddir)
    dedir = os.path.join(builddir, 'de')
    os.mkdir(dedir)
    de_lc_messages_dir = os.path.join(dedir, 'LC_MESSAGES')
    os.mkdir(de_lc_messages_dir)
    with open(os.path.join(de_lc_messages_dir, 'app.mo'), 'w') as f:
        f.write('foo')
    with open(os.path.join(de_lc_messages_dir, 'app2.mo'), 'w') as f:
        f.write('foo')
    assert set(gather_built_files(builddir)) == set([
        os.path.join(de_lc_messages_dir, 'app.mo'),
        os.path.join(de_lc_messages_dir, 'app2.mo'),
    ])

