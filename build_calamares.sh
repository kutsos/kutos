#!/bin/bash
# ========================================
# KutOS — Calamares AUR Build Script
# ========================================
# Bu script Calamares ve ckbcomp AUR paketlerini
# yerel bir paket deposunda derler. ISO derleme aşamasında kullanılır.
# 
# ÖNEMLİ: Normal kullanıcı olarak çalıştırın!
#
# Kullanım:
#   ./build_calamares.sh
# ========================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOCALREPO="${SCRIPT_DIR}/localrepo"
BUILD_DIR="/tmp/kutos-aur-build-$(date +%s)"

RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
NC='\033[0m'

log()     { echo -e "${CYAN}[KutOS]${NC} $1"; }
success() { echo -e "${GREEN}[✓]${NC} $1"; }
error()   { echo -e "${RED}[✗]${NC} $1" >&2; }

if [[ $EUID -eq 0 ]]; then
    error "Bu script root olarak çalıştırılmamalıdır!"
    exit 1
fi

mkdir -p "${LOCALREPO}"
mkdir -p "${BUILD_DIR}"

# 1. ckbcomp
log "Building ckbcomp..."
cd "${BUILD_DIR}"
git clone https://aur.archlinux.org/ckbcomp.git
cd ckbcomp
makepkg -sf --noconfirm --needed
cp *.pkg.tar.zst "${LOCALREPO}/" || true

# 2. calamares
log "Building calamares..."
cd "${BUILD_DIR}"
git clone https://aur.archlinux.org/calamares.git
cd calamares
makepkg -sf --noconfirm --needed
cp *.pkg.tar.zst "${LOCALREPO}/" || true

# Generate repo database
log "Yerel repo veritabanı oluşturuluyor..."
cd "${LOCALREPO}"
rm -f *.sig # Remove signature files that crash repo-add
repo-add kutos-local.db.tar.gz *.pkg.tar.zst

cd "${SCRIPT_DIR}"
rm -rf "${BUILD_DIR}"

success "Yerel repo hazır: ${LOCALREPO}"
echo ""
log "Şimdi ISO'yu derleyebilirsiniz:"
echo "  sudo rm -rf /tmp/kutos-build"
echo "  sudo ./build.sh"
