"""KutOS Installer — System Configuration (arch-chroot operations)"""

import subprocess
import os

MOUNT_POINT = "/mnt"


def generate_fstab(mount_point, log_cb):
    """Generate /etc/fstab using genfstab."""
    fstab_path = os.path.join(mount_point, "etc", "fstab")
    log_cb("[FSTAB] Generating /etc/fstab...")
    result = subprocess.run(
        ["genfstab", "-U", mount_point],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"genfstab failed: {result.stderr}")

    with open(fstab_path, "w") as f:
        f.write(result.stdout)
    log_cb("[FSTAB] /etc/fstab oluşturuldu.")


def configure_locale(mount_point, language, log_cb):
    """Configure system locale."""
    log_cb(f"[LOCALE] Dil ayarlanıyor: {language}")

    # Determine base locale string (e.g., "tr_TR" from "tr_TR.UTF-8")
    locale_base = language.split(".")[0] if "." in language else language

    # Uncomment locale in locale.gen
    locale_gen = os.path.join(mount_point, "etc", "locale.gen")
    if os.path.exists(locale_gen):
        with open(locale_gen, "r") as f:
            content = f.read()
        # Uncomment the desired locale
        content = content.replace(f"#{language} UTF-8", f"{language} UTF-8")
        # Also always enable en_US.UTF-8
        content = content.replace("#en_US.UTF-8 UTF-8", "en_US.UTF-8 UTF-8")
        with open(locale_gen, "w") as f:
            f.write(content)
    else:
        # Create locale.gen
        with open(locale_gen, "w") as f:
            f.write(f"{language} UTF-8\n")
            f.write("en_US.UTF-8 UTF-8\n")

    _chroot(mount_point, ["locale-gen"], log_cb)

    # Set locale.conf
    locale_conf = os.path.join(mount_point, "etc", "locale.conf")
    with open(locale_conf, "w") as f:
        f.write(f"LANG={language}\n")

    log_cb("[LOCALE] Dil yapılandırması tamamlandı.")


def configure_timezone(mount_point, timezone, log_cb):
    """Configure system timezone."""
    log_cb(f"[TZ] Saat dilimi ayarlanıyor: {timezone}")

    localtime = os.path.join(mount_point, "etc", "localtime")
    if os.path.exists(localtime):
        os.remove(localtime)

    _chroot(
        mount_point,
        ["ln", "-sf", f"/usr/share/zoneinfo/{timezone}", "/etc/localtime"],
        log_cb,
    )
    _chroot(mount_point, ["hwclock", "--systohc"], log_cb)
    log_cb("[TZ] Saat dilimi yapılandırıldı.")


def configure_hostname(mount_point, hostname, log_cb):
    """Configure hostname and /etc/hosts."""
    log_cb(f"[HOST] Hostname ayarlanıyor: {hostname}")

    with open(os.path.join(mount_point, "etc", "hostname"), "w") as f:
        f.write(f"{hostname}\n")

    with open(os.path.join(mount_point, "etc", "hosts"), "w") as f:
        f.write(f"127.0.0.1\tlocalhost\n")
        f.write(f"::1\t\tlocalhost\n")
        f.write(f"127.0.1.1\t{hostname}.localdomain\t{hostname}\n")

    log_cb("[HOST] Hostname yapılandırıldı.")


def create_user(mount_point, username, password, sudo, root_same_pw, log_cb):
    """Create user with optional sudo access."""
    log_cb(f"[USER] Kullanıcı oluşturuluyor: {username}")

    # Create user with home directory, zsh shell, and groups
    _chroot(
        mount_point,
        [
            "useradd", "-m", "-G", "wheel,audio,video,storage,network,power",
            "-s", "/bin/zsh", username,
        ],
        log_cb,
    )

    # Set password
    _chroot_pipe(mount_point, f"{username}:{password}", ["chpasswd"], log_cb)
    log_cb(f"[USER] Kullanıcı şifresi ayarlandı.")

    # Set root password
    if root_same_pw:
        _chroot_pipe(mount_point, f"root:{password}", ["chpasswd"], log_cb)
        log_cb("[USER] Root şifresi kullanıcı ile aynı olarak ayarlandı.")

    # Configure sudo
    if sudo:
        sudoers_dir = os.path.join(mount_point, "etc", "sudoers.d")
        os.makedirs(sudoers_dir, exist_ok=True)
        sudoers_file = os.path.join(sudoers_dir, "00-kutos")
        with open(sudoers_file, "w") as f:
            f.write(f"# KutOS sudo configuration\n")
            f.write(f"%wheel ALL=(ALL:ALL) ALL\n")
        os.chmod(sudoers_file, 0o440)
        log_cb("[USER] sudo yetkisi verildi (wheel grubu).")

    # Create xdg user dirs
    _chroot(
        mount_point,
        ["su", "-", username, "-c", "xdg-user-dirs-update"],
        log_cb,
    )
    log_cb("[USER] Kullanıcı dizinleri oluşturuldu.")


def install_yay(mount_point, username, log_cb):
    """Install yay AUR helper."""
    log_cb("[YAY] yay AUR helper kuruluyor...")

    # Create temporary build script
    build_script = os.path.join(mount_point, "tmp", "install-yay.sh")
    with open(build_script, "w") as f:
        f.write("#!/bin/bash\n")
        f.write("set -e\n")
        f.write("cd /tmp\n")
        f.write("git clone https://aur.archlinux.org/yay-bin.git\n")
        f.write("cd yay-bin\n")
        # Ensure makepkg doesn't freeze waiting for sudo password
        f.write("export MAKEFLAGS='-j$(nproc)'\n")
        f.write("makepkg -si --noconfirm --needed\n")
        f.write("cd /tmp && rm -rf yay-bin\n")
    os.chmod(build_script, 0o755)

    # Temporarily allow passwordless sudo for the user to prevent makepkg from freezing
    sudoers_tmp = os.path.join(mount_point, "etc", "sudoers.d", "99-installer-yay")
    with open(sudoers_tmp, "w") as f:
        f.write(f"{username} ALL=(ALL) NOPASSWD: ALL\n")
    os.chmod(sudoers_tmp, 0o440)

    # Run as the created user without dropping into a full login shell to maintain /tmp access
    _chroot(
        mount_point,
        ["su", username, "-c", "bash /tmp/install-yay.sh"],
        log_cb,
    )

    # Cleanup temporary script and sudoers
    try:
        os.remove(build_script)
        os.remove(sudoers_tmp)
    except Exception:
        pass

    log_cb("[YAY] yay başarıyla kuruldu.")


def configure_grub(mount_point, disk, is_uefi, log_cb):
    """Install and configure GRUB bootloader."""
    log_cb("[GRUB] Bootloader kuruluyor...")

    if is_uefi:
        log_cb("[GRUB] UEFI modu — grub-install EFI")
        _chroot(
            mount_point,
            [
                "grub-install",
                "--target=x86_64-efi",
                "--efi-directory=/boot/efi",
                "--bootloader-id=KutOS",
                "--recheck",
            ],
            log_cb,
        )
    else:
        log_cb(f"[GRUB] BIOS modu — grub-install {disk}")
        _chroot(
            mount_point,
            [
                "grub-install",
                "--target=i386-pc",
                "--recheck",
                disk,
            ],
            log_cb,
        )

    # Configure GRUB defaults for faster boot
    grub_default = os.path.join(mount_point, "etc", "default", "grub")
    if os.path.exists(grub_default):
        with open(grub_default, "r") as f:
            content = f.read()
        # Set timeout
        content = content.replace("GRUB_TIMEOUT=5", "GRUB_TIMEOUT=3")
        # Set title
        if "GRUB_DISTRIBUTOR=" in content:
            lines = content.split("\n")
            for i, line in enumerate(lines):
                if line.startswith("GRUB_DISTRIBUTOR="):
                    lines[i] = 'GRUB_DISTRIBUTOR="KutOS"'
            content = "\n".join(lines)
        with open(grub_default, "w") as f:
            f.write(content)

    _chroot(mount_point, ["grub-mkconfig", "-o", "/boot/grub/grub.cfg"], log_cb)
    log_cb("[GRUB] Bootloader yapılandırıldı.")


def enable_services(mount_point, display_manager, log_cb):
    """Enable essential systemd services."""
    log_cb("[SERVICES] Servisler etkinleştiriliyor...")

    services = [
        "NetworkManager",
        display_manager,
        "fstrim.timer",
    ]

    for svc in services:
        _chroot(mount_point, ["systemctl", "enable", svc], log_cb)
        log_cb(f"[SERVICES] {svc} aktif edildi.")

    # Mask unnecessary services for minimal RAM usage
    masked = [
        "bluetooth.service",
        "cups.service",
        "avahi-daemon.service",
    ]
    for svc in masked:
        _chroot(mount_point, ["systemctl", "mask", svc], log_cb, check=False)

    log_cb("[SERVICES] Servis yapılandırması tamamlandı.")


def _chroot(mount_point, cmd, log_cb, check=True):
    """Run a command inside arch-chroot."""
    full_cmd = ["arch-chroot", mount_point] + cmd
    log_cb(f"$ {' '.join(full_cmd)}")
    result = subprocess.run(full_cmd, capture_output=True, text=True)
    if result.stdout.strip():
        for line in result.stdout.strip().split("\n"):
            log_cb(f"  {line}")
    if result.stderr.strip():
        for line in result.stderr.strip().split("\n"):
            log_cb(f"  [stderr] {line}")
    if check and result.returncode != 0:
        raise RuntimeError(
            f"arch-chroot komutu başarısız: {' '.join(cmd)}\n{result.stderr}"
        )


def _chroot_pipe(mount_point, input_data, cmd, log_cb):
    """Run a command inside arch-chroot with stdin pipe."""
    full_cmd = ["arch-chroot", mount_point] + cmd
    result = subprocess.run(full_cmd, input=input_data, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"arch-chroot pipe komutu başarısız: {' '.join(cmd)}\n{result.stderr}"
        )
