package pages

import (
	"strings"

	"github.com/gotk3/gotk3/gtk"
	"kutos/installer/backend"
	"kutos/installer/config"
)

type LocalePage struct {
	box     *gtk.Box
	cfg     *config.InstallConfig
	zones   []string
	listbox *gtk.ListBox
	notify  func()
}

func NewLocalePage(cfg *config.InstallConfig, notify func()) *LocalePage {
	return &LocalePage{cfg: cfg, notify: notify}
}

func (p *LocalePage) Widget() gtk.IWidget {
	if p.box != nil {
		return p.box
	}

	box, _ := gtk.BoxNew(gtk.ORIENTATION_VERTICAL, 0)

	title, _ := gtk.LabelNew("Konum ve Zaman Dilimi")
	sc(title, "page-title")
	title.SetXAlign(0)
	box.PackStart(title, false, false, 0)

	sub, _ := gtk.LabelNew("Zaman diliminizi seçin")
	sc(sub, "page-subtitle")
	sub.SetXAlign(0)
	box.PackStart(sub, false, false, 6)

	search, _ := gtk.SearchEntryNew()
	search.SetPlaceholderText("Ara…  örn: Istanbul")
	box.PackStart(search, false, false, 0)

	scroll, _ := gtk.ScrolledWindowNew(nil, nil)
	scroll.SetPolicy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
	scroll.SetMinContentHeight(320)
	scroll.SetMarginTop(10)

	p.listbox, _ = gtk.ListBoxNew()
	p.listbox.SetSelectionMode(gtk.SELECTION_SINGLE)
	scroll.Add(p.listbox)
	box.PackStart(scroll, true, true, 0)

	p.zones = backend.ListTimezones()
	for _, z := range p.zones {
		row, _ := gtk.ListBoxRowNew()
		lbl, _ := gtk.LabelNew(z)
		lbl.SetXAlign(0)
		lbl.SetMarginStart(4)
		row.Add(lbl)
		p.listbox.Add(row)
	}

	p.selectByValue(p.cfg.Timezone)

	p.listbox.Connect("row-selected", func(_ *gtk.ListBox, row *gtk.ListBoxRow) {
		if row == nil {
			return
		}
		idx := row.GetIndex()
		if idx >= 0 && idx < len(p.zones) {
			p.cfg.Timezone = p.zones[idx]
			if p.notify != nil {
				p.notify()
			}
		}
	})

	search.Connect("search-changed", func(e *gtk.SearchEntry) {
		text, _ := e.GetText()
		q := strings.ToLower(text)
		p.listbox.SetFilterFunc(func(row *gtk.ListBoxRow) bool {
			if q == "" {
				return true
			}
			child, _ := row.GetChild()
			if lbl, ok := child.(*gtk.Label); ok {
				t, _ := lbl.GetText()
				return strings.Contains(strings.ToLower(t), q)
			}
			return true
		})
		p.listbox.InvalidateFilter()
	})

	p.box = box
	return box
}

func (p *LocalePage) selectByValue(val string) {
	for i, z := range p.zones {
		if z == val {
			if row := p.listbox.GetRowAtIndex(i); row != nil {
				p.listbox.SelectRow(row)
			}
			return
		}
	}
}

func (p *LocalePage) Title() string    { return "Konum" }
func (p *LocalePage) CanProceed() bool { return p.cfg.Timezone != "" }
func (p *LocalePage) OnEnter()         {}
