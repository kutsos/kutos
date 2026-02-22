"""About page — app info, version, and links."""

import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, Gio


class AboutPage(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.set_valign(Gtk.Align.CENTER)
        self.set_halign(Gtk.Align.CENTER)

        # App icon placeholder
        icon = Gtk.Image.new_from_icon_name("preferences-system")
        icon.set_pixel_size(96)
        icon.set_margin_bottom(16)
        icon.add_css_class("about-icon")
        self.append(icon)

        # App name
        name_label = Gtk.Label(label="KutOS Settings")
        name_label.add_css_class("about-title")
        self.append(name_label)

        # Version
        version_label = Gtk.Label(label="Version 1.0")
        version_label.add_css_class("about-version")
        version_label.set_margin_top(4)
        self.append(version_label)

        # Distribution
        distro_label = Gtk.Label(label="Distribution: KutOS")
        distro_label.add_css_class("about-distro")
        distro_label.set_margin_top(4)
        distro_label.set_margin_bottom(20)
        self.append(distro_label)

        # Separator
        sep = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        sep.set_margin_start(60)
        sep.set_margin_end(60)
        sep.set_margin_bottom(20)
        self.append(sep)

        # Description
        desc = Gtk.Label(
            label="KutOS Settings is the central configuration tool\nfor the KutOS Linux distribution."
        )
        desc.add_css_class("about-description")
        desc.set_justify(Gtk.Justification.CENTER)
        desc.set_margin_bottom(30)
        self.append(desc)

        # Link buttons
        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        btn_box.set_halign(Gtk.Align.CENTER)

        website_btn = Gtk.Button(label="Website")
        website_btn.add_css_class("suggested-action")
        website_btn.add_css_class("link-btn")
        website_btn.connect("clicked", self._open_url, "https://github.com/kutos-linux")
        btn_box.append(website_btn)

        github_btn = Gtk.Button(label="GitHub")
        github_btn.add_css_class("suggested-action")
        github_btn.add_css_class("link-btn")
        github_btn.connect("clicked", self._open_url, "https://github.com/kutos-linux")
        btn_box.append(github_btn)

        self.append(btn_box)

    def _open_url(self, _button, url):
        launcher = Gtk.UriLauncher.new(url)
        window = self.get_root()
        launcher.launch(window, None, None)
