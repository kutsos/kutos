"""Network Page — KutOS Installer"""

import gi
import threading
import subprocess
import os

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib
import i18n


class NetworkPage(Gtk.Box):
    def __init__(self, window):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        self.window = window
        self.set_margin_start(60)
        self.set_margin_end(60)
        self.set_valign(Gtk.Align.CENTER)

        self._build_ui()

    def _build_ui(self):
        # Clear existing children
        for child in self.get_children():
            self.remove(child)

        # Title Section
        title_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        self.pack_start(title_box, False, False, 0)

        self.title_label = Gtk.Label()
        self.title_label.set_markup(f'<span font_weight="bold" size="24000" foreground="#fafafa">{i18n._("network_title")}</span>')
        self.title_label.set_halign(Gtk.Align.START)
        title_box.pack_start(self.title_label, False, False, 0)

        self.desc_label = Gtk.Label(label=i18n._("network_desc"))
        self.desc_label.set_halign(Gtk.Align.START)
        self.desc_label.get_style_context().add_class("page-description")
        title_box.pack_start(self.desc_label, False, False, 0)

        # Status & Connection
        main_content = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=30)
        self.pack_start(main_content, True, True, 0)

        # Left: Status & Password
        left_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        main_content.pack_start(left_box, True, True, 0)

        status_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        status_card.get_style_context().add_class("summary-section")
        left_box.pack_start(status_card, False, False, 0)

        status_header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        status_card.pack_start(status_header, False, False, 0)
        
        self.status_title = Gtk.Label(label=i18n._("net_status_label"))
        self.status_title.get_style_context().add_class("summary-label")
        status_header.pack_start(self.status_title, False, False, 0)

        self.status_value = Gtk.Label(label="...")
        self.status_value.get_style_context().add_class("summary-value")
        status_header.pack_start(self.status_value, False, False, 0)

        # Wi-Fi Password Entry
        self.pass_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.pass_box.set_visible(False)
        left_box.pack_start(self.pass_box, False, False, 0)

        self.pass_label = Gtk.Label(label=i18n._("wifi_password_label"))
        self.pass_label.set_halign(Gtk.Align.START)
        self.pass_label.get_style_context().add_class("field-label")
        self.pass_box.pack_start(self.pass_label, False, False, 0)

        self.pass_entry = Gtk.Entry()
        self.pass_entry.set_visibility(False)
        self.pass_entry.set_invisible_char("*")
        self.pass_box.pack_start(self.pass_entry, False, False, 0)

        self.connect_btn = Gtk.Button(label=i18n._("wifi_connect_btn"))
        self.connect_btn.get_style_context().add_class("btn-primary")
        self.connect_btn.connect("clicked", self._on_connect_clicked)
        self.pass_box.pack_start(self.connect_btn, False, False, 10)

        # Right: Wi-Fi List
        self.right_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.right_box.set_size_request(300, -1)
        main_content.pack_start(self.right_box, False, False, 0)

        wifi_header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.right_box.pack_start(wifi_header, False, False, 0)

        self.wifi_list_label = Gtk.Label(label=i18n._("wifi_list_label"))
        self.wifi_list_label.get_style_context().add_class("field-label")
        wifi_header.pack_start(self.wifi_list_label, True, True, 0)

        self.refresh_btn = Gtk.Button()
        self.refresh_btn.set_image(Gtk.Image.new_from_icon_name("view-refresh-symbolic", Gtk.IconSize.BUTTON))
        self.refresh_btn.get_style_context().add_class("btn-secondary")
        self.refresh_btn.connect("clicked", lambda _: self.scan_wifi())
        wifi_header.pack_end(self.refresh_btn, False, False, 0)

        # Scrolled List
        self.scroll = Gtk.ScrolledWindow()
        self.scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.scroll.get_style_context().add_class("card")
        self.right_box.pack_start(self.scroll, True, True, 0)

        self.listbox = Gtk.ListBox()
        self.listbox.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.listbox.connect("row-selected", self._on_wifi_selected)
        self.scroll.add(self.listbox)
        
        self.show_all()

    def on_enter(self):
        self.check_connectivity()
        self.scan_wifi()

    def check_connectivity(self):
        def _check():
            try:
                # Check for specific internet access via ping
                ping = subprocess.run(["ping", "-c", "1", "-W", "2", "8.8.8.8"], capture_output=True)
                GLib.idle_add(self._update_status, ping.returncode == 0)
            except Exception:
                GLib.idle_add(self._update_status, False)

        threading.Thread(target=_check, daemon=True).start()

    def _update_status(self, connected):
        if connected:
            self.status_value.set_text(i18n._("net_status_connected"))
            self.status_value.get_style_context().add_class("success-text")
            self.status_value.get_style_context().remove_class("error-text")
            self.window.btn_next.set_sensitive(True)
        else:
            self.status_value.set_text(i18n._("net_status_disconnected"))
            self.status_value.get_style_context().add_class("error-text")
            self.status_value.get_style_context().remove_class("success-text")
            # We don't block Next for testing, but we should notify.

    def scan_wifi(self):
        def _scan():
            try:
                # nmcli -t -f SSID,SIGNAL,SECURITY dev wifi list
                res = subprocess.run(["nmcli", "-t", "-f", "SSID,SIGNAL,SECURITY,ACTIVE", "dev", "wifi", "list"], 
                                   capture_output=True, text=True)
                lines = res.stdout.strip().split("\n")
                networks = []
                for line in lines:
                    if not line: continue
                    parts = line.split(":")
                    if len(parts) >= 3:
                        networks.append({
                            "ssid": parts[0],
                            "signal": parts[1],
                            "security": parts[2],
                            "active": parts[3] == "yes"
                        })
                GLib.idle_add(self._populate_wifi_list, networks)
            except Exception as e:
                print(f"Scan error: {e}")

        threading.Thread(target=_scan, daemon=True).start()

    def _populate_wifi_list(self, networks):
        for child in self.listbox.get_children():
            self.listbox.remove(child)

        for net in networks:
            if not net["ssid"]: continue
            row = Gtk.ListBoxRow()
            box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            box.set_margin_start(10)
            box.set_margin_end(10)
            box.set_margin_top(8)
            box.set_margin_bottom(8)
            
            icon_name = "network-wireless-signal-excellent-symbolic" if int(net["signal"]) > 75 else \
                        "network-wireless-signal-good-symbolic" if int(net["signal"]) > 50 else \
                        "network-wireless-signal-ok-symbolic"
            
            icon = Gtk.Image.new_from_icon_name(icon_name, Gtk.IconSize.MENU)
            box.pack_start(icon, False, False, 0)
            
            lbl = Gtk.Label(label=net["ssid"])
            lbl.set_halign(Gtk.Align.START)
            box.pack_start(lbl, True, True, 0)
            
            if net["security"]:
                sec_icon = Gtk.Image.new_from_icon_name("network-wireless-encrypted-symbolic", Gtk.IconSize.MENU)
                box.pack_start(sec_icon, False, False, 0)
            
            if net["active"]:
                active_icon = Gtk.Image.new_from_icon_name("emblem-ok-symbolic", Gtk.IconSize.MENU)
                box.pack_start(active_icon, False, False, 0)

            row.add(box)
            row.ssid = net["ssid"]
            row.security = net["security"]
            self.listbox.add(row)
        
        self.listbox.show_all()

    def _on_wifi_selected(self, listbox, row):
        if row:
            self.pass_box.set_visible(bool(row.security))
            self.selected_ssid = row.ssid
            self.show_all()

    def _on_connect_clicked(self, _btn):
        ssid = self.selected_ssid
        password = self.pass_entry.get_text()
        
        self.connect_btn.set_sensitive(False)
        self.status_value.set_text("Connecting...")
        
        def _connect():
            try:
                cmd = ["nmcli", "dev", "wifi", "connect", ssid]
                if password:
                    cmd.extend(["password", password])
                
                res = subprocess.run(cmd, capture_output=True, text=True)
                GLib.idle_add(self._on_connection_result, res.returncode == 0)
            except Exception:
                GLib.idle_add(self._on_connection_result, False)

        threading.Thread(target=_connect, daemon=True).start()

    def _on_connection_result(self, success):
        self.connect_btn.set_sensitive(True)
        if success:
            self.check_connectivity()
            self.scan_wifi()
        else:
            self.status_value.set_text("Connection Failed")
            self.status_value.get_style_context().add_class("error-text")

    def refresh(self):
        self._build_ui()
        self.check_connectivity()
        self.scan_wifi()
