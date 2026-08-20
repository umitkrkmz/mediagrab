# Changelog

Bu dosya MediaGrab'daki önemli değişiklikleri sürüm bazında listeler.
This file lists notable changes to MediaGrab, by release.

---

## [Türkçe](#türkçe-1) · [English](#english-1)

---

## Türkçe

### [1.3.0] — 2026-08-20

#### Eklenen

- **Kolay kurulum aracı** (`MediaGrabSetup.exe`, GitHub Release'de) — Git/Python'un kurulu olup olmadığını kontrol eder (eksikse resmi indirme sayfasına yönlendirir), tek tıkla kurar/günceller/kaldırır; isteğe bağlı Masaüstü ve Başlat menüsü kısayolu ekler. Kurulum, `indirilenler/` ve `channels.json`'a hiçbir zaman dokunmaz. Başlatmak için oluşturulan `MediaGrab Baslat.bat` dosyasına çift tıklamak yeterli, terminal gerekmez
- **Transkripti video/sesle birlikte indirme** — transkript artık ayrı bir "chip" olarak seçilebiliyor; seçiliyken herhangi bir ses/video kalitesine tıklayınca ikisi de tek seferde, linki tekrar çözümlemeden iniyor
- **Otomatik altyazı artık indirilebilir altyazı olarak da sunuluyor** — bir videoda hiç elle eklenmiş altyazı yoksa, tek otomatik altyazı artık "Altyazı" bölümünde de bir seçenek olarak çıkıyor (`.srt` olarak videoyla birlikte iner), önceden sadece düz metin transkript olarak indirilebiliyordu
- **Zaman damgalı transkript** — transkript indirirken isteğe bağlı bir kutucukla `[SS:DD:SS] satır` formatında zaman damgalı çıktı alınabiliyor, varsayılan hâlâ düz paragraf

#### Düzeltilen

- Kurulum aracı Windows'ta git'in salt-okunur işaretlediği bazı dosyalar yüzünden `.git` klasörünü tam silemiyordu (Onar/Kaldır sırasında) — düzeltildi

### [1.2.0] — 2026-08-19

#### Eklenen

- **Transkript indirme** — altyazısı (elle eklenmiş veya otomatik oluşturulmuş) olan videolar için düz metin transkript (`.txt`) ayrıca indirilebiliyor
- **Link yapıştır ve hızlı seçenekler** — panodaki linki otomatik algılayan yapıştır butonu; en iyi ses/en iyi video için tek tıkla hızlı indirme butonları, diğer tüm kalite/format seçenekleri daraltılmış "gelişmiş seçenekler" alanında
- **Kalıcı indirme paneli** — aynı anda birden fazla indirmeyi takip edin; sayfa değiştirseniz veya uygulamayı kapatıp tekrar açsanız bile ilerleme durumu korunur
- **Tek tıkla yt-dlp güncelleme** (`/settings`) — güncelleme mevcutsa tek tıkla kurulur, uygulama otomatik olarak kendini yeniden başlatır
- **Geçmişte arama ve kanal filtresi** — indirme geçmişinde başlığa göre arama, kanala göre filtreleme
- **Sayfa içi önizleme** — ses/video dosyalarını indirme detay sayfasından, dosya gezgini açmadan doğrudan oynatın
- **Uygulama olarak yükleme (PWA)** — tarayıcının "Ana ekrana ekle" seçeneğiyle bağımsız bir uygulama gibi kullanılabilir
- **Anlaşılır hata mesajları** — yaygın durumlar (yaş sınırı, bot koruması, coğrafi kısıtlama, kaldırılmış video vb.) için yt-dlp'nin ham çıktısı yerine açıklayıcı mesajlar gösteriliyor

#### Değiştirilen

- **`mutagen` bağımlılığı kaldırıldı** — etiket/kapak/süre okuma artık zaten sistemde kurulu olan `ffprobe`/`ffmpeg` üzerinden yapılıyor; GPL bağımlılık ortadan kalktı, tüm doğrudan bağımlılıklar artık izin verici (MIT/BSD) veya kamu malı lisanslı

#### Düzeltilen

- Kalıcı indirme paneli, sunucu yeniden başladığında oluşan geçersiz iş kayıtlarını artık hata göstermeden sessizce temizliyor
- Otomatik oluşturulmuş (YouTube) altyazılardan üretilen transkriptlerde metin iki kere tekrar ediyordu — düzeltildi

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

### [1.3.0] — 2026-08-20

#### Added

- **Easy-install tool** (`MediaGrabSetup.exe`, on the GitHub Release) — checks whether Git/Python are installed (points to the official download page if not), installs/updates/removes with one click, and can optionally add a Desktop and/or Start Menu shortcut. Never touches `indirilenler/` or `channels.json`. Once installed, just double-click the generated `MediaGrab Baslat.bat` to launch - no terminal needed
- **Bundle the transcript with a video/audio download** — the transcript is now a selectable "chip"; with it selected, clicking any audio/video quality downloads both together in one go, without having to re-resolve the link
- **Auto-generated captions are now offered as a downloadable subtitle too** — when a video has no manual subtitles at all, its single auto-generated caption now also shows up as an option in the Subtitles section (downloads as `.srt` alongside the video), not just as a plain-text transcript
- **Timestamped transcript** — an optional checkbox produces `[HH:MM:SS] line` formatted output instead of one flowing paragraph

#### Fixed

- The installer tool couldn't fully delete the `.git` folder on Windows during Repair/Remove, because git marks some of its files read-only - fixed

### [1.2.0] — 2026-08-19

#### Added

- **Transcript download** — for videos with subtitles (manual or auto-generated), a plain-text transcript (`.txt`) can now be downloaded separately
- **Paste-to-resolve & quick options** — a paste button that auto-detects the clipboard link; one-click buttons for best audio/best video, with every other quality/format option tucked under a collapsed "advanced options" section
- **Persistent download panel** — track multiple downloads at once; progress survives page navigation and even closing and reopening the app
- **One-click yt-dlp update** (`/settings`) — if an update is available, it installs with one click and the app restarts itself automatically
- **History search & channel filter** — search download history by title, filter by channel
- **In-place preview** — play audio/video files straight from the item detail page without opening a file explorer
- **Installable app (PWA)** — use your browser's "Add to Home Screen" to run MediaGrab like a standalone app
- **Friendly error messages** — common cases (age restriction, bot check, geo-restriction, removed videos, and more) now show an explanatory message instead of yt-dlp's raw output

#### Changed

- **Removed the `mutagen` dependency** — tag/cover-art/duration reading now goes through the `ffprobe`/`ffmpeg` you already have installed; this removes the project's only GPL dependency, so every direct dependency is now permissively licensed (MIT/BSD) or public domain

#### Fixed

- The persistent download panel now silently cleans up stale job entries left over from a server restart instead of showing them as errors
- Transcripts generated from auto-generated (YouTube) captions had every line duplicated — fixed

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
