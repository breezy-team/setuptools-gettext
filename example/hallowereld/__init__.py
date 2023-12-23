"""A simple example of a Python package with translations."""

# Use the "_" shorthand for gettext
from gettext import gettext as _


def hallo() -> str:
    return _("Hello World!")


def load_translations():
    import gettext
    import os

    if os.path.exists("setup.py"):
        # We are running from source, so we need to install the translations
        locale_dir = os.path.join(os.path.dirname(__file__), "locale")
    else:
        # Otherwise, we assume the translations are installed in the relevant
        # system directory that shares our prefix

        # Note that we can't just use sys.prefix, since while Python might be
        # installed in /usr, our package (and thus the translations) might be
        # in /usr/local
        locale_dir = os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "..",
            "..",
            "share",
            "locale",
        )
    gettext.bindtextdomain("hallowereld", localedir=locale_dir)
    print("Loading translations from", locale_dir)

    # Set the default domain, so we can use gettext (or _()) instead of
    # dgettext
    gettext.textdomain("hallowereld")
