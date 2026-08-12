# MediaGrab

**[🇹🇷 Türkçe](#türkçe) · [🇬🇧 English](#english)** · **[Latest Release: v1.1.0](https://github.com/umitkrkmz/mediagrab/releases/tag/v1.1.0)** · **[Changelog](CHANGELOG.md)**

---

## Türkçe

Link yapıştır, indir. Lokalde çalışan, kişisel kullanım için video/ses indirme aracı.

### Ne yapar

Bir YouTube veya YouTube Music linki (tekil video, playlist ya da albüm) yapıştırırsınız; MediaGrab linki çözümler, mevcut ses/video kalitelerini ve varsa altyazı dillerini listeler. Seçtiğiniz seçenek indirilir ve tarayıcıdan diskinize kaydedilir. YouTube dışında, yt-dlp'nin desteklediği diğer birçok site de (Vimeo, SoundCloud, X/Twitter, Twitch, archive.org vb. — [tam liste](https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md)) aynı akıştan çalışır; kanal takibi özelliği ise şimdilik yalnızca YouTube kanallarını destekler.

### Özellikler

- **Ses** — Opus / M4A (yeniden kodlanmadan, kalite kaybı yok) veya MP3 (evrensel uyumluluk için yeniden kodlanır)
- **Video** — mevcut tüm çözünürlükler, ses ile otomatik birleştirilmiş mp4 olarak
- **Altyazı** — elle eklenmiş altyazı dillerini işaretleyip seçtiğiniz videoyla birlikte, aynı dosya adıyla (`video.mp4` + `video.tr.srt`) indirir; medya oynatıcılar otomatik eşleştirir
- **Playlist & YouTube Music** — playlist linki yapıştırınca video listesi kapak/başlık/süre ile gelir, birine tıklayınca normal indirme akışı açılır
- **Çoklu platform** — YouTube'a özel değil; yt-dlp'nin desteklediği 1700'den fazla site (Vimeo, SoundCloud, X/Twitter, Twitch, archive.org vb.) aynı arayüzden çalışır
- **Meta veri (JSON) dışa aktarma** — her indirmeyle birlikte aynı dosya adıyla (`video.mp4` + `video.json`) başlık, kanal, yükleme tarihi, açıklama, etiketler ve kaynak linki gibi bilgileri içeren bir JSON dosyası kaydedilir; indirme detay sayfasından ayrıca indirilebilir
- **Otomatik klasörleme** — her indirme, kanal/yükleyici adına göre kendi alt klasörüne (`indirilenler/Kanal Adı/`) kaydedilir; disk üzerinde dosya gezgininde veya medya kitaplığı uygulamalarında düzenli görünür
- **Desteklenen Siteler sayfası** (`/supported-sites`) — yt-dlp'nin desteklediği popüler sitelerin kategorilere ayrılmış kısa bir listesi, tam listeye (1700+ site) link ile
- **yt-dlp sürüm kontrolü** (`/settings`) — kurulu yt-dlp sürümünü PyPI'daki güncel sürümle karşılaştırır, güncelleme gerekiyorsa adım adım talimat ve kopyalanabilir komut sunar
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
python run.py
```

Bu, sunucuyu başlatır ve tarayıcınızı otomatik olarak açar (varsayılan port 8420). Durdurmak için terminalde `Ctrl+C`.

Alternatif olarak, `uvicorn`'u doğrudan da çalıştırabilirsiniz:

```bash
uvicorn mediagrab.app:app --port 8420
```

Bu durumda tarayıcıda `http://127.0.0.1:8420` adresini elle açmanız gerekir.

> **Port çakışması:** 8000/3000/5000/8080 gibi "standart" portlar başka projelerle çakışabildiği için varsayılan 8420 seçildi. Ama `python run.py` ile çalıştırırsanız bununla da sınırlı değilsiniz: 8420 doluysa önce orada gerçekten MediaGrab çalışıp çalışmadığını kontrol eder — öyleyse aynı sekmeyi açar, değilse (başka bir projeniz o portu tutuyorsa) işletim sisteminden otomatik olarak boş bir port bulup onu kullanır. `uvicorn` komutunu doğrudan çalıştırırsanız bu otomatik davranış devreye girmez, çakışma durumunda `--port` ile elle farklı bir port seçmeniz gerekir.

### Kanal Takibi Nasıl Çalışır

MediaGrab sürekli arka planda çalışan bir servis **değil** — sadece siz açtığınızda çalışır. Bu yüzden kanal takibi de "her açılışta bir kez kontrol et" mantığıyla çalışır: uygulamayı başlattığınızda (`python run.py` veya `uvicorn` komutunu çalıştırdığınızda), takip listenizdeki tüm kanallar arka planda kontrol edilir. Uygulama kapalıyken yeni yüklenen videolar, siz tekrar açana kadar tespit edilmez — kişisel/lokal bir araç için beklenen davranış budur; 7/24 arka planda çalışan bir Windows servisi haline getirmek istemiyoruz.

Takip listesi ve son görülen video bilgisi, veritabanı yerine `channels.json` dosyasında (git'e dahil değil) tutulur — projenin geri kalanıyla aynı "gerçek veri diskte, ayrı bir DB yok" felsefesi.

### Sorun Giderme

**`ModuleNotFoundError` veya "paket bulunamadı" hatası**
Sanal ortamın etkin olduğundan emin olun (istem başında `(.venv)` görünmeli), sonra `pip install -r requirements.txt`'i tekrar çalıştırın.

**`ffmpeg`/`ffprobe` bulunamadı hatası**
ffmpeg'i kurduktan sonra **yeni bir terminal** açtığınızdan emin olun — PATH güncellemesi zaten açık olan terminalde görünmez. `ffmpeg -version` ile doğrulayın.

**`[Errno 10048] ... address already in use` / port 8420 dolu hatası**
`python run.py` ile çalıştırıyorsanız bu durum kendiliğinden çözülür (bkz. yukarıdaki port çakışması notu). `uvicorn` komutunu doğrudan kullanıyorsanız: muhtemelen önceki bir MediaGrab örneği hâlâ arka planda çalışıyor, ya da başka bir projeniz aynı portu kullanıyor — `--port` ile farklı bir port seçin.

Windows'ta hangi sürecin portu tuttuğunu bulup kapatmak için:

```powershell
Get-NetTCPConnection -LocalPort 8420 | Select-Object OwningProcess
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
    templates/      # Jinja2: base, index, history, item, settings, supported_sites
    static/         # style.css, app.js
indirilenler/       # indirilen dosyalar, kanal adına göre alt klasörlenir (git'e dahil değil)
    Kanal Adı/
        Video.mp4
        Video.json  # meta veri sidecar dosyası
channels.json       # takip edilen kanallar (git'e dahil değil)
run.py              # `python run.py` ile çalıştırmak için giriş noktası
requirements.txt
LICENSE
README.md
```

### Lisans ve Üçüncü Taraf Bildirimleri

MediaGrab'ın kendi kaynak kodu **MIT** lisansı ile lisanslanmıştır (bkz. [LICENSE](LICENSE)). Proje, dağıtım şekli olarak yalnızca **kaynak kod** olarak paylaşılır — kullanıcı repoyu klonlar, `pip install -r requirements.txt` ile kendi bağımlılıklarını kendi ortamına kurar ve `python run.py` ile çalıştırır. Paketlenmiş/derlenmiş bir `.exe` dağıtımı **yapılmıyor**.

| Paket | Lisans | Not |
|---|---|---|
| `yt-dlp` | Unlicense (kamu malı) | indirme/çözümleme motoru |
| `mutagen` | GPL-2.0-or-later | etiket/kapak/süre okuma — kodumuz bunu doğrudan `import` ediyor |
| `fastapi` | MIT | web çatısı |
| `starlette` | BSD-3-Clause | fastapi'nin ASGI katmanı |
| `uvicorn` | BSD-3-Clause | ASGI sunucusu |
| `pydantic` | MIT | veri doğrulama |
| `jinja2` | BSD-3-Clause | HTML şablonlama |
| `ffmpeg` / `ffprobe` | LGPL-2.1+ veya GPL-2+ (derlemeye göre değişir) | projeye dahil DEĞİL — kullanıcı kendi sistemine ayrıca kurar |

> **GPL notu:** `mutagen` GPL-2.0-or-later lisanslıdır ve kodumuz onu doğrudan `import` eder. Bu, GPL'in copyleft yükümlülüklerini tetikleyen bir "birleşik/derlenmiş yapıt dağıtımı" değildir — kullanıcı `pip` üzerinden kendi bağımlılığını kendi kurduğu için "mere aggregation" sayılır. Yükümlülük yalnızca MediaGrab'ın kodunu mutagen ile aynı pakette (ör. tek bir `.exe`) birleştirip dağıtırsanız devreye girerdi; bu proje bunu yapmıyor.

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

Paste a YouTube or YouTube Music link (a single video, a playlist, or an album). MediaGrab resolves it, lists the available audio/video qualities and any subtitle languages, and downloads whichever option you pick straight to your disk. Beyond YouTube, many other sites supported by yt-dlp (Vimeo, SoundCloud, X/Twitter, Twitch, archive.org, and more — [full list](https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md)) work through the same flow; channel following, however, currently supports YouTube channels only.

### Features

- **Audio** — Opus / M4A (remuxed, no re-encoding, no quality loss) or MP3 (re-encoded for universal compatibility)
- **Video** — every available resolution, auto-merged with audio into an mp4
- **Subtitles** — check off manually-provided subtitle languages and they download together with whichever video you pick, sharing the same filename (`video.mp4` + `video.en.srt`) so media players auto-match them
- **Playlists & YouTube Music** — paste a playlist link and get a list of videos with covers/titles/durations; click one to open the normal download flow
- **Multi-platform** — not YouTube-only; works through the same UI with any of the 1700+ sites yt-dlp supports (Vimeo, SoundCloud, X/Twitter, Twitch, archive.org, and more)
- **Metadata (JSON) export** — every download also saves a JSON file with the same base name (`video.mp4` + `video.json`) containing title, uploader, upload date, description, tags, and the source URL; also downloadable from the item detail page
- **Automatic folder organization** — every download is saved into its own subfolder by channel/uploader (`indirilenler/Channel Name/`), so files stay organized in your file explorer or media library apps
- **Supported Sites page** (`/supported-sites`) — a short, categorized list of popular sites yt-dlp supports, with a link to the full list (1700+ sites)
- **yt-dlp version check** (`/settings`) — compares your installed yt-dlp version against the latest on PyPI, and shows step-by-step instructions with a copyable command if an update is available
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
python run.py
```

This starts the server and opens your browser automatically (default port 8420). Stop it with `Ctrl+C` in the terminal.

Alternatively, you can run `uvicorn` directly:

```bash
uvicorn mediagrab.app:app --port 8420
```

In that case you'll need to open `http://127.0.0.1:8420` in your browser yourself.

> **Port conflicts:** 8420 was chosen as the default because "standard" ports like 8000/3000/5000/8080 tend to collide with other local projects. But `python run.py` isn't limited to that either: if 8420 is taken, it first checks whether it's actually another MediaGrab instance already running there — if so, it opens that same tab; if not (some other project is holding the port), it automatically asks the OS for a free port and uses that instead. Running `uvicorn` directly skips this automatic behavior, so you'd need to pick a different port yourself with `--port` if there's a conflict.

### How Channel Following Works

MediaGrab is **not** a persistent background service - it only runs while you have it open. So channel following works on a "check once per launch" basis: every time you start the app (running `python run.py` or the `uvicorn` command), every channel on your list is checked in the background. New uploads that happen while the app is closed aren't detected until you open it again - that's the expected behavior for a personal/local tool; we deliberately didn't turn this into a 24/7 Windows service.

The followed-channel list and each channel's "last seen video" state live in a `channels.json` file (not committed to git) instead of a database - same "real data lives on disk, no separate DB" philosophy as the rest of the project.

### Troubleshooting

**`ModuleNotFoundError` or "package not found" errors**
Make sure the virtual environment is active (you should see `(.venv)` in your prompt), then run `pip install -r requirements.txt` again.

**`ffmpeg`/`ffprobe` not found**
Make sure you opened a **new terminal** after installing ffmpeg — the PATH update doesn't show up in a terminal that was already open. Verify with `ffmpeg -version`.

**`[Errno 10048] ... address already in use` / port 8420 is busy**
If you're running with `python run.py`, this resolves itself automatically (see the port conflicts note above). If you're running `uvicorn` directly: a previous MediaGrab instance is probably still running in the background, or another project of yours is using the same port - pick a different one with `--port` in that case.

On Windows, find out which process holds the port and stop it with:

```powershell
Get-NetTCPConnection -LocalPort 8420 | Select-Object OwningProcess
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
    templates/      # Jinja2: base, index, history, item, settings, supported_sites
    static/         # style.css, app.js
indirilenler/       # downloaded files, auto-organized into per-channel subfolders (not in git)
    Channel Name/
        Video.mp4
        Video.json  # metadata sidecar
channels.json       # followed channels (not in git)
run.py              # entry point for `python run.py`
requirements.txt
LICENSE
README.md
```

### License & Third-Party Notices

MediaGrab's own source code is licensed under **MIT** (see [LICENSE](LICENSE)). The project is distributed as **source code only** — you clone the repo, install dependencies into your own environment with `pip install -r requirements.txt`, and run it with `python run.py`. No packaged/compiled `.exe` is distributed.

| Package | License | Note |
|---|---|---|
| `yt-dlp` | Unlicense (public domain) | download/resolve engine |
| `mutagen` | GPL-2.0-or-later | reads tags/cover art/duration — our code `import`s it directly |
| `fastapi` | MIT | web framework |
| `starlette` | BSD-3-Clause | fastapi's ASGI layer |
| `uvicorn` | BSD-3-Clause | ASGI server |
| `pydantic` | MIT | data validation |
| `jinja2` | BSD-3-Clause | HTML templating |
| `ffmpeg` / `ffprobe` | LGPL-2.1+ or GPL-2+ (depends on the build) | NOT bundled — the user installs it separately on their own system |

> **GPL note:** `mutagen` is GPL-2.0-or-later, and our code `import`s it directly. This doesn't trigger GPL's copyleft obligations, which apply to distributing a combined/compiled artifact — since users install their own copy of the dependency via `pip`, this counts as mere aggregation. The obligation would only kick in if MediaGrab's code were bundled together with mutagen into a single distributed package (e.g. one `.exe`), which this project does not do.

### Legal Notice

This tool is for **personal use only**. You are solely responsible for the copyright status of any content you download and for complying with the relevant platform's (including YouTube's) terms of service. MediaGrab is not a platform-circumvention or DRM-stripping tool — it only downloads publicly available, downloadable media via yt-dlp.

### Keep yt-dlp updated

YouTube changes its interface often; older yt-dlp versions eventually start failing to resolve or download. If you run into trouble, update first:

```bash
pip install -U yt-dlp
```
