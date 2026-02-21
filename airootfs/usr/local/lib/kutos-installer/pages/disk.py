"""Disk Selection Page — KutOS Installer"""

import json
import subprocess
import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib
import i18n


class DiskPage(Gtk.Box):
    def __init__(self, window):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        self.window = window
        self.set_margin_start(40)
        self.set_margin_end(40)
        self.set_margin_top(30)
        
        self.partition_mode = "auto"
        self.selected_disk = None

        self._build_ui()

    def _build_ui(self):
        # Clear existing
        for child in self.get_children():
            self.remove(child)

        # Title
        title = Gtk.Label(xalign=0)
        title.set_markup(f'<span font_weight="bold" size="20000" foreground="#fafafa">{i18n._("disk_title")}</span>')
        self.pack_start(title, False, False, 0)

        desc = Gtk.Label(label=i18n._("disk_desc"), xalign=0)
        desc.get_style_context().add_class("page-description")
        self.pack_start(desc, False, False, 0)

        # Mode Selection
        mode_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        self.pack_start(mode_box, False, False, 0)

        # Auto card
        self.auto_card_ev = self._create_mode_card(
            "view-refresh-symbolic",
            i18n._("disk_mode_auto_title"),
            i18n._("disk_mode_auto_desc"),
            self.partition_mode == "auto",
        )
        self.auto_card_ev.connect("button-press-event", self._on_auto_click)
        mode_box.pack_start(self.auto_card_ev, True, True, 0)

        # Manual card
        self.manual_card_ev = self._create_mode_card(
            "preferences-system-symbolic",
            i18n._("disk_mode_manual_title"),
            i18n._("disk_mode_manual_desc"),
            self.partition_mode == "manual",
        )
        self.manual_card_ev.connect("button-press-event", self._on_manual_click)
        mode_box.pack_start(self.manual_card_ev, True, True, 0)

        # Separator
        sep = Gtk.Separator()
        sep.set_margin_top(8)
        sep.set_margin_bottom(8)
        self.pack_start(sep, False, False, 0)

        # Disk list
        disk_label = Gtk.Label(label=i18n._("disk_select_label"), xalign=0)
        disk_label.get_style_context().add_class("field-label")
        self.pack_start(disk_label, False, False, 0)

        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.set_min_content_height(150)
        self.pack_start(scroll, True, True, 0)

        self.disk_list_box = Gtk.ListBox()
        self.disk_list_box.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.disk_list_box.connect("row-selected", self._on_disk_selected)
        scroll.add(self.disk_list_box)

        # Manual partitioned frame
        self.manual_frame = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.manual_frame.set_no_show_all(True)
        self.pack_start(self.manual_frame, False, False, 0)
        
        # ... (Manual entries logic remains similar but with translations)
        for label_key, placeholder, attr in [
            ("Root (/) Bölümü:", "/dev/sdaX", "root_entry"),
            ("EFI Bölümü:", "/dev/sdaY", "efi_entry"),
            ("Swap Bölümü:", "/dev/sdaZ", "swap_entry")
        ]:
            box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            lbl = Gtk.Label(label=label_key, xalign=0)
            lbl.get_style_context().add_class("field-label")
            lbl.set_size_request(140, -1)
            box.pack_start(lbl, False, False, 0)
            entry = Gtk.Entry()
            entry.set_placeholder_text(placeholder)
            box.pack_start(entry, True, True, 0)
            setattr(self, attr, entry)
            self.manual_frame.pack_start(box, False, False, 0)

        # Warning
        self.warning = Gtk.Label(xalign=0)
        self.warning.set_markup(f'<span foreground="#ef4444" size="small">WARNING: Auto mode wipes the ENTIRE disk!</span>')
        self.pack_start(self.warning, False, False, 0)

        if self.partition_mode == "manual":
            self.manual_frame.show_all()
            self.warning.hide()
        else:
            self.manual_frame.hide()
            self.warning.show()

        self.show_all()

    def _create_mode_card(self, icon, title, desc, is_selected):
        event = Gtk.EventBox()
        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        card.get_style_context().add_class("card")
        if is_selected:
            card.get_style_context().add_class("selected")
        card.set_size_request(-1, 110)

        img = Gtk.Image.new_from_icon_name(icon, Gtk.IconSize.DIALOG)
        img.set_pixel_size(32)
        card.pack_start(img, False, False, 4)

        t = Gtk.Label()
        t.set_markup(f'<span font_weight="bold" foreground="#fafafa">{title}</span>')
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
        self._build_ui()
        self._refresh_disks()

    def _on_manual_click(self, *_args):
        self.partition_mode = "manual"
        self._build_ui()
        self._refresh_disks()

    def on_enter(self):
        self._refresh_disks()

    def _refresh_disks(self):
        for child in self.disk_list_box.get_children():
            self.disk_list_box.remove(child)
        try:
            res = subprocess.run(["lsblk", "-J", "-d", "-o", "NAME,SIZE,MODEL,TYPE,TRAN"], capture_output=True, text=True)
            data = json.loads(res.stdout)
            for dev in data.get("blockdevices", []):
                if dev.get("type") != "disk": continue
                row = Gtk.ListBoxRow()
                box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)
                box.get_style_context().add_class("card")
                box.set_margin_start(4)
                box.set_margin_end(4)
                
                icon = Gtk.Image.new_from_icon_name("drive-harddisk-symbolic", Gtk.IconSize.DND)
                box.pack_start(icon, False, False, 8)
                
                info = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
                dev_lbl = Gtk.Label(xalign=0)
                dev_lbl.set_markup(f'<span font_weight="bold" foreground="#fafafa">/dev/{dev["name"]}</span> <span foreground="#3b82f6">{dev["size"]}</span>')
                info.pack_start(dev_lbl, False, False, 0)
                
                model = dev.get("model", "Unknown").strip() or "Unknown"
                model_lbl = Gtk.Label(label=f"{model} ({dev.get('tran','').upper()})", xalign=0)
                model_lbl.get_style_context().add_class("info-text")
                info.pack_start(model_lbl, False, False, 0)
                
                box.pack_start(info, True, True, 0)
                row.add(box)
                row._disk_name = f"/dev/{dev['name']}"
                if self.selected_disk == row._disk_name:
                    self.disk_list_box.select_row(row)
                self.disk_list_box.add(row)
            self.disk_list_box.show_all()
        except Exception as e:
            print(f"Disk error: {e}")

    def _on_disk_selected(self, _listbox, row):
        if row and hasattr(row, "_disk_name"):
            self.selected_disk = row._disk_name

    def validate(self):
        if self.partition_mode == "auto" and not self.selected_disk:
            return False
        return True

    def collect(self):
        self.window.config["partition_mode"] = self.partition_mode
        self.window.config["disk"] = self.selected_disk
        if self.partition_mode == "manual":
            self.window.config["root_partition"] = self.root_entry.get_text().strip()
            self.window.config["efi_partition"] = self.efi_entry.get_text().strip()
            self.window.config["swap_partition"] = self.swap_entry.get_text().strip()

    def refresh(self):
        self._build_ui()
        self._refresh_disks()
