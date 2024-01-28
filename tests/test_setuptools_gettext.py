import os
import tempfile

from setuptools_gettext import lang_from_dir, parse_lang


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
