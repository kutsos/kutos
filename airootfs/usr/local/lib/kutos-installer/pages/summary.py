"""Summary Page — KutOS Installer"""

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk


DE_NAMES = {"xfce": "XFCE", "hyprland": "Hyprland", "gnome": "GNOME"}


class SummaryPage(Gtk.Box):
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
            "Kurulum Özeti"
            "</span>"
        )
        self.pack_start(title, False, False, 0)

        desc = Gtk.Label(
            label="Aşağıdaki ayarlar sisteminize uygulanacak. "
            "Onaylamadan önce lütfen kontrol edin.",
            xalign=0,
        )
        desc.set_line_wrap(True)
        desc.get_style_context().add_class("page-description")
        self.pack_start(desc, False, False, 0)

        # Summary sections container
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.pack_start(scroll, True, True, 0)

        self.summary_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        scroll.add(self.summary_box)

        # Warning
        warning = Gtk.Label(xalign=0)
        warning.set_markup(
            '<span foreground="#ecc94b">'
            "UYARI: Kurulumu başlattıktan sonra geri alınamaz!\n"
            "Hedef diskteki veriler silinecektir."
            "</span>"
        )
        warning.set_margin_top(12)
        self.pack_start(warning, False, False, 0)

    def on_enter(self):
        """Refresh summary when page becomes visible."""
        for child in self.summary_box.get_children():
            self.summary_box.remove(child)

        config = self.window.config

        sections = [
            ("computer-symbolic", "Masaüstü Ortamı", DE_NAMES.get(config.get("desktop", "xfce"), "?")),
            ("drive-harddisk-symbolic", "Hedef Disk", config.get("disk", "Seçilmedi")),
            ("folder-symbolic", "Bölümlendirme", "Otomatik" if config.get("partition_mode") == "auto" else "Manuel"),
            ("avatar-default-symbolic", "Kullanıcı", config.get("username", "")),
            ("network-server-symbolic", "Bilgisayar Adı", config.get("hostname", "kutos")),
            ("preferences-desktop-locale-symbolic", "Dil", config.get("language", "tr_TR.UTF-8")),
            ("preferences-system-time-symbolic", "Saat Dilimi", config.get("timezone", "Europe/Istanbul")),
            ("dialog-password-symbolic", "Sudo", "Evet" if config.get("sudo", True) else "Hayır"),
        ]

        for icon_name, label, value in sections:
            self._add_summary_row(icon_name, label, value)

        # Extra packages
        extras = config.get("extra_packages", [])
        if extras:
            pkg_str = ", ".join(extras[:10])
            if len(extras) > 10:
                pkg_str += f" (+{len(extras) - 10} daha)"
            self._add_summary_row("package-x-generic-symbolic", f"Ek Paketler ({len(extras)})", pkg_str)
        else:
            self._add_summary_row("package-x-generic-symbolic", "Ek Paketler", "Hiçbiri seçilmedi")

        self.summary_box.show_all()

    def _add_summary_row(self, icon_name, label, value):
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        row.get_style_context().add_class("summary-section")

        img = Gtk.Image.new_from_icon_name(icon_name, Gtk.IconSize.BUTTON)
        row.pack_start(img, False, False, 0)

        lbl = Gtk.Label(label=label, xalign=0)
        lbl.get_style_context().add_class("summary-label")
        lbl.set_size_request(180, -1)
        row.pack_start(lbl, False, False, 0)

        val = Gtk.Label(label=value, xalign=0)
        val.get_style_context().add_class("summary-value")
        val.set_line_wrap(True)
        row.pack_start(val, True, True, 0)

        self.summary_box.pack_start(row, False, False, 0)
