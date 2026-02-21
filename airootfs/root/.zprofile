# KutOS Live — Auto-start XFCE on tty1
# Only runs on tty1 and only if X is not already running
if [[ -z "$DISPLAY" ]] && [[ "$(tty)" == "/dev/tty1" ]]; then
    exec startx
fi
