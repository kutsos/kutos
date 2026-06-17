package pages

import "github.com/gotk3/gotk3/gtk"

// sc widget'a CSS class ekler; GetStyleContext hatasını yutar.
func sc(w interface {
	GetStyleContext() (*gtk.StyleContext, error)
}, classes ...string) {
	ctx, err := w.GetStyleContext()
	if err != nil {
		return
	}
	for _, c := range classes {
		ctx.AddClass(c)
	}
}

// rmsc widget'tan CSS class kaldırır.
func rmsc(w interface {
	GetStyleContext() (*gtk.StyleContext, error)
}, classes ...string) {
	ctx, err := w.GetStyleContext()
	if err != nil {
		return
	}
	for _, c := range classes {
		ctx.RemoveClass(c)
	}
}

// clearBox bir gtk.Box'ın tüm child'larını kaldırır.
// GetChildren() *glib.List döndürdüğü için for-range yerine Next() kullanılır.
func clearBox(box *gtk.Box) {
	children := box.GetChildren()
	for l := children; l != nil; l = l.Next() {
		if w, ok := l.Data().(gtk.IWidget); ok {
			box.Remove(w)
		}
	}
}

// clearListBox bir gtk.ListBox'ın tüm row'larını kaldırır.
func clearListBox(lb *gtk.ListBox) {
	for {
		row := lb.GetRowAtIndex(0)
		if row == nil {
			break
		}
		lb.Remove(row)
	}
}
