#!/bin/bash
# Host makinede test etmek için çalıştırıcı script

export PYTHONPATH="/home/bugrapc/KutOs/airootfs/usr/local/lib/kutos-bootstrapper:$PYTHONPATH"

echo "KutOS Bootstrapper test ortamında başlatılıyor..."
python3 /home/bugrapc/KutOs/airootfs/usr/local/lib/kutos-bootstrapper/main.py
