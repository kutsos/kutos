"""KutOS Installer — Main Installation Engine

Orchestrates the full installation process:
1. Disk partitioning
2. Mounting
3. pacstrap base system
4. System configuration
5. Desktop environment
6. yay (AUR helper)
7. Bootloader (GRUB)
8. User creation
9. Service enablement
10. Cleanup
"""

import subprocess
import os
import time

from backend.disk import partition_auto, mount_partitions, unmount_all, detect_uefi
from backend.packages import get_de_packages, BASE_PACKAGES
from backend.config import (
    generate_fstab,
    configure_locale,
    configure_timezone,
    configure_hostname,
    create_user,
    install_yay,
    enable_services,
    configure_grub,
)

MOUNT_POINT = "/mnt"


def run_installation(config, progress_cb, log_cb, done_cb):
    """Run the full installation. Called from a background thread.

    Args:
        config: dict with all user selections
        progress_cb: callable(fraction, phase, detail)
        log_cb: callable(message)
        done_cb: callable(success, error_msg)
    """
    try:
        total_steps = 10
        step = 0

        def advance(phase, detail=""):
            nonlocal step
            step += 1
            progress_cb(step / total_steps, phase, detail)

        is_uefi = detect_uefi()
        log_cb(f"[INFO] Boot modu: {'UEFI' if is_uefi else 'BIOS/Legacy'}")

        # === Step 1: Disk Partitioning ===
        advance("Disk bölümlendiriliyor...", config.get("disk", ""))
        log_cb(f"[DISK] Hedef disk: {config.get('disk')}")
        log_cb(f"[DISK] Mod: {config.get('partition_mode')}")

        if config.get("partition_mode") == "auto":
            disk = config["disk"]
            partitions = partition_auto(disk, is_uefi, log_cb)
            config["_partitions"] = partitions
        else:
            config["_partitions"] = {
                "root": config.get("root_partition", ""),
                "efi": config.get("efi_partition", ""),
                "swap": config.get("swap_partition", ""),
            }

        log_cb("[DISK] Bölümlendirme tamamlandı.")

        # === Step 2: Formatting & Mounting ===
        advance("Dosya sistemleri oluşturuluyor...", "Format & Mount")
        parts = config["_partitions"]
        mount_partitions(parts, is_uefi, log_cb)
        log_cb("[MOUNT] Bölümler bağlandı.")

        # === Step 3: pacstrap base packages ===
        advance("Temel sistem kuruluyor...", "pacstrap çalışıyor (bu biraz sürebilir)")
        log_cb("[PACSTRAP] Temel paketler kuruluyor...")

        base_pkgs = list(BASE_PACKAGES)
        cmd = ["pacstrap", "-K", MOUNT_POINT] + base_pkgs
        _run_cmd(cmd, log_cb)
        log_cb("[PACSTRAP] Temel sistem kuruldu.")

        # === Step 4: Generate fstab ===
        advance("fstab oluşturuluyor...", "/etc/fstab")
        generate_fstab(MOUNT_POINT, log_cb)

        # === Step 5: Locale & Timezone ===
        advance("Sistem yapılandırılıyor...", "Dil, saat dilimi, hostname")
        language = config.get("language", "tr_TR.UTF-8")
        timezone = config.get("timezone", "Europe/Istanbul")
        hostname = config.get("hostname", "kutos")

        configure_locale(MOUNT_POINT, language, log_cb)
        configure_timezone(MOUNT_POINT, timezone, log_cb)
        configure_hostname(MOUNT_POINT, hostname, log_cb)

        # === Step 6: Desktop Environment ===
        advance("Masaüstü ortamı kuruluyor...", config.get("desktop", "xfce"))
        de = config.get("desktop", "xfce")
        de_pkgs = get_de_packages(de)
        log_cb(f"[DE] {de.upper()} paketleri kuruluyor: {', '.join(de_pkgs[:5])}...")

        cmd = ["arch-chroot", MOUNT_POINT, "pacman", "-S", "--noconfirm", "--needed"] + de_pkgs
        _run_cmd(cmd, log_cb)
        log_cb(f"[DE] {de.upper()} kuruldu.")

        # === Step 7: Extra Packages ===
        extras = config.get("extra_packages", [])
        if extras:
            advance("Ek paketler kuruluyor...", f"{len(extras)} paket")
            log_cb(f"[PKG] {len(extras)} ek paket kuruluyor...")
            cmd = [
                "arch-chroot", MOUNT_POINT,
                "pacman", "-S", "--noconfirm", "--needed",
            ] + extras
            _run_cmd(cmd, log_cb)
        else:
            advance("Ek paketler...", "Seçilmedi, atlanıyor")
            log_cb("[PKG] Ek paket seçilmedi, atlanıyor.")

        # === Step 8: yay (AUR Helper) ===
        advance("yay kuruluyor...", "AUR helper")
        username = config.get("username", "kutos")
        install_yay(MOUNT_POINT, username, log_cb)

        # === Step 9: GRUB Bootloader ===
        advance("Bootloader kuruluyor...", "GRUB")
        disk = config.get("disk", "")
        configure_grub(MOUNT_POINT, disk, is_uefi, log_cb)

        # === Step 10: User & Services ===
        advance("Kullanıcı ve servisler yapılandırılıyor...", "Son adım")
        password = config.get("password", "")
        sudo = config.get("sudo", True)
        root_same = config.get("root_same_password", True)
        create_user(MOUNT_POINT, username, password, sudo, root_same, log_cb)

        de_dm = {"xfce": "lightdm", "hyprland": "sddm", "gnome": "gdm"}
        dm = de_dm.get(de, "lightdm")
        enable_services(MOUNT_POINT, dm, log_cb)

        # === Cleanup ===
        log_cb("[CLEANUP] Bölümler ayrılıyor...")
        unmount_all(MOUNT_POINT, log_cb)

        log_cb("")
        log_cb("=" * 50)
        log_cb("  ✅ KutOS kurulumu başarıyla tamamlandı!")
        log_cb("  USB'yi çıkarıp sistemi yeniden başlatın.")
        log_cb("=" * 50)

        done_cb(True, "")

    except Exception as e:
        log_cb(f"\n[HATA] {str(e)}")
        try:
            unmount_all(MOUNT_POINT, log_cb)
        except Exception:
            pass
        done_cb(False, str(e))


def _run_cmd(cmd, log_cb, check=True):
    """Run a shell command and stream output to log."""
    log_cb(f"$ {' '.join(cmd)}")
    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        for line in proc.stdout:
            line = line.rstrip()
            if line:
                log_cb(f"  {line}")
        proc.wait()
        if check and proc.returncode != 0:
            raise RuntimeError(
                f"Komut başarısız (kod {proc.returncode}): {' '.join(cmd)}"
            )
    except FileNotFoundError:
        raise RuntimeError(f"Komut bulunamadı: {cmd[0]}")
