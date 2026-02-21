"""User Configuration Page — KutOS Installer"""

import re
import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
import i18n


class UserPage(Gtk.Box):
    def __init__(self, window):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        self.window = window
        self.set_margin_start(40)
        self.set_margin_end(40)
        self.set_margin_top(30)
        
        # Internal state to preserve values across refreshes
        self.val_hostname = "kutos"
        self.val_username = ""
        self.val_pass = ""
        self.val_pass2 = ""
        self.val_root_same = True
        self.val_sudo = True
        self.val_timezone = "Europe/Istanbul"

        self._build_ui()

    def _build_ui(self):
        # Clear existing
        for child in self.get_children():
            self.remove(child)

        # Title
        title = Gtk.Label(xalign=0)
        title.set_markup(f'<span font_weight="bold" size="20000" foreground="#fafafa">{i18n._("user_title")}</span>')
        self.pack_start(title, False, False, 0)

        desc = Gtk.Label(label=i18n._("user_desc"), xalign=0)
        desc.get_style_context().add_class("page-description")
        self.pack_start(desc, False, False, 0)

        # Form container
        form = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        form.get_style_context().add_class("card")
        self.pack_start(form, False, False, 0)

        # Hostname
        self.hostname_entry = self._add_field(form, i18n._("user_host_label"), "kutos", self.val_hostname)
        
        # Username
        self.username_entry = self._add_field(form, i18n._("user_name_label"), "user", self.val_username)

        # Password
        self.password_entry = self._add_field(form, i18n._("user_pass_label"), "****", self.val_pass, is_pass=True)
        self.password2_entry = self._add_field(form, i18n._("user_pass_confirm_label"), "****", self.val_pass2, is_pass=True)

        # Root password same
        self.root_same = Gtk.CheckButton(label=i18n._("user_root_same_label"))
        self.root_same.set_active(self.val_root_same)
        form.pack_start(self.root_same, False, False, 0)

        # Sudo
        self.sudo_check = Gtk.CheckButton(label=i18n._("user_sudo_label"))
        self.sudo_check.set_active(self.val_sudo)
        form.pack_start(self.sudo_check, False, False, 0)

        # Timezone (keep it simple for now as per user preference for "simple premium")
        tz_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        tz_lbl = Gtk.Label(label="Timezone:", xalign=0)
        tz_lbl.get_style_context().add_class("field-label")
        tz_box.pack_start(tz_lbl, False, False, 0)
        
        self.tz_combo = Gtk.ComboBoxText()
        for tz in ["Europe/Istanbul", "Europe/London", "America/New_York", "UTC"]:
            self.tz_combo.append(tz, tz)
        self.tz_combo.set_active_id(self.val_timezone)
        tz_box.pack_start(self.tz_combo, True, True, 0)
        form.pack_start(tz_box, False, False, 0)

        self.show_all()

    def _add_field(self, parent, label, placeholder, value, is_pass=False):
        lbl = Gtk.Label(label=label, xalign=0)
        lbl.get_style_context().add_class("field-label")
        parent.pack_start(lbl, False, False, 0)

        entry = Gtk.Entry()
        entry.set_placeholder_text(placeholder)
        entry.set_text(value)
        if is_pass:
            entry.set_visibility(False)
        parent.pack_start(entry, False, False, 0)
        return entry

    def collect(self):
        self.val_hostname = self.hostname_entry.get_text()
        self.val_username = self.username_entry.get_text()
        self.val_pass = self.password_entry.get_text()
        self.val_pass2 = self.password2_entry.get_text()
        self.val_root_same = self.root_same.get_active()
        self.val_sudo = self.sudo_check.get_active()
        self.val_timezone = self.tz_combo.get_active_id() or "UTC"
        
        self.window.config.update({
            "hostname": self.val_hostname,
            "username": self.val_username,
            "password": self.val_pass,
            "root_same_password": self.val_root_same,
            "sudo": self.val_sudo,
            "timezone": self.val_timezone
        })

    def validate(self):
        self.collect()
        if not self.val_username or not self.val_pass:
            return False
        if self.val_pass != self.val_pass2:
            return False
        return True

    def refresh(self):
        self.collect()
        self._build_ui()
