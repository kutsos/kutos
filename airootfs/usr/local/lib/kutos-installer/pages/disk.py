"""Disk Selection Page — KutOS Installer"""

import json
import subprocess

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib


class DiskPage(Gtk.Box):
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
            "Disk Seçimi"
            "</span>"
        )
        self.pack_start(title, False, False, 0)

        desc = Gtk.Label(
            label="Kurulumun yapılacağı diski ve bölümlendirme yöntemini seçin.",
            xalign=0,
        )
        desc.get_style_context().add_class("page-description")
        self.pack_start(desc, False, False, 0)

        # Partition mode selection
        mode_label = Gtk.Label(label="Bölümlendirme Yöntemi", xalign=0)
        mode_label.get_style_context().add_class("field-label")
        self.pack_start(mode_label, False, False, 0)

        mode_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        self.pack_start(mode_box, False, False, 0)

        # Auto card
        self.auto_card = self._create_mode_card(
            "🔄",
            "Otomatik",
            "Tüm diski kullanarak otomatik bölümlendir.\nEFI + Root + Swap oluşturulur.",
            True,
        )
        self.auto_card.connect("button-press-event", self._on_auto_click)
        mode_box.pack_start(self.auto_card, True, True, 0)

        # Manual card
        self.manual_card = self._create_mode_card(
            "🛠️",
            "Manuel (GParted)",
            "GParted ile disk bölümlerini kendiniz yönetin.\nİleri düzey kullanıcılar için.",
            False,
        )
        self.manual_card.connect("button-press-event", self._on_manual_click)
        mode_box.pack_start(self.manual_card, True, True, 0)

        self.partition_mode = "auto"

        # Separator
        sep = Gtk.Separator()
        sep.set_margin_top(8)
        sep.set_margin_bottom(8)
        self.pack_start(sep, False, False, 0)

        # Disk list
        disk_label = Gtk.Label(label="Hedef Disk", xalign=0)
        disk_label.get_style_context().add_class("field-label")
        self.pack_start(disk_label, False, False, 0)

        # Scrollable disk list
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.set_min_content_height(200)
        self.pack_start(scroll, True, True, 0)

        self.disk_list_box = Gtk.ListBox()
        self.disk_list_box.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.disk_list_box.connect("row-selected", self._on_disk_selected)
        scroll.add(self.disk_list_box)

        # GParted button (hidden initially)
        self.gparted_btn = Gtk.Button(label="🛠️  GParted'i Aç")
        self.gparted_btn.get_style_context().add_class("btn-secondary")
        self.gparted_btn.connect("clicked", self._on_gparted)
        self.gparted_btn.set_halign(Gtk.Align.START)
        self.gparted_btn.set_no_show_all(True)
        self.pack_start(self.gparted_btn, False, False, 0)

        # Manual partition entries (hidden initially)
        self.manual_frame = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.manual_frame.set_no_show_all(True)
        self.pack_start(self.manual_frame, False, False, 0)

        # Root partition
        root_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        root_lbl = Gtk.Label(label="Root (/) Bölümü:", xalign=0)
        root_lbl.get_style_context().add_class("field-label")
        root_lbl.set_size_request(140, -1)
        root_box.pack_start(root_lbl, False, False, 0)
        self.root_entry = Gtk.Entry()
        self.root_entry.set_placeholder_text("/dev/sdaX")
        root_box.pack_start(self.root_entry, True, True, 0)
        self.manual_frame.pack_start(root_box, False, False, 0)

        # EFI partition
        efi_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        efi_lbl = Gtk.Label(label="EFI Bölümü:", xalign=0)
        efi_lbl.get_style_context().add_class("field-label")
        efi_lbl.set_size_request(140, -1)
        efi_box.pack_start(efi_lbl, False, False, 0)
        self.efi_entry = Gtk.Entry()
        self.efi_entry.set_placeholder_text("/dev/sdaY (UEFI için)")
        efi_box.pack_start(self.efi_entry, True, True, 0)
        self.manual_frame.pack_start(efi_box, False, False, 0)

        # Swap partition
        swap_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        swap_lbl = Gtk.Label(label="Swap Bölümü:", xalign=0)
        swap_lbl.get_style_context().add_class("field-label")
        swap_lbl.set_size_request(140, -1)
        swap_box.pack_start(swap_lbl, False, False, 0)
        self.swap_entry = Gtk.Entry()
        self.swap_entry.set_placeholder_text("/dev/sdaZ (opsiyonel)")
        swap_box.pack_start(self.swap_entry, True, True, 0)
        self.manual_frame.pack_start(swap_box, False, False, 0)

        # Warning
        self.warning = Gtk.Label(xalign=0)
        self.warning.set_markup(
            '<span foreground="#ecc94b" size="small">'
            "⚠️  Otomatik mod seçilen diskteki TÜM verileri silecektir!"
            "</span>"
        )
        self.warning.set_margin_top(8)
        self.pack_start(self.warning, False, False, 0)

        self.selected_disk = None

    def _create_mode_card(self, icon, title, desc, is_selected):
        event = Gtk.EventBox()
        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        card.get_style_context().add_class("card")
        if is_selected:
            card.get_style_context().add_class("selected")
        card.set_size_request(-1, 100)

        icon_lbl = Gtk.Label()
        icon_lbl.set_markup(f'<span size="20000">{icon}</span>')
        card.pack_start(icon_lbl, False, False, 4)

        t = Gtk.Label()
        t.set_markup(f'<span font_weight="bold" foreground="#e0e0ff">{title}</span>')
        card.pack_start(t, False, False, 2)

        d = Gtk.Label(label=desc)
        d.set_line_wrap(True)
        d.get_style_context().add_class("info-text")
        d.set_justify(Gtk.Justification.CENTER)
        card.pack_start(d, False, False, 2)

        event.add(card)
        return event

    def _on_auto_click(self, *_args):
        self.partition_mode = "auto"
        self.auto_card.get_child().get_style_context().add_class("selected")
        self.manual_card.get_child().get_style_context().remove_class("selected")
        self.gparted_btn.hide()
        self.manual_frame.hide()
        self.warning.show()

    def _on_manual_click(self, *_args):
        self.partition_mode = "manual"
        self.manual_card.get_child().get_style_context().add_class("selected")
        self.auto_card.get_child().get_style_context().remove_class("selected")
        self.gparted_btn.show()
        self.manual_frame.show_all()
        self.warning.hide()

    def _on_gparted(self, _btn):
        try:
            subprocess.Popen(["gparted"])
        except FileNotFoundError:
            dialog = Gtk.MessageDialog(
                transient_for=self.window,
                message_type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.OK,
                text="GParted bulunamadı!",
            )
            dialog.run()
            dialog.destroy()

    def on_enter(self):
        self._refresh_disks()

    def _refresh_disks(self):
        for child in self.disk_list_box.get_children():
            self.disk_list_box.remove(child)

        try:
            result = subprocess.run(
                ["lsblk", "-J", "-d", "-o", "NAME,SIZE,MODEL,TYPE,TRAN"],
                capture_output=True,
                text=True,
            )
            data = json.loads(result.stdout)
            for dev in data.get("blockdevices", []):
                if dev.get("type") != "disk":
                    continue
                name = dev.get("name", "?")
                size = dev.get("size", "?")
                model = dev.get("model", "Unknown").strip() if dev.get("model") else "Unknown"
                tran = dev.get("tran", "").upper()

                row = Gtk.ListBoxRow()
                box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)
                box.get_style_context().add_class("card")
                box.set_margin_start(4)
                box.set_margin_end(4)
                box.set_margin_top(2)
                box.set_margin_bottom(2)

                icon = Gtk.Label()
                icon.set_markup('<span size="18000">💾</span>')
                box.pack_start(icon, False, False, 8)

                info = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
                dev_lbl = Gtk.Label(xalign=0)
                dev_lbl.set_markup(
                    f'<span font_weight="bold" foreground="#e0e0ff">'
                    f"/dev/{name}</span>"
                    f'  <span foreground="#00b4d8">{size}</span>'
                )
                info.pack_start(dev_lbl, False, False, 0)

                model_lbl = Gtk.Label(label=f"{model} ({tran})", xalign=0)
                model_lbl.get_style_context().add_class("info-text")
                info.pack_start(model_lbl, False, False, 0)

                box.pack_start(info, True, True, 0)
                row.add(box)
                row._disk_name = f"/dev/{name}"
                self.disk_list_box.add(row)

            self.disk_list_box.show_all()

        except Exception as e:
            err = Gtk.Label(label=f"Disk listesi alınamadı: {e}")
            err.get_style_context().add_class("error-text")
            self.disk_list_box.add(err)
            self.disk_list_box.show_all()

    def _on_disk_selected(self, _listbox, row):
        if row and hasattr(row, "_disk_name"):
            self.selected_disk = row._disk_name

    def validate(self):
        if self.partition_mode == "auto":
            if not self.selected_disk:
                self._show_error("Lütfen bir hedef disk seçin.")
                return False
        else:
            root = self.root_entry.get_text().strip()
            if not root:
                self._show_error("Manuel modda root (/) bölümü zorunludur.")
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
        self.window.config["partition_mode"] = self.partition_mode
        if self.partition_mode == "auto":
            self.window.config["disk"] = self.selected_disk
        else:
            self.window.config["disk"] = self.selected_disk
            self.window.config["root_partition"] = self.root_entry.get_text().strip()
            self.window.config["efi_partition"] = self.efi_entry.get_text().strip()
            self.window.config["swap_partition"] = self.swap_entry.get_text().strip()
