package pages

import (
	"fmt"

	"github.com/gotk3/gotk3/gtk"
	"kutos/installer/backend"
	"kutos/installer/config"
)

type PartitionPage struct {
	box     *gtk.Box
	cfg     *config.InstallConfig
	disks   []backend.Disk
	listbox *gtk.ListBox
	notify  func()
}

func NewPartitionPage(cfg *config.InstallConfig, notify func()) *PartitionPage {
	return &PartitionPage{cfg: cfg, notify: notify}
}

func (p *PartitionPage) Widget() gtk.IWidget {
	if p.box != nil {
		return p.box
	}

	box, _ := gtk.BoxNew(gtk.ORIENTATION_VERTICAL, 0)

	title, _ := gtk.LabelNew("Disk Seçimi")
	sc(title, "page-title")
	title.SetXAlign(0)
	box.PackStart(title, false, false, 0)

	sub, _ := gtk.LabelNew("KutOS'un kurulacağı diski seçin")
	sc(sub, "page-subtitle")
	sub.SetXAlign(0)
	box.PackStart(sub, false, false, 6)

	scroll, _ := gtk.ScrolledWindowNew(nil, nil)
	scroll.SetPolicy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
	scroll.SetMinContentHeight(180)

	p.listbox, _ = gtk.ListBoxNew()
	scroll.Add(p.listbox)
	box.PackStart(scroll, false, false, 0)

	// Seçenekler
	optRow, _ := gtk.BoxNew(gtk.ORIENTATION_HORIZONTAL, 24)
	optRow.SetMarginTop(16)

	fsGroup, _ := gtk.BoxNew(gtk.ORIENTATION_VERTICAL, 6)
	fsLbl, _ := gtk.LabelNew("DOSYA SİSTEMİ")
	sc(fsLbl, "field-label")
	fsLbl.SetXAlign(0)
	fsGroup.PackStart(fsLbl, false, false, 0)
	fsCombo, _ := gtk.ComboBoxTextNew()
	fsCombo.AppendText("ext4")
	fsCombo.AppendText("btrfs")
	fsCombo.SetActive(0)
	fsCombo.Connect("changed", func(c *gtk.ComboBoxText) {
		p.cfg.Filesystem = c.GetActiveText()
	})
	fsGroup.PackStart(fsCombo, false, false, 0)
	optRow.PackStart(fsGroup, false, false, 0)

	swapGroup, _ := gtk.BoxNew(gtk.ORIENTATION_VERTICAL, 6)
	swapLbl, _ := gtk.LabelNew("SWAP")
	sc(swapLbl, "field-label")
	swapLbl.SetXAlign(0)
	swapGroup.PackStart(swapLbl, false, false, 0)
	swapCombo, _ := gtk.ComboBoxTextNew()
	for _, s := range []string{"none", "2G", "4G", "8G"} {
		swapCombo.AppendText(s)
	}
	swapCombo.SetActive(0)
	swapCombo.Connect("changed", func(c *gtk.ComboBoxText) {
		p.cfg.SwapSize = c.GetActiveText()
	})
	swapGroup.PackStart(swapCombo, false, false, 0)
	optRow.PackStart(swapGroup, false, false, 0)

	box.PackStart(optRow, false, false, 0)

	warn, _ := gtk.LabelNew("⚠  Seçilen disk tamamen silinecektir! Tüm veriler kaybolur.")
	sc(warn, "warning-box")
	warn.SetMarginTop(16)
	warn.SetXAlign(0)
	warn.SetLineWrap(true)
	box.PackStart(warn, false, false, 0)

	p.listbox.Connect("row-selected", func(_ *gtk.ListBox, row *gtk.ListBoxRow) {
		if row == nil {
			return
		}
		idx := row.GetIndex()
		if idx >= 0 && idx < len(p.disks) {
			p.cfg.TargetDisk = p.disks[idx].Path
			if p.notify != nil {
				p.notify()
			}
		}
	})

	p.box = box
	return box
}

// OnEnter sayfaya her gelindiğinde diskleri yeniden tarar.
func (p *PartitionPage) OnEnter() {
	disks, err := backend.ListDisks()
	if err != nil || len(disks) == 0 {
		return
	}
	p.disks = disks
	p.cfg.EFIMode = backend.IsEFI()

	// Mevcut satırları temizle (index 0'dan başlayarak sil)
	for {
		row := p.listbox.GetRowAtIndex(0)
		if row == nil {
			break
		}
		p.listbox.Remove(row)
	}

	for _, d := range disks {
		row, _ := gtk.ListBoxRowNew()
		vbox, _ := gtk.BoxNew(gtk.ORIENTATION_VERTICAL, 3)
		vbox.SetMarginTop(2)
		vbox.SetMarginBottom(2)

		nameLbl, _ := gtk.LabelNew(fmt.Sprintf("%s  —  %s", d.Path, d.Size))
		sc(nameLbl, "disk-name")
		nameLbl.SetXAlign(0)
		vbox.PackStart(nameLbl, false, false, 0)

		modelLbl, _ := gtk.LabelNew(d.Model)
		sc(modelLbl, "disk-meta")
		modelLbl.SetXAlign(0)
		vbox.PackStart(modelLbl, false, false, 0)

		row.Add(vbox)
		p.listbox.Add(row)
	}
	p.listbox.ShowAll()
}

func (p *PartitionPage) Title() string    { return "Disk" }
func (p *PartitionPage) CanProceed() bool { return p.cfg.TargetDisk != "" }
