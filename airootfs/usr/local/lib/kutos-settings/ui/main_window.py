"""Main application window with HeaderBar and StackSidebar navigation."""

import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk

from pages.desktop_env import DesktopEnvPage
from pages.system_update import SystemUpdatePage
from pages.about import AboutPage


class MainWindow(Gtk.ApplicationWindow):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_title("KutOS Settings")
        self.set_default_size(900, 600)

        self._build_ui()

    def _build_ui(self):
        # HeaderBar
        header = Gtk.HeaderBar()
        header.set_show_title_buttons(True)

        title_label = Gtk.Label(label="KutOS Settings")
        title_label.add_css_class("header-title")
        header.set_title_widget(title_label)

        self.set_titlebar(header)

        # Main layout: sidebar + stack
        paned = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        paned.set_hexpand(True)
        paned.set_vexpand(True)

        # Stack holds the pages
        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        self.stack.set_transition_duration(200)
        self.stack.set_hexpand(True)
        self.stack.set_vexpand(True)

        # Sidebar navigates the stack
        sidebar = Gtk.StackSidebar()
        sidebar.set_stack(self.stack)
        sidebar.set_size_request(220, -1)
        sidebar.add_css_class("sidebar")

        # Add pages
        de_page = DesktopEnvPage()
        self.stack.add_titled(de_page, "desktop_env", "Desktop Environment")

        update_page = SystemUpdatePage()
        self.stack.add_titled(update_page, "system_update", "System Update")

        about_page = AboutPage()
        self.stack.add_titled(about_page, "about", "About")

        # Assemble
        paned.append(sidebar)

        separator = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
        paned.append(separator)

        paned.append(self.stack)

        self.set_child(paned)
