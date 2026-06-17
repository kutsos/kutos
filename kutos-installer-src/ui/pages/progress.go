package pages

import (
	"fmt"

	"github.com/gotk3/gotk3/glib"
	"github.com/gotk3/gotk3/gtk"
	"kutos/installer/backend"
	"kutos/installer/config"
)

type ProgressPage struct {
	box     *gtk.Box
	bar     *gtk.ProgressBar
	stepLbl *gtk.Label
	logBuf  *gtk.TextBuffer
	logView *gtk.TextView
	cfg     *config.InstallConfig
	onDone  func()
	started bool
}

func NewProgressPage(cfg *config.InstallConfig, onDone func()) *ProgressPage {
	return &ProgressPage{cfg: cfg, onDone: onDone}
}

func (p *ProgressPage) Widget() gtk.IWidget {
	if p.box != nil {
		return p.box
	}

	box, _ := gtk.BoxNew(gtk.ORIENTATION_VERTICAL, 0)

	title, _ := gtk.LabelNew("Kurulum")
	sc(title, "page-title")
	title.SetXAlign(0)
	box.PackStart(title, false, false, 0)

	p.stepLbl, _ = gtk.LabelNew("Hazırlanıyor…")
	sc(p.stepLbl, "page-subtitle")
	p.stepLbl.SetXAlign(0)
	box.PackStart(p.stepLbl, false, false, 4)

	p.bar, _ = gtk.ProgressBarNew()
	p.bar.SetMarginBottom(14)
	box.PackStart(p.bar, false, false, 0)

	scroll, _ := gtk.ScrolledWindowNew(nil, nil)
	scroll.SetPolicy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
	scroll.SetMinContentHeight(340)

	p.logView, _ = gtk.TextViewNew()
	p.logView.SetEditable(false)
	p.logView.SetCursorVisible(false)
	p.logView.SetWrapMode(gtk.WRAP_CHAR)
	sc(p.logView, "log-view")
	p.logBuf, _ = p.logView.GetBuffer()
	scroll.Add(p.logView)
	box.PackStart(scroll, true, true, 0)

	p.box = box
	return box
}

func (p *ProgressPage) OnEnter() {
	if p.started {
		return
	}
	p.started = true
	go p.runInstall()
}

func (p *ProgressPage) appendLog(line string) {
	glib.IdleAdd(func() bool {
		end := p.logBuf.GetEndIter()
		p.logBuf.Insert(end, line+"\n")
		mark := p.logBuf.GetInsert()
		p.logView.ScrollToMark(mark, 0.0, false, 0.0, 1.0)
		return false
	})
}

func (p *ProgressPage) runInstall() {
	steps := backend.Steps()
	total := float64(len(steps))

	for i, step := range steps {
		fraction := float64(i) / total
		label := fmt.Sprintf("[%d/%d]  %s", i+1, len(steps), step.Name)

		glib.IdleAdd(func() bool {
			p.stepLbl.SetText(label)
			p.bar.SetFraction(fraction)
			return false
		})

		p.appendLog("\n▶  " + step.Name)

		if err := step.Fn(p.cfg, p.appendLog); err != nil {
			errMsg := "HATA: " + err.Error()
			p.appendLog(errMsg)
			glib.IdleAdd(func() bool {
				p.stepLbl.SetText("Kurulum başarısız!")
				return false
			})
			return
		}
	}

	glib.IdleAdd(func() bool {
		p.bar.SetFraction(1.0)
		p.stepLbl.SetText("Kurulum tamamlandı ✓")
		if p.onDone != nil {
			p.onDone()
		}
		return false
	})
}

func (p *ProgressPage) Title() string    { return "Kurulum" }
func (p *ProgressPage) CanProceed() bool { return false }
