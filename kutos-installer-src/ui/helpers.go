package ui

import "github.com/gotk3/gotk3/gtk"

// sc widget'a bir CSS class ekler; GetStyleContext hatasını gizler.
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

// rmClass widget'tan bir CSS class kaldırır.
func rmClass(w interface {
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
