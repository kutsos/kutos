package ui

import (
	"fmt"

	"github.com/gotk3/gotk3/gdk"
	"github.com/gotk3/gotk3/gtk"
)

// Page bir kurulum sayfasının uygulaması gereken arayüz.
type Page interface {
	Widget() gtk.IWidget
	Title() string
	CanProceed() bool
	OnEnter()
}

// MainWindow uygulamanın ana penceresi: sidebar + içerik + footer.
type MainWindow struct {
	win        *gtk.Window
	stack      *gtk.Stack
	pageList   []Page
	currentIdx int
	btnBack    *gtk.Button
	btnNext    *gtk.Button
	stepRows   []*stepRow
}

type stepRow struct {
	box    *gtk.Box
	numLbl *gtk.Label
}

var stepLabels = []string{
	"Hoş Geldin",
	"Konum",
	"Klavye",
	"Disk",
	"Kullanıcı",
	"Özet",
	"Kurulum",
	"Bitti",
}

// NewMainWindow yeni bir GTK ana penceresi oluşturur.
func NewMainWindow() (*MainWindow, error) {
	win, err := gtk.WindowNew(gtk.WINDOW_TOPLEVEL)
	if err != nil {
		return nil, err
	}

	mw := &MainWindow{win: win}
	mw.loadCSS()
	mw.build()

	win.SetTitle("KutOS Installer")
	win.SetDefaultSize(980, 660)
	win.SetPosition(gtk.WIN_POS_CENTER)
	win.SetResizable(false)
	win.Connect("destroy", gtk.MainQuit)

	return mw, nil
}

func (mw *MainWindow) loadCSS() {
	provider, _ := gtk.CssProviderNew()
	_ = provider.LoadFromData(AppCSS)
	screen, _ := gdk.ScreenGetDefault()
	gtk.AddProviderForScreen(screen, provider, gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
}

func (mw *MainWindow) build() {
	root, _ := gtk.BoxNew(gtk.ORIENTATION_HORIZONTAL, 0)
	mw.win.Add(root)

	sidebar := mw.buildSidebar()
	root.PackStart(sidebar, false, false, 0)

	right, _ := gtk.BoxNew(gtk.ORIENTATION_VERTICAL, 0)
	root.PackStart(right, true, true, 0)

	scroll, _ := gtk.ScrolledWindowNew(nil, nil)
	scroll.SetPolicy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
	sc(scroll, "content-area")

	mw.stack, _ = gtk.StackNew()
	mw.stack.SetTransitionType(gtk.STACK_TRANSITION_TYPE_SLIDE_LEFT_RIGHT)
	mw.stack.SetTransitionDuration(180)
	scroll.Add(mw.stack)
	right.PackStart(scroll, true, true, 0)

	footer := mw.buildFooter()
	right.PackStart(footer, false, false, 0)
}

func (mw *MainWindow) buildSidebar() *gtk.Box {
	sidebar, _ := gtk.BoxNew(gtk.ORIENTATION_VERTICAL, 0)
	sc(sidebar, "sidebar")

	logoBox, _ := gtk.BoxNew(gtk.ORIENTATION_HORIZONTAL, 0)
	sc(logoBox, "sidebar-logo")
	kut, _ := gtk.LabelNew("Kut")
	sc(kut, "logo-text")
	os_, _ := gtk.LabelNew("OS")
	sc(os_, "logo-accent")
	logoBox.PackStart(kut, false, false, 0)
	logoBox.PackStart(os_, false, false, 0)
	sidebar.PackStart(logoBox, false, false, 0)

	mw.stepRows = make([]*stepRow, len(stepLabels))
	for i, label := range stepLabels {
		sr := mw.buildStepRow(i+1, label)
		mw.stepRows[i] = sr
		sidebar.PackStart(sr.box, false, false, 0)
	}

	return sidebar
}

func (mw *MainWindow) buildStepRow(num int, label string) *stepRow {
	box, _ := gtk.BoxNew(gtk.ORIENTATION_HORIZONTAL, 0)
	sc(box, "step-row")

	numLbl, _ := gtk.LabelNew(fmt.Sprintf("%d", num))
	sc(numLbl, "step-num")
	box.PackStart(numLbl, false, false, 0)

	namLbl, _ := gtk.LabelNew(label)
	namLbl.SetXAlign(0)
	box.PackStart(namLbl, true, true, 0)

	return &stepRow{box: box, numLbl: numLbl}
}

func (mw *MainWindow) buildFooter() *gtk.Box {
	footer, _ := gtk.BoxNew(gtk.ORIENTATION_HORIZONTAL, 0)
	sc(footer, "footer")

	mw.btnBack, _ = gtk.ButtonNewWithLabel("← Geri")
	sc(mw.btnBack, "btn-secondary")
	mw.btnBack.Connect("clicked", mw.goBack)
	footer.PackStart(mw.btnBack, false, false, 0)

	spacer, _ := gtk.BoxNew(gtk.ORIENTATION_HORIZONTAL, 0)
	footer.PackStart(spacer, true, true, 0)

	mw.btnNext, _ = gtk.ButtonNewWithLabel("İleri →")
	sc(mw.btnNext, "btn-primary")
	mw.btnNext.Connect("clicked", mw.goNext)
	footer.PackEnd(mw.btnNext, false, false, 0)

	return footer
}

// SetPages sayfa listesini yükler ve ilk sayfayı gösterir.
func (mw *MainWindow) SetPages(pages []Page) {
	mw.pageList = pages
	for i, p := range pages {
		mw.stack.AddNamed(p.Widget(), fmt.Sprintf("p%d", i))
	}
	mw.goTo(0)
}

// EnableNext progress sayfası kurulumu bitirince Next butonunu açar.
func (mw *MainWindow) EnableNext() {
	mw.btnNext.SetSensitive(true)
	mw.btnNext.SetLabel("İleri →")
}

// Show pencereyi ekranda gösterir.
func (mw *MainWindow) Show() {
	mw.win.ShowAll()
}

// NotifyPageChanged bir sayfa durumu değiştiğinde sidebar + butonları yeniler.
func (mw *MainWindow) NotifyPageChanged() {
	mw.refreshUI()
}

func (mw *MainWindow) goTo(idx int) {
	if idx < 0 || idx >= len(mw.pageList) {
		return
	}
	mw.currentIdx = idx
	mw.stack.SetVisibleChildName(fmt.Sprintf("p%d", idx))
	mw.pageList[idx].OnEnter()
	mw.refreshUI()
}

func (mw *MainWindow) goNext() {
	idx := mw.currentIdx
	total := len(mw.pageList)
	if idx == total-1 {
		gtk.MainQuit()
		return
	}
	if !mw.pageList[idx].CanProceed() {
		return
	}
	mw.goTo(idx + 1)
}

func (mw *MainWindow) goBack() {
	mw.goTo(mw.currentIdx - 1)
}

func (mw *MainWindow) refreshUI() {
	idx := mw.currentIdx
	total := len(mw.pageList)
	isLast := idx == total-1
	isProgress := idx == total-2

	mw.btnBack.SetSensitive(idx > 0 && !isLast && !isProgress)

	switch {
	case isLast:
		mw.btnNext.SetLabel("Kapat")
		mw.btnNext.SetSensitive(true)
	case isProgress:
		mw.btnNext.SetLabel("İleri →")
		mw.btnNext.SetSensitive(false)
	default:
		mw.btnNext.SetLabel("İleri →")
		mw.btnNext.SetSensitive(mw.pageList[idx].CanProceed())
	}

	for i, sr := range mw.stepRows {
		rmClass(sr.box, "active", "done")
		rmClass(sr.numLbl, "active-num", "done-num")
		switch {
		case i < idx:
			sc(sr.box, "done")
			sc(sr.numLbl, "done-num")
		case i == idx:
			sc(sr.box, "active")
			sc(sr.numLbl, "active-num")
		}
	}
}
