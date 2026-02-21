"""Welcome Page — KutOS Installer"""

import gi
import os

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GdkPixbuf
import i18n


class WelcomePage(Gtk.Box):
    def __init__(self, window):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        self.window = window
        self.set_halign(Gtk.Align.CENTER)
        self.set_valign(Gtk.Align.CENTER)
        self.set_margin_start(60)
        self.set_margin_end(60)

        self._build_ui()

    def _build_ui(self):
        # Clear existing
        for child in self.get_children():
            self.remove(child)

        # Logo
        try:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            logo_path = os.path.join(base_dir, "theme", "logo.svg")
            pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(logo_path, 96, 96, True)
            logo = Gtk.Image.new_from_pixbuf(pixbuf)
        except Exception:
            logo = Gtk.Image.new_from_icon_name("system-software-install-symbolic", Gtk.IconSize.DIALOG)
            logo.set_pixel_size(72)

        logo.get_style_context().add_class("welcome-logo")
        self.pack_start(logo, False, False, 0)

        # Title
        self.title_label = Gtk.Label()
        self.title_label.set_markup(
            f'<span font_weight="bold" size="28000" foreground="#fafafa">{i18n._("welcome_title")}</span>'
        )
        self.title_label.get_style_context().add_class("welcome-title")
        self.pack_start(self.title_label, False, False, 0)

        # Subtitle
        self.subtitle_label = Gtk.Label(label=i18n._("welcome_subtitle"))
        self.subtitle_label.set_justify(Gtk.Justification.CENTER)
        self.subtitle_label.set_line_wrap(True)
        self.subtitle_label.get_style_context().add_class("welcome-subtitle")
        self.pack_start(self.subtitle_label, False, False, 10)

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
            ("computer-symbolic", i18n._("feature_desktop_title"), i18n._("feature_desktop_desc")),
            ("applications-system-symbolic", i18n._("feature_minimal_title"), i18n._("feature_minimal_desc")),
        ]
        for icon_name, title_text, desc in features:
            card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
            card.get_style_context().add_class("card")
            card.set_size_request(160, -1)

            img = Gtk.Image.new_from_icon_name(icon_name, Gtk.IconSize.DIALOG)
            img.set_pixel_size(32)
            img.set_margin_bottom(8)
            card.pack_start(img, False, False, 4)

            t = Gtk.Label()
            t.set_markup(f'<span font_weight="bold" foreground="#fafafa">{title_text}</span>')
            card.pack_start(t, False, False, 2)

            d = Gtk.Label(label=desc)
            d.get_style_context().add_class("info-text")
            card.pack_start(d, False, False, 2)

            features_box.pack_start(card, False, False, 0)

        # Language selection
        lang_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        lang_box.set_halign(Gtk.Align.CENTER)
        lang_box.set_margin_top(20)

        self.lang_label = Gtk.Label(label=i18n._("system_language"))
        self.lang_label.get_style_context().add_class("field-label")
        lang_box.pack_start(self.lang_label, False, False, 0)

        self.lang_combo = Gtk.ComboBoxText()
        self.lang_combo.append("tr_TR.UTF-8", "Türkçe")
        self.lang_combo.append("en_US.UTF-8", "English")
        
        # Match current lang from config if possible
        current_lang = self.window.config.get("language", "tr_TR.UTF-8")
        self.lang_combo.set_active_id(current_lang)
        
        self.lang_combo.connect("changed", self._on_lang_changed)
        lang_box.pack_start(self.lang_combo, False, False, 0)

        self.pack_start(lang_box, False, False, 0)
        self.show_all()

    def _on_lang_changed(self, combo):
        lang_id = combo.get_active_id()
        if lang_id:
            self.window.config["language"] = lang_id
            i18n.init(lang_id)
            self.window.refresh_translations()

    def collect(self):
        self.window.config["language"] = self.lang_combo.get_active_id() or "tr_TR.UTF-8"

    def refresh(self):
        # Block signal while updating combo manually if needed
        # self.lang_combo.handler_block(...) 
        self._build_ui()
