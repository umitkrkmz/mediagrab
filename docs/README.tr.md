# MediaGrab — Kullanım Kılavuzu

**[🇬🇧 English version](README.en.md)** · **[← Ana README'ye dön](../README.md)**

---

**İçindekiler**

- [Ne yapar](#ne-yapar)
- [Özellikler](#özellikler)
- [Kurulum](#kurulum)
  - [Yöntem A: Kolay kurulum (Windows)](#yöntem-a-kolay-kurulum-windows-mediagrabsetupexe)
  - [Yöntem B: Elle kurulum (her platform)](#yöntem-b-elle-kurulum-kaynak-koddan-her-platform)
- [Çalıştırma](#çalıştırma)
- [Kanal Takibi Nasıl Çalışır](#kanal-takibi-nasıl-çalışır)
- [Testler](#testler)
- [Sorun Giderme](#sorun-giderme)
- [Proje yapısı](#proje-yapısı)
- [Lisans ve Üçüncü Taraf Bildirimleri](#lisans-ve-üçüncü-taraf-bildirimleri)
- [Yasal Uyarı](#yasal-uyarı)
- [yt-dlp güncel tutulmalı](#yt-dlp-güncel-tutulmalı)

---

Link yapıştır, indir. Lokalde çalışan, kişisel kullanım için video/ses indirme aracı.

## Ne yapar

Bir YouTube veya YouTube Music linki (tekil video, playlist ya da albüm) yapıştırırsınız; MediaGrab linki çözümler, mevcut ses/video kalitelerini ve varsa altyazı dillerini listeler. Seçtiğiniz seçenek indirilir ve tarayıcıdan diskinize kaydedilir. YouTube dışında, yt-dlp'nin desteklediği diğer birçok site de (Vimeo, SoundCloud, X/Twitter, Twitch, archive.org vb. — [tam liste](https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md)) aynı akıştan çalışır; kanal takibi özelliği ise şimdilik yalnızca YouTube kanallarını destekler.

## Özellikler

- **Ses** — Opus / M4A (yeniden kodlanmadan, kalite kaybı yok) veya MP3 (evrensel uyumluluk için yeniden kodlanır)
- **Video** — mevcut tüm çözünürlükler, ses ile otomatik birleştirilmiş mp4 olarak; YouTube gerçek dosya boyutunu vermediğinde ortalama bit hızından tahmini boyut (`~1.2 GB`) gösterilir
- **Ses parçası (dublaj) seçimi, birden fazlası bir arada** — birden fazla dilde seslendirilmiş bir video için istediğiniz dili (veya videoyu `.mkv` olarak indirip birden fazla dili aynı anda, ör. orijinal + Türkçe) seçebilirsiniz; sadece gerçekten dublajı varsa görünür, hiçbirini seçmezseniz orijinal dil iner. Çoklu seçim yalnızca video indirmede geçerli, tekli seçim sesle de çalışır. `/settings`'ten bir varsayılan dil kaydedebilirsiniz, böylece her seferinde chip'e tıklamanıza gerek kalmaz — kanal otomatik indirmesi de bu ayarı kullanır (tek dil ile). Dil kodunu bilmiyorsanız [dil kodu sözlüğüne](language-codes.tr.md) bakabilirsiniz
- **Altyazı** — elle eklenmiş altyazı dillerini işaretleyip seçtiğiniz videoyla birlikte, aynı dosya adıyla (`video.mp4` + `video.tr.srt`) indirir; medya oynatıcılar otomatik eşleştirir
- **Transkript indirme** — altyazısı (elle eklenmiş veya otomatik oluşturulmuş) olan videolar için düz metin transkripti (`.txt`) ayrıca indirebilirsiniz
- **Link yapıştır & hızlı seçenekler** — panodaki linki otomatik algılayan yapıştır butonu; en iyi ses/en iyi video için tek tıkla hızlı indirme, diğer tüm kalite/format seçenekleri "gelişmiş seçenekler" altında
- **Kalıcı indirme paneli** — aynı anda birden fazla indirmeyi takip edin; hız yanında kalan tahmini süre de gösterilir; sayfa değiştirseniz veya uygulamayı kapatıp tekrar açsanız bile ilerleme durumu korunur
- **Sayfa içi önizleme** — indirme detay sayfasından ses/video dosyalarını dosya gezgini açmadan doğrudan oynatın
- **Uygulama olarak yükleme (PWA)** — tarayıcının "Ana ekrana ekle" seçeneğiyle MediaGrab'ı bağımsız bir uygulama gibi kullanabilirsiniz
- **Playlist & YouTube Music** — playlist linki yapıştırınca video listesi kapak/başlık/süre ile gelir; birine tıklayıp tek tek indirebilir ya da aralık seçip (ör. 1–19) **tümünü tek tıkla** kuyruğa atabilirsiniz
- **Çoklu platform** — YouTube'a özel değil; yt-dlp'nin desteklediği 1700'den fazla site (Vimeo, SoundCloud, X/Twitter, Twitch, archive.org vb.) aynı arayüzden çalışır
- **Meta veri (JSON) dışa aktarma** — her indirmeyle birlikte aynı dosya adıyla (`video.mp4` + `video.json`) başlık, kanal, yükleme tarihi, açıklama, etiketler ve kaynak linki gibi bilgileri içeren bir JSON dosyası kaydedilir; indirme detay sayfasından ayrıca indirilebilir
- **Otomatik klasörleme** — her indirme, kanal/yükleyici adına göre kendi alt klasörüne (`indirilenler/Kanal Adı/`) kaydedilir; disk üzerinde dosya gezgininde veya medya kitaplığı uygulamalarında düzenli görünür
- **Desteklenen Siteler sayfası** (`/supported-sites`) — yt-dlp'nin desteklediği popüler sitelerin kategorilere ayrılmış kısa bir listesi, tam listeye (1700+ site) link ile; her site kendi marka renginde/logosuyla ve tıklanınca ilgili sitenin ana sayfasına gidiyor
- **Hakkında sayfası** (`/about`) — proje ne yapar, GPL-3.0 lisansı ve kaynak kod/geri bildirim linkleri
- **yt-dlp sürüm kontrolü ve tek tıkla güncelleme** (`/settings`) — kurulu yt-dlp sürümünü PyPI'daki güncel sürümle karşılaştırır; güncelleme varsa tek tıkla kurar ve uygulamayı otomatik olarak yeniden başlatır
- **Kanal takibi** (`/channels`) — bir kanalı takibe alın; uygulamayı her açtığınızda yeni video var mı diye kontrol edilir. İki mod: **Bildir** (ana sayfada banner ile haber verir, siz seçersiniz) veya **Otomatik indir** (seçtiğiniz formatta kendiliğinden indirir). Sürekli arka planda çalışan bir servis değil — bkz. aşağıdaki not.
- **Uzaktan erişim** (`/settings`) — bir şifre belirleyip açtığınızda, aynı Wi-Fi/ağdaki telefon veya başka bir bilgisayar tarayıcıdan MediaGrab'e bağlanıp kendi başına indirme yapabilir; detaylar için aşağıdaki bölüme bakın.
- **İndirme geçmişi** — ayrı bir sayfada (`/history`), kapak resimli kart görünümü veya kompakt liste görünümü arasında geçiş yapılabilir; başlığa göre arama, kanala göre ve dosya türüne göre (diskteki gerçek uzantılardan otomatik oluşan) filtreleme, tekrar indirme, silme, tümünü silme
- **Açık / koyu tema** — sistem ayarını takip eder, `/settings` sayfasından veya başlıktaki düğmeyle elle de seçilebilir
- **İndirmeyi iptal etme** — süren bir indirmeyi panelden durdurun; yarım kalan dosyalar otomatik temizlenir
- **Var olan dosyayı koruma** — aynı videoyu tekrar indirirken iptal, hata veya çökme olursa eski dosyanız aynen geri gelir
- **Çerez desteği** (`/settings`) — yaş sınırlı, üyelere özel veya giriş gerektiren içerik için tarayıcı oturumunuzun çerezlerini kullanın: `cookies.txt` dosyası (her yerde çalışır) veya doğrudan tarayıcıdan. Çerezleriniz kopyalanmaz, yalnızca kaynağın adı saklanır
- **Ortam kontrolü** (`/settings`) — ffmpeg/ffprobe sürümü ve Python bağımlılıkları güncel mi diye kontrol edilir; paketler tek tıkla güncellenebilir
- **Geri bildirim** (`/settings`) — hata bildirmek veya özellik önermek için GitHub'daki hazır şablonlara tek tıkla gidin
- **Anlaşılır hata mesajları** — yaygın durumlar (yaş sınırı, bot koruması, coğrafi kısıtlama, kaldırılmış video vb.) için yt-dlp'nin ham çıktısı yerine açıklayıcı Türkçe/İngilizce mesajlar gösterilir
- **Otomatik dosya gezgini** — "Dosyayı indir"e tıklayınca dosya, işletim sisteminin dosya gezgininde seçili şekilde açılır
- **Türkçe / İngilizce arayüz** — sistem diline göre otomatik, elle de değiştirilebilir
- Veritabanı, hesap sistemi veya bulut bağlantısı **yok** — yalnızca bu bilgisayarda çalışır

## Kurulum

Windows'ta iki yol var: **kolay kurulum** (hazır `.exe`, terminal komutu yazmadan) veya **elle kurulum** (git clone + pip, her platformda çalışır).

### Yöntem A: Kolay kurulum (Windows, `MediaGrabSetup.exe`)

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

`MediaGrabSetup.exe`'ye çift tıklayın. Açılış sayfası sistem dilinize göre Türkçe veya İngilizce gelir (sağ üstteki **TR / EN** ile değiştirebilirsiniz) ve üç seçenek sunar: **Kur**, **Onar / Güncelle**, **Kaldır**. **Kur**'u seçince sihirbaz sırayla ilerler:

- **Gereksinimler** — Git, Python (sürümüyle birlikte) ve ffmpeg kontrol edilir; eksik varsa indirme düğmeleri ve kopyalanabilir komut gösterilir, kurduktan sonra **Durumu yenile** ile tekrar bakar.
- **Kurulum klasörü** — 3. adımdaki klasörü seçin; Masaüstüne / Başlat menüsüne kısayol kutucukları da burada.
- **Özet** — ne yapılacağı (klasör, bulunan araçlar, kısayollar, varsa üzerine yazılacak mevcut dosyalar) tek sayfada; **Kur**'a basınca başlar.
- **İşlem** — ilerleme canlı günlükte görünür; bitince **"MediaGrab'ı Başlat"** düğmesiyle doğrudan açabilirsiniz.

Kurulum programı son kurulum klasörünü hatırlar: daha sonra **Onar / Güncelle** ya da **Kaldır**'ı seçtiğinizde klasör kendiliğinden dolu gelir (isterseniz değiştirebilirsiniz).

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

### Yöntem B: Elle kurulum (kaynak koddan, her platform)

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

## Çalıştırma

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

## Kanal Takibi Nasıl Çalışır

MediaGrab sürekli arka planda çalışan bir servis **değil** — sadece siz açtığınızda çalışır. Bu yüzden kanal takibi de "her açılışta bir kez kontrol et" mantığıyla çalışır: uygulamayı başlattığınızda (`python run.py` veya `uvicorn` komutunu çalıştırdığınızda), takip listenizdeki tüm kanallar arka planda kontrol edilir. Uygulama kapalıyken yeni yüklenen videolar, siz tekrar açana kadar tespit edilmez — kişisel/lokal bir araç için beklenen davranış budur; 7/24 arka planda çalışan bir Windows servisi haline getirmek istemiyoruz.

Takip listesi ve son görülen video bilgisi, veritabanı yerine `channels.json` dosyasında (git'e dahil değil) tutulur — projenin geri kalanıyla aynı "gerçek veri diskte, ayrı bir DB yok" felsefesi.

## Uzaktan Erişim (Yerel Ağdan)

MediaGrab'ı bir bilgisayarda çalıştırıp aynı Wi-Fi/ağdaki telefonunuzdan veya başka bir cihazdan tarayıcıyla açabilirsiniz — MediaGrab'ı her cihaza ayrı ayrı kurmanıza gerek kalmaz.

**Nasıl açılır:** `/settings` → **Uzaktan Erişim** sekmesi → önce bir şifre belirleyin, sonra "Yerel ağdan erişime izin ver" seçeneğini açın. Ayar uygulanırken sunucu kendini bir kez yeniden başlatır; işlem bitince aynı panelde bağlantı adresi (`http://192.168.x.x:8420` gibi) görünür — bu adresi diğer cihazın tarayıcısına yazmanız yeterli. İlk açılışta o cihaz da şifreyle giriş yapar.

- **Bağlı cihazlar** — aynı panelde o an oturum açmış her cihazı (tarayıcı + işletim sistemi tahmini, ör. "Chrome · Windows") ve bağlantı zamanını görürsünüz; istediğiniz birini tek başına çıkışa zorlayabilirsiniz, kendi cihazınız etkilenmez.
- **Şifre değiştirme** — mevcut şifre / yeni şifre / yeni şifre (tekrar) ile değiştirilir. Şifreyi unutursanız: bu bilgisayardaki `settings.json` dosyasından `remote_access_password_salt` ve `remote_access_password_hash` alanlarını silip MediaGrab'ı yeniden başlatın, ayarlar sayfasından yeni bir şifre belirleyebilirsiniz. Şifre her değiştiğinde (veya bu kurtarma yoluyla sıfırlandığında), değiştiren dahil oturum açmış her cihaz otomatik çıkışa zorlanır.
- **Depolama modu** — **Bende Kalsın** (varsayılan): indirilen dosyalar her zamanki gibi bu bilgisayarda `indirilenler/` klasöründe kalıcı olarak durur; kişisel bilgisayar için önerilen mod. **Cihaza Aktar**: depolaması sınırlı bir cihazda (ör. Raspberry Pi) çalıştırıyorsanız, bir dosya bir cihaza tam olarak gönderildikten hemen sonra bu bilgisayardaki kopyası silinir. Kendi bilgisayarınızdan (host'un kendi tarayıcısından) yaptığınız indirmeler bu ayardan hiçbir zaman etkilenmez — yalnızca başka bir cihaza gönderilen dosyalar için geçerlidir.

> **Güvenlik notu:** Bu bağlantı düz HTTP üzerinden çalışır (HTTPS değildir) — yalnızca güvendiğiniz bir ev/ofis ağında kullanın, yönlendirici (router) ayarlarından doğrudan internete açmayın. Oturumlar bellekte tutulur; sunucu yeniden başladığında (güncelleme, bilgisayarın kapanması vb.) herkes tekrar şifreyle giriş yapmalıdır — bu bilinçli bir sadeleştirme, kişisel/lokal bir araç için diskte kalıcı oturum tutmaya gerek görülmedi.

## Testler

Ağ erişimi gerektirmeyen, birkaç saniyede biten bir test paketi var (yol güvenliği, VTT/transkript ayrıştırma, sürüm karşılaştırma, yedekle-geri-yükle, çeviri bütünlüğü, arayüzdeki HTML kaçışı).

```bash
pip install -r requirements-dev.txt
pytest
```

JavaScript testleri için Node.js kurulu olmalı; değilse o testler otomatik atlanır.

## Sorun Giderme

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

## Proje yapısı

```
mediagrab/
    app.py          # FastAPI uygulaması, endpoint'ler
    downloader.py   # yt-dlp sarmalayıcı — yt_dlp importu SADECE burada
    models.py       # Pydantic modelleri
    i18n.py         # sunucuda basılan arayüz metinleri (TR/EN) — tek kaynak
    deps.py         # ffmpeg/ffprobe ve Python paket sürüm kontrolleri
    store.py        # channels.json / settings.json okuma-yazma, DB değil
    paths.py         # kaynak/exe modunda doğru klasör yollarını çözer
    templates/      # Jinja2: base, index, history, item, channels, settings, supported_sites, about
    static/         # style.css, app.js
    static/icons/   # desteklenen site logoları (Simple Icons'tan, yerelde tutulur)
indirilenler/       # indirilen dosyalar, kanal adına göre alt klasörlenir (git'e dahil değil)
    Kanal Adı/
        Video.mp4
        Video.json  # meta veri sidecar dosyası
channels.json       # takip edilen kanallar (git'e dahil değil)
settings.json       # çerez ve varsayılan ses dili ayarları (git'e dahil değil)
run.py              # `python run.py` ile çalıştırmak için giriş noktası
setup_mediagrab.py  # kurulum aracı (Release'deki MediaGrabSetup.exe'nin kaynağı)
tests/              # pytest paketi (ağ gerektirmez)
docs/               # bu dosya, İngilizce karşılığı ve dil kodu sözlüğü (language-codes.*.md)
maps/               # ayrıntılı proje haritası ve rota haritası (test-korumalı, AI araçları ve katkıcılar için)
requirements.txt
requirements-dev.txt  # yalnızca geliştirme (pytest) — uygulama bunu okumaz
LICENSE             # v1.9.0+ (GPL-3.0-or-later)
LICENSE-MIT         # v1.0.0 – v1.8.0 (MIT)
README.md
```

## Lisans ve Üçüncü Taraf Bildirimleri

**MediaGrab v1.0.0 – v1.8.0** sürümleri **MIT** lisansıyla yayınlandı (bkz. [LICENSE-MIT](../LICENSE-MIT)) ve bu hak geriye dönük değişmez — o sürümleri MIT şartlarıyla kullanmaya, fork'lamaya devam edebilirsiniz.

**MediaGrab v1.9.0 ve sonrası GNU GPL-3.0 (veya sonrası)** ile lisanslanmıştır (bkz. [LICENSE](../LICENSE)). Geçişin sebebi basit: `mutagen` gibi GPL lisanslı bir bağımlılığı MIT kalarak kullanmak, onu hiç doğrudan `import` etmemeyi ve yalnızca yt-dlp'nin arka planda, ayrı bir süreç olarak çalıştırmasına güvenmeyi gerektiriyordu (aşağıda anlatılıyor). GPL-3.0'a geçmek bu kısıtı ortadan kaldırıyor — ileride bir özellik gerçekten GPL lisanslı bir kütüphaneyi doğrudan kullanmak isterse, bunu MIT'te olduğu gibi dolambaçlı bir savunmaya ihtiyaç duymadan yapabiliriz. AGPL gibi daha kısıtlayıcı bir lisans yerine GPL-3.0 seçildi çünkü MediaGrab bir ağ servisi olarak sunulmuyor, yalnızca yerelde çalışan bir araç.

**Uygulamanın kendisi kaynak kod olarak dağıtılır.** Kullanıcı repoyu klonlar, `pip install -r requirements.txt` ile bağımlılıkları kendi ortamına kurar ve çalıştırır. Aşağıdaki paketlerin hiçbiri MediaGrab ile birlikte paketlenmez — hepsini `pip` kendi indirir, yani lisans açısından "mere aggregation" (yan yana bulundurma) söz konusudur.

**Release'deki `MediaGrabSetup.exe` bir istisna değil:** o dosya yalnızca *kurulumu yapan* küçük bir yardımcı programdır ve içinde **hiçbir üçüncü taraf paket yoktur** — sadece MediaGrab'ın kendi kodu, Python standart kütüphanesi ([PSF lisansı](https://docs.python.org/3/license.html)) ve arayüz için Tcl/Tk (BSD tarzı) bulunur. yt-dlp, ffmpeg ve diğer paketler bu exe'nin içinde **değildir**; exe onları çalıştırdığında `pip` ve sistem paket yöneticisi indirir.

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

**`mutagen` hakkında:** MediaGrab'ın kaynak kodunda şu an `mutagen` importu **yoktur**; onu yt-dlp kendi içinde kullanır ve `pip` kullanıcının kendi ortamına indirir — biz onu paketlemiyor, dağıtmıyoruz. v1.8.0 ve öncesinde MIT kalabilmemizin sebebi tam olarak buydu: GPL'in copyleft yükümlülüğü ancak GPL kodu *birleştirip dağıttığınızda* devreye giriyor, biz hiç birleştirmediğimiz için MIT geçerliydi. v1.9.0'dan itibaren bu artık bir zorunluluk değil, tercih meselesi — MediaGrab kendisi GPL-3.0 olduğu için `mutagen`'i (GPL-2.0-or-later, GPL-3.0 ile uyumlu) ileride doğrudan import etsek bile sorun olmaz. `ffmpeg` için durum değişmedi: dağıtıma hiç dahil değil, yalnızca ayrı bir program olarak `subprocess` ile çağrılıyor.

Projeyi faydalı bulduysanız ⭐ vermeniz, başkalarının da bulmasına yardımcı olur.

## Yasal Uyarı

Bu araç yalnızca **kişisel kullanım** içindir. İndirdiğiniz içeriğin telif durumundan ve ilgili platformun (YouTube dahil) kullanım şartlarına uyumdan tamamen siz sorumlusunuz. MediaGrab bir platformu atlatma veya DRM kırma aracı değildir; yalnızca herkese açık, indirilebilir medyayı yt-dlp aracılığıyla indirir.

## yt-dlp güncel tutulmalı

YouTube arayüzünü sık değiştirir; eski yt-dlp sürümleri zamanla çözümleme/indirme hatası vermeye başlar. Sorun yaşarsanız önce güncelleyin:

```bash
pip install -U yt-dlp
```
