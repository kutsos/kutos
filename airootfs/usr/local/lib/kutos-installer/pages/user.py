"""User Configuration Page — KutOS Installer"""

import re

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk


class UserPage(Gtk.Box):
    def __init__(self, window):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        self.window = window
        self.set_margin_start(40)
        self.set_margin_end(40)
        self.set_margin_top(30)

        # Title
        title = Gtk.Label(xalign=0)
        title.set_markup(
            '<span font_weight="bold" size="20000" foreground="#e0e0ff">'
            "Kullanıcı Ayarları"
            "</span>"
        )
        self.pack_start(title, False, False, 0)

        desc = Gtk.Label(
            label="Sistem kullanıcı bilgilerini ve bilgisayar adını girin.",
            xalign=0,
        )
        desc.get_style_context().add_class("page-description")
        self.pack_start(desc, False, False, 0)

        # Form container
        form = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        form.get_style_context().add_class("card")
        self.pack_start(form, False, False, 0)

        # Hostname
        self.hostname_entry = self._add_field(
            form,
            "Bilgisayar Adı",
            "Ağda görünecek isim",
            "kutos",
        )

        sep1 = Gtk.Separator()
        form.pack_start(sep1, False, False, 4)

        # Username
        self.username_entry = self._add_field(
            form,
            "Kullanıcı Adı",
            "Giriş yapacağınız kullanıcı adı (küçük harf)",
            "",
        )

        # Password
        pw_label = Gtk.Label(label="Şifre", xalign=0)
        pw_label.get_style_context().add_class("field-label")
        form.pack_start(pw_label, False, False, 0)

        self.password_entry = Gtk.Entry()
        self.password_entry.set_visibility(False)
        self.password_entry.set_placeholder_text("Kullanıcı şifresi")
        form.pack_start(self.password_entry, False, False, 0)

        # Confirm password
        pw2_label = Gtk.Label(label="Şifre Tekrar", xalign=0)
        pw2_label.get_style_context().add_class("field-label")
        form.pack_start(pw2_label, False, False, 0)

        self.password2_entry = Gtk.Entry()
        self.password2_entry.set_visibility(False)
        self.password2_entry.set_placeholder_text("Şifreyi tekrar girin")
        form.pack_start(self.password2_entry, False, False, 0)

        # Show password toggle
        show_pw = Gtk.CheckButton(label="Şifreyi göster")
        show_pw.connect("toggled", self._toggle_password_visibility)
        form.pack_start(show_pw, False, False, 0)

        sep2 = Gtk.Separator()
        form.pack_start(sep2, False, False, 4)

        # Root password option
        self.root_same = Gtk.CheckButton(label="Root şifresi kullanıcı ile aynı olsun")
        self.root_same.set_active(True)
        form.pack_start(self.root_same, False, False, 0)

        # Sudo
        self.sudo_check = Gtk.CheckButton(label="Kullanıcıya sudo yetkisi ver")
        self.sudo_check.set_active(True)
        form.pack_start(self.sudo_check, False, False, 0)

        # Timezone
        tz_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        tz_box.set_margin_top(8)
        tz_lbl = Gtk.Label(label="Saat Dilimi:", xalign=0)
        tz_lbl.get_style_context().add_class("field-label")
        tz_lbl.set_size_request(120, -1)
        tz_box.pack_start(tz_lbl, False, False, 0)

        self.tz_combo = Gtk.ComboBoxText()
        timezones = [
            "Europe/Istanbul",
            "Europe/Berlin",
            "Europe/London",
            "America/New_York",
            "America/Los_Angeles",
            "Asia/Tokyo",
            "UTC",
        ]
        for tz in timezones:
            self.tz_combo.append(tz, tz)
        self.tz_combo.set_active_id("Europe/Istanbul")
        tz_box.pack_start(self.tz_combo, True, True, 0)
        form.pack_start(tz_box, False, False, 0)

    def _add_field(self, parent, label, placeholder, default):
        lbl = Gtk.Label(label=label, xalign=0)
        lbl.get_style_context().add_class("field-label")
        parent.pack_start(lbl, False, False, 0)

        entry = Gtk.Entry()
        entry.set_placeholder_text(placeholder)
        if default:
            entry.set_text(default)
        parent.pack_start(entry, False, False, 0)
        return entry

    def _toggle_password_visibility(self, check):
        visible = check.get_active()
        self.password_entry.set_visibility(visible)
        self.password2_entry.set_visibility(visible)

    def validate(self):
        username = self.username_entry.get_text().strip()
        password = self.password_entry.get_text()
        password2 = self.password2_entry.get_text()
        hostname = self.hostname_entry.get_text().strip()

        if not username:
            self._show_error("Kullanıcı adı boş olamaz.")
            return False

        if not re.match(r"^[a-z_][a-z0-9_-]*$", username):
            self._show_error(
                "Kullanıcı adı küçük harf ile başlamalı ve sadece\n"
                "küçük harf, rakam, '-' veya '_' içermelidir."
            )
            return False

        if len(username) > 32:
            self._show_error("Kullanıcı adı en fazla 32 karakter olabilir.")
            return False

        if not password:
            self._show_error("Şifre boş olamaz.")
            return False

        if len(password) < 4:
            self._show_error("Şifre en az 4 karakter olmalıdır.")
            return False

        if password != password2:
            self._show_error("Şifreler eşleşmiyor.")
            return False

        if not hostname:
            self._show_error("Bilgisayar adı boş olamaz.")
            return False

        if not re.match(r"^[a-zA-Z0-9-]+$", hostname):
            self._show_error("Bilgisayar adı sadece harf, rakam ve '-' içerebilir.")
            return False

        return True

    def _show_error(self, msg):
        dialog = Gtk.MessageDialog(
            transient_for=self.window,
            message_type=Gtk.MessageType.WARNING,
            buttons=Gtk.ButtonsType.OK,
            text=msg,
        )
        dialog.run()
        dialog.destroy()

    def collect(self):
        self.window.config["username"] = self.username_entry.get_text().strip()
        self.window.config["password"] = self.password_entry.get_text()
        self.window.config["hostname"] = self.hostname_entry.get_text().strip()
        self.window.config["root_same_password"] = self.root_same.get_active()
        self.window.config["sudo"] = self.sudo_check.get_active()
        self.window.config["timezone"] = (
            self.tz_combo.get_active_id() or "Europe/Istanbul"
        )
