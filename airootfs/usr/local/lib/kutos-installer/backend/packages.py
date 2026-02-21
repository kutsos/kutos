"""KutOS Installer — Desktop Environment Package Groups"""

BASE_PACKAGES = [
    # Core
    "base",
    "linux",
    "linux-firmware",
    "linux-headers",
    # Boot
    "grub",
    "efibootmgr",
    "os-prober",
    # CPU
    "amd-ucode",
    "intel-ucode",
    # Filesystem
    "btrfs-progs",
    "dosfstools",
    "e2fsprogs",
    "ntfs-3g",
    "xfsprogs",
    # Network
    "networkmanager",
    "dhcpcd",
    "wpa_supplicant",
    # Essential tools
    "base-devel",
    "git",
    "wget",
    "curl",
    "sudo",
    "nano",
    "vim",
    "zsh",
    "less",
    "man-db",
    "man-pages",
    "reflector",
    # Audio
    "pipewire",
    "pipewire-alsa",
    "pipewire-pulse",
    "wireplumber",
    # Fonts
    "ttf-dejavu",
    "noto-fonts",
    # X11 base
    "xorg-server",
    "xorg-xinit",
    "xorg-xrandr",
    # GPU drivers
    "xf86-video-vesa",
    "xf86-video-amdgpu",
    "xf86-video-intel",
    "xf86-video-nouveau",
    "mesa",
]

DE_PACKAGES = {
    "xfce": {
        "packages": [
            "xfce4",
            "xfce4-goodies",
            "lightdm",
            "lightdm-gtk-greeter",
            "lightdm-gtk-greeter-settings",
            "xfce4-terminal",
            "thunar",
            "thunar-archive-plugin",
            "thunar-volman",
            "mousepad",
            "ristretto",
            "xfce4-screenshooter",
            "network-manager-applet",
            "pavucontrol",
            "gvfs",
            "gvfs-mtp",
            "xdg-user-dirs",
            "xdg-utils",
        ],
        "dm": "lightdm",
    },
    "hyprland": {
        "packages": [
            "hyprland",
            "xdg-desktop-portal-hyprland",
            "waybar",
            "wofi",
            "foot",
            "swaybg",
            "swaylock",
            "swayidle",
            "grim",
            "slurp",
            "wl-clipboard",
            "mako",
            "thunar",
            "polkit-gnome",
            "network-manager-applet",
            "pavucontrol",
            "brightnessctl",
            "playerctl",
            "sddm",
            "qt5-graphicaleffects",
            "qt5-quickcontrols2",
            "gvfs",
            "gvfs-mtp",
            "xdg-user-dirs",
            "xdg-utils",
        ],
        "dm": "sddm",
    },
    "gnome": {
        "packages": [
            "gnome",
            "gnome-tweaks",
            "gnome-themes-extra",
            "gdm",
            "networkmanager",
            "gvfs",
            "gvfs-mtp",
            "xdg-user-dirs",
            "xdg-utils",
        ],
        "dm": "gdm",
    },
}


def get_de_packages(de_id):
    """Get the package list for a desktop environment."""
    de = DE_PACKAGES.get(de_id, DE_PACKAGES["xfce"])
    return de["packages"]


def get_de_dm(de_id):
    """Get the display manager for a desktop environment."""
    de = DE_PACKAGES.get(de_id, DE_PACKAGES["xfce"])
    return de["dm"]
