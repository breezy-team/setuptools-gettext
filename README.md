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
