# MediaGrab

**[🇹🇷 Türkçe](#türkçe) · [🇬🇧 English](#english)** · **[Latest Release: v1.5.0](https://github.com/umitkrkmz/mediagrab/releases/tag/v1.5.0)** · **[Changelog](CHANGELOG.md)**

---

## Türkçe

Link yapıştır, indir. Lokalde çalışan, kişisel kullanım için video/ses indirme aracı.

### Ne yapar

Bir YouTube veya YouTube Music linki (tekil video, playlist ya da albüm) yapıştırırsınız; MediaGrab linki çözümler, mevcut ses/video kalitelerini ve varsa altyazı dillerini listeler. Seçtiğiniz seçenek indirilir ve tarayıcıdan diskinize kaydedilir. YouTube dışında, yt-dlp'nin desteklediği diğer birçok site de (Vimeo, SoundCloud, X/Twitter, Twitch, archive.org vb. — [tam liste](https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md)) aynı akıştan çalışır; kanal takibi özelliği ise şimdilik yalnızca YouTube kanallarını destekler.

### Özellikler

- **Ses** — Opus / M4A (yeniden kodlanmadan, kalite kaybı yok) veya MP3 (evrensel uyumluluk için yeniden kodlanır)
- **Video** — mevcut tüm çözünürlükler, ses ile otomatik birleştirilmiş mp4 olarak
- **Altyazı** — elle eklenmiş altyazı dillerini işaretleyip seçtiğiniz videoyla birlikte, aynı dosya adıyla (`video.mp4` + `video.tr.srt`) indirir; medya oynatıcılar otomatik eşleştirir
- **Transkript indirme** — altyazısı (elle eklenmiş veya otomatik oluşturulmuş) olan videolar için düz metin transkripti (`.txt`) ayrıca indirebilirsiniz
- **Link yapıştır & hızlı seçenekler** — panodaki linki otomatik algılayan yapıştır butonu; en iyi ses/en iyi video için tek tıkla hızlı indirme, diğer tüm kalite/format seçenekleri "gelişmiş seçenekler" altında
- **Kalıcı indirme paneli** — aynı anda birden fazla indirmeyi takip edin; sayfa değiştirseniz veya uygulamayı kapatıp tekrar açsanız bile ilerleme durumu korunur
- **Sayfa içi önizleme** — indirme detay sayfasından ses/video dosyalarını dosya gezgini açmadan doğrudan oynatın
- **Uygulama olarak yükleme (PWA)** — tarayıcının "Ana ekrana ekle" seçeneğiyle MediaGrab'ı bağımsız bir uygulama gibi kullanabilirsiniz
- **Playlist & YouTube Music** — playlist linki yapıştırınca video listesi kapak/başlık/süre ile gelir; birine tıklayıp tek tek indirebilir ya da aralık seçip (ör. 1–19) **tümünü tek tıkla** kuyruğa atabilirsiniz
- **Çoklu platform** — YouTube'a özel değil; yt-dlp'nin desteklediği 1700'den fazla site (Vimeo, SoundCloud, X/Twitter, Twitch, archive.org vb.) aynı arayüzden çalışır
- **Meta veri (JSON) dışa aktarma** — her indirmeyle birlikte aynı dosya adıyla (`video.mp4` + `video.json`) başlık, kanal, yükleme tarihi, açıklama, etiketler ve kaynak linki gibi bilgileri içeren bir JSON dosyası kaydedilir; indirme detay sayfasından ayrıca indirilebilir
- **Otomatik klasörleme** — her indirme, kanal/yükleyici adına göre kendi alt klasörüne (`indirilenler/Kanal Adı/`) kaydedilir; disk üzerinde dosya gezgininde veya medya kitaplığı uygulamalarında düzenli görünür
- **Desteklenen Siteler sayfası** (`/supported-sites`) — yt-dlp'nin desteklediği popüler sitelerin kategorilere ayrılmış kısa bir listesi, tam listeye (1700+ site) link ile
- **yt-dlp sürüm kontrolü ve tek tıkla güncelleme** (`/settings`) — kurulu yt-dlp sürümünü PyPI'daki güncel sürümle karşılaştırır; güncelleme varsa tek tıkla kurar ve uygulamayı otomatik olarak yeniden başlatır
- **Kanal takibi** (`/channels`) — bir kanalı takibe alın; uygulamayı her açtığınızda yeni video var mı diye kontrol edilir. İki mod: **Bildir** (ana sayfada banner ile haber verir, siz seçersiniz) veya **Otomatik indir** (seçtiğiniz formatta kendiliğinden indirir). Sürekli arka planda çalışan bir servis değil — bkz. aşağıdaki not.
- **İndirme geçmişi** — kapak resimli kart görünümünde, ayrı bir sayfada (`/history`); başlığa göre arama ve kanala göre filtreleme, tekrar indirme, silme, tümünü silme
- **Açık / koyu tema** — sistem ayarını takip eder, `/settings` sayfasından veya başlıktaki düğmeyle elle de seçilebilir
- **İndirmeyi iptal etme** — süren bir indirmeyi panelden durdurun; yarım kalan dosyalar otomatik temizlenir
- **Var olan dosyayı koruma** — aynı videoyu tekrar indirirken iptal, hata veya çökme olursa eski dosyanız aynen geri gelir
- **Ortam kontrolü** (`/settings`) — ffmpeg/ffprobe sürümü ve Python bağımlılıkları güncel mi diye kontrol edilir; paketler tek tıkla güncellenebilir
- **Anlaşılır hata mesajları** — yaygın durumlar (yaş sınırı, bot koruması, coğrafi kısıtlama, kaldırılmış video vb.) için yt-dlp'nin ham çıktısı yerine açıklayıcı Türkçe/İngilizce mesajlar gösterilir
- **Otomatik dosya gezgini** — "Dosyayı indir"e tıklayınca dosya, işletim sisteminin dosya gezgininde seçili şekilde açılır
- **Türkçe / İngilizce arayüz** — sistem diline göre otomatik, elle de değiştirilebilir
- Veritabanı, hesap sistemi veya bulut bağlantısı **yok** — yalnızca bu bilgisayarda çalışır

### Kurulum

Windows'ta iki yol var: **kolay kurulum** (hazır `.exe`, terminal komutu yazmadan) veya **elle kurulum** (git clone + pip, her platformda çalışır).

#### Yöntem A: Kolay kurulum (Windows, `MediaGrabSetup.exe`)

**1. Önce Git ve Python'u kurun**

- Git: [git-scm.com/downloads](https://git-scm.com/downloads)
- Python 3.9+: [python.org/downloads](https://www.python.org/downloads/) — kurulum ekranında **"Add python.exe to PATH"** kutusunu işaretlemeyi unutmayın.

**2. Kurulum programını indirin**

[GitHub Release sayfasından](https://github.com/umitkrkmz/mediagrab/releases/latest) `MediaGrabSetup.exe`'yi indirin.

İsterseniz dosyanın bozulmadığını doğrulayın — **o sürüme ait SHA256, release notlarının içinde yazar** (her sürümde farklıdır, çünkü exe her seferinde yeniden derlenir). PowerShell'de:

```powershell
certutil -hashfile MediaGrabSetup.exe SHA256
```

Çıkan değeri release sayfasındaki ile karşılaştırın.

**3. Kurulum klasörünü seçin**

Varsayılan olarak MediaGrab, `MediaGrabSetup.exe`'nin bulunduğu klasöre kurulur — ama kurulum penceresindeki **"Gözat…"** ile başka bir klasör de seçebilirsiniz. **MediaGrab'a ayrılmış boş bir klasör** kullanın (örn. `C:\MediaGrab\`).

> **Önemli:** Bu klasör **OneDrive, Dropbox, Google Drive gibi bulut senkronizasyon servislerinin izlediği bir yerde olmasın** (dikkat: Windows'ta "Masaüstü" veya "Belgelerim" genellikle OneDrive ile senkronize edilir). İndirme sırasında çok sayıda küçük geçici dosya hızlıca yazılıp siliniyor; senkron servisi tam o anda bir dosyayı kilitlerse indirme "No such file or directory" hatasıyla yarıda kesilebilir. `C:\MediaGrab\` gibi senkronlanmayan düz bir klasör kullanmanızı öneririz.
>
> Kurulum programı bunu zaten kendisi de kontrol eder: bulut klasörü seçerseniz uyarır, sürücü kökü ve kişisel klasörlerinizi (Masaüstü, Belgeler, kullanıcı klasörü) ise kabul etmez — çünkü **Kaldır** işlemi kurulum klasörünün içeriğini siler.

**4. Çalıştırın**

`MediaGrabSetup.exe`'ye çift tıklayın. Pencere sistem dilinize göre Türkçe veya İngilizce açılır ve Git, Python (sürümüyle birlikte) ve ffmpeg'i kontrol eder. Hepsi yeşilse **Kur**'a basın — isterseniz Masaüstüne/Başlat menüsüne kısayol ekleme kutucuklarını da işaretleyebilirsiniz. İlerleme alttaki günlükte görünür; bitince **"MediaGrab'ı Başlat"** düğmesiyle doğrudan açabilirsiniz.

> Windows, imzasız bir `.exe` olduğu için ilk çalıştırmada "Windows bilgisayarınızı korudu" uyarısı gösterebilir — **Daha fazla bilgi → Yine de çalıştır** ile devam edebilirsiniz. Kaynak kodu repodaki `setup_mediagrab.py` dosyasında, isteyen inceleyebilir.

**5. ffmpeg'i kurun (zorunlu — kurulum programı bunu yapmaz)**

MediaGrab, ses/video birleştirme, format dönüştürme ve süre/kapak okuma için `ffmpeg` ve `ffprobe`'a ihtiyaç duyar. Bunlar MediaGrab ile birlikte gelmez ve `pip` ile de kurulmaz; **sisteminize ayrıca kurmanız gerekir.** Kurmazsanız uygulama açılır ama indirmeler birleştirme aşamasında hata verir.

Kendi işletim sisteminize uygun komutu bir terminalde çalıştırın:

```powershell
winget install --id Gyan.FFmpeg -e
```

```bash
brew install ffmpeg
```

```bash
sudo apt install ffmpeg
```

Sırasıyla: Windows (PowerShell) · macOS (Homebrew) · Linux (Debian/Ubuntu).

Kurduktan sonra **yeni bir terminal açın** (PATH güncellemesi zaten açık olan terminale yansımaz) ve `ffmpeg -version` ile doğrulayın.

> Bu komutları uygulamanın içinden de bulabilirsiniz: **Ayarlar → ffmpeg / ffprobe** bölümü kurulu sürümü gösterir ve her platformun komutunu kopyalanabilir şekilde listeler.

**6. Başlatın**

Kurulum bitince oluşan **`MediaGrab Baslat.bat`** dosyasına çift tıklamanız yeterli — terminal açmanıza gerek yok (3. adımda kısayol eklediyseniz Masaüstünden/Başlat menüsünden de açabilirsiniz).

Kurulumu daha sonra güncellemek veya kaldırmak isterseniz: `MediaGrabSetup.exe`'yi tekrar çalıştırın, **Onar / Güncelle** ya da **Kaldır**'a basın (indirdiğiniz dosyalar ve kanal takip listeniz her durumda korunur).

#### Yöntem B: Elle kurulum (kaynak koddan, her platform)

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

### Testler

Ağ erişimi gerektirmeyen, birkaç saniyede biten bir test paketi var (yol güvenliği, VTT/transkript ayrıştırma, sürüm karşılaştırma, yedekle-geri-yükle, çeviri bütünlüğü, arayüzdeki HTML kaçışı).

```bash
pip install -r requirements-dev.txt
pytest
```

JavaScript testleri için Node.js kurulu olmalı; değilse o testler otomatik atlanır.

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
    i18n.py         # sunucuda basılan arayüz metinleri (TR/EN) — tek kaynak
    deps.py         # ffmpeg/ffprobe ve Python paket sürüm kontrolleri
    store.py        # channels.json okuma/yazma (kanal takibi, DB değil)
    paths.py         # kaynak/exe modunda doğru klasör yollarını çözer
    templates/      # Jinja2: base, index, history, item, channels, settings, supported_sites
    static/         # style.css, app.js
indirilenler/       # indirilen dosyalar, kanal adına göre alt klasörlenir (git'e dahil değil)
    Kanal Adı/
        Video.mp4
        Video.json  # meta veri sidecar dosyası
channels.json       # takip edilen kanallar (git'e dahil değil)
run.py              # `python run.py` ile çalıştırmak için giriş noktası
setup_mediagrab.py  # kurulum aracı (Release'deki MediaGrabSetup.exe'nin kaynağı)
tests/              # pytest paketi (ağ gerektirmez)
requirements.txt
requirements-dev.txt  # yalnızca geliştirme (pytest) — uygulama bunu okumaz
LICENSE
README.md
```

### Lisans ve Üçüncü Taraf Bildirimleri

MediaGrab'ın kendi kaynak kodu **MIT** lisansı ile lisanslanmıştır (bkz. [LICENSE](LICENSE)).

**Uygulamanın kendisi kaynak kod olarak dağıtılır.** Kullanıcı repoyu klonlar, `pip install -r requirements.txt` ile bağımlılıkları kendi ortamına kurar ve çalıştırır. Aşağıdaki paketlerin hiçbiri MediaGrab ile birlikte paketlenmez — hepsini `pip` kendi indirir, yani lisans açısından "mere aggregation" (yan yana bulundurma) söz konusudur.

**Release'deki `MediaGrabSetup.exe` bir istisna değil:** o dosya yalnızca *kurulumu yapan* küçük bir yardımcı programdır ve içinde **hiçbir üçüncü taraf paket yoktur** — sadece MediaGrab'ın kendi MIT kodu, Python standart kütüphanesi ([PSF lisansı](https://docs.python.org/3/license.html)) ve arayüz için Tcl/Tk (BSD tarzı) bulunur. yt-dlp, ffmpeg ve diğer paketler bu exe'nin içinde **değildir**; exe onları çalıştırdığında `pip` ve sistem paket yöneticisi indirir. Dolayısıyla exe'nin dağıtımı da ek bir copyleft yükümlülüğü doğurmaz.

| Paket | Lisans | Not |
|---|---|---|
| [`yt-dlp`](https://github.com/yt-dlp/yt-dlp) | [Unlicense](https://github.com/yt-dlp/yt-dlp/blob/master/LICENSE) (kamu malı) | indirme/çözümleme motoru |
| [`fastapi`](https://github.com/fastapi/fastapi) | [MIT](https://github.com/fastapi/fastapi/blob/master/LICENSE) | web çatısı |
| [`starlette`](https://github.com/encode/starlette) | [BSD-3-Clause](https://github.com/encode/starlette/blob/master/LICENSE.md) | fastapi'nin ASGI katmanı |
| [`uvicorn`](https://github.com/encode/uvicorn) | [BSD-3-Clause](https://github.com/encode/uvicorn/blob/master/LICENSE.md) | ASGI sunucusu |
| [`pydantic`](https://github.com/pydantic/pydantic) | [MIT](https://github.com/pydantic/pydantic/blob/main/LICENSE) | veri doğrulama |
| [`jinja2`](https://github.com/pallets/jinja) | [BSD-3-Clause](https://github.com/pallets/jinja/blob/main/LICENSE.txt) | HTML şablonlama |
| [`mutagen`](https://github.com/quodlibet/mutagen) | [GPL-2.0-or-later](https://github.com/quodlibet/mutagen/blob/master/COPYING) | **MediaGrab bunu import etmez** — yt-dlp, Opus dosyalarına kapak resmi gömmek için kullanır |
| [`ffmpeg`](https://github.com/FFmpeg/FFmpeg) / `ffprobe` | [LGPL-2.1+ veya GPL-2+](https://www.ffmpeg.org/legal.html) (derlemeye göre değişir) | projeye dahil DEĞİL — kullanıcı kendi sistemine ayrıca kurar; etiket/kapak okuma ve süre hesaplama da subprocess ile buradan yapılır |

MediaGrab'ın kendi kodu yalnızca izin verici (MIT/BSD) veya kamu malı lisanslı paketleri import eder.

**`mutagen` hakkında (GPL):** MediaGrab'ın kaynak kodunda `mutagen` importu **yoktur**; onu yt-dlp kendi içinde kullanır ve `pip` kullanıcının kendi ortamına indirir. Biz mutagen'i paketlemiyor, dağıtmıyoruz — bu nedenle GPL'in copyleft yükümlülüğü (birleşik eseri dağıtmak) devreye girmez ve MediaGrab MIT olarak kalır. Aynı şey `ffmpeg` için de geçerli: dağıtıma dahil değildir, yalnızca ayrı bir program olarak `subprocess` ile çağrılır.

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
- **Transcript download** — for videos with subtitles (manual or auto-generated), you can separately download a plain-text transcript (`.txt`)
- **Paste-to-resolve & quick options** — a paste button that auto-detects the clipboard link; one-click buttons for best audio/best video, with every other quality/format tucked under "advanced options"
- **Persistent download panel** — track multiple downloads at once; progress survives page navigation and even closing and reopening the app
- **In-place preview** — play audio/video files straight from the item detail page without opening a file explorer
- **Installable app (PWA)** — use your browser's "Add to Home Screen" to run MediaGrab like a standalone app
- **Playlists & YouTube Music** — paste a playlist link and get a list of videos with covers/titles/durations; click one to download it individually, or pick a range (e.g. 1–19) and **queue them all with one click**
- **Multi-platform** — not YouTube-only; works through the same UI with any of the 1700+ sites yt-dlp supports (Vimeo, SoundCloud, X/Twitter, Twitch, archive.org, and more)
- **Metadata (JSON) export** — every download also saves a JSON file with the same base name (`video.mp4` + `video.json`) containing title, uploader, upload date, description, tags, and the source URL; also downloadable from the item detail page
- **Automatic folder organization** — every download is saved into its own subfolder by channel/uploader (`indirilenler/Channel Name/`), so files stay organized in your file explorer or media library apps
- **Supported Sites page** (`/supported-sites`) — a short, categorized list of popular sites yt-dlp supports, with a link to the full list (1700+ sites)
- **yt-dlp version check with one-click update** (`/settings`) — compares your installed yt-dlp version against the latest on PyPI; if an update is available, installs it with one click and restarts the app automatically
- **Channel following** (`/channels`) — follow a channel; every time you open the app, it's checked for new videos. Two modes: **Notify** (a banner on the home page tells you, you pick what to download) or **Auto-download** (downloads new uploads automatically in your chosen format). Not a persistent background service - see the note below.
- **Download history** — cover-art cards on their own page (`/history`); search by title and filter by channel, re-download, delete, or clear all
- **Light / dark theme** — follows your system setting, or pick it by hand from `/settings` or the header toggle
- **Cancel a download** — stop a running download from the panel; partial files are cleaned up automatically
- **Existing files are protected** — if a re-download is cancelled, fails, or the app crashes, your previous file comes back untouched
- **Environment checks** (`/settings`) — ffmpeg/ffprobe version plus a Python dependency check, with one-click package updates
- **Friendly error messages** — common cases (age restriction, bot check, geo-restriction, removed videos, and more) show an explanatory message in your language instead of yt-dlp's raw output
- **Auto reveal in file explorer** — clicking "Download file" opens your OS file explorer with the file selected
- **Turkish / English UI** — follows your system locale by default, switchable by hand
- **No** database, account system, or cloud connection — runs only on this machine

### Installation

On Windows there are two paths: **easy install** (a ready-made `.exe`, no typing commands) or **manual install** (git clone + pip, works on every platform).

#### Method A: Easy install (Windows, `MediaGrabSetup.exe`)

**1. Install Git and Python first**

- Git: [git-scm.com/downloads](https://git-scm.com/downloads)
- Python 3.9+: [python.org/downloads](https://www.python.org/downloads/) — check **"Add python.exe to PATH"** during setup.

**2. Download the installer**

Grab `MediaGrabSetup.exe` from the [GitHub Releases page](https://github.com/umitkrkmz/mediagrab/releases/latest).

Optionally verify it's intact — **that release's SHA256 is printed in its release notes** (it differs per release, since the exe is rebuilt each time). In PowerShell:

```powershell
certutil -hashfile MediaGrabSetup.exe SHA256
```

Compare the output against the value on the release page.

**3. Choose the install folder**

By default MediaGrab installs into whichever folder `MediaGrabSetup.exe` sits in — but you can pick a different one with **"Browse…"** in the setup window. Use an **empty folder dedicated to MediaGrab** (e.g. `C:\MediaGrab\`).

> **Important:** don't use a folder that's **watched by a cloud sync service** like OneDrive, Dropbox, or Google Drive (note: on Windows, "Desktop" and "Documents" are often OneDrive-synced by default). Downloads write and delete a lot of small temp files in quick succession; if the sync client locks one of them at just the wrong moment, the download can fail mid-way with a "No such file or directory" error. A plain, non-synced folder like `C:\MediaGrab\` avoids this entirely.
>
> The installer checks this for you too: it warns if you pick a cloud-synced folder, and refuses drive roots and your personal folders (Desktop, Documents, your user folder) outright — because **Remove** deletes the install folder's contents.

**4. Run it**

Double-click `MediaGrabSetup.exe`. The window opens in Turkish or English depending on your system language, and checks Git, Python (including its version) and ffmpeg. Once everything is green, click **Install** — optionally tick the Desktop/Start Menu shortcut boxes first. Progress shows in the log at the bottom, and when it's done **"Start MediaGrab"** launches the app directly.

> Since it's an unsigned `.exe`, Windows may show a "Windows protected your PC" warning the first time — click **More info → Run anyway** to continue. The source is `setup_mediagrab.py` in this repo if you'd like to inspect it first.

**5. Install ffmpeg (required — the installer does not do this)**

MediaGrab needs `ffmpeg` and `ffprobe` to merge audio/video, convert formats, and read duration/cover art. They are not bundled with MediaGrab and `pip` does not install them; **you install them on your system separately.** Without them the app still starts, but downloads fail at the merge step.

Run the command for your OS in a terminal:

```powershell
winget install --id Gyan.FFmpeg -e
```

```bash
brew install ffmpeg
```

```bash
sudo apt install ffmpeg
```

In order: Windows (PowerShell) · macOS (Homebrew) · Linux (Debian/Ubuntu).

Afterwards **open a new terminal** (a PATH update doesn't reach an already-open one) and verify with `ffmpeg -version`.

> You can also find these inside the app: **Settings → ffmpeg / ffprobe** shows the installed version and lists every platform's command with a copy button.

**6. Launch it**

Once install finishes, just double-click the **`MediaGrab Baslat.bat`** file it created — no terminal needed (or use the Desktop/Start Menu shortcut if you added one in step 3).

To update or remove later: run `MediaGrabSetup.exe` again and click **Onar / Güncelle** (Repair/Update) or **Kaldır** (Remove) — your downloads and followed-channel list are preserved either way.

#### Method B: Manual install (from source, any platform)

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

### Tests

There's a small suite that needs no network access and finishes in a couple of seconds (path safety, VTT/transcript parsing, version comparison, backup-and-restore, translation integrity, front-end HTML escaping).

```bash
pip install -r requirements-dev.txt
pytest
```

The JavaScript tests need Node.js installed; they're skipped automatically if it isn't.

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
    i18n.py         # server-rendered UI strings (TR/EN) - single source
    deps.py         # ffmpeg/ffprobe and Python package version checks
    store.py        # reads/writes channels.json (channel following, not a DB)
    paths.py         # resolves the right folders whether running from source or as the exe
    templates/      # Jinja2: base, index, history, item, channels, settings, supported_sites
    static/         # style.css, app.js
indirilenler/       # downloaded files, auto-organized into per-channel subfolders (not in git)
    Channel Name/
        Video.mp4
        Video.json  # metadata sidecar
channels.json       # followed channels (not in git)
run.py              # entry point for `python run.py`
setup_mediagrab.py  # the installer tool (source of MediaGrabSetup.exe on Releases)
tests/              # pytest suite (no network required)
requirements.txt
requirements-dev.txt  # development only (pytest) — the app never reads this
LICENSE
README.md
```

### License & Third-Party Notices

MediaGrab's own source code is licensed under **MIT** (see [LICENSE](LICENSE)).

**The application itself ships as source code.** You clone the repo, install dependencies into your own environment with `pip install -r requirements.txt`, and run it. None of the packages below are bundled with MediaGrab — `pip` fetches each one itself, which makes this "mere aggregation" as far as licensing goes.

**`MediaGrabSetup.exe` on the Releases page is not an exception:** it is only a small helper that *performs the install*, and it contains **no third-party packages at all** — just MediaGrab's own MIT code, the Python standard library ([PSF license](https://docs.python.org/3/license.html)), and Tcl/Tk (BSD-style) for its window. yt-dlp, ffmpeg and the rest are **not** inside that exe; `pip` and your system package manager fetch them when you run it. Distributing the exe therefore adds no copyleft obligation either.

| Package | License | Note |
|---|---|---|
| [`yt-dlp`](https://github.com/yt-dlp/yt-dlp) | [Unlicense](https://github.com/yt-dlp/yt-dlp/blob/master/LICENSE) (public domain) | download/resolve engine |
| [`fastapi`](https://github.com/fastapi/fastapi) | [MIT](https://github.com/fastapi/fastapi/blob/master/LICENSE) | web framework |
| [`starlette`](https://github.com/encode/starlette) | [BSD-3-Clause](https://github.com/encode/starlette/blob/master/LICENSE.md) | fastapi's ASGI layer |
| [`uvicorn`](https://github.com/encode/uvicorn) | [BSD-3-Clause](https://github.com/encode/uvicorn/blob/master/LICENSE.md) | ASGI server |
| [`pydantic`](https://github.com/pydantic/pydantic) | [MIT](https://github.com/pydantic/pydantic/blob/main/LICENSE) | data validation |
| [`jinja2`](https://github.com/pallets/jinja) | [BSD-3-Clause](https://github.com/pallets/jinja/blob/main/LICENSE.txt) | HTML templating |
| [`mutagen`](https://github.com/quodlibet/mutagen) | [GPL-2.0-or-later](https://github.com/quodlibet/mutagen/blob/master/COPYING) | **not imported by MediaGrab** — yt-dlp uses it to embed cover art into Opus files |
| [`ffmpeg`](https://github.com/FFmpeg/FFmpeg) / `ffprobe` | [LGPL-2.1+ or GPL-2+](https://www.ffmpeg.org/legal.html) (depends on the build) | NOT bundled — the user installs it separately on their own system; tag/cover-art reading and duration are also done through it via subprocess |

MediaGrab's own code only imports permissively licensed (MIT/BSD) or public-domain packages.

**About `mutagen` (GPL):** MediaGrab's source contains no `import mutagen` — yt-dlp uses it internally, and `pip` fetches it into your own environment. We neither bundle nor redistribute it, so GPL's copyleft obligation (which attaches to distributing a combined work) is not triggered and MediaGrab stays MIT. The same holds for `ffmpeg`: never redistributed, only invoked as a separate program via `subprocess`.

### Legal Notice

This tool is for **personal use only**. You are solely responsible for the copyright status of any content you download and for complying with the relevant platform's (including YouTube's) terms of service. MediaGrab is not a platform-circumvention or DRM-stripping tool — it only downloads publicly available, downloadable media via yt-dlp.

### Keep yt-dlp updated

YouTube changes its interface often; older yt-dlp versions eventually start failing to resolve or download. If you run into trouble, update first:

```bash
pip install -U yt-dlp
```
