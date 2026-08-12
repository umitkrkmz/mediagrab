# MediaGrab

**[🇹🇷 Türkçe](#türkçe) · [🇬🇧 English](#english)** · **[Latest Release: v1.0.0](https://github.com/umitkrkmz/mediagrab/releases/tag/v1.0.0)**

---

## Türkçe

Link yapıştır, indir. Lokalde çalışan, kişisel kullanım için video/ses indirme aracı.

### Ne yapar

Bir YouTube veya YouTube Music linki (tekil video, playlist ya da albüm) yapıştırırsınız; MediaGrab linki çözümler, mevcut ses/video kalitelerini ve varsa altyazı dillerini listeler. Seçtiğiniz seçenek indirilir ve tarayıcıdan diskinize kaydedilir.

### Özellikler

- **Ses** — Opus / M4A (yeniden kodlanmadan, kalite kaybı yok) veya MP3 (evrensel uyumluluk için yeniden kodlanır)
- **Video** — mevcut tüm çözünürlükler, ses ile otomatik birleştirilmiş mp4 olarak
- **Altyazı** — elle eklenmiş altyazı dillerini işaretleyip seçtiğiniz videoyla birlikte, aynı dosya adıyla (`video.mp4` + `video.tr.srt`) indirir; medya oynatıcılar otomatik eşleştirir
- **Playlist & YouTube Music** — playlist linki yapıştırınca video listesi kapak/başlık/süre ile gelir, birine tıklayınca normal indirme akışı açılır
- **Kanal takibi** (`/settings`) — bir kanalı takibe alın; uygulamayı her açtığınızda yeni video var mı diye kontrol edilir. İki mod: **Bildir** (ana sayfada banner ile haber verir, siz seçersiniz) veya **Otomatik indir** (seçtiğiniz formatta kendiliğinden indirir). Sürekli arka planda çalışan bir servis değil — bkz. aşağıdaki not.
- **İndirme geçmişi** — kapak resimli kart görünümünde, ayrı bir sayfada (`/history`); tekrar indirme, silme, tümünü silme
- **Otomatik dosya gezgini** — "Dosyayı indir"e tıklayınca dosya, işletim sisteminin dosya gezgininde seçili şekilde açılır
- **Türkçe / İngilizce arayüz** — sistem diline göre otomatik, elle de değiştirilebilir
- Veritabanı, hesap sistemi veya bulut bağlantısı **yok** — yalnızca bu bilgisayarda çalışır

### Kurulum

**1. Proje dosyalarını indirin**

```bash
git clone https://github.com/umitkrkmz/mediagrab.git
cd mediagrab
```

**2. Sanal ortam oluşturun ve etkinleştirin**

Bağımlılıkları sisteminize değil, projeye özel bir ortama kurmak için:

Windows (PowerShell):

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

macOS / Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

İstem satırının başında `(.venv)` görünüyorsa ortam etkindir. Bundan sonraki tüm komutları bu ortam etkinken, aynı terminalde çalıştırın.

**3. Python bağımlılıklarını kurun**

```bash
pip install -r requirements.txt
```

**4. ffmpeg (sistem bağımlılığı — zorunlu)**

yt-dlp, remux/merge/encode işlemleri için; MediaGrab ise doğru medya süresini okumak için `ffprobe`'u sistem PATH'inden çağırır.

Windows:

```bash
winget install --id Gyan.FFmpeg -e
```

Kurulumdan sonra **yeni bir terminal** açın — PATH güncellemesi zaten açık olan terminalde görünmeyebilir.

macOS:

```bash
brew install ffmpeg
```

Linux (Debian/Ubuntu):

```bash
sudo apt install ffmpeg
```

Doğrulamak için: `ffmpeg -version`

### Çalıştırma

Sanal ortam etkinken, proje kök dizininden:

```bash
uvicorn mediagrab.app:app
```

Tarayıcıda `http://127.0.0.1:8000` adresini açın. Durdurmak için terminalde `Ctrl+C`.

Kaynak kod yerine hazır Windows exe'sini kullanıyorsanız (bkz. [Releases](../../releases)): sunucuyu kapatmak için konsol penceresini X ile kapatmak yerine tıklayıp **`Ctrl+C`** yapın. X ile kapatmak süreci arka planda bırakabilir, 8000 portunu tutmaya devam eder ve bir dahaki açışta yeni sunucu başlamaz (sadece eski pencereyi tarayıcıda açar). Böyle bir durumda Görev Yöneticisi'nden `MediaGrab.exe`'yi sonlandırın.

### Kanal Takibi Nasıl Çalışır

MediaGrab sürekli arka planda çalışan bir servis **değil** — sadece siz açtığınızda çalışır. Bu yüzden kanal takibi de "her açılışta bir kez kontrol et" mantığıyla çalışır: uygulamayı başlattığınızda (`uvicorn` komutunu çalıştırdığınızda ya da exe'yi açtığınızda), takip listenizdeki tüm kanallar arka planda kontrol edilir. Uygulama kapalıyken yeni yüklenen videolar, siz tekrar açana kadar tespit edilmez — kişisel/lokal bir araç için beklenen davranış budur; 7/24 arka planda çalışan bir Windows servisi haline getirmek istemiyoruz.

Takip listesi ve son görülen video bilgisi, veritabanı yerine `channels.json` dosyasında (git'e dahil değil) tutulur — projenin geri kalanıyla aynı "gerçek veri diskte, ayrı bir DB yok" felsefesi.

### Sorun Giderme

**`ModuleNotFoundError` veya "paket bulunamadı" hatası**
Sanal ortamın etkin olduğundan emin olun (istem başında `(.venv)` görünmeli), sonra `pip install -r requirements.txt`'i tekrar çalıştırın.

**`ffmpeg`/`ffprobe` bulunamadı hatası**
ffmpeg'i kurduktan sonra **yeni bir terminal** açtığınızdan emin olun — PATH güncellemesi zaten açık olan terminalde görünmez. `ffmpeg -version` ile doğrulayın.

**`[Errno 10048] ... address already in use` / port 8000 dolu hatası**
Muhtemelen önceki bir MediaGrab örneği (kaynak koddan ya da exe'den) hâlâ arka planda çalışıyor.

Windows'ta bulup kapatmak için:

```powershell
Get-NetTCPConnection -LocalPort 8000 | Select-Object OwningProcess
Stop-Process -Id <yukarıdaki PID> -Force
```

**`ImportError: attempted relative import with no known parent package`**
`mediagrab/app.py`'yi doğrudan `python app.py` ile çalıştırmayın; her zaman proje kök dizininden `uvicorn mediagrab.app:app` kullanın — aksi halde paket içi göreli importlar çalışmaz.

**yt-dlp bir videoyu çözemiyor / "Unable to extract" hatası**
YouTube arayüzünü değiştirdiğinde eski yt-dlp sürümleri bozulur. Güncelleyin:

```bash
pip install -U yt-dlp
```

### Proje yapısı

```
mediagrab/
    app.py          # FastAPI uygulaması, endpoint'ler
    downloader.py   # yt-dlp sarmalayıcı — yt_dlp importu SADECE burada
    models.py       # Pydantic modelleri
    store.py        # channels.json okuma/yazma (kanal takibi, DB değil)
    paths.py         # kaynak/exe modunda doğru klasör yollarını çözer
    templates/      # Jinja2: base, index, history, item, settings
    static/         # style.css, app.js
indirilenler/       # indirilen dosyalar (git'e dahil değil)
channels.json       # takip edilen kanallar (git'e dahil değil)
requirements.txt
LICENSE
README.md
```

### Lisans ve Üçüncü Taraf Bildirimleri

MediaGrab'ın kendi kaynak kodu **MIT** lisansı ile lisanslanmıştır (bkz. [LICENSE](LICENSE)). Ancak proje, kendi lisanslarına sahip üçüncü taraf paketlere bağımlıdır — bunlardan biri **copyleft (GPL)**'dir ve toplu/derlenmiş bir dağıtım (ör. paketlenmiş `.exe`'yi başkalarıyla paylaşmak) yaparsanız ek yükümlülük getirir:

| Paket | Lisans | Not |
|---|---|---|
| `yt-dlp` | Unlicense (kamu malı) | indirme/çözümleme motoru |
| `mutagen` | **GPL-2.0-or-later** | etiket/kapak/süre okuma — kodumuz bunu doğrudan `import` ediyor, paketlenmiş `.exe`'ye de gömülüyor |
| `fastapi` | MIT | web çatısı |
| `starlette` | BSD-3-Clause | fastapi'nin ASGI katmanı |
| `uvicorn` | BSD-3-Clause | ASGI sunucusu |
| `pydantic` | MIT | veri doğrulama |
| `jinja2` | BSD-3-Clause | HTML şablonlama |
| `ffmpeg` / `ffprobe` | LGPL-2.1+ veya GPL-2+ (derlemeye göre değişir) | projeye dahil DEĞİL — kullanıcı kendi sistemine ayrıca kurar |

> **GPL notu:** `mutagen` GPL-2.0-or-later lisanslıdır ve kodumuz onu doğrudan `import` eder (ffmpeg gibi ayrı bir süreç olarak çağırmak değil). Bu depoyu *kaynak kod* olarak paylaşmak — kullanıcıların `pip install` ile kendi bağımlılıklarını kurduğu bu kurulum şekli — pratikte bir sorun oluşturmaz. Paketlenmiş `.exe`'yi yalnızca kendiniz kullandığınız sürece de bir sorun yok (GPL yükümlülüğü ancak *dağıtımda* devreye girer). Ancak exe'yi başkalarına dağıtmayı planlarsanız, birleşik yapıt GPL yükümlülüklerine tabi olur: ya tüm paketi GPL uyumlu bir lisansla dağıtmanız ya da `mutagen` yerine izin verici lisanslı bir alternatif kullanmanız gerekir.

### Yasal Uyarı

Bu araç yalnızca **kişisel kullanım** içindir. İndirdiğiniz içeriğin telif durumundan ve ilgili platformun (YouTube dahil) kullanım şartlarına uyumdan tamamen siz sorumlusunuz. MediaGrab bir platformu atlatma veya DRM kırma aracı değildir; yalnızca herkese açık, indirilebilir medyayı yt-dlp aracılığıyla indirir.

### yt-dlp güncel tutulmalı

YouTube arayüzünü sık değiştirir; eski yt-dlp sürümleri zamanla çözümleme/indirme hatası vermeye başlar. Sorun yaşarsanız önce güncelleyin:

```bash
pip install -U yt-dlp
```

---

## English

Paste a link, download it. A local, personal-use video/audio downloader.

### What it does

Paste a YouTube or YouTube Music link (a single video, a playlist, or an album). MediaGrab resolves it, lists the available audio/video qualities and any subtitle languages, and downloads whichever option you pick straight to your disk.

### Features

- **Audio** — Opus / M4A (remuxed, no re-encoding, no quality loss) or MP3 (re-encoded for universal compatibility)
- **Video** — every available resolution, auto-merged with audio into an mp4
- **Subtitles** — check off manually-provided subtitle languages and they download together with whichever video you pick, sharing the same filename (`video.mp4` + `video.en.srt`) so media players auto-match them
- **Playlists & YouTube Music** — paste a playlist link and get a list of videos with covers/titles/durations; click one to open the normal download flow
- **Channel following** (`/settings`) — follow a channel; every time you open the app, it's checked for new videos. Two modes: **Notify** (a banner on the home page tells you, you pick what to download) or **Auto-download** (downloads new uploads automatically in your chosen format). Not a persistent background service - see the note below.
- **Download history** — cover-art cards on their own page (`/history`); re-download, delete, or clear all
- **Auto reveal in file explorer** — clicking "Download file" opens your OS file explorer with the file selected
- **Turkish / English UI** — follows your system locale by default, switchable by hand
- **No** database, account system, or cloud connection — runs only on this machine

### Installation

**1. Get the project files**

```bash
git clone https://github.com/umitkrkmz/mediagrab.git
cd mediagrab
```

**2. Create and activate a virtual environment**

Keeps dependencies scoped to the project instead of your whole system:

Windows (PowerShell):

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

macOS / Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

You'll see `(.venv)` at the start of your prompt once it's active. Run every command below in that same terminal, with the environment active.

**3. Install Python dependencies**

```bash
pip install -r requirements.txt
```

**4. ffmpeg (system dependency — required)**

yt-dlp uses it for remux/merge/encode steps; MediaGrab itself calls `ffprobe` from PATH to read accurate media duration.

Windows:

```bash
winget install --id Gyan.FFmpeg -e
```

Open a **new terminal** afterwards — the PATH update may not show up in a terminal that was already open.

macOS:

```bash
brew install ffmpeg
```

Linux (Debian/Ubuntu):

```bash
sudo apt install ffmpeg
```

Verify with: `ffmpeg -version`

### Running

With the virtual environment active, from the project root:

```bash
uvicorn mediagrab.app:app
```

Open `http://127.0.0.1:8000` in your browser. Stop it with `Ctrl+C` in the terminal.

If you're using the prebuilt Windows exe instead of source (see [Releases](../../releases)): stop it by clicking the console window and pressing **`Ctrl+C`**, not by closing the window with the X button. Closing with X can leave the process running in the background holding port 8000, so the next launch won't start a fresh server (it'll just reopen your browser to the old instance). If that happens, end `MediaGrab.exe` in Task Manager.

### How Channel Following Works

MediaGrab is **not** a persistent background service - it only runs while you have it open. So channel following works on a "check once per launch" basis: every time you start the app (running the `uvicorn` command, or opening the exe), every channel on your list is checked in the background. New uploads that happen while the app is closed aren't detected until you open it again - that's the expected behavior for a personal/local tool; we deliberately didn't turn this into a 24/7 Windows service.

The followed-channel list and each channel's "last seen video" state live in a `channels.json` file (not committed to git) instead of a database - same "real data lives on disk, no separate DB" philosophy as the rest of the project.

### Troubleshooting

**`ModuleNotFoundError` or "package not found" errors**
Make sure the virtual environment is active (you should see `(.venv)` in your prompt), then run `pip install -r requirements.txt` again.

**`ffmpeg`/`ffprobe` not found**
Make sure you opened a **new terminal** after installing ffmpeg — the PATH update doesn't show up in a terminal that was already open. Verify with `ffmpeg -version`.

**`[Errno 10048] ... address already in use` / port 8000 is busy**
A previous MediaGrab instance (from source or the exe) is probably still running in the background.

On Windows, find and stop it with:

```powershell
Get-NetTCPConnection -LocalPort 8000 | Select-Object OwningProcess
Stop-Process -Id <PID from above> -Force
```

**`ImportError: attempted relative import with no known parent package`**
Don't run `mediagrab/app.py` directly with `python app.py`; always use `uvicorn mediagrab.app:app` from the project root — otherwise the package's internal relative imports break.

**yt-dlp fails to resolve a video / "Unable to extract" error**
Older yt-dlp versions break whenever YouTube changes its interface. Update it:

```bash
pip install -U yt-dlp
```

### Project structure

```
mediagrab/
    app.py          # FastAPI app, endpoints
    downloader.py   # yt-dlp wrapper — the ONLY file that imports yt_dlp
    models.py       # Pydantic models
    store.py        # reads/writes channels.json (channel following, not a DB)
    paths.py         # resolves the right folders whether running from source or as the exe
    templates/      # Jinja2: base, index, history, item, settings
    static/         # style.css, app.js
indirilenler/       # downloaded files (not in git)
channels.json       # followed channels (not in git)
requirements.txt
LICENSE
README.md
```

### License & Third-Party Notices

MediaGrab's own source code is licensed under **MIT** (see [LICENSE](LICENSE)). The project depends on third-party packages under their own licenses, though — one of which is **copyleft (GPL)** and carries extra obligations if you distribute a bundled build (e.g. sharing the packaged `.exe` with others):

| Package | License | Note |
|---|---|---|
| `yt-dlp` | Unlicense (public domain) | download/resolve engine |
| `mutagen` | **GPL-2.0-or-later** | reads tags/cover art/duration — our code `import`s it directly, and it's bundled into the packaged `.exe` |
| `fastapi` | MIT | web framework |
| `starlette` | BSD-3-Clause | fastapi's ASGI layer |
| `uvicorn` | BSD-3-Clause | ASGI server |
| `pydantic` | MIT | data validation |
| `jinja2` | BSD-3-Clause | HTML templating |
| `ffmpeg` / `ffprobe` | LGPL-2.1+ or GPL-2+ (depends on the build) | NOT bundled — the user installs it separately on their own system |

> **GPL note:** `mutagen` is GPL-2.0-or-later, and our code `import`s it directly (unlike ffmpeg, which we only invoke as a separate process). Sharing this repo as *source code* — where users run `pip install` themselves — isn't a practical problem. Using the packaged `.exe` yourself isn't either (GPL obligations only kick in on *distribution*). But if you plan to hand the exe to other people, the combined artifact becomes subject to GPL obligations: either license the whole bundle under a GPL-compatible license, or swap `mutagen` for a permissively-licensed alternative.

### Legal Notice

This tool is for **personal use only**. You are solely responsible for the copyright status of any content you download and for complying with the relevant platform's (including YouTube's) terms of service. MediaGrab is not a platform-circumvention or DRM-stripping tool — it only downloads publicly available, downloadable media via yt-dlp.

### Keep yt-dlp updated

YouTube changes its interface often; older yt-dlp versions eventually start failing to resolve or download. If you run into trouble, update first:

```bash
pip install -U yt-dlp
```
