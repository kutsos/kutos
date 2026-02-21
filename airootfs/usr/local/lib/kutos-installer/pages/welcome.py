"""Welcome Page — KutOS Installer"""

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Pango


class WelcomePage(Gtk.Box):
    def __init__(self, window):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        self.window = window
        self.set_halign(Gtk.Align.CENTER)
        self.set_valign(Gtk.Align.CENTER)
        self.set_margin_start(60)
        self.set_margin_end(60)

        # Logo
        logo = Gtk.Label(label="⚡")
        logo.set_markup('<span size="72000">⚡</span>')
        logo.get_style_context().add_class("welcome-logo")
        self.pack_start(logo, False, False, 0)

        # Title
        title = Gtk.Label()
        title.set_markup(
            '<span font_weight="bold" size="28000" foreground="#e0e0ff">'
            "KutOS'a Hoş Geldiniz"
            "</span>"
        )
        title.get_style_context().add_class("welcome-title")
        self.pack_start(title, False, False, 0)

        # Subtitle
        subtitle = Gtk.Label(
            label="Minimal, hızlı ve modern bir Arch Linux deneyimi.\n"
            "Bu sihirbaz sizi kurulum adımlarında yönlendirecek."
        )
        subtitle.set_justify(Gtk.Justification.CENTER)
        subtitle.set_line_wrap(True)
        subtitle.get_style_context().add_class("welcome-subtitle")
        self.pack_start(subtitle, False, False, 10)

        # Separator
        sep = Gtk.Separator()
        sep.set_margin_top(10)
        sep.set_margin_bottom(10)
        self.pack_start(sep, False, False, 0)

        # Features
        features_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=30)
        features_box.set_halign(Gtk.Align.CENTER)
        self.pack_start(features_box, False, False, 0)

        features = [
            ("🖥️", "3 Masaüstü", "XFCE, Hyprland, GNOME"),
            ("📦", "AUR Desteği", "yay hazır kurulu"),
            ("🚀", "Minimal", "Düşük RAM kullanımı"),
        ]
        for icon, title_text, desc in features:
            card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
            card.get_style_context().add_class("card")
            card.set_size_request(160, -1)

            icon_lbl = Gtk.Label()
            icon_lbl.set_markup(f'<span size="24000">{icon}</span>')
            card.pack_start(icon_lbl, False, False, 4)

            t = Gtk.Label()
            t.set_markup(
                f'<span font_weight="bold" foreground="#e0e0ff">{title_text}</span>'
            )
            card.pack_start(t, False, False, 2)

            d = Gtk.Label(label=desc)
            d.get_style_context().add_class("info-text")
            card.pack_start(d, False, False, 2)

            features_box.pack_start(card, False, False, 0)

        # Language selection
        lang_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        lang_box.set_halign(Gtk.Align.CENTER)
        lang_box.set_margin_top(20)

        lang_label = Gtk.Label(label="Sistem Dili:")
        lang_label.get_style_context().add_class("field-label")
        lang_box.pack_start(lang_label, False, False, 0)

        self.lang_combo = Gtk.ComboBoxText()
        self.lang_combo.append("tr_TR.UTF-8", "Türkçe")
        self.lang_combo.append("en_US.UTF-8", "English")
        self.lang_combo.append("de_DE.UTF-8", "Deutsch")
        self.lang_combo.set_active_id("tr_TR.UTF-8")
        lang_box.pack_start(self.lang_combo, False, False, 0)

        self.pack_start(lang_box, False, False, 0)

    def collect(self):
        self.window.config["language"] = self.lang_combo.get_active_id() or "tr_TR.UTF-8"
