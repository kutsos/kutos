"""System Update page — runs pacman/yay/paru with live output."""

import threading

import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, GLib, Pango

from utils.updater import run_system_update


class SystemUpdatePage(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.set_margin_top(40)
        self.set_margin_bottom(40)
        self.set_margin_start(40)
        self.set_margin_end(40)

        # Title
        title = Gtk.Label(label="System Update")
        title.add_css_class("page-title")
        title.set_halign(Gtk.Align.START)
        self.append(title)

        subtitle = Gtk.Label(
            label="Update your system packages using all available package managers."
        )
        subtitle.add_css_class("page-subtitle")
        subtitle.set_halign(Gtk.Align.START)
        subtitle.set_margin_bottom(20)
        self.append(subtitle)

        # Update button
        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        btn_box.set_margin_bottom(20)

        self.update_btn = Gtk.Button(label="Update System")
        self.update_btn.add_css_class("suggested-action")
        self.update_btn.add_css_class("update-btn")
        self.update_btn.connect("clicked", self._on_update_clicked)
        btn_box.append(self.update_btn)

        self.spinner = Gtk.Spinner()
        btn_box.append(self.spinner)

        self.append(btn_box)

        # Scrollable output area
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        scrolled.set_hexpand(True)
        scrolled.set_min_content_height(300)
        scrolled.add_css_class("output-scroll")

        self.textview = Gtk.TextView()
        self.textview.set_editable(False)
        self.textview.set_cursor_visible(False)
        self.textview.set_monospace(True)
        self.textview.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self.textview.set_top_margin(12)
        self.textview.set_bottom_margin(12)
        self.textview.set_left_margin(12)
        self.textview.set_right_margin(12)
        self.textview.add_css_class("terminal-output")

        self.text_buffer = self.textview.get_buffer()

        scrolled.set_child(self.textview)
        self.append(scrolled)

        self._is_running = False

    def _on_update_clicked(self, _button):
        if self._is_running:
            return

        self._is_running = True
        self.update_btn.set_sensitive(False)
        self.spinner.start()
        self.text_buffer.set_text("")

        threading.Thread(target=self._run_update, daemon=True).start()

    def _run_update(self):
        def on_output(line):
            GLib.idle_add(self._append_output, line)

        def on_done(success):
            GLib.idle_add(self._on_update_done, success)

        run_system_update(on_output, on_done)

    def _append_output(self, line):
        end_iter = self.text_buffer.get_end_iter()
        self.text_buffer.insert(end_iter, line)

        # Auto-scroll to bottom
        mark = self.text_buffer.create_mark(None, self.text_buffer.get_end_iter(), False)
        self.textview.scroll_mark_onscreen(mark)
        self.text_buffer.delete_mark(mark)

    def _on_update_done(self, success):
        self.spinner.stop()
        self.update_btn.set_sensitive(True)
        self._is_running = False

        status = "\n✓ Update completed successfully." if success else "\n✗ Update finished with errors."
        self._append_output(status + "\n")
