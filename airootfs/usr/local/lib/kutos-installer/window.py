"""KutOS Installer — Main Window with Wizard Navigation"""

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib

from pages.welcome import WelcomePage
from pages.disk import DiskPage
from pages.desktop import DesktopPage
from pages.user import UserPage
from pages.packages import PackagesPage
from pages.summary import SummaryPage
from pages.progress import ProgressPage


STEPS = [
    ("welcome", "Hoş Geldiniz", "0"),
    ("disk", "Disk Seçimi", "1"),
    ("desktop", "Masaüstü Ortamı", "2"),
    ("user", "Kullanıcı Ayarları", "3"),
    ("packages", "Ek Paketler", "4"),
    ("summary", "Özet", "5"),
    ("progress", "Kurulum", "6"),
]


class InstallerWindow(Gtk.ApplicationWindow):
    def __init__(self, **kwargs):
        super().__init__(
            title="KutOS Installer",
            default_width=960,
            default_height=640,
            **kwargs,
        )
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_resizable(True)

        self.config = {
            "language": "tr",
            "disk": None,
            "partition_mode": "auto",
            "desktop": "xfce",
            "username": "",
            "password": "",
            "hostname": "kutos",
            "extra_packages": [],
        }
        self.current_step = 0

        self._build_ui()

    def _build_ui(self):
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.add(main_box)

        # Header
        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        header.get_style_context().add_class("header-bar")

        logo_label = Gtk.Label(label="⚡ KutOS")
        logo_label.get_style_context().add_class("header-title")
        header.pack_start(logo_label, False, False, 0)

        subtitle = Gtk.Label(label="  Sistem Kurulumu")
        subtitle.get_style_context().add_class("header-subtitle")
        header.pack_start(subtitle, False, False, 0)
        main_box.pack_start(header, False, False, 0)

        # Body: Sidebar + Content
        body = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        body.set_vexpand(True)
        main_box.pack_start(body, True, True, 0)

        # Sidebar
        self.sidebar = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.sidebar.get_style_context().add_class("sidebar")
        self.sidebar.set_size_request(220, -1)
        body.pack_start(self.sidebar, False, False, 0)

        self.step_labels = []
        self.step_numbers = []
        for i, (_, label, _) in enumerate(STEPS):
            row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            row.get_style_context().add_class("step-item")

            num = Gtk.Label(label=str(i + 1))
            num.get_style_context().add_class("step-number")
            num.set_size_request(28, 28)
            num.set_halign(Gtk.Align.CENTER)
            num.set_valign(Gtk.Align.CENTER)
            row.pack_start(num, False, False, 0)

            lbl = Gtk.Label(label=label, xalign=0)
            row.pack_start(lbl, True, True, 0)

            self.sidebar.pack_start(row, False, False, 0)
            self.step_labels.append(row)
            self.step_numbers.append(num)

        # Content Stack
        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        self.stack.set_transition_duration(300)
        self.stack.get_style_context().add_class("content-area")
        body.pack_start(self.stack, True, True, 0)

        # Create all pages
        self.pages = {
            "welcome": WelcomePage(self),
            "disk": DiskPage(self),
            "desktop": DesktopPage(self),
            "user": UserPage(self),
            "packages": PackagesPage(self),
            "summary": SummaryPage(self),
            "progress": ProgressPage(self),
        }
        for name, page in self.pages.items():
            self.stack.add_named(page, name)

        # Bottom Navigation
        nav_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        nav_bar.set_margin_start(20)
        nav_bar.set_margin_end(20)
        nav_bar.set_margin_top(12)
        nav_bar.set_margin_bottom(12)
        main_box.pack_end(nav_bar, False, False, 0)

        self.btn_back = Gtk.Button(label="◀  Geri")
        self.btn_back.get_style_context().add_class("btn-secondary")
        self.btn_back.connect("clicked", self._on_back)
        nav_bar.pack_start(self.btn_back, False, False, 0)

        spacer = Gtk.Box()
        nav_bar.pack_start(spacer, True, True, 0)

        self.btn_next = Gtk.Button(label="İleri  ▶")
        self.btn_next.get_style_context().add_class("btn-primary")
        self.btn_next.connect("clicked", self._on_next)
        nav_bar.pack_end(self.btn_next, False, False, 0)

        self._update_ui()
        self.show_all()

    def _update_ui(self):
        page_name = STEPS[self.current_step][0]
        self.stack.set_visible_child_name(page_name)

        # Update sidebar
        for i, (row, num) in enumerate(zip(self.step_labels, self.step_numbers)):
            ctx = row.get_style_context()
            num_ctx = num.get_style_context()

            ctx.remove_class("active")
            ctx.remove_class("completed")
            num_ctx.remove_class("active")
            num_ctx.remove_class("completed")

            if i == self.current_step:
                ctx.add_class("active")
                num_ctx.add_class("active")
            elif i < self.current_step:
                ctx.add_class("completed")
                num_ctx.add_class("completed")

        # Update buttons
        self.btn_back.set_visible(self.current_step > 0)

        if self.current_step == len(STEPS) - 2:  # Summary page
            self.btn_next.set_label("🚀  Kurulumu Başlat")
            self.btn_next.get_style_context().remove_class("btn-primary")
            self.btn_next.get_style_context().add_class("btn-danger")
        elif self.current_step == len(STEPS) - 1:  # Progress page
            self.btn_next.set_visible(False)
            self.btn_back.set_visible(False)
        else:
            self.btn_next.set_label("İleri  ▶")
            self.btn_next.get_style_context().remove_class("btn-danger")
            self.btn_next.get_style_context().add_class("btn-primary")

        # Notify the page it's now visible
        current_page = self.pages[page_name]
        if hasattr(current_page, "on_enter"):
            current_page.on_enter()

    def _on_next(self, _btn):
        page_name = STEPS[self.current_step][0]
        current_page = self.pages[page_name]

        # Validate current page
        if hasattr(current_page, "validate"):
            if not current_page.validate():
                return

        # Collect data from current page
        if hasattr(current_page, "collect"):
            current_page.collect()

        if self.current_step < len(STEPS) - 1:
            self.current_step += 1
            self._update_ui()

    def _on_back(self, _btn):
        if self.current_step > 0:
            self.current_step -= 1
            self._update_ui()

    def go_to_step(self, step_index):
        self.current_step = step_index
        self._update_ui()
