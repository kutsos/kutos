#!/bin/bash
# KutOS Settings — Test launcher for local development
# Run from the project root to test the GTK4 application

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/airootfs/usr/local/lib/kutos-settings"

export PYTHONPATH="${APP_DIR}:${PYTHONPATH}"

echo "KutOS Settings başlatılıyor..."
echo "  App dir: ${APP_DIR}"
python3 "${APP_DIR}/main.py"
