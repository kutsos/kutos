"""Optional Packages Page — KutOS Installer"""

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk


PACKAGE_GROUPS = [
    {
        "name": "İnternet",
        "packages": [
            ("firefox", "Firefox Web Tarayıcı", True),
            ("chromium", "Chromium Tarayıcı", False),
            ("thunderbird", "Thunderbird E-posta", False),
            ("transmission-gtk", "Transmission Torrent", False),
        ],
    },
    {
        "name": "Ofis &amp; Üretkenlik",
        "packages": [
            ("libreoffice-fresh", "LibreOffice Paketi", False),
            ("evince", "PDF Görüntüleyici", True),
            ("file-roller", "Arşiv Yöneticisi", True),
        ],
    },
    {
        "name": "Medya &amp; Grafik",
        "packages": [
            ("vlc", "VLC Medya Oynatıcı", False),
            ("gimp", "GIMP Görüntü Düzenleyici", False),
            ("obs-studio", "OBS Studio", False),
            ("shotwell", "Fotoğraf Yöneticisi", False),
        ],
    },
    {
        "name": "Geliştirme",
        "packages": [
            ("code", "Visual Studio Code (OSS)", False),
            ("docker", "Docker Container Engine", False),
            ("nodejs", "Node.js Runtime", False),
            ("python-pip", "Python pip", True),
            ("go", "Go Programlama Dili", False),
            ("rust", "Rust Programlama Dili", False),
        ],
    },
    {
        "name": "Oyun &amp; Eğlence",
        "packages": [
            ("steam", "Steam Oyun Platformu", False),
            ("lutris", "Lutris Oyun Yöneticisi", False),
            ("wine", "Wine (Windows Uyumluluk)", False),
        ],
    },
    {
        "name": "Sistem Araçları",
        "packages": [
            ("htop", "htop Süreç İzleyici", True),
            ("fastfetch", "Fastfetch Sistem Bilgisi", True),
            ("timeshift", "Timeshift Yedekleme", False),
            ("flatpak", "Flatpak Paket Yöneticisi", False),
            ("bluez", "Bluetooth Desteği", False),
            ("cups", "Yazıcı Desteği (CUPS)", False),
        ],
    },
]


class PackagesPage(Gtk.Box):
    def __init__(self, window):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.window = window
        self.set_margin_start(40)
        self.set_margin_end(40)
        self.set_margin_top(30)

        # Title
        title = Gtk.Label(xalign=0)
        title.set_markup(
            '<span font_weight="bold" size="20000" foreground="#e0e0ff">'
            "Ek Paketler"
            "</span>"
        )
        self.pack_start(title, False, False, 0)

        desc = Gtk.Label(
            label="Kurulmasını istediğiniz opsiyonel paketleri seçin. "
            "İşaretli olanlar önerilir.",
            xalign=0,
        )
        desc.set_line_wrap(True)
        desc.get_style_context().add_class("page-description")
        self.pack_start(desc, False, False, 0)

        # Quick actions
        actions_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.pack_start(actions_box, False, False, 0)

        btn_all = Gtk.Button(label="Tümünü Seç")
        btn_all.get_style_context().add_class("btn-secondary")
        btn_all.connect("clicked", lambda _: self._set_all(True))
        actions_box.pack_start(btn_all, False, False, 0)

        btn_none = Gtk.Button(label="Hiçbirini Seçme")
        btn_none.get_style_context().add_class("btn-secondary")
        btn_none.connect("clicked", lambda _: self._set_all(False))
        actions_box.pack_start(btn_none, False, False, 0)

        btn_rec = Gtk.Button(label="Önerilenleri Seç")
        btn_rec.get_style_context().add_class("btn-secondary")
        btn_rec.connect("clicked", lambda _: self._set_recommended())
        actions_box.pack_start(btn_rec, False, False, 0)

        # Scrollable content
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.pack_start(scroll, True, True, 0)

        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        scroll.add(content)

        self.checkboxes = {}  # {pkg_name: (checkbutton, is_recommended)}

        for group in PACKAGE_GROUPS:
            group_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
            group_box.get_style_context().add_class("card")
            content.pack_start(group_box, False, False, 0)

            group_label = Gtk.Label(xalign=0)
            group_label.set_markup(
                f'<span font_weight="bold" foreground="#e0e0ff">'
                f'{group["name"]}</span>'
            )
            group_box.pack_start(group_label, False, False, 4)

            for pkg_name, pkg_desc, recommended in group["packages"]:
                cb = Gtk.CheckButton()
                cb.set_active(recommended)

                label_text = f"  {pkg_name}"
                if recommended:
                    label_text += "  ★"
                cb.set_label(label_text)
                cb.set_tooltip_text(pkg_desc)

                group_box.pack_start(cb, False, False, 2)
                self.checkboxes[pkg_name] = (cb, recommended)

    def _set_all(self, state):
        for cb, _ in self.checkboxes.values():
            cb.set_active(state)

    def _set_recommended(self):
        for cb, recommended in self.checkboxes.values():
            cb.set_active(recommended)

    def collect(self):
        selected = [
            pkg for pkg, (cb, _) in self.checkboxes.items() if cb.get_active()
        ]
        self.window.config["extra_packages"] = selected
