package backend

import (
	"encoding/json"
	"fmt"
	"os"
	"os/exec"
	"strings"
)

// Disk bir blok aygıtı temsil eder.
type Disk struct {
	Path  string
	Name  string
	Size  string
	Model string
}

type lsblkOutput struct {
	Blockdevices []struct {
		Name  string `json:"name"`
		Size  string `json:"size"`
		Model string `json:"model"`
		Type  string `json:"type"`
	} `json:"blockdevices"`
}

// ListDisks sistemdeki fiziksel diskleri listeler.
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

// IsEFI sistemin UEFI modunda açılıp açılmadığını döndürür.
func IsEFI() bool {
	_, err := os.Stat("/sys/firmware/efi")
	return err == nil
}

// PartitionDisk seçilen diski GPT ile yeniden bölümler.
// efi=true → EFI + (swap) + root
// efi=false → BIOS boot + (swap) + root
func PartitionDisk(disk string, efi bool, swapSize string) error {
	hasSwap := swapSize != "none" && swapSize != ""

	if err := run("sgdisk", "--zap-all", disk); err != nil {
		return fmt.Errorf("zap: %w", err)
	}

	if efi {
		if err := run("sgdisk", "-n", "1:0:+512M", "-t", "1:EF00", "-c", "1:EFI", disk); err != nil {
			return fmt.Errorf("efi partition: %w", err)
		}
		if hasSwap {
			if err := run("sgdisk", "-n", "2:0:+"+swapSize, "-t", "2:8200", "-c", "2:swap", disk); err != nil {
				return fmt.Errorf("swap partition: %w", err)
			}
			if err := run("sgdisk", "-n", "3:0:0", "-t", "3:8300", "-c", "3:root", disk); err != nil {
				return fmt.Errorf("root partition: %w", err)
			}
		} else {
			if err := run("sgdisk", "-n", "2:0:0", "-t", "2:8300", "-c", "2:root", disk); err != nil {
				return fmt.Errorf("root partition: %w", err)
			}
		}
	} else {
		// BIOS boot partition (1 MiB, tipi EF02)
		if err := run("sgdisk", "-n", "1:0:+1M", "-t", "1:EF02", "-c", "1:bios_boot", disk); err != nil {
			return fmt.Errorf("bios boot partition: %w", err)
		}
		if hasSwap {
			if err := run("sgdisk", "-n", "2:0:+"+swapSize, "-t", "2:8200", "-c", "2:swap", disk); err != nil {
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

	_ = run("partprobe", disk)
	return nil
}

// FormatPartitions oluşturulan bölümleri formatlar.
func FormatPartitions(disk string, efi bool, fs string, hasSwap bool) error {
	if efi {
		efiPart := partPath(disk, 1)
		if err := run("mkfs.fat", "-F32", "-n", "EFI", efiPart); err != nil {
			return fmt.Errorf("format efi: %w", err)
		}
		if hasSwap {
			if err := run("mkswap", "-L", "swap", partPath(disk, 2)); err != nil {
				return fmt.Errorf("mkswap: %w", err)
			}
			return formatRoot(partPath(disk, 3), fs)
		}
		return formatRoot(partPath(disk, 2), fs)
	}
	// BIOS: partition 1 = bios_boot (format gerekmez)
	if hasSwap {
		if err := run("mkswap", "-L", "swap", partPath(disk, 2)); err != nil {
			return fmt.Errorf("mkswap: %w", err)
		}
		return formatRoot(partPath(disk, 3), fs)
	}
	return formatRoot(partPath(disk, 2), fs)
}

const MountPoint = "/mnt"

// MountPartitions bölümleri /mnt altına bağlar.
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

	mountOpts := "defaults,noatime"
	if fs == "btrfs" {
		mountOpts += ",compress=zstd,space_cache=v2"
	}
	if err := run("mount", "-o", mountOpts, rootPart, MountPoint); err != nil {
		return fmt.Errorf("mount root: %w", err)
	}

	if efi && efiPart != "" {
		if err := os.MkdirAll(MountPoint+"/boot/efi", 0755); err != nil {
			return err
		}
		if err := run("mount", efiPart, MountPoint+"/boot/efi"); err != nil {
			return fmt.Errorf("mount efi: %w", err)
		}
	}

	if swapPart != "" {
		_ = run("swapon", swapPart)
	}

	return nil
}

// UnmountAll /mnt altındaki tüm bölümleri söker.
func UnmountAll() {
	_ = run("swapoff", "-a")
	_ = run("umount", "-R", MountPoint)
}

// partPath /dev/sda + 1 → /dev/sda1, /dev/nvme0n1 + 1 → /dev/nvme0n1p1
func partPath(disk string, num int) string {
	if strings.Contains(disk, "nvme") || strings.Contains(disk, "mmcblk") {
		return fmt.Sprintf("%sp%d", disk, num)
	}
	return fmt.Sprintf("%s%d", disk, num)
}

func formatRoot(part, fs string) error {
	switch fs {
	case "btrfs":
		return run("mkfs.btrfs", "-f", "-L", "root", part)
	default:
		return run("mkfs.ext4", "-F", "-L", "root", part)
	}
}

// run bir komutu çalıştırır, stdout/stderr'i terminale yönlendirir.
func run(name string, args ...string) error {
	cmd := exec.Command(name, args...)
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	return cmd.Run()
}
