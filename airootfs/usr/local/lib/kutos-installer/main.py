#!/usr/bin/env python3
"""KutOS Installer — Main Entry Point"""

import sys
import os
import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, Gio

from window import InstallerWindow
import i18n

def _load_css():
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
    i18n.init() # Default to Turkish
    _load_css()
    win = InstallerWindow(application=None)
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()

if __name__ == "__main__":
    main()
