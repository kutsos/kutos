#!/usr/bin/env python3
"""KutOS Settings — Central configuration tool for KutOS Linux."""

import sys
import os
import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, Gdk, Gio

APP_ID = "org.kutos.settings"
APP_DIR = os.path.dirname(os.path.abspath(__file__))


class KutOSSettingsApp(Gtk.Application):
    def __init__(self):
        super().__init__(
            application_id=APP_ID,
            flags=Gio.ApplicationFlags.DEFAULT_FLAGS,
        )

    def do_activate(self):
        self._load_css()

        from ui.main_window import MainWindow

        win = MainWindow(application=self)
        win.present()

    def _load_css(self):
        css_path = os.path.join(APP_DIR, "theme", "style.css")
        if not os.path.exists(css_path):
            return
        provider = Gtk.CssProvider()
        provider.load_from_path(css_path)
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(),
            provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )


def main():
    # Ensure our package is importable
    if APP_DIR not in sys.path:
        sys.path.insert(0, APP_DIR)

    app = KutOSSettingsApp()
    return app.run(sys.argv)


if __name__ == "__main__":
    raise SystemExit(main())
