#!/bin/bash
# ========================================
# KutOS Live ISO Build Script
# ========================================
# Gereksinimler:
#   - Arch Linux host sistemi
#   - archiso paketi kurulu (sudo pacman -S archiso)
#   - Root yetkisi
#
# Kullanım:
#   sudo ./build.sh
#
# Çıktı:
#   ./out/kutos-YYYY.MM.DD-x86_64.iso
# ========================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORK_DIR="/tmp/kutos-build"
OUT_DIR="${SCRIPT_DIR}/out"

RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
NC='\033[0m'

log() { echo -e "${CYAN}[KutOS]${NC} $1"; }
success() { echo -e "${GREEN}[✓]${NC} $1"; }
error() { echo -e "${RED}[✗]${NC} $1" >&2; }

# Root check
if [[ $EUID -ne 0 ]]; then
    error "Bu script root olarak çalıştırılmalıdır!"
    echo "  sudo ./build.sh"
    exit 1
fi

# archiso check
if ! command -v mkarchiso &>/dev/null; then
    error "archiso kurulu değil!"
    echo "  sudo pacman -S archiso"
    exit 1
fi

# Clean previous build
if [[ -d "$WORK_DIR" ]]; then
    log "Önceki build temizleniyor..."
    rm -rf "$WORK_DIR"
fi

# Create output directory
mkdir -p "$OUT_DIR"

# Build ISO
log "KutOS ISO oluşturuluyor..."
log "  Profil: ${SCRIPT_DIR}"
log "  Çalışma dizini: ${WORK_DIR}"
log "  Çıktı: ${OUT_DIR}"
echo ""

mkarchiso -v -w "$WORK_DIR" -o "$OUT_DIR" "$SCRIPT_DIR"

echo ""
success "ISO başarıyla oluşturuldu!"
echo ""

# Show result
ISO_FILE=$(ls -1t "${OUT_DIR}"/kutos-*.iso 2>/dev/null | head -1)
if [[ -n "$ISO_FILE" ]]; then
    ISO_SIZE=$(du -h "$ISO_FILE" | cut -f1)
    success "Dosya: ${ISO_FILE}"
    success "Boyut: ${ISO_SIZE}"
    echo ""
    log "Test etmek için:"
    echo "  # QEMU ile test"
    echo "  qemu-img create -f qcow2 /tmp/kutos-test.qcow2 20G"
    echo "  qemu-system-x86_64 -cdrom ${ISO_FILE} -m 2G -enable-kvm -boot d -hda /tmp/kutos-test.qcow2"
    echo ""
    echo "  # VirtualBox ile test"
    echo "  VBoxManage createmedium disk --filename /tmp/kutos-test.vdi --size 20480"
fi
