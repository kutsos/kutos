package pages

import (
	"regexp"
	"strings"

	"github.com/gotk3/gotk3/gtk"
	"kutos/installer/config"
)

var usernameRe = regexp.MustCompile(`^[a-z_][a-z0-9_-]{0,31}$`)

type UsersPage struct {
	box           *gtk.Box
	cfg           *config.InstallConfig
	userEntry     *gtk.Entry
	passEntry     *gtk.Entry
	pass2Entry    *gtk.Entry
	rootPassEntry *gtk.Entry
	hostEntry     *gtk.Entry
	errorLbl      *gtk.Label
	notify        func()
}

func NewUsersPage(cfg *config.InstallConfig, notify func()) *UsersPage {
	return &UsersPage{cfg: cfg, notify: notify}
}

func (p *UsersPage) Widget() gtk.IWidget {
	if p.box != nil {
		return p.box
	}

	box, _ := gtk.BoxNew(gtk.ORIENTATION_VERTICAL, 0)

	title, _ := gtk.LabelNew("Kullanıcı Ayarları")
	sc(title, "page-title")
	title.SetXAlign(0)
	box.PackStart(title, false, false, 0)

	sub, _ := gtk.LabelNew("Yeni sistem için bir kullanıcı hesabı oluşturun")
	sc(sub, "page-subtitle")
	sub.SetXAlign(0)
	box.PackStart(sub, false, false, 6)

	form, _ := gtk.BoxNew(gtk.ORIENTATION_VERTICAL, 14)
	box.PackStart(form, false, false, 0)

	p.userEntry = p.addField(form, "KULLANICI ADI", "örn: ali", false)
	p.hostEntry = p.addField(form, "BİLGİSAYAR ADI (HOSTNAME)", "örn: kutos-pc", false)
	p.passEntry = p.addField(form, "ŞİFRE", "", true)
	p.pass2Entry = p.addField(form, "ŞİFRE TEKRAR", "", true)
	p.rootPassEntry = p.addField(form, "ROOT ŞİFRESİ  (boş = kullanıcı şifresi)", "", true)

	autoCheck, _ := gtk.CheckButtonNewWithLabel("Oturumu otomatik aç")
	autoCheck.SetMarginTop(4)
	autoCheck.Connect("toggled", func(c *gtk.CheckButton) {
		p.cfg.Autologin = c.GetActive()
	})
	form.PackStart(autoCheck, false, false, 0)

	p.errorLbl, _ = gtk.LabelNew("")
	sc(p.errorLbl, "warning-box")
	p.errorLbl.SetMarginTop(8)
	p.errorLbl.SetXAlign(0)
	p.errorLbl.SetLineWrap(true)
	p.errorLbl.SetVisible(false)
	box.PackStart(p.errorLbl, false, false, 0)

	onChange := func() { p.validate() }
	for _, e := range []*gtk.Entry{p.userEntry, p.passEntry, p.pass2Entry, p.hostEntry, p.rootPassEntry} {
		e.Connect("changed", onChange)
	}

	p.box = box
	return box
}

func (p *UsersPage) addField(parent *gtk.Box, label, placeholder string, secret bool) *gtk.Entry {
	group, _ := gtk.BoxNew(gtk.ORIENTATION_VERTICAL, 5)

	lbl, _ := gtk.LabelNew(label)
	sc(lbl, "field-label")
	lbl.SetXAlign(0)
	group.PackStart(lbl, false, false, 0)

	entry, _ := gtk.EntryNew()
	if placeholder != "" {
		entry.SetPlaceholderText(placeholder)
	}
	if secret {
		entry.SetVisibility(false)
		entry.SetInvisibleChar('•')
	}
	group.PackStart(entry, false, false, 0)
	parent.PackStart(group, false, false, 0)
	return entry
}

func (p *UsersPage) validate() {
	user, _ := p.userEntry.GetText()
	pass, _ := p.passEntry.GetText()
	pass2, _ := p.pass2Entry.GetText()
	host, _ := p.hostEntry.GetText()
	rootPass, _ := p.rootPassEntry.GetText()

	p.cfg.Username = user
	p.cfg.Password = pass
	p.cfg.Hostname = host
	if rootPass == "" {
		p.cfg.RootPassword = pass
	} else {
		p.cfg.RootPassword = rootPass
	}

	var errMsg string
	switch {
	case !usernameRe.MatchString(user):
		errMsg = "Geçersiz kullanıcı adı — küçük harf, rakam, _ veya - kullanın"
	case strings.Contains(host, " ") || host == "":
		errMsg = "Hostname boşluk içeremez ve boş olamaz"
	case len(pass) < 4:
		errMsg = "Şifre en az 4 karakter olmalı"
	case pass != pass2:
		errMsg = "Şifreler eşleşmiyor"
	}

	if errMsg != "" {
		p.errorLbl.SetText("⚠  " + errMsg)
		p.errorLbl.SetVisible(true)
	} else {
		p.errorLbl.SetVisible(false)
	}

	if p.notify != nil {
		p.notify()
	}
}

func (p *UsersPage) CanProceed() bool {
	if p.userEntry == nil {
		return false
	}
	user, _ := p.userEntry.GetText()
	pass, _ := p.passEntry.GetText()
	pass2, _ := p.pass2Entry.GetText()
	host, _ := p.hostEntry.GetText()
	return usernameRe.MatchString(user) &&
		!strings.Contains(host, " ") && host != "" &&
		len(pass) >= 4 &&
		pass == pass2
}

func (p *UsersPage) Title() string { return "Kullanıcı" }
func (p *UsersPage) OnEnter()      {}
