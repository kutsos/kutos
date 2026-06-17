package config

// InstallConfig kurulum sihirbazı boyunca tüm sayfalara geçilen ortak durum.
type InstallConfig struct {
	// Disk
	TargetDisk    string // örn: /dev/sda
	PartitionMode string // "erase" (şimdilik tek mod)
	Filesystem    string // "ext4" | "btrfs"
	SwapSize      string // "none" | "2G" | "4G" | "8G"

	// Locale
	Timezone string // örn: Europe/Istanbul
	Locale   string // örn: tr_TR.UTF-8

	// Keyboard
	KeyboardLayout  string // örn: tr
	KeyboardVariant string // boş veya örn: f

	// Kullanıcı
	Username     string
	Password     string
	RootPassword string
	Hostname     string
	Autologin    bool

	// Bootloader
	InstallGRUB bool
	EFIMode     bool // true = UEFI, false = BIOS
}

func New() *InstallConfig {
	return &InstallConfig{
		Filesystem:     "ext4",
		SwapSize:       "none",
		Timezone:       "Europe/Istanbul",
		Locale:         "tr_TR.UTF-8",
		KeyboardLayout: "tr",
		InstallGRUB:    true,
	}
}
