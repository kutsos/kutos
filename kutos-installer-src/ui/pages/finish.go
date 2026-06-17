package pages

import (
	"os/exec"

	"github.com/gotk3/gotk3/gtk"
	"kutos/installer/config"
)

type FinishPage struct {
	box *gtk.Box
	cfg *config.InstallConfig
}

func NewFinishPage(cfg *config.InstallConfig) *FinishPage {
	return &FinishPage{cfg: cfg}
}

func (p *FinishPage) Widget() gtk.IWidget {
	if p.box != nil {
		return p.box
	}

	box, _ := gtk.BoxNew(gtk.ORIENTATION_VERTICAL, 0)
	box.SetVAlign(gtk.ALIGN_CENTER)
	box.SetHAlign(gtk.ALIGN_CENTER)
	box.SetSpacing(12)

	icon, _ := gtk.LabelNew("")
	icon.SetMarkup(`<span font="56" foreground="#4ade80">✓</span>`)
	sc(icon, "finish-icon")
	box.PackStart(icon, false, false, 0)

	title, _ := gtk.LabelNew("KutOS Başarıyla Kuruldu!")
	sc(title, "finish-title")
	box.PackStart(title, false, false, 0)

	sub, _ := gtk.LabelNew("Sisteminiz hazır. USB belleği çıkarıp\nyeniden başlatabilirsiniz.")
	sc(sub, "finish-sub")
	sub.SetJustify(gtk.JUSTIFY_CENTER)
	sub.SetLineWrap(true)
	box.PackStart(sub, false, false, 8)

	btnBox, _ := gtk.BoxNew(gtk.ORIENTATION_HORIZONTAL, 12)
	btnBox.SetHAlign(gtk.ALIGN_CENTER)
	btnBox.SetMarginTop(8)

	rebootBtn, _ := gtk.ButtonNewWithLabel("Yeniden Başlat")
	sc(rebootBtn, "btn-primary")
	rebootBtn.Connect("clicked", func() {
		_ = exec.Command("systemctl", "reboot").Run()
	})
	btnBox.PackStart(rebootBtn, false, false, 0)

	closeBtn, _ := gtk.ButtonNewWithLabel("Kapat")
	sc(closeBtn, "btn-secondary")
	closeBtn.Connect("clicked", gtk.MainQuit)
	btnBox.PackStart(closeBtn, false, false, 0)

	box.PackStart(btnBox, false, false, 0)

	p.box = box
	return box
}

func (p *FinishPage) Title() string    { return "Bitti" }
func (p *FinishPage) CanProceed() bool { return true }
func (p *FinishPage) OnEnter()         {}
