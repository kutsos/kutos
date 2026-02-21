#!/bin/bash
# Host makinede test etmek için çalıştırıcı script

export PYTHONPATH="/home/bugrapc/KutOs/airootfs/usr/local/lib/kutos-installer:$PYTHONPATH"

echo "KutOS Installer test ortamında başlatılıyor..."
python3 /home/bugrapc/KutOs/airootfs/usr/local/lib/kutos-installer/main.py
