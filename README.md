# setuptools plugin for gettext

Compile .po files into .mo files.

This plugin adds `build_mo`, `clean_mo` and `install_mo` subcommands for
setup.py as well as hooking those into standard commands.

## Usage

By default, setuptools_gettext compiles and installs mo files when there is a
`po` directory present that contains ``.po`` files. It also supports the
standard gettext layout with ``locale/*/LC_MESSAGES/*.po`` files. If ``po`` is
absent and a top-level ``locale`` directory contains standard gettext catalogs,
that directory is used automatically.

The .mo files are installed adjacent to your package as package data in a subdirectory called ``locale``.

You can override these settings in ``pyproject.toml``:

```toml
[build-system]
requires = ["setuptools", "setuptools-gettext"]
...

[tool.setuptools-gettext]
# directory in which the .po files can be found 
source_dir = "po"
# directory in which the generated .mo files are placed when building
build_dir = "breezy/locale"
# compiler to use: "auto", "msgfmt", or "translate-toolkit"
compiler = "auto"
```

For standard gettext layouts, point both directories at the locale tree:

```toml
[tool.setuptools-gettext]
source_dir = "breezy/locale"
build_dir = "breezy/locale"
```

Flat ``po/de.po`` files compile to
``<build_dir>/de/LC_MESSAGES/<project-name>.mo`` by default. Standard
``locale/de/LC_MESSAGES/django.po`` files compile to
``<build_dir>/de/LC_MESSAGES/django.mo`` by default. Passing
``--output-base`` overrides the output name for both layouts.

## Compilation tool

By default, either ``msgfmt`` or the `translate-toolkit` package is used to
compile the .po files into .mo files - whichever is available.

Set ``compiler = "msgfmt"`` or ``compiler = "translate-toolkit"`` in
``[tool.setuptools-gettext]`` to force a compiler from ``pyproject.toml``.
Use ``compiler = "auto"`` to keep the default automatic detection.

The ``--msgfmt`` option can be used to force the use of ``msgfmt``, and the
``--translate-toolkit`` option can be used to force the use of the
translate-toolkit. Command line options take precedence over the
``pyproject.toml`` setting.

At the moment, ``msgfmt`` is preferred. In the future, the translate-toolkit
will become the default.

You can use the ``translate-toolkit`` extra to install the translate-toolkit
package.
