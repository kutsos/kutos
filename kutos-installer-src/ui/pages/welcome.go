package pages

import (
	"github.com/gotk3/gotk3/gtk"
	"kutos/installer/config"
)

type WelcomePage struct {
	box *gtk.Box
	cfg *config.InstallConfig
}

func NewWelcomePage(cfg *config.InstallConfig) *WelcomePage {
	return &WelcomePage{cfg: cfg}
}

func (p *WelcomePage) Widget() gtk.IWidget {
	if p.box != nil {
		return p.box
	}

	box, _ := gtk.BoxNew(gtk.ORIENTATION_VERTICAL, 0)
	box.SetMarginTop(60)

	title, _ := gtk.LabelNew("KutOS'a Hoş Geldiniz")
	sc(title, "page-title")
	title.SetXAlign(0)
	box.PackStart(title, false, false, 0)

	sub, _ := gtk.LabelNew("Bu sihirbaz KutOS'u bilgisayarınıza kuracak.\nBaşlamak için İleri'ye basın.")
	sc(sub, "page-subtitle")
	sub.SetXAlign(0)
	sub.SetLineWrap(true)
	box.PackStart(sub, false, false, 8)

	items := []struct{ icon, text string }{
		{"⏱", "Kurulum yaklaşık 5–10 dakika sürer"},
		{"💾", "En az 8 GB boş disk alanı gereklidir"},
		{"🌐", "İnternet bağlantısı gerekmez"},
		{"⚠", "Hedef disk tamamen silinecektir — verilerinizi yedekleyin!"},
	}

	infoBox, _ := gtk.BoxNew(gtk.ORIENTATION_VERTICAL, 10)
	infoBox.SetMarginTop(28)
	for _, item := range items {
		row, _ := gtk.BoxNew(gtk.ORIENTATION_HORIZONTAL, 0)
		iconLbl, _ := gtk.LabelNew(item.icon)
		sc(iconLbl, "info-icon")
		iconLbl.SetXAlign(0)
		row.PackStart(iconLbl, false, false, 0)

		txt, _ := gtk.LabelNew(item.text)
		sc(txt, "info-text")
		txt.SetXAlign(0)
		txt.SetLineWrap(true)
		row.PackStart(txt, true, true, 0)

		infoBox.PackStart(row, false, false, 0)
	}
	box.PackStart(infoBox, false, false, 0)

	p.box = box
	return box
}

func (p *WelcomePage) Title() string    { return "Hoş Geldin" }
func (p *WelcomePage) CanProceed() bool { return true }
func (p *WelcomePage) OnEnter()         {}
