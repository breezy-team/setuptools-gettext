# setuptools plugin for gettext

Compile .po files into .mo files.

This plugin adds `build_mo`, `clean_mo` and `install_mo` subcommands for
setup.py as well as hooking those into standard commands.

## Usage

By default, setuptools_gettext compiles and installs mo files when there is a
`po` directory present that contains ``.po`` files.

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
```

## Compilation tool

By default, either ``msgfmt`` or the `translate-toolkit` package is used to
compile the .po files into .mo files - whichever is available.

The ``--msgfmt`` option can be used to force the use of ``msgfmt``, and the
``--translate-toolkit`` option can be used to force the use of the
translate-toolkit.

At the moment, ``msgfmt`` is preferred. In the future, the translate-toolkit
will become the default.

You can use the ``translate-toolkit`` extra to install the translate-toolkit
package.
