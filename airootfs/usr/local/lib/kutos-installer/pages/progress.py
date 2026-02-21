"""Installation Progress Page — KutOS Installer"""

import threading

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib, Pango

from backend.installer import run_installation


class ProgressPage(Gtk.Box):
    def __init__(self, window):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.window = window
        self.set_margin_start(40)
        self.set_margin_end(40)
        self.set_margin_top(30)
        self.install_started = False

        # Title
        self.title = Gtk.Label(xalign=0)
        self.title.set_markup(
            '<span font_weight="bold" size="20000" foreground="#e0e0ff">'
            "Kurulum Yapılıyor..."
            "</span>"
        )
        self.pack_start(self.title, False, False, 0)

        # Phase indicator
        self.phase_label = Gtk.Label(label="Hazırlanıyor...", xalign=0)
        self.phase_label.get_style_context().add_class("progress-phase")
        self.pack_start(self.phase_label, False, False, 0)

        # Progress bar
        self.progress = Gtk.ProgressBar()
        self.progress.set_show_text(True)
        self.pack_start(self.progress, False, False, 8)

        # Detail label
        self.detail_label = Gtk.Label(label="", xalign=0)
        self.detail_label.get_style_context().add_class("progress-detail")
        self.pack_start(self.detail_label, False, False, 0)

        # Log view
        log_label = Gtk.Label(label="Kurulum Günlüğü", xalign=0)
        log_label.get_style_context().add_class("field-label")
        log_label.set_margin_top(12)
        self.pack_start(log_label, False, False, 0)

        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        self.pack_start(scroll, True, True, 0)

        self.log_view = Gtk.TextView()
        self.log_view.set_editable(False)
        self.log_view.set_cursor_visible(False)
        self.log_view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self.log_view.modify_font(Pango.FontDescription("DejaVu Sans Mono 10"))
        self.log_buffer = self.log_view.get_buffer()
        scroll.add(self.log_view)

        # Bottom status area (hidden until complete)
        self.complete_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        self.complete_box.set_halign(Gtk.Align.CENTER)
        self.complete_box.set_margin_top(16)
        self.complete_box.set_no_show_all(True)
        self.pack_start(self.complete_box, False, False, 0)

        self.reboot_btn = Gtk.Button(label="Yeniden Başlat")
        self.reboot_btn.get_style_context().add_class("btn-primary")
        self.reboot_btn.connect("clicked", self._on_reboot)
        self.complete_box.pack_start(self.reboot_btn, False, False, 0)

        self.close_btn = Gtk.Button(label="Kapat")
        self.close_btn.get_style_context().add_class("btn-secondary")
        self.close_btn.connect("clicked", lambda _: self.window.destroy())
        self.complete_box.pack_start(self.close_btn, False, False, 0)

    def on_enter(self):
        if not self.install_started:
            self.install_started = True
            self._start_install()

    def _start_install(self):
        thread = threading.Thread(
            target=run_installation,
            args=(self.window.config, self._update_progress, self._log, self._on_done),
            daemon=True,
        )
        thread.start()

    def _update_progress(self, fraction, phase, detail):
        GLib.idle_add(self._do_update_progress, fraction, phase, detail)

    def _do_update_progress(self, fraction, phase, detail):
        self.progress.set_fraction(fraction)
        self.progress.set_text(f"{int(fraction * 100)}%")
        if phase:
            self.phase_label.set_text(phase)
        if detail:
            self.detail_label.set_text(detail)

    def _log(self, message):
        GLib.idle_add(self._do_log, message)

    def _do_log(self, message):
        end_iter = self.log_buffer.get_end_iter()
        self.log_buffer.insert(end_iter, message + "\n")
        # Auto-scroll to bottom
        mark = self.log_buffer.create_mark(None, self.log_buffer.get_end_iter(), False)
        self.log_view.scroll_to_mark(mark, 0, False, 0, 0)

    def _on_done(self, success, error_msg):
        GLib.idle_add(self._do_done, success, error_msg)

    def _do_done(self, success, error_msg):
        if success:
            self.title.set_markup(
                '<span font_weight="bold" size="20000" foreground="#48bb78">'
                "Kurulum Başarıyla Tamamlandı!"
                "</span>"
            )
            self.phase_label.set_text("Sistem başarıyla kuruldu.")
            self.progress.set_fraction(1.0)
            self.progress.set_text("100%")
            self.detail_label.set_text(
                "USB'yi çıkarıp sistemi yeniden başlatabilirsiniz."
            )
        else:
            self.title.set_markup(
                '<span font_weight="bold" size="20000" foreground="#fc8181">'
                "Kurulum Başarısız!"
                "</span>"
            )
            self.phase_label.set_text("Bir hata oluştu.")
            self.detail_label.set_text(error_msg or "Bilinmeyen hata")

        self.complete_box.show_all()

    def _on_reboot(self, _btn):
        import subprocess

        subprocess.run(["reboot"])
