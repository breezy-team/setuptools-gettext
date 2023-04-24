# setuptools plugin for gettext

Compile .po files into .mo files.

This plugin adds `build_mo`, 'clean_mo' and 'install_mo' subcommands for
setup.py as well as hooking those into standard commands.

## Usage

By default, setuptools_gettext compiles and installs mo files when there is a
`po` directory present that contains ``.po`` files.
