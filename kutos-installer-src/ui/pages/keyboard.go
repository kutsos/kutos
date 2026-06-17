package pages

import (
	"fmt"
	"strings"

	"github.com/gotk3/gotk3/gtk"
	"kutos/installer/backend"
	"kutos/installer/config"
)

type KeyboardPage struct {
	box     *gtk.Box
	cfg     *config.InstallConfig
	layouts []backend.KeyboardLayout
	listbox *gtk.ListBox
	notify  func()
}

func NewKeyboardPage(cfg *config.InstallConfig, notify func()) *KeyboardPage {
	return &KeyboardPage{cfg: cfg, notify: notify}
}

func (p *KeyboardPage) Widget() gtk.IWidget {
	if p.box != nil {
		return p.box
	}

	box, _ := gtk.BoxNew(gtk.ORIENTATION_VERTICAL, 0)

	title, _ := gtk.LabelNew("Klavye Düzeni")
	sc(title, "page-title")
	title.SetXAlign(0)
	box.PackStart(title, false, false, 0)

	sub, _ := gtk.LabelNew("Kullanmak istediğiniz klavye düzenini seçin")
	sc(sub, "page-subtitle")
	sub.SetXAlign(0)
	box.PackStart(sub, false, false, 6)

	search, _ := gtk.SearchEntryNew()
	search.SetPlaceholderText("Ara…  örn: Turkish veya tr")
	box.PackStart(search, false, false, 0)

	scroll, _ := gtk.ScrolledWindowNew(nil, nil)
	scroll.SetPolicy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
	scroll.SetMinContentHeight(320)
	scroll.SetMarginTop(10)

	p.listbox, _ = gtk.ListBoxNew()
	scroll.Add(p.listbox)
	box.PackStart(scroll, true, true, 0)

	p.layouts = backend.ListKeyboardLayouts()
	for _, l := range p.layouts {
		row, _ := gtk.ListBoxRowNew()
		lbl, _ := gtk.LabelNew(fmt.Sprintf("%s  (%s)", l.Description, l.Code))
		lbl.SetXAlign(0)
		lbl.SetMarginStart(4)
		row.Add(lbl)
		p.listbox.Add(row)
	}

	p.selectByCode(p.cfg.KeyboardLayout)

	p.listbox.Connect("row-selected", func(_ *gtk.ListBox, row *gtk.ListBoxRow) {
		if row == nil {
			return
		}
		idx := row.GetIndex()
		if idx >= 0 && idx < len(p.layouts) {
			p.cfg.KeyboardLayout = p.layouts[idx].Code
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

func (p *KeyboardPage) selectByCode(code string) {
	for i, l := range p.layouts {
		if l.Code == code {
			if row := p.listbox.GetRowAtIndex(i); row != nil {
				p.listbox.SelectRow(row)
			}
			return
		}
	}
}

func (p *KeyboardPage) Title() string    { return "Klavye" }
func (p *KeyboardPage) CanProceed() bool { return p.cfg.KeyboardLayout != "" }
func (p *KeyboardPage) OnEnter()         {}
