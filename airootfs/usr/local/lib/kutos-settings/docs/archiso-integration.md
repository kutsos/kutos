# ArchISO Integration Guide — kutos-settings

This guide explains how to properly integrate the `kutos-settings` package into the KutOS ArchISO project so the application persists after OS installation.

---

## Strategy Overview

There are **two complementary approaches**:

| Approach | Purpose |
|----------|---------|
| **Direct airootfs** | App is available in the live ISO immediately |
| **PKGBUILD package** | App persists after installation via pacman |

The KutOS project already uses direct airootfs placement. For installed systems, build a proper package.

---

## 1. Build the Package with makepkg

```bash
# Create a clean build directory
mkdir -p /tmp/kutos-settings-build
cd /tmp/kutos-settings-build

# Copy all source files + PKGBUILD
cp -r /path/to/kutos-settings/* .

# Rename launcher for the PKGBUILD
cp /path/to/kutos-settings/../bin/kutos-settings kutos-settings.sh

# Build the package (do NOT run as root)
makepkg -sf

# Result: kutos-settings-1.0-1-any.pkg.tar.zst
```

---

## 2. Place Built Package in the ISO Project

```bash
# Create a local repo inside the ISO project
mkdir -p /path/to/KutOs/airootfs/usr/local/repo

# Copy the built package
cp kutos-settings-1.0-1-any.pkg.tar.zst /path/to/KutOs/airootfs/usr/local/repo/

# Generate repo database
cd /path/to/KutOs/airootfs/usr/local/repo
repo-add kutos.db.tar.gz kutos-settings-1.0-1-any.pkg.tar.zst
```

Then add the local repo to `pacman.conf`:

```ini
# In KutOs/pacman.conf, add at the bottom:
[kutos]
SigLevel = Optional TrustAll
Server = file:///usr/local/repo
```

---

## 3. Add to packages.x86_64

Already done — `gtk4` and `python-requests` are added. For the package itself:

```text
# In packages.x86_64, add:
kutos-settings
```

> **Note:** This only works if the local repo (step 2) is configured.
> Alternatively, keep using direct airootfs placement for simplicity.

---

## 4. How pacstrap Installs It

During installation, the installer runs:

```bash
pacstrap /mnt base linux linux-firmware ...
```

If `kutos-settings` is in `packages.x86_64` and the local repo is configured in `pacman.conf`, pacstrap will install it automatically to the target system.

### Alternative: Post-install Copy (Current Approach)

Since the files already exist in `airootfs/usr/local/lib/kutos-settings/`, they're present in the live ISO. The bootstrapper/installer copies them to the target during installation.

---

## 5. Test in a VM

```bash
# Build the ISO
sudo ./build.sh

# Test with QEMU
qemu-img create -f qcow2 /tmp/kutos-test.qcow2 20G
qemu-system-x86_64 \
    -cdrom out/kutos-*.iso \
    -m 2G \
    -enable-kvm \
    -boot d \
    -hda /tmp/kutos-test.qcow2

# Inside the live environment, test:
/usr/local/bin/kutos-settings

# Or from the desktop, click "KutOS Settings" icon
```

### Verify After Installation

```bash
# After installing KutOS to disk and rebooting:
which kutos-settings
kutos-settings
```

---

## Quick Reference

| File | Location in ISO |
|------|----------------|
| Application source | `airootfs/usr/local/lib/kutos-settings/` |
| Launcher script | `airootfs/usr/local/bin/kutos-settings` |
| Desktop entry | `airootfs/usr/share/applications/kutos-settings.desktop` |
| Desktop shortcut | `airootfs/etc/skel/Desktop/kutos-settings.desktop` |
| PKGBUILD | `airootfs/usr/local/lib/kutos-settings/PKGBUILD` |
