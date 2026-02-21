#!/usr/bin/env python3
"""KutOS Installer — Main Entry Point"""

import sys
import os
import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, Gio

from window import InstallerWindow


class KutOSInstaller(Gtk.Application):
    def __init__(self):
        super().__init__(
            application_id="org.kutos.installer",
            flags=Gio.ApplicationFlags.FLAGS_NONE,
        )

    def do_activate(self):
        self._load_css()
        win = InstallerWindow(application=self)
        win.present()

    def _load_css(self):
        css_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "theme", "style.css"
        )
        provider = Gtk.CssProvider()
        provider.load_from_path(css_path)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )

        settings = Gtk.Settings.get_default()
        settings.set_property("gtk-application-prefer-dark-theme", True)


def main():
    app = KutOSInstaller()
    sys.exit(app.run(sys.argv))


if __name__ == "__main__":
    main()
