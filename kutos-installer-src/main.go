package main

import (
	"fmt"
	"os"

	"github.com/gotk3/gotk3/gtk"
	"kutos/installer/config"
	"kutos/installer/ui"
	"kutos/installer/ui/pages"
)

func main() {
	if os.Geteuid() != 0 {
		fmt.Fprintln(os.Stderr, "KutOS Installer root yetkisi gerektiriyor.")
		fmt.Fprintln(os.Stderr, "Kullanım: pkexec kutos-installer")
		os.Exit(1)
	}

	gtk.Init(nil)

	cfg := config.New()

	win, err := ui.NewMainWindow()
	if err != nil {
		fmt.Fprintln(os.Stderr, "Pencere oluşturulamadı:", err)
		os.Exit(1)
	}

	// Progress sayfası kurulumu tamamlayınca İleri butonunu aç
	progressPage := pages.NewProgressPage(cfg, func() {
		win.EnableNext()
	})

	allPages := []ui.Page{
		pages.NewWelcomePage(cfg),
		pages.NewLocalePage(cfg, win.NotifyPageChanged),
		pages.NewKeyboardPage(cfg, win.NotifyPageChanged),
		pages.NewPartitionPage(cfg, win.NotifyPageChanged),
		pages.NewUsersPage(cfg, win.NotifyPageChanged),
		pages.NewSummaryPage(cfg),
		progressPage,
		pages.NewFinishPage(cfg),
	}

	win.SetPages(allPages)
	win.Show()

	gtk.Main()
}
