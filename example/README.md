This directory contains an example project that uses ``setuptools_gettext``.

Note that while it uses the standard Python ``gettext`` module to access translations,
``setuptools_gettext`` will also happily work with other gettext-compatible
packages.

The pot file can be updated by running ``./setup.py update-pot`` in the current
directory.

A new translation file can be created by
running ``msginit -l $LANG -o po/$LANG.po po/hallowereld.pot``.
