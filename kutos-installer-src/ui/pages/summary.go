package pages

import (
	"fmt"

	"github.com/gotk3/gotk3/gtk"
	"kutos/installer/config"
)

type SummaryPage struct {
	box      *gtk.Box
	itemsBox *gtk.Box
	cfg      *config.InstallConfig
}

func NewSummaryPage(cfg *config.InstallConfig) *SummaryPage {
	return &SummaryPage{cfg: cfg}
}

func (p *SummaryPage) Widget() gtk.IWidget {
	if p.box != nil {
		return p.box
	}

	box, _ := gtk.BoxNew(gtk.ORIENTATION_VERTICAL, 0)

	title, _ := gtk.LabelNew("Kurulum Özeti")
	sc(title, "page-title")
	title.SetXAlign(0)
	box.PackStart(title, false, false, 0)

	sub, _ := gtk.LabelNew("Ayarları kontrol edin — kurulum başladıktan sonra geri dönülemez.")
	sc(sub, "page-subtitle")
	sub.SetXAlign(0)
	sub.SetLineWrap(true)
	box.PackStart(sub, false, false, 6)

	p.itemsBox, _ = gtk.BoxNew(gtk.ORIENTATION_VERTICAL, 0)
	box.PackStart(p.itemsBox, false, false, 0)

	p.box = box
	return box
}

func (p *SummaryPage) OnEnter() {
	clearBox(p.itemsBox)

	efiStr := "BIOS"
	if p.cfg.EFIMode {
		efiStr = "UEFI"
	}
	autoStr := "Hayır"
	if p.cfg.Autologin {
		autoStr = "Evet"
	}

	rows := []struct{ key, val string }{
		{"Hedef Disk", p.cfg.TargetDisk},
		{"Dosya Sistemi", p.cfg.Filesystem},
		{"Swap", p.cfg.SwapSize},
		{"Kullanıcı", p.cfg.Username},
		{"Hostname", p.cfg.Hostname},
		{"Zaman Dilimi", p.cfg.Timezone},
		{"Klavye", p.cfg.KeyboardLayout},
		{"Boot Modu", efiStr},
		{"Otomatik Giriş", autoStr},
	}

	grid, _ := gtk.GridNew()
	grid.SetRowSpacing(10)
	grid.SetColumnSpacing(20)
	grid.SetMarginBottom(16)

	for i, r := range rows {
		keyLbl, _ := gtk.LabelNew(r.key)
		sc(keyLbl, "summary-key")
		keyLbl.SetXAlign(0)
		grid.Attach(keyLbl, 0, i, 1, 1)

		sep, _ := gtk.LabelNew(":")
		sc(sep, "summary-key")
		grid.Attach(sep, 1, i, 1, 1)

		valLbl, _ := gtk.LabelNew(r.val)
		sc(valLbl, "summary-val")
		valLbl.SetXAlign(0)
		grid.Attach(valLbl, 2, i, 1, 1)
	}
	p.itemsBox.PackStart(grid, false, false, 0)

	warn, _ := gtk.LabelNew(fmt.Sprintf(
		"⚠  %s üzerindeki tüm veriler kalıcı olarak silinecek!", p.cfg.TargetDisk,
	))
	sc(warn, "warning-box")
	warn.SetMarginTop(8)
	warn.SetXAlign(0)
	warn.SetLineWrap(true)
	p.itemsBox.PackStart(warn, false, false, 0)

	p.itemsBox.ShowAll()
}

func (p *SummaryPage) Title() string    { return "Özet" }
func (p *SummaryPage) CanProceed() bool { return true }
