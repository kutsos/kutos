"""KutOS Installer — Disk Partitioning & Mounting"""

import subprocess
import os
import math

MOUNT_POINT = "/mnt"


def detect_uefi():
    """Check if system booted in UEFI mode."""
    return os.path.isdir("/sys/firmware/efi/efivars")


def get_ram_gb():
    """Get total RAM in GB."""
    try:
        with open("/proc/meminfo") as f:
            for line in f:
                if line.startswith("MemTotal:"):
                    kb = int(line.split()[1])
                    return math.ceil(kb / 1024 / 1024)
    except Exception:
        pass
    return 4


def partition_auto(disk, is_uefi, log_cb):
    """Auto-partition the given disk.

    UEFI layout:
        1. EFI  (512MB, FAT32)
        2. Swap (RAM size, max 8GB)
        3. Root (remaining, ext4)

    BIOS layout:
        1. Swap (RAM size, max 8GB)
        2. Root (remaining, ext4)

    Returns dict with 'efi', 'swap', 'root' partition paths.
    """
    log_cb(f"[PART] Otomatik bölümlendirme başlıyor: {disk}")

    swap_gb = min(get_ram_gb(), 8)
    log_cb(f"[PART] Swap boyutu: {swap_gb}GB")

    # Wipe existing partition table
    _run(["wipefs", "--all", "--force", disk], log_cb)
    _run(["sgdisk", "--zap-all", disk], log_cb)

    partitions = {}

    if is_uefi:
        log_cb("[PART] UEFI GPT düzeni oluşturuluyor...")
        # Create GPT
        _run(["parted", "-s", disk, "mklabel", "gpt"], log_cb)

        # EFI partition (512MB)
        _run(
            ["parted", "-s", disk, "mkpart", "EFI", "fat32", "1MiB", "513MiB"],
            log_cb,
        )
        _run(["parted", "-s", disk, "set", "1", "esp", "on"], log_cb)

        # Swap partition
        swap_end = 513 + (swap_gb * 1024)
        _run(
            [
                "parted", "-s", disk, "mkpart", "swap",
                "linux-swap", f"513MiB", f"{swap_end}MiB",
            ],
            log_cb,
        )

        # Root partition (remaining)
        _run(
            [
                "parted", "-s", disk, "mkpart", "root",
                "ext4", f"{swap_end}MiB", "100%",
            ],
            log_cb,
        )

        # Determine partition names (nvme uses p1, sda uses 1)
        sep = "p" if "nvme" in disk or "mmcblk" in disk else ""
        partitions = {
            "efi": f"{disk}{sep}1",
            "swap": f"{disk}{sep}2",
            "root": f"{disk}{sep}3",
        }
    else:
        log_cb("[PART] BIOS MBR düzeni oluşturuluyor...")
        _run(["parted", "-s", disk, "mklabel", "msdos"], log_cb)

        # Swap partition
        swap_end = 1 + (swap_gb * 1024)
        _run(
            [
                "parted", "-s", disk, "mkpart", "primary",
                "linux-swap", "1MiB", f"{swap_end}MiB",
            ],
            log_cb,
        )

        # Root partition
        _run(
            [
                "parted", "-s", disk, "mkpart", "primary",
                "ext4", f"{swap_end}MiB", "100%",
            ],
            log_cb,
        )
        _run(["parted", "-s", disk, "set", "2", "boot", "on"], log_cb)

        sep = "p" if "nvme" in disk or "mmcblk" in disk else ""
        partitions = {
            "efi": "",
            "swap": f"{disk}{sep}1",
            "root": f"{disk}{sep}2",
        }

    # Wait for kernel to register partitions
    _run(["partprobe", disk], log_cb)
    _run(["sleep", "2"], log_cb)

    # Format partitions
    log_cb("[FORMAT] Dosya sistemleri oluşturuluyor...")

    if partitions.get("efi"):
        _run(["mkfs.fat", "-F32", partitions["efi"]], log_cb)
        log_cb(f"[FORMAT] {partitions['efi']} → FAT32")

    if partitions.get("swap"):
        _run(["mkswap", partitions["swap"]], log_cb)
        log_cb(f"[FORMAT] {partitions['swap']} → swap")

    _run(["mkfs.ext4", "-F", partitions["root"]], log_cb)
    log_cb(f"[FORMAT] {partitions['root']} → ext4")

    return partitions


def mount_partitions(partitions, is_uefi, log_cb):
    """Mount partitions to /mnt."""
    root = partitions.get("root", "")
    efi = partitions.get("efi", "")
    swap = partitions.get("swap", "")

    if not root:
        raise RuntimeError("Root bölümü belirtilmedi!")

    # Mount root
    os.makedirs(MOUNT_POINT, exist_ok=True)
    _run(["mount", root, MOUNT_POINT], log_cb)
    log_cb(f"[MOUNT] {root} → {MOUNT_POINT}")

    # Mount EFI
    if efi and is_uefi:
        efi_mount = os.path.join(MOUNT_POINT, "boot", "efi")
        os.makedirs(efi_mount, exist_ok=True)
        _run(["mount", efi, efi_mount], log_cb)
        log_cb(f"[MOUNT] {efi} → {efi_mount}")

    # Enable swap
    if swap:
        _run(["swapon", swap], log_cb)
        log_cb(f"[SWAP] {swap} aktif")


def unmount_all(mount_point, log_cb):
    """Unmount all partitions."""
    try:
        _run(["swapoff", "-a"], log_cb, check=False)
    except Exception:
        pass

    try:
        _run(["umount", "-R", mount_point], log_cb, check=False)
    except Exception:
        pass


def _run(cmd, log_cb, check=True):
    """Run command with logging."""
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.stdout.strip():
        for line in result.stdout.strip().split("\n"):
            log_cb(f"  {line}")
    if result.stderr.strip():
        for line in result.stderr.strip().split("\n"):
            log_cb(f"  [stderr] {line}")
    if check and result.returncode != 0:
        raise RuntimeError(
            f"Komut başarısız: {' '.join(cmd)}\n{result.stderr}"
        )
