import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib, Gdk
import subprocess
import threading

class NetworkSetupPage(Gtk.Box):
    def __init__(self, on_connected_cb):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        self.on_connected_cb = on_connected_cb
        self.set_valign(Gtk.Align.CENTER)
        self.set_halign(Gtk.Align.CENTER)
        self.set_margin_top(50)
        
        self._build_ui()
        self._start_scan()

    def _build_ui(self):
        title = Gtk.Label(label="Internet Setup")
        title.get_style_context().add_class("title")
        self.pack_start(title, False, False, 0)

        subtitle = Gtk.Label(label="Please connect to the internet to download the latest installer.")
        subtitle.get_style_context().add_class("subtitle")
        self.pack_start(subtitle, False, False, 0)

        # Scrolled window for Wi-Fi list
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.Policy.NEVER, Gtk.Policy.AUTOMATIC)
        scrolled.set_min_content_height(200)
        scrolled.set_min_content_width(400)
        
        self.listbox = Gtk.ListBox()
        self.listbox.set_selection_mode(Gtk.SelectionMode.NONE)
        scrolled.add(self.listbox)
        self.pack_start(scrolled, True, True, 0)

        # Connect button
        self.connect_btn = Gtk.Button(label="Connect")
        self.connect_btn.get_style_context().add_class("suggested-action")
        self.connect_btn.set_sensitive(False)
        self.connect_btn.connect("clicked", self._on_connect_clicked)
        self.pack_start(self.connect_btn, False, False, 0)

        self.listbox.connect("row-activated", self._on_row_activated)

    def _start_scan(self):
        threading.Thread(target=self._scan_wifi, daemon=True).start()

    def _scan_wifi(self):
        try:
            # Simple nmcli scan
            subprocess.run(["nmcli", "dev", "wifi", "rescan"], check=False)
            output = subprocess.check_output(
                ["nmcli", "-t", "-f", "SSID,BARS,SECURITY", "dev", "wifi"],
                text=True
            )
            
            networks = []
            for line in output.strip().split("\n"):
                if line.strip():
                    parts = line.split(":")
                    if len(parts) >= 2 and parts[0]:
                        networks.append({
                            "ssid": parts[0],
                            "signal": parts[1],
                            "security": parts[2] if len(parts) > 2 else ""
                        })

            GLib.idle_add(self._update_list, networks)
        except Exception as e:
            print(f"Scan error: {e}")

    def _update_list(self, networks):
        for child in self.listbox.get_children():
            self.listbox.remove(child)

        for net in networks:
            row = Gtk.ListBoxRow()
            box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
            box.get_style_context().add_class("network-item")
            
            lbl = Gtk.Label(label=net["ssid"], xalign=0)
            box.pack_start(lbl, True, True, 0)
            
            sig = Gtk.Label(label=net["signal"])
            box.pack_end(sig, False, False, 0)
            
            row.add(box)
            row.ssid = net["ssid"]
            row.security = net["security"]
            self.listbox.add(row)
        
        self.listbox.show_all()

    def _on_row_activated(self, listbox, row):
        self.selected_ssid = row.ssid
        self.selected_security = row.security
        self.connect_btn.set_sensitive(True)

    def _on_connect_clicked(self, btn):
        if not self.selected_ssid:
            return

        if "WPA" in self.selected_security or "WEP" in self.selected_security:
            self._show_password_dialog()
        else:
            self._connect_to_wifi(self.selected_ssid)

    def _show_password_dialog(self):
        dialog = Gtk.MessageDialog(
            transient_for=self.get_toplevel(),
            modal=True,
            message_type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.OK_CANCEL,
            text=f"Password for {self.selected_ssid}"
        )
        
        entry = Gtk.Entry()
        entry.set_visibility(False)
        entry.set_invisible_char("*")
        dialog.get_content_area().add(entry)
        dialog.show_all()
        
        response = dialog.run()
        password = entry.get_text()
        dialog.destroy()
        
        if response == Gtk.ResponseType.OK:
            self._connect_to_wifi(self.selected_ssid, password)

    def _connect_to_wifi(self, ssid, password=None):
        def task():
            try:
                cmd = ["nmcli", "dev", "wifi", "connect", ssid]
                if password:
                    cmd += ["password", password]
                
                subprocess.run(cmd, check=True)
                GLib.idle_add(self.on_connected_cb)
            except Exception as e:
                print(f"Connection failed: {e}")
        
        threading.Thread(target=task, daemon=True).start()
