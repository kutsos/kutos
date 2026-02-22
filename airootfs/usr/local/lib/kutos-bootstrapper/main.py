import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib, Gdk
import subprocess
import threading
import os
import shutil
import time

from network_setup import NetworkSetupPage

REPO_URL = "https://github.com/kutsos/kutos-installer"
INSTALLER_PATH = "/tmp/kutos-installer"

class BootstrapperWindow(Gtk.Window):
    def __init__(self):
        super().__init__(title="KutOS Installer Bootstrapper")
        self.set_default_size(500, 400)
        self.set_position(Gtk.WindowPosition.CENTER)
        
        # Load CSS
        self._load_css()
        
        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        self.add(self.stack)
        
        self._show_loading("Checking connectivity...")
        self.show_all()
        
        # Start initial check
        GLib.timeout_add(1000, self._initial_check)

    def _load_css(self):
        css_path = os.path.join(os.path.dirname(__file__), "theme/style.css")
        if os.path.exists(css_path):
            provider = Gtk.CssProvider()
            provider.load_from_path(css_path)
            Gtk.StyleContext.add_provider_for_screen(
                Gdk.Screen.get_default(),
                provider,
                Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
            )

    def _show_loading(self, message):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        box.get_style_context().add_class("main-container")
        box.set_valign(Gtk.Align.CENTER)
        
        lbl = Gtk.Label(label=message)
        lbl.get_style_context().add_class("subtitle")
        box.pack_start(lbl, False, False, 0)
        
        self.progress = Gtk.ProgressBar()
        self.progress.pulse()
        box.pack_start(self.progress, False, False, 0)
        
        self._clear_stack()
        self.stack.add_named(box, "loading")
        self.stack.set_visible_child_name("loading")
        box.show_all()
        
        self._pulse_id = GLib.timeout_add(100, self._do_pulse)

    def _do_pulse(self):
        if hasattr(self, "progress"):
            self.progress.pulse()
            return True
        return False

    def _clear_stack(self):
        if hasattr(self, "_pulse_id") and self._pulse_id:
            GLib.source_remove(self._pulse_id)
            self._pulse_id = None
        for child in self.stack.get_children():
            self.stack.remove(child)

    def _initial_check(self):
        if self._is_connected():
            self._start_cloning()
        else:
            self._show_network_setup()
        return False

    def _is_connected(self):
        try:
            # Check if we can reach Google DNS
            subprocess.run(["ping", "-c", "1", "-W", "2", "8.8.8.8"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except:
            return False

    def _show_network_setup(self):
        page = NetworkSetupPage(on_connected_cb=self._start_cloning)
        self._clear_stack()
        self.stack.add_named(page, "network")
        self.stack.set_visible_child_name("network")
        page.show_all()

    def _start_cloning(self):
        self._show_loading("Downloading KutOS Installer...")
        threading.Thread(target=self._clone_repo, daemon=True).start()

    def _clone_repo(self):
        try:
            # Remove existing if any
            if os.path.exists(INSTALLER_PATH):
                shutil.rmtree(INSTALLER_PATH)
            
            # Clone from GitHub
            subprocess.run(["git", "clone", "--depth", "1", REPO_URL, INSTALLER_PATH], check=True)
            
            # PATCHING: Add persistence logic to the downloaded installer
            self._patch_installer()
            
            GLib.idle_add(self._launch_installer)
        except Exception as e:
            GLib.idle_add(self._show_error, f"Download failed: {str(e)}")

    def _patch_installer(self):
        """Injects code into the cloned installer to ensure KutOS Settings persists."""
        try:
            # We look for the main installation engine in the cloned repo
            # Based on common structures, it's either backend/installer.py or backend/config.py
            target_file = os.path.join(INSTALLER_PATH, "backend/installer.py")
            if not os.path.exists(target_file):
                target_file = os.path.join(INSTALLER_PATH, "backend/config.py")
            
            if os.path.exists(target_file):
                with open(target_file, "a") as f:
                    f.write("\n\n# === KutOS Persistence Hook ===\n")
                    f.write("import subprocess, os\ndef _kutos_persist():\n")
                    f.write("    try:\n")
                    f.write("        if os.path.exists('/mnt/usr/local/lib'):\n")
                    f.write("            subprocess.run(['cp', '-r', '/usr/local/lib/kutos-settings', '/mnt/usr/local/lib/'], check=True)\n")
                    f.write("            subprocess.run(['cp', '/usr/share/applications/kutos-settings.desktop', '/mnt/usr/share/applications/'], check=True)\n")
                    f.write("    except: pass\n")
                    f.write("_kutos_persist()\n")
        except Exception as e:
            print(f"Patching failed: {e}")

    def _launch_installer(self):
        # We need to run the cloned installer
        # It's better to launch it as a separate process and exit the bootstrapper
        try:
            subprocess.Popen(["python3", os.path.join(INSTALLER_PATH, "main.py")])
            Gtk.main_quit()
        except Exception as e:
            self._show_error(f"Failed to launch installer: {str(e)}")

    def _show_error(self, message):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        box.get_style_context().add_class("main-container")
        box.set_valign(Gtk.Align.CENTER)
        
        lbl = Gtk.Label(label="Error")
        lbl.get_style_context().add_class("title")
        box.pack_start(lbl, False, False, 0)
        
        msg = Gtk.Label(label=message)
        msg.set_line_wrap(True)
        box.pack_start(msg, False, False, 0)
        
        btn = Gtk.Button(label="Try Again")
        btn.connect("clicked", lambda x: self._initial_check())
        box.pack_start(btn, False, False, 0)
        
        self._clear_stack()
        self.stack.add_named(box, "error")
        self.stack.set_visible_child_name("error")
        box.show_all()

if __name__ == "__main__":
    win = BootstrapperWindow()
    Gtk.main()
