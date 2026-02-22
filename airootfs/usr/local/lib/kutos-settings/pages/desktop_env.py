"""Desktop Environment selection page."""

import threading

import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, GLib

from utils.downloader import download_and_extract

DE_CONFIGS = {
    "XFCE": "https://github.com/kutos-linux/configs/raw/main/xfce.tar.gz",
    "KDE": "https://github.com/kutos-linux/configs/raw/main/kde.tar.gz",
    "GNOME": "https://github.com/kutos-linux/configs/raw/main/gnome.tar.gz",
    "Hyprland": "https://github.com/kutos-linux/configs/raw/main/hyprland.tar.gz",
}

DE_ICONS = {
    "XFCE": "xfce4-logo",
    "KDE": "kde",
    "GNOME": "gnome-logo",
    "Hyprland": "wayland",
}


class DesktopEnvPage(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.set_margin_top(40)
        self.set_margin_bottom(40)
        self.set_margin_start(40)
        self.set_margin_end(40)
        self.set_valign(Gtk.Align.START)

        # Title
        title = Gtk.Label(label="Desktop Environment")
        title.add_css_class("page-title")
        title.set_halign(Gtk.Align.START)
        self.append(title)

        subtitle = Gtk.Label(
            label="Choose a desktop environment to download and apply its configuration."
        )
        subtitle.add_css_class("page-subtitle")
        subtitle.set_halign(Gtk.Align.START)
        subtitle.set_margin_bottom(30)
        self.append(subtitle)

        # Grid of DE buttons
        grid = Gtk.Grid()
        grid.set_column_spacing(16)
        grid.set_row_spacing(16)
        grid.set_column_homogeneous(True)
        grid.set_halign(Gtk.Align.FILL)
        grid.set_hexpand(True)

        for i, (name, url) in enumerate(DE_CONFIGS.items()):
            card = self._make_de_card(name, url)
            grid.attach(card, i % 2, i // 2, 1, 1)

        self.append(grid)

        # Status area
        self.status_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.status_box.set_margin_top(30)
        self.status_box.set_halign(Gtk.Align.CENTER)
        self.append(self.status_box)

    def _make_de_card(self, name, url):
        card = Gtk.Button()
        card.add_css_class("de-card")
        card.set_hexpand(True)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        box.set_margin_top(20)
        box.set_margin_bottom(20)
        box.set_margin_start(16)
        box.set_margin_end(16)

        label = Gtk.Label(label=name)
        label.add_css_class("de-card-title")
        box.append(label)

        desc = Gtk.Label(label=f"Apply {name} configuration")
        desc.add_css_class("de-card-desc")
        box.append(desc)

        card.set_child(box)
        card.connect("clicked", self._on_de_clicked, name, url)
        return card

    def _on_de_clicked(self, _button, name, url):
        # Clear previous status
        child = self.status_box.get_first_child()
        while child:
            next_child = child.get_next_sibling()
            self.status_box.remove(child)
            child = next_child

        # Show spinner
        spinner_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        spinner_box.set_halign(Gtk.Align.CENTER)

        spinner = Gtk.Spinner()
        spinner.start()
        spinner_box.append(spinner)

        lbl = Gtk.Label(label=f"Downloading {name} configuration…")
        lbl.add_css_class("status-text")
        spinner_box.append(lbl)

        self.status_box.append(spinner_box)

        # Start download in background
        threading.Thread(
            target=self._download_config,
            args=(name, url, spinner),
            daemon=True,
        ).start()

    def _download_config(self, name, url, spinner):
        success, message = download_and_extract(url)
        GLib.idle_add(self._on_download_done, name, success, message, spinner)

    def _on_download_done(self, name, success, message, spinner):
        spinner.stop()

        # Clear status
        child = self.status_box.get_first_child()
        while child:
            next_child = child.get_next_sibling()
            self.status_box.remove(child)
            child = next_child

        if success:
            self._show_dialog(
                "Success",
                f"{name} configuration installed successfully!",
            )
        else:
            self._show_dialog("Error", f"Failed to install {name} config:\n{message}")

    def _show_dialog(self, title, message):
        dialog = Gtk.AlertDialog()
        dialog.set_message(title)
        dialog.set_detail(message)
        dialog.set_buttons(["OK"])
        dialog.set_default_button(0)
        dialog.set_cancel_button(0)

        window = self.get_root()
        dialog.show(window)
