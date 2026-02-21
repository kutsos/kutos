"""Desktop Environment Selection Page — KutOS Installer"""

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk


DE_OPTIONS = [
    {
        "id": "xfce",
        "name": "XFCE",
        "type": "X11 • Geleneksel",
        "icon": "computer-symbolic",
        "desc": "Hafif, kararlı ve özelleştirilebilir masaüstü.\n"
        "Düşük kaynak tüketimi, eski donanıma uygun.\n"
        "~300MB RAM kullanımı.",
        "packages": "xfce4, xfce4-goodies, lightdm",
        "ram": "~300MB",
    },
    {
        "id": "hyprland",
        "name": "Hyprland",
        "type": "Wayland • Tiling WM",
        "icon": "preferences-system-windows-symbolic",
        "desc": "Modern, animasyonlu Wayland tiling compositor.\n"
        "Yüksek performans, güçlü özelleştirme.\n"
        "Klavye odaklı iş akışı.",
        "packages": "hyprland, waybar, wofi, foot, swaybg",
        "ram": "~200MB",
    },
    {
        "id": "gnome",
        "name": "GNOME",
        "type": "Wayland • Modern DE",
        "icon": "user-desktop-symbolic",
        "desc": "Modern, sade ve kullanıcı dostu masaüstü.\n"
        "Dokunmatik ekran desteği, entegre uygulamalar.\n"
        "Daha yüksek kaynak kullanımı.",
        "packages": "gnome, gnome-tweaks, gdm",
        "ram": "~800MB",
    },
]


class DesktopPage(Gtk.Box):
    def __init__(self, window):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        self.window = window
        self.set_margin_start(40)
        self.set_margin_end(40)
        self.set_margin_top(30)
        self.selected_de = "xfce"

        # Title
        title = Gtk.Label(xalign=0)
        title.set_markup(
            '<span font_weight="bold" size="20000" foreground="#e0e0ff">'
            "Masaüstü Ortamı"
            "</span>"
        )
        self.pack_start(title, False, False, 0)

        desc = Gtk.Label(
            label="Kurulacak masaüstü ortamını seçin. "
            "Her birinin avantaj ve kaynak kullanımı farklıdır.",
            xalign=0,
        )
        desc.set_line_wrap(True)
        desc.get_style_context().add_class("page-description")
        self.pack_start(desc, False, False, 0)

        # DE Cards
        self.cards_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)
        self.pack_start(self.cards_box, True, True, 0)

        self.de_cards = {}
        for de in DE_OPTIONS:
            card = self._create_de_card(de)
            self.cards_box.pack_start(card, True, True, 0)

        # Details panel
        self.details_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.details_box.get_style_context().add_class("summary-section")
        self.details_box.set_margin_top(8)
        self.pack_start(self.details_box, False, False, 0)

        self.detail_title = Gtk.Label(xalign=0)
        self.details_box.pack_start(self.detail_title, False, False, 0)

        self.detail_pkgs = Gtk.Label(xalign=0)
        self.detail_pkgs.set_line_wrap(True)
        self.detail_pkgs.get_style_context().add_class("info-text")
        self.details_box.pack_start(self.detail_pkgs, False, False, 0)

        self.detail_ram = Gtk.Label(xalign=0)
        self.detail_ram.get_style_context().add_class("info-text")
        self.details_box.pack_start(self.detail_ram, False, False, 0)

        # Select XFCE by default
        self._select_de("xfce")

    def _create_de_card(self, de):
        event = Gtk.EventBox()
        event.connect("button-press-event", lambda *_a, d=de["id"]: self._select_de(d))

        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        card.get_style_context().add_class("de-card")
        card.set_halign(Gtk.Align.CENTER)
        card.set_valign(Gtk.Align.CENTER)

        icon = Gtk.Image.new_from_icon_name(de["icon"], Gtk.IconSize.DIALOG)
        icon.set_pixel_size(48)
        card.pack_start(icon, False, False, 4)

        type_lbl = Gtk.Label(label=de["type"])
        type_lbl.get_style_context().add_class("de-card-type")
        card.pack_start(type_lbl, False, False, 0)

        name = Gtk.Label(label=de["name"])
        name.get_style_context().add_class("de-card-name")
        card.pack_start(name, False, False, 0)

        desc_lbl = Gtk.Label(label=de["desc"])
        desc_lbl.set_line_wrap(True)
        desc_lbl.set_justify(Gtk.Justification.CENTER)
        desc_lbl.get_style_context().add_class("de-card-desc")
        desc_lbl.set_max_width_chars(25)
        card.pack_start(desc_lbl, False, False, 4)

        event.add(card)
        self.de_cards[de["id"]] = card
        return event

    def _select_de(self, de_id):
        self.selected_de = de_id
        for did, card in self.de_cards.items():
            ctx = card.get_style_context()
            if did == de_id:
                ctx.add_class("selected")
            else:
                ctx.remove_class("selected")
        self._update_details(de_id)

    def _update_details(self, de_id):
        de = next(d for d in DE_OPTIONS if d["id"] == de_id)
        self.detail_title.set_markup(
            f'<span font_weight="bold" foreground="#e0e0ff">'
            f"Seçili: {de['name']}</span>"
        )
        self.detail_pkgs.set_markup(
            f'<span foreground="#8888aa">Paketler: {de["packages"]}</span>'
        )
        self.detail_ram.set_markup(
            f'<span foreground="#8888aa">Tahmini RAM: {de["ram"]}</span>'
        )

    def collect(self):
        self.window.config["desktop"] = self.selected_de
