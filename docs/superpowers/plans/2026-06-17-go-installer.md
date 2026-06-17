# KutOS Go Installer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Python bootstrapper + Calamares'i tamamen kaldır, sıfırdan Go + GTK3 ile profesyonel bir live-ISO installer yaz.

**Architecture:** Tek bir Go binary'si (`kutos-installer`) — `gotk3` ile GTK3 UI, `backend/` paketi ile tüm disk/chroot işlemleri. Binary ISO build sırasında derlenir, `airootfs/usr/local/bin/kutos-installer`'a kopyalanır. Runtime'da internet gerekmez.

**Tech Stack:** Go 1.22+, github.com/gotk3/gotk3 (GTK3 bindings), sgdisk/mkfs/rsync/arch-chroot (sistem araçları, ISO'da mevcut)

---

## Dosya Haritası

### Yeni oluşturulacak

```
kutos-installer-src/
├── main.go                        # Entry point: root check, GTK init, window aç
├── go.mod                         # module kutos/installer + gotk3
├── config/
│   └── config.go                  # InstallConfig struct — tüm sayfalara geçilen shared state
├── backend/
│   ├── disk.go                    # lsblk ile disk listele, sgdisk ile partition, mkfs ile format, mount
│   ├── install.go                 # Kurulum adımları: rsync, genfstab, chroot ops, grub
│   ├── locale.go                  # Timezone ve locale listeleri
│   └── keyboard.go                # Klavye layout listesi (xkb)
└── ui/
    ├── window.go                  # Ana pencere: sidebar + Stack + footer buttons
    ├── style.go                   # Gömülü CSS string
    └── pages/
        ├── welcome.go             # Hoş geldin sayfası
        ├── locale.go              # Timezone/bölge seçimi
        ├── keyboard.go            # Klavye seçimi
        ├── partition.go           # Disk seçimi + partition modu (erase/manual)
        ├── users.go               # Kullanıcı adı, şifre, hostname
        ├── summary.go             # Kurulum özeti, onay
        ├── progress.go            # Kurulum progressi (log stream)
        └── finish.go              # Bitti + reboot butonu
```

### Değiştirilecek

```
build.sh                                           # Go derleme adımı ekle
profiledef.sh                                      # BUG-001 düzelt, Python ref kaldır
airootfs/usr/local/bin/kutos-installer             # Yeni binary launcher
airootfs/root/Desktop/kutos-installer.desktop      # pkexec kutos-installer
airootfs/root/.config/autostart/kutos-installer.desktop  # aynı
airootfs/etc/skel/Desktop/kutos-installer.desktop  # aynı
```

### Silinecek

```
airootfs/usr/local/lib/kutos-bootstrapper/    # Python bootstrapper — tamamen kaldır
airootfs/usr/local/bin/kutos-bootstrapper     # launcher — kaldır
```

### Dokunulmayacak

```
airootfs/usr/local/lib/kutos-settings/        # Settings app — ayrı, kalsın
airootfs/etc/calamares/                       # Calamares config — şimdilik kalsın (ileride silinir)
```

---

## Task 1: Go modülü ve config struct

**Files:**
- Create: `kutos-installer-src/go.mod`
- Create: `kutos-installer-src/config/config.go`

- [ ] **Step 1: go.mod oluştur**

```
kutos-installer-src/
```
dizininde:

```go
// kutos-installer-src/go.mod
module kutos/installer

go 1.22

require github.com/gotk3/gotk3 v0.6.3
```

- [ ] **Step 2: Shared config struct yaz**

```go
// kutos-installer-src/config/config.go
package config

type InstallConfig struct {
	// Disk
	TargetDisk    string // örn: /dev/sda
	PartitionMode string // "erase" | "manual"
	Filesystem    string // "ext4" | "btrfs"
	SwapSize      string // "none" | "2G" | "4G"

	// Locale
	Timezone string // örn: Europe/Istanbul
	Locale   string // örn: tr_TR.UTF-8

	// Keyboard
	KeyboardLayout  string // örn: tr
	KeyboardVariant string // örn: (boş)

	// Users
	Username     string
	Password     string
	RootPassword string
	Hostname     string
	Autologin    bool

	// Bootloader
	InstallGRUB bool
	EFIMode     bool // UEFI mi BIOS mu
}

func New() *InstallConfig {
	return &InstallConfig{
		Filesystem:  "ext4",
		SwapSize:    "none",
		Timezone:    "Europe/Istanbul",
		Locale:      "tr_TR.UTF-8",
		KeyboardLayout: "tr",
		InstallGRUB: true,
		Autologin:   false,
	}
}
```

- [ ] **Step 3: Commit**

```bash
cd kutos-installer-src && git add go.mod config/config.go
git commit -m "feat: go module ve InstallConfig struct"
```

---

## Task 2: Backend — Disk tespiti ve işlemleri

**Files:**
- Create: `kutos-installer-src/backend/disk.go`

- [ ] **Step 1: Disk listele (lsblk JSON parse)**

```go
// kutos-installer-src/backend/disk.go
package backend

import (
	"encoding/json"
	"fmt"
	"os"
	"os/exec"
	"strings"
)

type Disk struct {
	Path  string
	Name  string
	Size  string
	Model string
}

type lsblkOutput struct {
	Blockdevices []struct {
		Name   string `json:"name"`
		Size   string `json:"size"`
		Model  string `json:"model"`
		Type   string `json:"type"`
	} `json:"blockdevices"`
}

func ListDisks() ([]Disk, error) {
	out, err := exec.Command("lsblk", "-d", "-J", "-o", "NAME,SIZE,MODEL,TYPE").Output()
	if err != nil {
		return nil, fmt.Errorf("lsblk: %w", err)
	}

	var parsed lsblkOutput
	if err := json.Unmarshal(out, &parsed); err != nil {
		return nil, fmt.Errorf("lsblk parse: %w", err)
	}

	var disks []Disk
	for _, d := range parsed.Blockdevices {
		if d.Type != "disk" {
			continue
		}
		model := strings.TrimSpace(d.Model)
		if model == "" {
			model = "Unknown"
		}
		disks = append(disks, Disk{
			Path:  "/dev/" + d.Name,
			Name:  d.Name,
			Size:  d.Size,
			Model: model,
		})
	}
	return disks, nil
}
```

- [ ] **Step 2: UEFI mi BIOS mu tespiti**

`disk.go`'ya ekle:

```go
func IsEFI() bool {
	_, err := os.Stat("/sys/firmware/efi")
	return err == nil
}
```

- [ ] **Step 3: Diski partition et**

```go
// "erase" modu: diski tamamen sil, GPT + EFI + root partition oluştur
func PartitionDisk(disk string, efi bool, swapSize string) error {
	// Mevcut partition tablosunu sil
	if err := run("sgdisk", "--zap-all", disk); err != nil {
		return fmt.Errorf("zap: %w", err)
	}

	if efi {
		// EFI partition: 512M, type EF00
		if err := run("sgdisk", "-n", "1:0:+512M", "-t", "1:EF00", "-c", "1:EFI", disk); err != nil {
			return fmt.Errorf("efi partition: %w", err)
		}
		if swapSize != "none" && swapSize != "" {
			// Swap partition: type 8200
			swapEnd := "+" + swapSize
			if err := run("sgdisk", "-n", "2:0:"+swapEnd, "-t", "2:8200", "-c", "2:swap", disk); err != nil {
				return fmt.Errorf("swap partition: %w", err)
			}
			// Root partition: kalan alan, type 8300
			if err := run("sgdisk", "-n", "3:0:0", "-t", "3:8300", "-c", "3:root", disk); err != nil {
				return fmt.Errorf("root partition: %w", err)
			}
		} else {
			// Root partition: kalan alan
			if err := run("sgdisk", "-n", "2:0:0", "-t", "2:8300", "-c", "2:root", disk); err != nil {
				return fmt.Errorf("root partition: %w", err)
			}
		}
	} else {
		// BIOS: MBR tarzı ama GPT kullan, BIOS boot partition
		if err := run("sgdisk", "-n", "1:0:+1M", "-t", "1:EF02", "-c", "1:bios_boot", disk); err != nil {
			return fmt.Errorf("bios boot partition: %w", err)
		}
		if swapSize != "none" && swapSize != "" {
			swapEnd := "+" + swapSize
			if err := run("sgdisk", "-n", "2:0:"+swapEnd, "-t", "2:8200", "-c", "2:swap", disk); err != nil {
				return fmt.Errorf("swap: %w", err)
			}
			if err := run("sgdisk", "-n", "3:0:0", "-t", "3:8300", "-c", "3:root", disk); err != nil {
				return fmt.Errorf("root: %w", err)
			}
		} else {
			if err := run("sgdisk", "-n", "2:0:0", "-t", "2:8300", "-c", "2:root", disk); err != nil {
				return fmt.Errorf("root: %w", err)
			}
		}
	}

	// Kernel partition tablosunu yenile
	_ = run("partprobe", disk)
	return nil
}
```

- [ ] **Step 4: Format işlemleri**

```go
// disk adı + numaradan partition path üret (/dev/sda → /dev/sda1, /dev/nvme0n1 → /dev/nvme0n1p1)
func partPath(disk string, num int) string {
	if strings.Contains(disk, "nvme") || strings.Contains(disk, "mmcblk") {
		return fmt.Sprintf("%sp%d", disk, num)
	}
	return fmt.Sprintf("%s%d", disk, num)
}

func FormatPartitions(disk string, efi bool, fs string, hasSwap bool) error {
	if efi {
		efiPart := partPath(disk, 1)
		if err := run("mkfs.fat", "-F32", "-n", "EFI", efiPart); err != nil {
			return fmt.Errorf("format efi: %w", err)
		}
		if hasSwap {
			swapPart := partPath(disk, 2)
			rootPart := partPath(disk, 3)
			if err := run("mkswap", "-L", "swap", swapPart); err != nil {
				return fmt.Errorf("mkswap: %w", err)
			}
			return formatRoot(rootPart, fs)
		}
		rootPart := partPath(disk, 2)
		return formatRoot(rootPart, fs)
	}
	// BIOS
	if hasSwap {
		swapPart := partPath(disk, 2)
		rootPart := partPath(disk, 3)
		if err := run("mkswap", "-L", "swap", swapPart); err != nil {
			return fmt.Errorf("mkswap: %w", err)
		}
		return formatRoot(rootPart, fs)
	}
	rootPart := partPath(disk, 2)
	return formatRoot(rootPart, fs)
}

func formatRoot(part, fs string) error {
	switch fs {
	case "btrfs":
		return run("mkfs.btrfs", "-f", "-L", "root", part)
	default: // ext4
		return run("mkfs.ext4", "-F", "-L", "root", part)
	}
}
```

- [ ] **Step 5: Mount/Unmount**

```go
const MountPoint = "/mnt"

func MountPartitions(disk string, efi bool, fs string, hasSwap bool) error {
	var rootPart, efiPart, swapPart string

	if efi {
		efiPart = partPath(disk, 1)
		if hasSwap {
			swapPart = partPath(disk, 2)
			rootPart = partPath(disk, 3)
		} else {
			rootPart = partPath(disk, 2)
		}
	} else {
		if hasSwap {
			swapPart = partPath(disk, 2)
			rootPart = partPath(disk, 3)
		} else {
			rootPart = partPath(disk, 2)
		}
	}

	// Root'u mount et
	mountOpts := "defaults,noatime"
	if fs == "btrfs" {
		mountOpts += ",compress=zstd,space_cache=v2"
	}
	if err := run("mount", "-o", mountOpts, rootPart, MountPoint); err != nil {
		return fmt.Errorf("mount root: %w", err)
	}

	// EFI mount
	if efi && efiPart != "" {
		if err := os.MkdirAll(MountPoint+"/boot/efi", 0755); err != nil {
			return err
		}
		if err := run("mount", efiPart, MountPoint+"/boot/efi"); err != nil {
			return fmt.Errorf("mount efi: %w", err)
		}
	}

	// Swap
	if swapPart != "" {
		_ = run("swapon", swapPart)
	}

	return nil
}

func UnmountAll() {
	_ = run("swapoff", "-a")
	_ = run("umount", "-R", MountPoint)
}
```

- [ ] **Step 6: run() yardımcı fonksiyon**

```go
func run(name string, args ...string) error {
	cmd := exec.Command(name, args...)
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	return cmd.Run()
}
```

- [ ] **Step 7: Commit**

```bash
git add backend/disk.go
git commit -m "feat: disk detection, partitioning, formatting, mounting"
```

---

## Task 3: Backend — Locale ve Keyboard listeleri

**Files:**
- Create: `kutos-installer-src/backend/locale.go`
- Create: `kutos-installer-src/backend/keyboard.go`

- [ ] **Step 1: Timezone listesi**

```go
// kutos-installer-src/backend/locale.go
package backend

import (
	"os"
	"path/filepath"
	"sort"
	"strings"
)

func ListTimezones() []string {
	var zones []string
	base := "/usr/share/zoneinfo"

	regions := []string{
		"Africa", "America", "Antarctica", "Arctic", "Asia",
		"Atlantic", "Australia", "Europe", "Indian", "Pacific",
	}

	for _, region := range regions {
		entries, err := os.ReadDir(filepath.Join(base, region))
		if err != nil {
			continue
		}
		for _, e := range entries {
			if !e.IsDir() {
				zones = append(zones, region+"/"+e.Name())
			}
		}
	}

	sort.Strings(zones)
	return zones
}

func ListLocales() []string {
	data, err := os.ReadFile("/etc/locale.gen")
	if err != nil {
		return []string{"tr_TR.UTF-8", "en_US.UTF-8"}
	}

	var locales []string
	for _, line := range strings.Split(string(data), "\n") {
		line = strings.TrimSpace(line)
		if strings.HasPrefix(line, "#") || line == "" {
			continue
		}
		if strings.Contains(line, "UTF-8") {
			parts := strings.Fields(line)
			if len(parts) > 0 {
				locales = append(locales, parts[0])
			}
		}
	}

	if len(locales) == 0 {
		return []string{"tr_TR.UTF-8", "en_US.UTF-8"}
	}
	sort.Strings(locales)
	return locales
}
```

- [ ] **Step 2: Klavye layout listesi**

```go
// kutos-installer-src/backend/keyboard.go
package backend

import (
	"bufio"
	"os"
	"sort"
	"strings"
)

type KeyboardLayout struct {
	Code        string
	Description string
}

func ListKeyboardLayouts() []KeyboardLayout {
	// xkb evren listesini oku
	f, err := os.Open("/usr/share/X11/xkb/rules/evdev.lst")
	if err != nil {
		return []KeyboardLayout{
			{Code: "tr", Description: "Turkish"},
			{Code: "us", Description: "English (US)"},
		}
	}
	defer f.Close()

	var layouts []KeyboardLayout
	inLayouts := false

	scanner := bufio.NewScanner(f)
	for scanner.Scan() {
		line := scanner.Text()
		if strings.HasPrefix(line, "! layout") {
			inLayouts = true
			continue
		}
		if inLayouts && strings.HasPrefix(line, "!") {
			break
		}
		if inLayouts && strings.TrimSpace(line) != "" {
			parts := strings.SplitN(strings.TrimSpace(line), " ", 2)
			if len(parts) == 2 {
				layouts = append(layouts, KeyboardLayout{
					Code:        strings.TrimSpace(parts[0]),
					Description: strings.TrimSpace(parts[1]),
				})
			}
		}
	}

	sort.Slice(layouts, func(i, j int) bool {
		return layouts[i].Description < layouts[j].Description
	})
	return layouts
}
```

- [ ] **Step 3: Commit**

```bash
git add backend/locale.go backend/keyboard.go
git commit -m "feat: locale ve keyboard layout listeleri"
```

---

## Task 4: Backend — Kurulum motoru

**Files:**
- Create: `kutos-installer-src/backend/install.go`

- [ ] **Step 1: Logger arayüzü ve Step tanımları**

```go
// kutos-installer-src/backend/install.go
package backend

import (
	"fmt"
	"io"
	"os"
	"os/exec"
	"strings"

	"kutos/installer/config"
)

// Logger her adımın logunu UI'a iletir
type Logger func(line string)

type InstallStep struct {
	Name string
	Fn   func(cfg *config.InstallConfig, log Logger) error
}

func Steps() []InstallStep {
	return []InstallStep{
		{"Disk bölümleniyor", stepPartition},
		{"Dosya sistemleri oluşturuluyor", stepFormat},
		{"Bölümler mount ediliyor", stepMount},
		{"Sistem kopyalanıyor", stepCopySystem},
		{"fstab oluşturuluyor", stepFstab},
		{"Hostname ayarlanıyor", stepHostname},
		{"Locale ayarlanıyor", stepLocale},
		{"Klavye ayarlanıyor", stepKeyboard},
		{"Kullanıcı oluşturuluyor", stepUsers},
		{"Servisler etkinleştiriliyor", stepServices},
		{"Bootloader kuruluyor", stepBootloader},
		{"Temizlik yapılıyor", stepCleanup},
	}
}
```

- [ ] **Step 2: Partition ve format adımları**

```go
func stepPartition(cfg *config.InstallConfig, log Logger) error {
	log("→ Disk: " + cfg.TargetDisk)
	hasSwap := cfg.SwapSize != "none" && cfg.SwapSize != ""
	return PartitionDisk(cfg.TargetDisk, cfg.EFIMode, cfg.SwapSize)
}

func stepFormat(cfg *config.InstallConfig, log Logger) error {
	hasSwap := cfg.SwapSize != "none" && cfg.SwapSize != ""
	log(fmt.Sprintf("→ Filesystem: %s, Swap: %v", cfg.Filesystem, hasSwap))
	return FormatPartitions(cfg.TargetDisk, cfg.EFIMode, cfg.Filesystem, hasSwap)
}

func stepMount(cfg *config.InstallConfig, log Logger) error {
	hasSwap := cfg.SwapSize != "none" && cfg.SwapSize != ""
	return MountPartitions(cfg.TargetDisk, cfg.EFIMode, cfg.Filesystem, hasSwap)
}
```

- [ ] **Step 3: Sistem kopyalama (rsync)**

```go
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

type logWriter struct {
	log Logger
}

func (w *logWriter) Write(p []byte) (int, error) {
	lines := strings.Split(string(p), "\n")
	for _, l := range lines {
		l = strings.TrimSpace(l)
		if l != "" {
			w.log(l)
		}
	}
	return len(p), nil
}
```

- [ ] **Step 4: fstab, hostname, locale, keyboard**

```go
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
	// locale.gen'de seçili locale'i uncomment et
	data, _ := os.ReadFile(MountPoint + "/etc/locale.gen")
	content := strings.ReplaceAll(string(data), "#"+cfg.Locale, cfg.Locale)
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
	// Timezone
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
```

- [ ] **Step 5: Kullanıcı oluşturma**

```go
func stepUsers(cfg *config.InstallConfig, log Logger) error {
	log("→ Kullanıcı: " + cfg.Username)

	// wheel grubunu sudo için ayarla
	sudoers := "%wheel ALL=(ALL:ALL) ALL\n"
	if err := os.WriteFile(MountPoint+"/etc/sudoers.d/wheel", []byte(sudoers), 0440); err != nil {
		return err
	}

	// Kullanıcı oluştur
	if err := chroot(log, "useradd", "-m", "-G",
		"wheel,audio,video,network,storage,optical,power",
		"-s", "/bin/bash", cfg.Username); err != nil {
		return fmt.Errorf("useradd: %w", err)
	}

	// Kullanıcı şifresi
	if err := chrootInput(cfg.Password+"\n"+cfg.Password+"\n", log, "passwd", cfg.Username); err != nil {
		return fmt.Errorf("passwd user: %w", err)
	}

	// Root şifresi
	if cfg.RootPassword != "" {
		if err := chrootInput(cfg.RootPassword+"\n"+cfg.RootPassword+"\n", log, "passwd"); err != nil {
			return fmt.Errorf("passwd root: %w", err)
		}
	}

	// Autologin (LightDM)
	if cfg.Autologin {
		lightdmConf := fmt.Sprintf("[Seat:*]\nautologin-user=%s\nautologin-user-timeout=0\n", cfg.Username)
		confDir := MountPoint + "/etc/lightdm/lightdm.conf.d"
		if err := os.MkdirAll(confDir, 0755); err != nil {
			return err
		}
		if err := os.WriteFile(confDir+"/50-autologin.conf", []byte(lightdmConf), 0644); err != nil {
			return err
		}
	}

	return nil
}
```

- [ ] **Step 6: Servisler ve Bootloader**

```go
func stepServices(cfg *config.InstallConfig, log Logger) error {
	services := []string{"NetworkManager", "lightdm"}
	for _, svc := range services {
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
	log("→ Bölümler unmount ediliyor")
	// Calamares artık yok — bootstrapper kısayollarını kaldır
	_ = os.Remove(MountPoint + "/root/Desktop/kutos-installer.desktop")
	_ = os.Remove(MountPoint + "/root/.config/autostart/kutos-installer.desktop")
	// Live-only dosyaları temizle
	_ = os.Remove(MountPoint + "/etc/lightdm/lightdm.conf")
	UnmountAll()
	return nil
}
```

- [ ] **Step 7: chroot yardımcıları**

```go
func chroot(log Logger, name string, args ...string) error {
	cmdArgs := append([]string{MountPoint, name}, args...)
	cmd := exec.Command("arch-chroot", cmdArgs...)
	cmd.Stdout = &logWriter{log: log}
	cmd.Stderr = &logWriter{log: log}
	return cmd.Run()
}

func chrootInput(input string, log Logger, name string, args ...string) error {
	cmdArgs := append([]string{MountPoint, name}, args...)
	cmd := exec.Command("arch-chroot", cmdArgs...)
	cmd.Stdin = strings.NewReader(input)
	cmd.Stdout = &logWriter{log: log}
	cmd.Stderr = &logWriter{log: log}
	return cmd.Run()
}
```

- [ ] **Step 8: Commit**

```bash
git add backend/install.go
git commit -m "feat: kurulum motoru — partition, format, rsync, chroot, grub"
```

---

## Task 5: UI — CSS ve Ana Pencere

**Files:**
- Create: `kutos-installer-src/ui/style.go`
- Create: `kutos-installer-src/ui/window.go`

- [ ] **Step 1: CSS**

```go
// kutos-installer-src/ui/style.go
package ui

const AppCSS = `
* {
    font-family: "Inter", "Noto Sans", sans-serif;
    font-size: 14px;
}

window {
    background-color: #09090b;
    color: #fafafa;
}

/* Sidebar */
.sidebar {
    background-color: #0f0f12;
    border-right: 1px solid #1e1e24;
    min-width: 220px;
    padding: 24px 0;
}

.sidebar-logo {
    font-size: 20px;
    font-weight: 700;
    color: #fafafa;
    padding: 0 24px 24px 24px;
    border-bottom: 1px solid #1e1e24;
    margin-bottom: 16px;
}

.sidebar-logo span {
    color: #3b82f6;
}

.step-row {
    padding: 10px 24px;
    border-radius: 0;
    color: #71717a;
    font-size: 13px;
}

.step-row.active {
    color: #fafafa;
    background-color: #1e1e28;
    border-left: 3px solid #3b82f6;
}

.step-row.done {
    color: #4ade80;
}

.step-number {
    width: 24px;
    height: 24px;
    border-radius: 12px;
    background-color: #27272a;
    color: #71717a;
    font-size: 12px;
    font-weight: 600;
    margin-right: 12px;
}

.step-number.active-num {
    background-color: #3b82f6;
    color: #ffffff;
}

.step-number.done-num {
    background-color: #166534;
    color: #4ade80;
}

/* Content area */
.content {
    background-color: #09090b;
    padding: 48px;
}

.page-title {
    font-size: 28px;
    font-weight: 700;
    color: #fafafa;
    margin-bottom: 8px;
}

.page-subtitle {
    font-size: 14px;
    color: #71717a;
    margin-bottom: 32px;
}

/* Form elements */
entry {
    background-color: #18181b;
    border: 1px solid #27272a;
    border-radius: 8px;
    color: #fafafa;
    padding: 10px 14px;
    min-height: 40px;
}

entry:focus {
    border-color: #3b82f6;
    box-shadow: 0 0 0 2px rgba(59,130,246,0.2);
}

label.field-label {
    font-size: 13px;
    font-weight: 500;
    color: #a1a1aa;
    margin-bottom: 6px;
}

/* Buttons */
.btn-primary {
    background-color: #3b82f6;
    color: #ffffff;
    border: none;
    border-radius: 8px;
    padding: 10px 24px;
    font-weight: 600;
    font-size: 14px;
    min-height: 40px;
}

.btn-primary:hover {
    background-color: #2563eb;
}

.btn-secondary {
    background-color: transparent;
    color: #a1a1aa;
    border: 1px solid #27272a;
    border-radius: 8px;
    padding: 10px 24px;
    font-size: 14px;
    min-height: 40px;
}

.btn-secondary:hover {
    background-color: #18181b;
    color: #fafafa;
}

/* Footer */
.footer {
    background-color: #0f0f12;
    border-top: 1px solid #1e1e24;
    padding: 16px 48px;
}

/* List items (disk, timezone, keyboard) */
listbox {
    background-color: transparent;
}

listbox row {
    background-color: #18181b;
    border: 1px solid #27272a;
    border-radius: 8px;
    margin: 3px 0;
    padding: 12px 16px;
    color: #fafafa;
}

listbox row:selected {
    background-color: #1d3a6e;
    border-color: #3b82f6;
}

listbox row:hover {
    background-color: #1e1e28;
}

/* Progress */
.progress-log {
    background-color: #030303;
    border: 1px solid #1e1e24;
    border-radius: 8px;
    color: #4ade80;
    font-family: "JetBrains Mono", "Fira Code", monospace;
    font-size: 12px;
    padding: 16px;
}

progressbar trough {
    background-color: #18181b;
    border-radius: 4px;
    min-height: 8px;
}

progressbar progress {
    background-color: #3b82f6;
    border-radius: 4px;
}

/* Disk cards */
.disk-card {
    background-color: #18181b;
    border: 1px solid #27272a;
    border-radius: 10px;
    padding: 16px;
    margin: 4px 0;
}

.disk-card.selected-card {
    border-color: #3b82f6;
    background-color: #1d3a6e;
}

.disk-name {
    font-size: 15px;
    font-weight: 600;
    color: #fafafa;
}

.disk-info {
    font-size: 12px;
    color: #71717a;
    margin-top: 2px;
}

/* Warning */
.warning-box {
    background-color: #431407;
    border: 1px solid #9a3412;
    border-radius: 8px;
    padding: 12px 16px;
    color: #fb923c;
    font-size: 13px;
}

/* Check button */
checkbutton {
    color: #fafafa;
    font-size: 14px;
}

combobox {
    background-color: #18181b;
    border: 1px solid #27272a;
    border-radius: 8px;
    color: #fafafa;
    min-height: 40px;
}
`
```

- [ ] **Step 2: Ana pencere ve navigasyon**

```go
// kutos-installer-src/ui/window.go
package ui

import (
	"fmt"

	"github.com/gotk3/gotk3/gdk"
	"github.com/gotk3/gotk3/gtk"
	"kutos/installer/config"
	"kutos/installer/ui/pages"
)

type Page interface {
	Widget() gtk.IWidget
	Title() string
	CanProceed() bool
	OnEnter()
}

type MainWindow struct {
	win        *gtk.Window
	cfg        *config.InstallConfig
	stack      *gtk.Stack
	pageList   []Page
	currentIdx int
	btnBack    *gtk.Button
	btnNext    *gtk.Button
	stepRows   []*gtk.Box
	sidebar    *gtk.Box
}

var stepNames = []string{
	"Hoş Geldin",
	"Konum",
	"Klavye",
	"Disk",
	"Kullanıcı",
	"Özet",
	"Kurulum",
	"Bitti",
}

func NewMainWindow(cfg *config.InstallConfig) (*MainWindow, error) {
	win, err := gtk.WindowNew(gtk.WINDOW_TOPLEVEL)
	if err != nil {
		return nil, err
	}

	mw := &MainWindow{win: win, cfg: cfg}
	mw.setupCSS()
	mw.build()

	win.SetTitle("KutOS Installer")
	win.SetDefaultSize(960, 640)
	win.SetPosition(gtk.WIN_POS_CENTER)
	win.Connect("destroy", gtk.MainQuit)

	return mw, nil
}

func (mw *MainWindow) setupCSS() {
	provider, _ := gtk.CssProviderNew()
	_ = provider.LoadFromData(AppCSS)
	screen, _ := gdk.ScreenGetDefault()
	gtk.AddProviderForScreen(screen, provider, gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
}

func (mw *MainWindow) build() {
	// Ana yatay kutu: sidebar | content
	hbox, _ := gtk.BoxNew(gtk.ORIENTATION_HORIZONTAL, 0)
	mw.win.Add(hbox)

	// Sidebar
	sidebar := mw.buildSidebar()
	hbox.PackStart(sidebar, false, false, 0)

	// Sağ taraf: stack + footer
	vbox, _ := gtk.BoxNew(gtk.ORIENTATION_VERTICAL, 0)
	hbox.PackStart(vbox, true, true, 0)

	// Stack (sayfa içerikleri)
	stack, _ := gtk.StackNew()
	stack.SetTransitionType(gtk.STACK_TRANSITION_TYPE_SLIDE_LEFT_RIGHT)
	stack.SetTransitionDuration(200)
	mw.stack = stack

	contentScroll, _ := gtk.ScrolledWindowNew(nil, nil)
	contentScroll.SetPolicy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
	contentScroll.Add(stack)
	contentScroll.GetStyleContext().AddClass("content")

	vbox.PackStart(contentScroll, true, true, 0)

	// Footer
	footer := mw.buildFooter()
	vbox.PackStart(footer, false, false, 0)
}

func (mw *MainWindow) buildSidebar() *gtk.Box {
	sidebar, _ := gtk.BoxNew(gtk.ORIENTATION_VERTICAL, 0)
	sidebar.GetStyleContext().AddClass("sidebar")
	mw.sidebar = sidebar

	// Logo
	logoBox, _ := gtk.BoxNew(gtk.ORIENTATION_HORIZONTAL, 0)
	logoBox.GetStyleContext().AddClass("sidebar-logo")
	logoLbl, _ := gtk.LabelNew("Kut")
	logoBox.PackStart(logoLbl, false, false, 0)
	logoAccent, _ := gtk.LabelNew("OS")
	logoAccent.GetStyleContext().AddClass("accent")
	logoBox.PackStart(logoAccent, false, false, 0)
	sidebar.PackStart(logoBox, false, false, 0)

	// Step listesi
	mw.stepRows = make([]*gtk.Box, len(stepNames))
	for i, name := range stepNames {
		row := mw.buildStepRow(i, name)
		mw.stepRows[i] = row
		sidebar.PackStart(row, false, false, 0)
	}

	return sidebar
}

func (mw *MainWindow) buildStepRow(idx int, name string) *gtk.Box {
	row, _ := gtk.BoxNew(gtk.ORIENTATION_HORIZONTAL, 0)
	row.GetStyleContext().AddClass("step-row")

	numLbl, _ := gtk.LabelNew(fmt.Sprintf("%d", idx+1))
	numLbl.GetStyleContext().AddClass("step-number")
	row.PackStart(numLbl, false, false, 0)

	nameLbl, _ := gtk.LabelNew(name)
	row.PackStart(nameLbl, false, false, 0)

	return row
}

func (mw *MainWindow) buildFooter() *gtk.Box {
	footer, _ := gtk.BoxNew(gtk.ORIENTATION_HORIZONTAL, 12)
	footer.GetStyleContext().AddClass("footer")

	mw.btnBack, _ = gtk.ButtonNewWithLabel("← Geri")
	mw.btnBack.GetStyleContext().AddClass("btn-secondary")
	mw.btnBack.Connect("clicked", mw.goBack)
	footer.PackStart(mw.btnBack, false, false, 0)

	spacer, _ := gtk.BoxNew(gtk.ORIENTATION_HORIZONTAL, 0)
	footer.PackStart(spacer, true, true, 0)

	mw.btnNext, _ = gtk.ButtonNewWithLabel("İleri →")
	mw.btnNext.GetStyleContext().AddClass("btn-primary")
	mw.btnNext.Connect("clicked", mw.goNext)
	footer.PackEnd(mw.btnNext, false, false, 0)

	return footer
}

func (mw *MainWindow) SetPages(ps []Page) {
	mw.pageList = ps
	for i, p := range ps {
		mw.stack.AddNamed(p.Widget(), fmt.Sprintf("page-%d", i))
	}
	mw.goTo(0)
}

func (mw *MainWindow) goTo(idx int) {
	if idx < 0 || idx >= len(mw.pageList) {
		return
	}
	mw.currentIdx = idx
	mw.stack.SetVisibleChildName(fmt.Sprintf("page-%d", idx))
	mw.pageList[idx].OnEnter()
	mw.updateUI()
}

func (mw *MainWindow) updateUI() {
	idx := mw.currentIdx
	total := len(mw.pageList)
	isLast := idx == total-1

	mw.btnBack.SetSensitive(idx > 0 && idx < total-1)

	if isLast {
		mw.btnNext.SetLabel("Kapat")
		mw.btnNext.SetSensitive(true)
	} else if idx == total-2 {
		// Progress sayfası — buton install tarafından yönetilir
		mw.btnNext.SetSensitive(false)
	} else {
		mw.btnNext.SetLabel("İleri →")
		mw.btnNext.SetSensitive(mw.pageList[idx].CanProceed())
	}

	// Sidebar güncelle
	for i, row := range mw.stepRows {
		sc := row.GetStyleContext()
		sc.RemoveClass("active")
		sc.RemoveClass("done")
		if i < idx {
			sc.AddClass("done")
		} else if i == idx {
			sc.AddClass("active")
		}
	}
}

func (mw *MainWindow) goNext() {
	if mw.currentIdx == len(mw.pageList)-1 {
		gtk.MainQuit()
		return
	}
	if !mw.pageList[mw.currentIdx].CanProceed() {
		return
	}
	mw.goTo(mw.currentIdx + 1)
}

func (mw *MainWindow) goBack() {
	mw.goTo(mw.currentIdx - 1)
}

func (mw *MainWindow) EnableNext() {
	mw.btnNext.SetSensitive(true)
	mw.btnNext.SetLabel("İleri →")
}

func (mw *MainWindow) Show() {
	mw.win.ShowAll()
}
```

- [ ] **Step 3: Commit**

```bash
git add ui/style.go ui/window.go
git commit -m "feat: ana pencere, sidebar navigasyon, CSS"
```

---

## Task 6: UI Sayfaları

**Files:**
- Create: `kutos-installer-src/ui/pages/welcome.go`
- Create: `kutos-installer-src/ui/pages/locale.go`
- Create: `kutos-installer-src/ui/pages/keyboard.go`
- Create: `kutos-installer-src/ui/pages/partition.go`
- Create: `kutos-installer-src/ui/pages/users.go`
- Create: `kutos-installer-src/ui/pages/summary.go`
- Create: `kutos-installer-src/ui/pages/progress.go`
- Create: `kutos-installer-src/ui/pages/finish.go`

- [ ] **Step 1: Welcome sayfası**

```go
// kutos-installer-src/ui/pages/welcome.go
package pages

import (
	"github.com/gotk3/gotk3/gtk"
	"kutos/installer/config"
)

type WelcomePage struct {
	box *gtk.Box
	cfg *config.InstallConfig
}

func NewWelcomePage(cfg *config.InstallConfig) *WelcomePage {
	return &WelcomePage{cfg: cfg}
}

func (p *WelcomePage) Widget() gtk.IWidget {
	if p.box != nil {
		return p.box
	}
	box, _ := gtk.BoxNew(gtk.ORIENTATION_VERTICAL, 0)
	box.SetValign(gtk.ALIGN_CENTER)
	box.SetMarginTop(60)
	box.SetMarginStart(60)

	title, _ := gtk.LabelNew("KutOS'a Hoş Geldiniz")
	title.GetStyleContext().AddClass("page-title")
	title.SetXalign(0)
	box.PackStart(title, false, false, 0)

	sub, _ := gtk.LabelNew("Bu sihirbaz KutOS'u diskinize kuracak. Devam etmek için İleri'ye basın.")
	sub.GetStyleContext().AddClass("page-subtitle")
	sub.SetXalign(0)
	sub.SetLineWrap(true)
	box.PackStart(sub, false, false, 8)

	// Bilgi kutuları
	for _, item := range []struct{ icon, text string }{
		{"⏱", "Kurulum yaklaşık 5-10 dakika sürer"},
		{"💾", "En az 8 GB disk alanı gereklidir"},
		{"⚠️", "Hedef disk silinecektir — yedek alın!"},
	} {
		row, _ := gtk.BoxNew(gtk.ORIENTATION_HORIZONTAL, 12)
		row.SetMarginTop(8)
		icon, _ := gtk.LabelNew(item.icon)
		row.PackStart(icon, false, false, 0)
		lbl, _ := gtk.LabelNew(item.text)
		lbl.SetXalign(0)
		row.PackStart(lbl, false, false, 0)
		box.PackStart(row, false, false, 0)
	}

	p.box = box
	return box
}

func (p *WelcomePage) Title() string     { return "Hoş Geldin" }
func (p *WelcomePage) CanProceed() bool  { return true }
func (p *WelcomePage) OnEnter()          {}
```

- [ ] **Step 2: Locale sayfası**

```go
// kutos-installer-src/ui/pages/locale.go
package pages

import (
	"strings"

	"github.com/gotk3/gotk3/gtk"
	"kutos/installer/backend"
	"kutos/installer/config"
)

type LocalePage struct {
	box      *gtk.Box
	cfg      *config.InstallConfig
	selected string
}

func NewLocalePage(cfg *config.InstallConfig) *LocalePage {
	return &LocalePage{cfg: cfg, selected: cfg.Timezone}
}

func (p *LocalePage) Widget() gtk.IWidget {
	if p.box != nil {
		return p.box
	}
	box, _ := gtk.BoxNew(gtk.ORIENTATION_VERTICAL, 0)
	box.SetMarginTop(48)
	box.SetMarginStart(48)
	box.SetMarginEnd(48)

	title, _ := gtk.LabelNew("Konum ve Zaman Dilimi")
	title.GetStyleContext().AddClass("page-title")
	title.SetXalign(0)
	box.PackStart(title, false, false, 0)

	sub, _ := gtk.LabelNew("Zaman diliminizi seçin")
	sub.GetStyleContext().AddClass("page-subtitle")
	sub.SetXalign(0)
	box.PackStart(sub, false, false, 8)

	// Arama
	search, _ := gtk.SearchEntryNew()
	search.SetPlaceholderText("Ara... örn: Istanbul")
	box.PackStart(search, false, false, 0)

	// Liste
	scroll, _ := gtk.ScrolledWindowNew(nil, nil)
	scroll.SetPolicy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
	scroll.SetMinContentHeight(300)

	listbox, _ := gtk.ListBoxNew()
	listbox.SetSelectionMode(gtk.SELECTION_SINGLE)
	scroll.Add(listbox)
	box.PackStart(scroll, true, true, 12)

	zones := backend.ListTimezones()
	for _, z := range zones {
		row, _ := gtk.ListBoxRowNew()
		lbl, _ := gtk.LabelNew(z)
		lbl.SetXalign(0)
		row.Add(lbl)
		listbox.Add(row)
		// Default seçimi highlight et
		if z == p.cfg.Timezone {
			listbox.SelectRow(row)
		}
	}

	listbox.Connect("row-selected", func(_ *gtk.ListBox, row *gtk.ListBoxRow) {
		if row == nil {
			return
		}
		idx := row.GetIndex()
		if idx >= 0 && idx < len(zones) {
			p.selected = zones[idx]
			p.cfg.Timezone = p.selected
		}
	})

	// Arama filtresi
	search.Connect("search-changed", func(e *gtk.SearchEntry) {
		text, _ := e.GetText()
		text = strings.ToLower(text)
		listbox.SetFilterFunc(func(row *gtk.ListBoxRow) bool {
			if text == "" {
				return true
			}
			child, _ := row.GetChild()
			if lbl, ok := child.(*gtk.Label); ok {
				t, _ := lbl.GetText()
				return strings.Contains(strings.ToLower(t), text)
			}
			return true
		})
	})

	p.box = box
	return box
}

func (p *LocalePage) Title() string    { return "Konum" }
func (p *LocalePage) CanProceed() bool { return p.selected != "" }
func (p *LocalePage) OnEnter()         {}
```

- [ ] **Step 3: Keyboard sayfası**

```go
// kutos-installer-src/ui/pages/keyboard.go
package pages

import (
	"strings"

	"github.com/gotk3/gotk3/gtk"
	"kutos/installer/backend"
	"kutos/installer/config"
)

type KeyboardPage struct {
	box      *gtk.Box
	cfg      *config.InstallConfig
	layouts  []backend.KeyboardLayout
	selected string
}

func NewKeyboardPage(cfg *config.InstallConfig) *KeyboardPage {
	return &KeyboardPage{cfg: cfg, selected: cfg.KeyboardLayout}
}

func (p *KeyboardPage) Widget() gtk.IWidget {
	if p.box != nil {
		return p.box
	}
	box, _ := gtk.BoxNew(gtk.ORIENTATION_VERTICAL, 0)
	box.SetMarginTop(48)
	box.SetMarginStart(48)
	box.SetMarginEnd(48)

	title, _ := gtk.LabelNew("Klavye Düzeni")
	title.GetStyleContext().AddClass("page-title")
	title.SetXalign(0)
	box.PackStart(title, false, false, 0)

	sub, _ := gtk.LabelNew("Klavye düzeninizi seçin")
	sub.GetStyleContext().AddClass("page-subtitle")
	sub.SetXalign(0)
	box.PackStart(sub, false, false, 8)

	// Arama
	search, _ := gtk.SearchEntryNew()
	search.SetPlaceholderText("Ara... örn: Turkish")
	box.PackStart(search, false, false, 0)

	scroll, _ := gtk.ScrolledWindowNew(nil, nil)
	scroll.SetPolicy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
	scroll.SetMinContentHeight(300)

	listbox, _ := gtk.ListBoxNew()
	scroll.Add(listbox)
	box.PackStart(scroll, true, true, 12)

	p.layouts = backend.ListKeyboardLayouts()
	for _, l := range p.layouts {
		row, _ := gtk.ListBoxRowNew()
		lbl, _ := gtk.LabelNew(l.Description + " (" + l.Code + ")")
		lbl.SetXalign(0)
		row.Add(lbl)
		listbox.Add(row)
		if l.Code == p.cfg.KeyboardLayout {
			listbox.SelectRow(row)
		}
	}

	listbox.Connect("row-selected", func(_ *gtk.ListBox, row *gtk.ListBoxRow) {
		if row == nil {
			return
		}
		idx := row.GetIndex()
		if idx >= 0 && idx < len(p.layouts) {
			p.selected = p.layouts[idx].Code
			p.cfg.KeyboardLayout = p.selected
		}
	})

	search.Connect("search-changed", func(e *gtk.SearchEntry) {
		text, _ := e.GetText()
		text = strings.ToLower(text)
		listbox.SetFilterFunc(func(row *gtk.ListBoxRow) bool {
			if text == "" {
				return true
			}
			child, _ := row.GetChild()
			if lbl, ok := child.(*gtk.Label); ok {
				t, _ := lbl.GetText()
				return strings.Contains(strings.ToLower(t), text)
			}
			return true
		})
	})

	p.box = box
	return box
}

func (p *KeyboardPage) Title() string    { return "Klavye" }
func (p *KeyboardPage) CanProceed() bool { return p.selected != "" }
func (p *KeyboardPage) OnEnter()         {}
```

- [ ] **Step 4: Partition sayfası**

```go
// kutos-installer-src/ui/pages/partition.go
package pages

import (
	"fmt"

	"github.com/gotk3/gotk3/gtk"
	"kutos/installer/backend"
	"kutos/installer/config"
)

type PartitionPage struct {
	box      *gtk.Box
	cfg      *config.InstallConfig
	disks    []backend.Disk
	rows     []*gtk.ListBoxRow
	listbox  *gtk.ListBox
}

func NewPartitionPage(cfg *config.InstallConfig) *PartitionPage {
	return &PartitionPage{cfg: cfg}
}

func (p *PartitionPage) Widget() gtk.IWidget {
	if p.box != nil {
		return p.box
	}
	box, _ := gtk.BoxNew(gtk.ORIENTATION_VERTICAL, 0)
	box.SetMarginTop(48)
	box.SetMarginStart(48)
	box.SetMarginEnd(48)

	title, _ := gtk.LabelNew("Disk Seçimi")
	title.GetStyleContext().AddClass("page-title")
	title.SetXalign(0)
	box.PackStart(title, false, false, 0)

	sub, _ := gtk.LabelNew("KutOS'un kurulacağı diski seçin")
	sub.GetStyleContext().AddClass("page-subtitle")
	sub.SetXalign(0)
	box.PackStart(sub, false, false, 8)

	// Disk listesi
	scroll, _ := gtk.ScrolledWindowNew(nil, nil)
	scroll.SetPolicy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
	scroll.SetMinContentHeight(200)

	p.listbox, _ = gtk.ListBoxNew()
	scroll.Add(p.listbox)
	box.PackStart(scroll, false, false, 0)

	// Filesystem seçimi
	fsBox, _ := gtk.BoxNew(gtk.ORIENTATION_HORIZONTAL, 12)
	fsBox.SetMarginTop(16)
	fsLbl, _ := gtk.LabelNew("Dosya sistemi:")
	fsLbl.GetStyleContext().AddClass("field-label")
	fsBox.PackStart(fsLbl, false, false, 0)

	fsCombo, _ := gtk.ComboBoxTextNew()
	fsCombo.AppendText("ext4")
	fsCombo.AppendText("btrfs")
	fsCombo.SetActive(0)
	fsCombo.Connect("changed", func(c *gtk.ComboBoxText) {
		p.cfg.Filesystem = c.GetActiveText()
	})
	fsBox.PackStart(fsCombo, false, false, 0)
	box.PackStart(fsBox, false, false, 0)

	// Swap seçimi
	swapBox, _ := gtk.BoxNew(gtk.ORIENTATION_HORIZONTAL, 12)
	swapBox.SetMarginTop(8)
	swapLbl, _ := gtk.LabelNew("Swap:")
	swapLbl.GetStyleContext().AddClass("field-label")
	swapBox.PackStart(swapLbl, false, false, 0)

	swapCombo, _ := gtk.ComboBoxTextNew()
	for _, s := range []string{"none", "2G", "4G", "8G"} {
		swapCombo.AppendText(s)
	}
	swapCombo.SetActive(0)
	swapCombo.Connect("changed", func(c *gtk.ComboBoxText) {
		p.cfg.SwapSize = c.GetActiveText()
	})
	swapBox.PackStart(swapCombo, false, false, 0)
	box.PackStart(swapBox, false, false, 0)

	// Uyarı
	warn, _ := gtk.LabelNew("⚠  Seçilen disk tamamen silinecektir!")
	warn.GetStyleContext().AddClass("warning-box")
	warn.SetMarginTop(16)
	box.PackStart(warn, false, false, 0)

	p.listbox.Connect("row-selected", func(_ *gtk.ListBox, row *gtk.ListBoxRow) {
		if row == nil {
			return
		}
		idx := row.GetIndex()
		if idx >= 0 && idx < len(p.disks) {
			p.cfg.TargetDisk = p.disks[idx].Path
		}
	})

	p.box = box
	return box
}

func (p *PartitionPage) OnEnter() {
	// Diskleri her sayfa açıldığında yeniden tara
	disks, err := backend.ListDisks()
	if err != nil || len(disks) == 0 {
		return
	}
	p.disks = disks

	// Listeyi temizle ve doldur
	for _, child := range p.listbox.GetChildren() {
		p.listbox.Remove(child)
	}

	for _, d := range disks {
		row, _ := gtk.ListBoxRowNew()
		vbox, _ := gtk.BoxNew(gtk.ORIENTATION_VERTICAL, 2)
		vbox.GetStyleContext().AddClass("disk-card")

		nameLbl, _ := gtk.LabelNew(fmt.Sprintf("%s  —  %s", d.Path, d.Size))
		nameLbl.GetStyleContext().AddClass("disk-name")
		nameLbl.SetXalign(0)
		vbox.PackStart(nameLbl, false, false, 0)

		modelLbl, _ := gtk.LabelNew(d.Model)
		modelLbl.GetStyleContext().AddClass("disk-info")
		modelLbl.SetXalign(0)
		vbox.PackStart(modelLbl, false, false, 0)

		row.Add(vbox)
		p.listbox.Add(row)
	}
	p.listbox.ShowAll()

	// EFI durumunu otomatik tespit et
	p.cfg.EFIMode = backend.IsEFI()
}

func (p *PartitionPage) Title() string    { return "Disk" }
func (p *PartitionPage) CanProceed() bool { return p.cfg.TargetDisk != "" }
```

- [ ] **Step 5: Users sayfası**

```go
// kutos-installer-src/ui/pages/users.go
package pages

import (
	"strings"

	"github.com/gotk3/gotk3/gtk"
	"kutos/installer/config"
)

type UsersPage struct {
	box *gtk.Box
	cfg *config.InstallConfig
	// field refs for CanProceed
	userEntry     *gtk.Entry
	passEntry     *gtk.Entry
	pass2Entry    *gtk.Entry
	rootPassEntry *gtk.Entry
	hostEntry     *gtk.Entry
	errorLbl      *gtk.Label
}

func NewUsersPage(cfg *config.InstallConfig) *UsersPage {
	return &UsersPage{cfg: cfg}
}

func (p *UsersPage) Widget() gtk.IWidget {
	if p.box != nil {
		return p.box
	}
	box, _ := gtk.BoxNew(gtk.ORIENTATION_VERTICAL, 0)
	box.SetMarginTop(48)
	box.SetMarginStart(48)
	box.SetMarginEnd(48)

	title, _ := gtk.LabelNew("Kullanıcı Ayarları")
	title.GetStyleContext().AddClass("page-title")
	title.SetXalign(0)
	box.PackStart(title, false, false, 0)

	sub, _ := gtk.LabelNew("Sisteminiz için bir kullanıcı oluşturun")
	sub.GetStyleContext().AddClass("page-subtitle")
	sub.SetXalign(0)
	box.PackStart(sub, false, false, 8)

	form, _ := gtk.BoxNew(gtk.ORIENTATION_VERTICAL, 8)
	box.PackStart(form, false, false, 0)

	p.userEntry = p.addField(form, "Kullanıcı Adı", false)
	p.passEntry = p.addField(form, "Şifre", true)
	p.pass2Entry = p.addField(form, "Şifre Tekrar", true)
	p.rootPassEntry = p.addField(form, "Root Şifresi", true)
	p.hostEntry = p.addField(form, "Bilgisayar Adı (hostname)", false)

	// Autologin
	autoCheck, _ := gtk.CheckButtonNewWithLabel("Otomatik giriş yap")
	autoCheck.Connect("toggled", func(c *gtk.CheckButton) {
		p.cfg.Autologin = c.GetActive()
	})
	form.PackStart(autoCheck, false, false, 4)

	// Hata mesajı
	p.errorLbl, _ = gtk.LabelNew("")
	p.errorLbl.GetStyleContext().AddClass("warning-box")
	p.errorLbl.SetVisible(false)
	box.PackStart(p.errorLbl, false, false, 8)

	// Değişiklik dinleyicileri
	for _, e := range []*gtk.Entry{p.userEntry, p.passEntry, p.pass2Entry, p.hostEntry} {
		e.Connect("changed", func() { p.validate() })
	}

	p.box = box
	return box
}

func (p *UsersPage) addField(parent *gtk.Box, label string, secret bool) *gtk.Entry {
	vbox, _ := gtk.BoxNew(gtk.ORIENTATION_VERTICAL, 4)
	lbl, _ := gtk.LabelNew(label)
	lbl.GetStyleContext().AddClass("field-label")
	lbl.SetXalign(0)
	vbox.PackStart(lbl, false, false, 0)

	entry, _ := gtk.EntryNew()
	if secret {
		entry.SetVisibility(false)
		entry.SetInvisibleChar('•')
	}
	vbox.PackStart(entry, false, false, 0)
	parent.PackStart(vbox, false, false, 0)
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
	p.cfg.RootPassword = rootPass
	p.cfg.Hostname = host

	var errMsg string
	switch {
	case strings.Contains(user, " ") || user == "":
		errMsg = "Kullanıcı adı boşluk içeremez ve boş olamaz"
	case len(pass) < 4:
		errMsg = "Şifre en az 4 karakter olmalı"
	case pass != pass2:
		errMsg = "Şifreler eşleşmiyor"
	case host == "":
		errMsg = "Hostname boş olamaz"
	}

	if errMsg != "" {
		p.errorLbl.SetText("⚠  " + errMsg)
		p.errorLbl.SetVisible(true)
	} else {
		p.errorLbl.SetVisible(false)
	}
}

func (p *UsersPage) Title() string { return "Kullanıcı" }
func (p *UsersPage) OnEnter()      {}
func (p *UsersPage) CanProceed() bool {
	user, _ := p.userEntry.GetText()
	pass, _ := p.passEntry.GetText()
	pass2, _ := p.pass2Entry.GetText()
	host, _ := p.hostEntry.GetText()
	return user != "" &&
		!strings.Contains(user, " ") &&
		len(pass) >= 4 &&
		pass == pass2 &&
		host != ""
}
```

- [ ] **Step 6: Summary sayfası**

```go
// kutos-installer-src/ui/pages/summary.go
package pages

import (
	"fmt"

	"github.com/gotk3/gotk3/gtk"
	"kutos/installer/config"
)

type SummaryPage struct {
	box *gtk.Box
	cfg *config.InstallConfig
}

func NewSummaryPage(cfg *config.InstallConfig) *SummaryPage {
	return &SummaryPage{cfg: cfg}
}

func (p *SummaryPage) Widget() gtk.IWidget {
	if p.box != nil {
		return p.box
	}
	box, _ := gtk.BoxNew(gtk.ORIENTATION_VERTICAL, 0)
	box.SetMarginTop(48)
	box.SetMarginStart(48)
	box.SetMarginEnd(48)

	title, _ := gtk.LabelNew("Kurulum Özeti")
	title.GetStyleContext().AddClass("page-title")
	title.SetXalign(0)
	box.PackStart(title, false, false, 0)

	sub, _ := gtk.LabelNew("Aşağıdaki ayarlarla kurulum başlayacak. Kontrol edin ve onaylayın.")
	sub.GetStyleContext().AddClass("page-subtitle")
	sub.SetXalign(0)
	sub.SetLineWrap(true)
	box.PackStart(sub, false, false, 8)

	p.box = box
	return box
}

func (p *SummaryPage) OnEnter() {
	// Önceki summary widget'larını temizle (sayfa her ziyarette güncellenmeli)
	for _, child := range p.box.GetChildren() {
		ctx, _ := child.GetStyleContext()
		if ctx.HasClass("summary-items") {
			p.box.Remove(child)
		}
	}

	items, _ := gtk.BoxNew(gtk.ORIENTATION_VERTICAL, 6)
	items.GetStyleContext().AddClass("summary-items")

	rows := []struct{ label, value string }{
		{"Disk", fmt.Sprintf("%s (tüm veriler silinecek!)", p.cfg.TargetDisk)},
		{"Dosya Sistemi", p.cfg.Filesystem},
		{"Swap", p.cfg.SwapSize},
		{"Kullanıcı", p.cfg.Username},
		{"Hostname", p.cfg.Hostname},
		{"Zaman Dilimi", p.cfg.Timezone},
		{"Klavye", p.cfg.KeyboardLayout},
		{"EFI Modu", fmt.Sprintf("%v", p.cfg.EFIMode)},
	}

	for _, r := range rows {
		row, _ := gtk.BoxNew(gtk.ORIENTATION_HORIZONTAL, 0)
		lbl, _ := gtk.LabelNew(r.label)
		lbl.GetStyleContext().AddClass("field-label")
		lbl.SetSizeRequest(160, -1)
		lbl.SetXalign(0)
		row.PackStart(lbl, false, false, 0)
		val, _ := gtk.LabelNew(r.value)
		val.SetXalign(0)
		val.SetLineWrap(true)
		row.PackStart(val, true, true, 0)
		items.PackStart(row, false, false, 0)
	}

	warn, _ := gtk.LabelNew("⚠  Kurulum geri alınamaz. Diskinizdeki tüm veriler silinecek!")
	warn.GetStyleContext().AddClass("warning-box")
	warn.SetMarginTop(16)
	warn.SetLineWrap(true)
	items.PackStart(warn, false, false, 0)

	p.box.PackStart(items, false, false, 0)
	p.box.ShowAll()
}

func (p *SummaryPage) Title() string    { return "Özet" }
func (p *SummaryPage) CanProceed() bool { return true }
```

- [ ] **Step 7: Progress sayfası**

```go
// kutos-installer-src/ui/pages/progress.go
package pages

import (
	"fmt"

	"github.com/gotk3/gotk3/glib"
	"github.com/gotk3/gotk3/gtk"
	"kutos/installer/backend"
	"kutos/installer/config"
)

type ProgressPage struct {
	box         *gtk.Box
	cfg         *config.InstallConfig
	textView    *gtk.TextView
	progressBar *gtk.ProgressBar
	stepLbl     *gtk.Label
	onDone      func()
	started     bool
}

func NewProgressPage(cfg *config.InstallConfig, onDone func()) *ProgressPage {
	return &ProgressPage{cfg: cfg, onDone: onDone}
}

func (p *ProgressPage) Widget() gtk.IWidget {
	if p.box != nil {
		return p.box
	}
	box, _ := gtk.BoxNew(gtk.ORIENTATION_VERTICAL, 0)
	box.SetMarginTop(48)
	box.SetMarginStart(48)
	box.SetMarginEnd(48)

	title, _ := gtk.LabelNew("Kurulum")
	title.GetStyleContext().AddClass("page-title")
	title.SetXalign(0)
	box.PackStart(title, false, false, 0)

	p.stepLbl, _ = gtk.LabelNew("Başlatılıyor...")
	p.stepLbl.GetStyleContext().AddClass("page-subtitle")
	p.stepLbl.SetXalign(0)
	box.PackStart(p.stepLbl, false, false, 4)

	p.progressBar, _ = gtk.ProgressBarNew()
	box.PackStart(p.progressBar, false, false, 8)

	// Log alanı
	scroll, _ := gtk.ScrolledWindowNew(nil, nil)
	scroll.SetPolicy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
	scroll.SetMinContentHeight(300)

	p.textView, _ = gtk.TextViewNew()
	p.textView.SetEditable(false)
	p.textView.SetCursorVisible(false)
	p.textView.GetStyleContext().AddClass("progress-log")
	scroll.Add(p.textView)
	box.PackStart(scroll, true, true, 0)

	p.box = box
	return box
}

func (p *ProgressPage) appendLog(line string) {
	glib.IdleAdd(func() {
		buf, _ := p.textView.GetBuffer()
		end := buf.GetEndIter()
		buf.Insert(end, line+"\n")
		// Scroll to bottom
		mark := buf.GetInsert()
		p.textView.ScrollToMark(mark, 0, false, 0, 0)
	})
}

func (p *ProgressPage) OnEnter() {
	if p.started {
		return
	}
	p.started = true
	go p.runInstall()
}

func (p *ProgressPage) runInstall() {
	steps := backend.Steps()
	total := len(steps)

	for i, step := range steps {
		glib.IdleAdd(func() {
			p.stepLbl.SetText(fmt.Sprintf("[%d/%d] %s", i+1, total, step.Name))
			p.progressBar.SetFraction(float64(i) / float64(total))
		})

		p.appendLog(fmt.Sprintf("\n=== %s ===", step.Name))

		if err := step.Fn(p.cfg, p.appendLog); err != nil {
			p.appendLog("HATA: " + err.Error())
			glib.IdleAdd(func() {
				p.stepLbl.SetText("Kurulum başarısız: " + err.Error())
				p.progressBar.SetFraction(0)
			})
			return
		}
	}

	glib.IdleAdd(func() {
		p.progressBar.SetFraction(1.0)
		p.stepLbl.SetText("Kurulum tamamlandı!")
		if p.onDone != nil {
			p.onDone()
		}
	})
}

func (p *ProgressPage) Title() string    { return "Kurulum" }
func (p *ProgressPage) CanProceed() bool { return false }
```

- [ ] **Step 8: Finish sayfası**

```go
// kutos-installer-src/ui/pages/finish.go
package pages

import (
	"os/exec"

	"github.com/gotk3/gotk3/gtk"
	"kutos/installer/config"
)

type FinishPage struct {
	box *gtk.Box
	cfg *config.InstallConfig
}

func NewFinishPage(cfg *config.InstallConfig) *FinishPage {
	return &FinishPage{cfg: cfg}
}

func (p *FinishPage) Widget() gtk.IWidget {
	if p.box != nil {
		return p.box
	}
	box, _ := gtk.BoxNew(gtk.ORIENTATION_VERTICAL, 0)
	box.SetValign(gtk.ALIGN_CENTER)
	box.SetHalign(gtk.ALIGN_CENTER)
	box.SetSpacing(16)

	icon, _ := gtk.LabelNew("✓")
	icon.SetMarkup(`<span font="48" foreground="#4ade80">✓</span>`)
	box.PackStart(icon, false, false, 0)

	title, _ := gtk.LabelNew("KutOS Kuruldu!")
	title.GetStyleContext().AddClass("page-title")
	box.PackStart(title, false, false, 0)

	sub, _ := gtk.LabelNew("Sisteminiz başarıyla kuruldu. Şimdi yeniden başlatabilirsiniz.")
	sub.GetStyleContext().AddClass("page-subtitle")
	sub.SetLineWrap(true)
	box.PackStart(sub, false, false, 0)

	rebootBtn, _ := gtk.ButtonNewWithLabel("Yeniden Başlat")
	rebootBtn.GetStyleContext().AddClass("btn-primary")
	rebootBtn.Connect("clicked", func() {
		_ = exec.Command("systemctl", "reboot").Run()
	})
	box.PackStart(rebootBtn, false, false, 8)

	p.box = box
	return box
}

func (p *FinishPage) Title() string    { return "Bitti" }
func (p *FinishPage) CanProceed() bool { return true }
func (p *FinishPage) OnEnter()         {}
```

- [ ] **Step 9: Commit**

```bash
git add ui/pages/
git commit -m "feat: tüm UI sayfaları (welcome, locale, keyboard, partition, users, summary, progress, finish)"
```

---

## Task 7: main.go — Hepsini bağla

**Files:**
- Create: `kutos-installer-src/main.go`

- [ ] **Step 1: main.go yaz**

```go
// kutos-installer-src/main.go
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
		fmt.Fprintln(os.Stderr, "KutOS Installer root yetkisi gerektiriyor. pkexec ile çalıştırın.")
		os.Exit(1)
	}

	gtk.Init(nil)

	cfg := config.New()

	win, err := ui.NewMainWindow(cfg)
	if err != nil {
		fmt.Fprintln(os.Stderr, "Pencere oluşturulamadı:", err)
		os.Exit(1)
	}

	// Progress sayfası "done" callback'i → Finish sayfasına geç
	var allPages []ui.Page
	progressPage := pages.NewProgressPage(cfg, func() {
		// Progress tamamlandı — finish sayfasına git (idx=7)
		// Bu callback glib.IdleAdd içinde zaten çalışıyor
		// win.EnableNext() ile Next butonunu aç
		win.EnableNext()
	})

	allPages = []ui.Page{
		pages.NewWelcomePage(cfg),
		pages.NewLocalePage(cfg),
		pages.NewKeyboardPage(cfg),
		pages.NewPartitionPage(cfg),
		pages.NewUsersPage(cfg),
		pages.NewSummaryPage(cfg),
		progressPage,
		pages.NewFinishPage(cfg),
	}

	win.SetPages(allPages)
	win.Show()

	gtk.Main()
}
```

- [ ] **Step 2: Commit**

```bash
git add main.go
git commit -m "feat: main.go — tüm sayfalar bağlandı"
```

---

## Task 8: Build sistemi entegrasyonu

**Files:**
- Modify: `build.sh`
- Modify: `profiledef.sh`
- Modify: `airootfs/usr/local/bin/kutos-installer`
- Modify: `airootfs/root/Desktop/kutos-installer.desktop`
- Modify: `airootfs/root/.config/autostart/kutos-installer.desktop`
- Modify: `airootfs/etc/skel/Desktop/kutos-installer.desktop`
- Delete: `airootfs/usr/local/lib/kutos-bootstrapper/`
- Delete: `airootfs/usr/local/bin/kutos-bootstrapper`

- [ ] **Step 1: build.sh'e Go derleme adımı ekle**

`mkarchiso` çağrısından ÖNCE:

```bash
# Go installer'ı derle
log "kutos-installer derleniyor..."
if ! command -v go &>/dev/null; then
    error "Go kurulu değil! sudo pacman -S go"
    exit 1
fi

INSTALLER_SRC="${SCRIPT_DIR}/kutos-installer-src"
INSTALLER_BIN="${SCRIPT_DIR}/airootfs/usr/local/bin/kutos-installer"

(cd "$INSTALLER_SRC" && \
    CGO_ENABLED=1 \
    go build -ldflags="-s -w" \
    -o "$INSTALLER_BIN" .)

chmod 755 "$INSTALLER_BIN"
success "kutos-installer derlendi: ${INSTALLER_BIN}"
```

- [ ] **Step 2: profiledef.sh — kutos-bootstrapper sil, kutos-installer permission doğrula**

`file_permissions`'dan kaldır:
```bash
# SİL: ["/usr/local/bin/kutos-bootstrapper"]="0:0:755"
```

Var olduğundan emin ol (zaten var):
```bash
["/usr/local/bin/kutos-installer"]="0:0:755"
```

- [ ] **Step 3: /usr/local/bin/kutos-installer binary launcher düzelt**

```bash
#!/bin/bash
# KutOS Installer — doğrudan binary, bu dosya sadece wrapper
exec /usr/local/bin/kutos-installer "$@"
```

NOT: build.sh binary'yi doğrudan bu path'e kopyalıyor, bu wrapper gerekmeyecek. build.sh çıktısı zaten bu dosyanın üstüne yazacak.

- [ ] **Step 4: Desktop dosyalarını güncelle**

`airootfs/root/Desktop/kutos-installer.desktop`:
```ini
[Desktop Entry]
Name=KutOS'u Kur
Comment=KutOS'u diskinize kurun
Exec=pkexec /usr/local/bin/kutos-installer
Icon=system-software-install
Terminal=false
Type=Application
Categories=System;
StartupNotify=true
```

`airootfs/root/.config/autostart/kutos-installer.desktop`:
```ini
[Desktop Entry]
Name=KutOS Installer
Exec=pkexec /usr/local/bin/kutos-installer
Icon=system-software-install
Terminal=false
Type=Application
Categories=System;
X-GNOME-Autostart-enabled=true
```

`airootfs/etc/skel/Desktop/kutos-installer.desktop` — **Bu dosyayı sil**, kurulu sisteme installer kısayolu gitmemeli.

- [ ] **Step 5: Python bootstrapper'ı kaldır**

```bash
rm -rf airootfs/usr/local/lib/kutos-bootstrapper/
rm -f airootfs/usr/local/bin/kutos-bootstrapper
```

- [ ] **Step 6: packages.x86_64'e Go build dep ekle (build host için değil, bu zaten host'ta — zaten var)**

NOT: `go` paketi ISO'ya eklenmez, sadece build host'ta lazım. ISO içinde Go runtime gerekmez (static binary).

GTK3 runtime ISO'da zaten var (XFCE kullandığı için). Sadece build zamanı için GTK3 dev headers lazım:
```bash
sudo pacman -S gtk3 gobject-introspection
```
Bu not build.sh yorumuna eklenmeli.

- [ ] **Step 7: known_issues.md güncelle**

BUG-001, BUG-003, BUG-004, BUG-005, BUG-006 → FIXED olarak işaretle.

- [ ] **Step 8: Commit**

```bash
git add build.sh profiledef.sh
git add airootfs/root/Desktop/kutos-installer.desktop
git add airootfs/root/.config/autostart/kutos-installer.desktop
git rm airootfs/etc/skel/Desktop/kutos-installer.desktop
git rm -r airootfs/usr/local/lib/kutos-bootstrapper/
git rm airootfs/usr/local/bin/kutos-bootstrapper
git commit -m "feat: build sistemi entegrasyonu, Python bootstrapper kaldırıldı"
```

---

## Task 9: Calamares config temizliği

**Files:**
- Modify: `airootfs/etc/calamares/settings.conf` — exec sequence'i temizle veya kaldır
- Modify: `packages.x86_64` — xorg-xinit tekrarını kaldır

- [ ] **Step 1: packages.x86_64 — xorg-xinit tekrarını kaldır**

```
# satır 103'teki ikinci xorg-xinit'i sil
```

- [ ] **Step 2: Calamares'i devre dışı bırak**

`airootfs/etc/calamares/settings.conf` dosyasını şimdilik bırak (ileride tamamen kaldırılacak). Autostart artık Calamares'i açmıyor, bu yeterli.

- [ ] **Step 3: Commit**

```bash
git add packages.x86_64
git commit -m "fix: xorg-xinit duplicate kaldırıldı"
```

---

## Self-Review

**Spec coverage:**
- ✅ Go + GTK3, Python yok
- ✅ Calamares bağımlılığı yok
- ✅ 0 runtime internet bağımlılığı (binary ISO'ya gömülü)
- ✅ Disk tespiti + partition (sgdisk) + format (mkfs) + mount
- ✅ rsync ile sistem kopyalama
- ✅ arch-chroot ile locale, keyboard, user, bootloader
- ✅ GRUB hem EFI hem BIOS
- ✅ Desktop kısayol tutarsızlığı giderildi
- ✅ Python bootstrapper kaldırıldı
- ✅ profiledef.sh executable permission BUG-001 fix
- ✅ Sidebar ile profesyonel UI

**Eksik / sonraya:**
- `go.sum` — `go mod tidy` ile oluşacak (otomatik)
- Unit test — disk ops root gerektirdiği için integration test scope'unda, şimdilik yok
- Manual partition modu — sadece "erase" modu şu an; tam partman UI gelecek sürümde
