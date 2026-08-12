# Changelog

Bu dosya MediaGrab'daki önemli değişiklikleri sürüm bazında listeler.
This file lists notable changes to MediaGrab, by release.

---

## [Türkçe](#türkçe-1) · [English](#english-1)

---

## Türkçe

### [1.1.0] — 2026-08-12

#### Eklenen

- **Çoklu platform desteği** — artık yalnızca YouTube değil, yt-dlp'nin desteklediği 1700'den fazla site (Vimeo, SoundCloud, X/Twitter, Twitch, archive.org vb.) aynı arayüzden çalışıyor
- **Meta veri (JSON) dışa aktarma** — her indirmeyle birlikte aynı dosya adıyla (`video.mp4` + `video.json`) başlık, kanal, yükleme tarihi, açıklama, etiketler ve kaynak linkini içeren bir JSON dosyası kaydediliyor; indirme detay sayfasından ayrıca indirilebiliyor
- **Otomatik klasörleme** — her indirme, kanal/yükleyici adına göre kendi alt klasörüne (`indirilenler/Kanal Adı/`) kaydediliyor
- **"Desteklenen Siteler" sayfası** (`/supported-sites`) — yt-dlp'nin desteklediği popüler sitelerin kategorilere ayrılmış kısa bir listesi, tam listeye link ile
- **yt-dlp sürüm kontrolü** (`/settings`) — kurulu yt-dlp sürümünü PyPI'daki güncel sürümle karşılaştırır, güncelleme gerekiyorsa adım adım talimat ve kopyalanabilir komut sunar, yt-dlp'ye GitHub'da teşekkür linki içerir
- **Otomatik boş port bulma** (`run.py`) — tercih edilen port (8420) başka bir uygulama tarafından tutuluyorsa, gerçekten MediaGrab mı çalışıyor diye kontrol eder; değilse işletim sisteminden boş bir port isteyip oraya geçer

#### Değiştirilen

- **"Dosyayı indir" → "Klasörde göster"** — bu buton artık yalnızca dosya gezgininde gösteriyor; önceden hem dosya gezgininde açıyor hem de tarayıcının kendi indirilenler klasörüne ikinci bir kopya kaydediyordu (gereksiz çift dosya oluşturuyordu)
- Varsayılan port `8000` → `8420` (yaygın portlarla çakışmayı azaltmak için; artık üstteki otomatik boş port bulma ile birlikte çalışıyor)
- README, kaynak koddan çalıştırma modelini (`python run.py`) birincil yöntem olarak belgeliyor; exe'ye özel talimatlar kaldırıldı

#### Düzeltilen

- Video kalite listesi, `vcodec` alanını YouTube dışındaki sitelerde (ör. archive.org) boş bırakan durumlarda tüm video seçeneklerini yanlışlıkla gizliyordu — artık yalnızca gerçekten "video yok" (`vcodec: "none"`) durumunda gizleniyor
- yt-dlp sürüm karşılaştırması, PyPI'nin normalize ettiği sürüm formatı (`2026.7.4`) ile yerel kurulu sürümün sıfır dolgulu formatını (`2026.07.04`) aynı sürüm olsa bile farklı gösteriyordu — sayısal karşılaştırmaya geçildi

### [1.0.0] — 2026-08-12

İlk kararlı sürüm. Bkz. [GitHub Release](https://github.com/umitkrkmz/mediagrab/releases/tag/v1.0.0).

---

## English

### [1.1.0] — 2026-08-12

#### Added

- **Multi-platform support** — no longer YouTube-only; works with any of the 1700+ sites yt-dlp supports (Vimeo, SoundCloud, X/Twitter, Twitch, archive.org, and more) through the same UI
- **Metadata (JSON) export** — every download also saves a JSON file with the same base name (`video.mp4` + `video.json`) containing title, uploader, upload date, description, tags, and the source URL; also downloadable from the item detail page
- **Automatic folder organization** — every download is saved into its own subfolder by channel/uploader (`indirilenler/Channel Name/`)
- **Supported Sites page** (`/supported-sites`) — a short, categorized list of popular sites yt-dlp supports, with a link to the full list
- **yt-dlp version check** (`/settings`) — compares your installed yt-dlp version against the latest on PyPI, shows step-by-step update instructions with a copyable command, and links to yt-dlp's GitHub as a thank-you to its contributors
- **Automatic free-port fallback** (`run.py`) — if the preferred port (8420) is taken, checks whether it's actually another MediaGrab instance; if not, asks the OS for a free port and uses that instead

#### Changed

- **"Download file" → "Show in folder"** — this button now only reveals the file in your OS file explorer; it used to also stream a second copy through the browser's own downloads folder, silently duplicating every download
- Default port `8000` → `8420` (to reduce collisions with common ports; now paired with the automatic free-port fallback above)
- README now documents running from source (`python run.py`) as the primary flow; exe-specific instructions removed

#### Fixed

- The video quality list was incorrectly hiding all video options on sites (e.g. archive.org) that leave the `vcodec` field unset instead of explicitly `"none"` (a YouTube-specific convention) — now only the explicit `"none"` marker is treated as "no video track"
- The yt-dlp version check compared PyPI's normalized version string (`2026.7.4`) against the locally zero-padded one (`2026.07.04`) as plain text, flagging up-to-date installs as outdated — switched to numeric comparison

### [1.0.0] — 2026-08-12

First stable release. See the [GitHub Release](https://github.com/umitkrkmz/mediagrab/releases/tag/v1.0.0).
