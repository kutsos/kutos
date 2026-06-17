package backend

import (
	"fmt"
	"os"
	"os/exec"
	"strings"

	"kutos/installer/config"
)

// Logger kurulum adımlarından gelen log satırlarını UI'a iletir.
type Logger func(line string)

// InstallStep bir kurulum adımını isim ve uygulama fonksiyonuyla tanımlar.
type InstallStep struct {
	Name string
	Fn   func(cfg *config.InstallConfig, log Logger) error
}

// Steps kurulum adımlarını sırayla döndürür.
func Steps() []InstallStep {
	return []InstallStep{
		{"Disk bölümleniyor", stepPartition},
		{"Dosya sistemleri oluşturuluyor", stepFormat},
		{"Bölümler bağlanıyor", stepMount},
		{"Sistem kopyalanıyor", stepCopySystem},
		{"fstab oluşturuluyor", stepFstab},
		{"Hostname ayarlanıyor", stepHostname},
		{"Locale ve zaman dilimi ayarlanıyor", stepLocale},
		{"Klavye ayarlanıyor", stepKeyboard},
		{"Kullanıcı oluşturuluyor", stepUsers},
		{"Servisler etkinleştiriliyor", stepServices},
		{"Bootloader kuruluyor", stepBootloader},
		{"Temizlik yapılıyor", stepCleanup},
	}
}

func stepPartition(cfg *config.InstallConfig, log Logger) error {
	log("→ Disk: " + cfg.TargetDisk)
	return PartitionDisk(cfg.TargetDisk, cfg.EFIMode, cfg.SwapSize)
}

func stepFormat(cfg *config.InstallConfig, log Logger) error {
	hasSwap := cfg.SwapSize != "none" && cfg.SwapSize != ""
	log(fmt.Sprintf("→ Filesystem: %s  Swap: %v", cfg.Filesystem, hasSwap))
	return FormatPartitions(cfg.TargetDisk, cfg.EFIMode, cfg.Filesystem, hasSwap)
}

func stepMount(cfg *config.InstallConfig, log Logger) error {
	hasSwap := cfg.SwapSize != "none" && cfg.SwapSize != ""
	return MountPartitions(cfg.TargetDisk, cfg.EFIMode, cfg.Filesystem, hasSwap)
}

func stepCopySystem(cfg *config.InstallConfig, log Logger) error {
	source := "/run/archiso/airootfs/"
	dest := MountPoint + "/"
	log("→ rsync başlatılıyor...")

	cmd := exec.Command("rsync", "-aAXH",
		"--exclude=/proc/*",
		"--exclude=/sys/*",
		"--exclude=/dev/*",
		"--exclude=/run/*",
		"--exclude=/tmp/*",
		"--exclude=/mnt/*",
		"--info=progress2",
		source, dest,
	)
	cmd.Stdout = &logWriter{log: log}
	cmd.Stderr = &logWriter{log: log}
	return cmd.Run()
}

func stepFstab(cfg *config.InstallConfig, log Logger) error {
	log("→ genfstab çalıştırılıyor")
	out, err := exec.Command("genfstab", "-U", MountPoint).Output()
	if err != nil {
		return fmt.Errorf("genfstab: %w", err)
	}
	return os.WriteFile(MountPoint+"/etc/fstab", out, 0644)
}

func stepHostname(cfg *config.InstallConfig, log Logger) error {
	log("→ Hostname: " + cfg.Hostname)
	if err := os.WriteFile(MountPoint+"/etc/hostname", []byte(cfg.Hostname+"\n"), 0644); err != nil {
		return err
	}
	hosts := fmt.Sprintf("127.0.0.1\tlocalhost\n::1\t\tlocalhost\n127.0.1.1\t%s\n", cfg.Hostname)
	return os.WriteFile(MountPoint+"/etc/hosts", []byte(hosts), 0644)
}

func stepLocale(cfg *config.InstallConfig, log Logger) error {
	log("→ Locale: " + cfg.Locale)

	data, _ := os.ReadFile(MountPoint + "/etc/locale.gen")
	content := strings.ReplaceAll(string(data), "#"+cfg.Locale, cfg.Locale)
	if !strings.Contains(content, cfg.Locale+" ") {
		content += "\n" + cfg.Locale + " UTF-8\n"
	}
	if err := os.WriteFile(MountPoint+"/etc/locale.gen", []byte(content), 0644); err != nil {
		return err
	}

	if err := chroot(log, "locale-gen"); err != nil {
		return err
	}

	localeConf := "LANG=" + cfg.Locale + "\nLC_TIME=" + cfg.Locale + "\n"
	if err := os.WriteFile(MountPoint+"/etc/locale.conf", []byte(localeConf), 0644); err != nil {
		return err
	}

	log("→ Timezone: " + cfg.Timezone)
	return chroot(log, "ln", "-sf", "/usr/share/zoneinfo/"+cfg.Timezone, "/etc/localtime")
}

func stepKeyboard(cfg *config.InstallConfig, log Logger) error {
	log("→ Keyboard: " + cfg.KeyboardLayout)

	vconsole := "KEYMAP=" + cfg.KeyboardLayout + "\n"
	if err := os.WriteFile(MountPoint+"/etc/vconsole.conf", []byte(vconsole), 0644); err != nil {
		return err
	}

	xkbDir := MountPoint + "/etc/X11/xorg.conf.d"
	if err := os.MkdirAll(xkbDir, 0755); err != nil {
		return err
	}

	xkbConf := fmt.Sprintf(`Section "InputClass"
    Identifier "keyboard"
    MatchIsKeyboard "yes"
    Option "XkbLayout" "%s"
EndSection
`, cfg.KeyboardLayout)
	return os.WriteFile(xkbDir+"/00-keyboard.conf", []byte(xkbConf), 0644)
}

func stepUsers(cfg *config.InstallConfig, log Logger) error {
	log("→ Kullanıcı: " + cfg.Username)

	sudoers := "%wheel ALL=(ALL:ALL) ALL\n"
	sudoDir := MountPoint + "/etc/sudoers.d"
	if err := os.MkdirAll(sudoDir, 0750); err != nil {
		return err
	}
	if err := os.WriteFile(sudoDir+"/wheel", []byte(sudoers), 0440); err != nil {
		return err
	}

	groups := "wheel,audio,video,network,storage,optical,power"
	if err := chroot(log, "useradd", "-m", "-G", groups, "-s", "/bin/bash", cfg.Username); err != nil {
		return fmt.Errorf("useradd: %w", err)
	}

	if err := chrootInput(cfg.Password+"\n"+cfg.Password+"\n", log, "passwd", cfg.Username); err != nil {
		return fmt.Errorf("passwd user: %w", err)
	}

	if cfg.RootPassword != "" {
		if err := chrootInput(cfg.RootPassword+"\n"+cfg.RootPassword+"\n", log, "passwd"); err != nil {
			return fmt.Errorf("passwd root: %w", err)
		}
	}

	if cfg.Autologin {
		confDir := MountPoint + "/etc/lightdm/lightdm.conf.d"
		if err := os.MkdirAll(confDir, 0755); err != nil {
			return err
		}
		lightdmConf := fmt.Sprintf("[Seat:*]\nautologin-user=%s\nautologin-user-timeout=0\n", cfg.Username)
		if err := os.WriteFile(confDir+"/50-autologin.conf", []byte(lightdmConf), 0644); err != nil {
			return err
		}
	}

	return nil
}

func stepServices(cfg *config.InstallConfig, log Logger) error {
	for _, svc := range []string{"NetworkManager", "lightdm"} {
		log("→ enable: " + svc)
		if err := chroot(log, "systemctl", "enable", svc); err != nil {
			return fmt.Errorf("enable %s: %w", svc, err)
		}
	}
	return nil
}

func stepBootloader(cfg *config.InstallConfig, log Logger) error {
	if !cfg.InstallGRUB {
		log("→ Bootloader atlandı")
		return nil
	}

	if cfg.EFIMode {
		log("→ GRUB (UEFI) kuruluyor")
		if err := chroot(log, "grub-install",
			"--target=x86_64-efi",
			"--efi-directory=/boot/efi",
			"--bootloader-id=KutOS",
			"--recheck",
		); err != nil {
			return fmt.Errorf("grub-install uefi: %w", err)
		}
	} else {
		log("→ GRUB (BIOS) kuruluyor: " + cfg.TargetDisk)
		if err := chroot(log, "grub-install",
			"--target=i386-pc",
			"--recheck",
			cfg.TargetDisk,
		); err != nil {
			return fmt.Errorf("grub-install bios: %w", err)
		}
	}

	log("→ grub.cfg oluşturuluyor")
	return chroot(log, "grub-mkconfig", "-o", "/boot/grub/grub.cfg")
}

func stepCleanup(cfg *config.InstallConfig, log Logger) error {
	log("→ Live-ortam dosyaları temizleniyor")

	// Live-only desktop kısayollarını ve lightdm config'i kaldır
	filesToRemove := []string{
		MountPoint + "/root/Desktop/kutos-installer.desktop",
		MountPoint + "/root/.config/autostart/kutos-installer.desktop",
		MountPoint + "/etc/lightdm/lightdm.conf", // live autologin config
	}
	for _, f := range filesToRemove {
		_ = os.Remove(f)
	}

	log("→ Bölümler kaldırılıyor")
	UnmountAll()
	return nil
}

// chroot arch-chroot ile hedef sistemde komut çalıştırır.
func chroot(log Logger, name string, args ...string) error {
	cmdArgs := append([]string{MountPoint, name}, args...)
	cmd := exec.Command("arch-chroot", cmdArgs...)
	cmd.Stdout = &logWriter{log: log}
	cmd.Stderr = &logWriter{log: log}
	return cmd.Run()
}

// chrootInput arch-chroot ile stdin besleyerek komut çalıştırır (passwd gibi).
func chrootInput(input string, log Logger, name string, args ...string) error {
	cmdArgs := append([]string{MountPoint, name}, args...)
	cmd := exec.Command("arch-chroot", cmdArgs...)
	cmd.Stdin = strings.NewReader(input)
	cmd.Stdout = &logWriter{log: log}
	cmd.Stderr = &logWriter{log: log}
	return cmd.Run()
}

// logWriter Logger callback'ini io.Writer'a çevirir.
type logWriter struct {
	log Logger
}

func (w *logWriter) Write(p []byte) (int, error) {
	for _, line := range strings.Split(string(p), "\n") {
		if l := strings.TrimSpace(line); l != "" {
			w.log(l)
		}
	}
	return len(p), nil
}
