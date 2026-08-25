# Changelog

Bu dosya MediaGrab'daki önemli değişiklikleri sürüm bazında listeler.
This file lists notable changes to MediaGrab, by release.

---

## [Türkçe](#türkçe-1) · [English](#english-1)

---

## Türkçe

### [1.6.0] — 2026-08-25

#### Eklenen

- **Çerez desteği geri geldi** (`/settings` → Çerezler) — yaş sınırlı, üyelere özel veya giriş gerektiren içerik için iki yol sunuluyor:
  - **`cookies.txt` dosyası** — tarayıcınızdan bir eklentiyle dışa aktardığınız dosyanın yolunu verirsiniz. Her tarayıcıda, her işletim sisteminde çalışır
  - **Doğrudan tarayıcıdan** — Firefox'ta çalışır. Chrome 127'den beri Windows'ta çerezler yalnızca Chrome'un kendi süreci tarafından çözülebildiği için (app-bound encryption) Chromium tabanlı tarayıcılarda bu yöntem Windows'ta çalışmaz; arayüz bunu açıkça uyarıyor. İlk denememizin (v1.1.0) başarısız olma sebebi tam olarak buydu
  - **"Bağlantıyı sına" düğmesi** — ayarın gerçekten çalışıp çalışmadığını indirme başlatmadan söyler; başarısızsa sebebini gösterir
  - Çerezleriniz MediaGrab'a kopyalanmaz veya hiçbir yere gönderilmez; yalnızca kaynağın adı (tarayıcı adı ya da dosya yolu) `settings.json` içinde bu bilgisayarda saklanır

### [1.5.0] — 2026-08-25

#### Düzeltilen

- **Opus ses indirme v1.2.0'dan beri bozuktu** — indirme tamamlanıyor, ardından son işleme adımında `module mutagen was not found` hatasıyla düşüyordu. v1.2.0'da `mutagen` bağımlılığı kaldırılmıştı; gözden kaçan nokta şuydu: MediaGrab'ın kendi kodu mutagen'i kullanmıyor ama **yt-dlp**, Opus dosyalarına kapak resmi gömmek için ona ihtiyaç duyuyor. Opus varsayılan ses formatı olduğu için ("En İyi Ses" düğmesi, ses listesindeki ilk seçenek, kanal otomatik indirmesi) en görünür ses yolu üç sürüm boyunca çalışmıyordu. M4A ve MP3 etkilenmemişti. Bağımlılık geri eklendi ve bir daha sessizce düşmemesi için test yazıldı
- **Opus dosyalarında başlık ve sanatçı görünmüyordu** — Ogg tabanlı formatlar etiketleri *akış* düzeyinde tutuyor, biz yalnızca *kapsayıcı* düzeyini okuyorduk; artık ikisine de bakılıyor
- **Kanal kontrolü başarısız olunca "son kontrol" tarihi hiç güncellenmiyordu** — hata durumunda tarihi yazan satıra ulaşılmadan çıkılıyordu, bu yüzden bozulmuş bir kanal (silinmiş, adı değişmiş, gizlenmiş) yeni videosu olmayan bir kanaldan ayırt edilemiyordu. Artık deneme her hâlükârda kaydediliyor ve kanal kartında "Son kontrol başarısız: [sebep]" görünüyor

#### Eklenen

- **Playlist'te toplu indirme** — playlist listesinin üstünde aralık seçimi (ör. `1 – 19`) ve tek tıkla "En İyi Ses" / "En İyi Video". Önceden her videoya tek tek tıklayıp formatı yeniden seçmek gerekiyordu. Yanlış yazılmış aralıklar düzeltilir (`5-3` ters çevrilir, sınır dışı değerler kırpılır)
- **Kuyruk sırası** — aynı anda 3 indirme çalışıyor; bekleyenler artık "Sırada 2." diyor. Önceden belirsiz şekilde "Başlıyor..." yazıyor ve takılmış bir indirmeden ayırt edilemiyordu
- **Otomatik sürüm yayınlama** (GitHub Actions) — sürüm etiketi push edildiğinde exe otomatik derlenir, testler çalıştırılır, exe'nin gerçekten açıldığı doğrulanır, SHA256 hesaplanıp release notlarına yazılır ve dosya release'e eklenir. PyInstaller çıktısı her derlemede farklı olduğu için hash artık README'ye sabitlenmiyor; README okuyucuyu release sayfasına yönlendiriyor

### [1.4.0] — 2026-08-22

#### Eklenen

- **Açık / koyu tema** — varsayılan olarak işletim sisteminizin ayarını takip eder; **Ayarlar → Görünüm**'den (Sistem / Açık / Koyu) veya başlıktaki düğmeden elle seçilebilir. Seçim ilk boyamadan önce uygulanır, sayfa açılırken tema titremesi olmaz
- **İndirmeyi iptal etme** — süren bir indirme, panelindeki ✕ ile gerçekten durdurulabiliyor (önceden ✕ yalnızca satırı gizliyor, indirme sunucuda devam ediyordu). Yarım kalan parça dosyaları da temizleniyor
- **Kanal takibi ayrı sayfaya taşındı** (`/channels`) — Ayarlar sayfası kalabalıklaşmıştı; kanal ekleme ve takip listesi artık kendi sayfasında
- **ffmpeg / ffprobe sürüm kontrolü** (`/settings`) — kurulu sürümü gösterir; Windows, macOS ve Linux kurulum komutlarını kopyalanabilir şekilde listeler (sizin sisteminiz işaretli)
- **Python bağımlılık kontrolü** (`/settings`) — sanal ortamdaki paketleri PyPI ile karşılaştırır, güncelleme varsa tek tıkla kurar ve uygulamayı yeniden başlatır
- **Test paketi** — ağ gerektirmeyen, birkaç saniyede biten 110 test (`pip install -r requirements-dev.txt && pytest`): yol güvenliği, VTT/transkript ayrıştırma, sürüm karşılaştırma, yedekle-geri-yükle, çeviri bütünlüğü ve arayüzdeki HTML kaçışı

#### Kurulum aracı (`MediaGrabSetup.exe`)

- **ffmpeg / ffprobe kontrolü** — gereksinimler listesine eklendi; eksikse platformunuza uygun kurulum komutunu kopyalanabilir şekilde gösterir. Kurulum sonunda da uyarır
- **Sistem diline göre Türkçe/İngilizce** — uygulamayla aynı mantık; arayüz, günlük ve uyarı metinlerinin tamamı
- **Python sürüm kontrolü** — sadece "kurulu mu" değil, sürümü de okur; 3.9'dan eskiyse kurulumu engelleyip gereken sürümü söyler
- **Kurulum klasörü seçilebiliyor** ("Gözat…") — artık exe'yi taşımaya gerek yok
- **Klasör uyarıları** — bulut senkronizasyon klasörü (OneDrive, Dropbox, Google Drive…) tespit edilip uyarılır; klasör boş değilse onay istenir; sürücü kökü ve kişisel klasörler (Masaüstü, Belgeler, kullanıcı klasörü) reddedilir — kaldırma işlemi klasör içeriğini sildiği için
- **"MediaGrab'ı Başlat" düğmesi** — kurulum bitince başlatma dosyasını aramaya gerek kalmıyor
- **Görsel yenileme** — `ttk` ile yerel tema, renkli durum göstergeleri, işlem sırasında ilerleme çubuğu; boş siyah günlük alanının yerinde artık "Kur'a bastığınızda ne olacak" özeti duruyor

#### Düzeltilen

- **Güvenlik: başlıklar üzerinden kod çalıştırma açığı** — arayüzdeki HTML kaçışı tırnak işaretlerini kaçırmıyordu; içinde tırnak geçen bir video başlığı (üçüncü taraf sitelerden gelen, güvenilmeyen veri) HTML özniteliğinden çıkıp sayfada betik çalıştırabiliyordu. Tırnaklı başlıklar ayrıca tooltip'leri de bozuyordu
- **Var olan dosya artık korunuyor** — aynı videoyu tekrar indirirken yt-dlp eski dosyayı *indirmenin başında* siliyordu; iptal, HTTP 403, bağlantı kopması veya çökme durumunda ne yeni ne eski dosya kalıyordu. Artık eski dosya kenara alınıyor ve indirme tamamlanmazsa aynen geri konuyor (uygulama çökerse bir sonraki açılışta kurtarılıyor)
- **İndirme panelindeki ✕ düğmesi** — panel her 800 ms'de baştan çiziliyor, düğme yok edilip yeniden yaratılıyordu; tıklama bu araya denk gelirse tarayıcı `click` olayını hiç üretmiyor ve düğme sessizce çalışmıyordu. Ayrıca düğme daire yerine mavi bir elips olarak çiziliyordu (temel `button` dolgusu sıfırlanmamıştı)
- **11 butonun vurgu (hover) rengi** — temel `button:hover` kuralı özgüllük nedeniyle bileşenlerin kendi renklerini eziyor, hepsi mavi görünüyordu
- **Mobilde üst menü taşması** — 375 px'te menü kutusundan 33 px taşıyor, "EN" dil düğmesi görünür alanın dışında kalıyordu
- **İngilizce arayüzde Türkçe metin görünmesi** — sunucu dili bildiği hâlde sayfayı Türkçe basıyor, JS sonradan değiştiriyordu; artık ilk boyama doğru dilde
- **Tek dosya silme onayı** — "Tümünü Sil" onay soruyordu ama tek bir dosyayı silmek onaysızdı (geri alınamaz bir işlem). Kanal kaldırma için de onay eklendi
- **Yarım kalan indirme dosyaları** — `.part` / `.ytdl` artıkları birikiyordu; artık iptalde ve uygulama açılışında temizleniyor

#### Değiştirilen

- **Geçmiş sayfası belirgin şekilde hızlandı** — her kapak resmi için her sayfa yüklemesinde yeniden ffprobe+ffmpeg çalıştırılıyordu (ölçüm: istek başına ~590 ms). Artık önbellekleniyor ve `ETag` gönderiliyor (~2 ms); altyazı/transkript dosyaları için hiç istek atılmıyor
- **Erişilebilirlik** — ikon düğmelerine ve geçmiş kartlarındaki butonlara açıklayıcı etiketler, gezinmeye `aria-current`, hata alanlarına `role="alert"` eklendi
- Tüm renkler CSS değişkenlerine taşındı (açık temanın ön koşulu); koyu tema görünümü birebir korundu
- Arayüz metinleri tek kaynaktan (`i18n.py`) sunucuda üretiliyor; JS'teki 27 ölü çeviri anahtarı ve 21 kullanılmayan DOM referansı temizlendi
- FastAPI'de kullanımdan kalkan `on_event` yerine `lifespan` kullanılıyor

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

### [1.6.0] — 2026-08-25

#### Added

- **Cookie support is back** (`/settings` → Cookies) — two routes for age-restricted, members-only or sign-in-required content:
  - **`cookies.txt` file** — point MediaGrab at a file you exported from your browser with an extension. Works in every browser, on every OS
  - **Straight from the browser** — works with Firefox. Since Chrome 127, cookies on Windows can only be decrypted by Chrome's own process (app-bound encryption), so this route does not work there for Chromium-based browsers; the UI says so plainly. That is exactly why our first attempt (v1.1.0) failed
  - **A "Test" button** — tells you whether the setting actually works without starting a download, and shows the reason when it doesn't
  - Your cookies are never copied into MediaGrab or sent anywhere; only the source name (a browser name or a file path) is stored in `settings.json` on this machine

### [1.5.0] — 2026-08-25

#### Fixed

- **Opus audio downloads had been broken since v1.2.0** — the download completed and then died in postprocessing with `module mutagen was not found`. The `mutagen` dependency was dropped in v1.2.0; what was missed is that while MediaGrab's own code doesn't use it, **yt-dlp** needs it to embed cover art into Opus files. Since Opus is the default audio format (the "Best Audio" button, the first option in the list, channel auto-download), the most visible audio path was dead for three releases. M4A and MP3 were unaffected. The dependency is back, with a test so it can't disappear quietly again
- **Opus files showed no title or artist** — Ogg-based formats keep tags at *stream* level while we only read the *container* level; both are checked now
- **A failed channel check never updated the "last checked" time** — the failure path returned before the line that records it, so a broken channel (deleted, renamed, made private) was indistinguishable from one with no new uploads. The attempt is now always recorded, and the channel card shows "Last check failed: [reason]"

#### Added

- **Bulk download for playlists** — a range selector (e.g. `1 – 19`) and one-click "Best Audio" / "Best Video" above the playlist. Previously every video had to be clicked and its format re-chosen individually. Mistyped ranges are corrected (`5-3` is swapped, out-of-range values are clamped)
- **Queue position** — three downloads run at once; the ones waiting now say "2nd in queue" instead of an indefinite "Starting…" that looked identical to a stuck download
- **Automated releases** (GitHub Actions) — pushing a version tag builds the exe, runs the tests, verifies the exe actually starts, computes the SHA256 into the release notes, and attaches the file. Since PyInstaller output differs on every build, the hash is no longer hard-coded in the README - it points readers at the release page instead

### [1.4.0] — 2026-08-22

#### Added

- **Light / dark theme** — follows your operating system by default; pick it by hand under **Settings → Appearance** (System / Light / Dark) or with the header toggle. The choice is applied before the first paint, so there's no theme flash on load
- **Cancel a download** — the ✕ on a running download now actually stops it (previously it only hid the row while the download kept going server-side), and leftover fragment files are cleaned up
- **Channel following moved to its own page** (`/channels`) — Settings had grown crowded; adding and listing followed channels now lives on a dedicated page
- **ffmpeg / ffprobe version check** (`/settings`) — shows the installed version and lists the Windows, macOS and Linux install commands with copy buttons (yours is marked)
- **Python dependency check** (`/settings`) — compares the virtual environment against PyPI and updates everything with one click, restarting the app afterwards
- **Test suite** — 110 tests that need no network and finish in seconds (`pip install -r requirements-dev.txt && pytest`): path safety, VTT/transcript parsing, version comparison, backup-and-restore, translation integrity, and front-end HTML escaping

#### Installer (`MediaGrabSetup.exe`)

- **ffmpeg / ffprobe check** — added to the requirements list; if it's missing, the right install command for your platform is shown with a copy button, and the install log warns about it too
- **Turkish/English from the system locale** — same logic as the app, covering the interface, log messages and warnings
- **Python version check** — not just "is it installed" but which version; anything older than 3.9 blocks the install and says what's needed
- **The install folder can be chosen** ("Browse…") — no need to move the exe around any more
- **Folder warnings** — cloud-sync folders (OneDrive, Dropbox, Google Drive…) are detected and warned about, a non-empty folder asks for confirmation, and drive roots plus personal folders (Desktop, Documents, your user folder) are refused outright, since removing MediaGrab deletes the folder's contents
- **"Start MediaGrab" button** — no hunting for the launcher once the install finishes
- **Visual refresh** — native `ttk` theming, colour-coded requirement rows, a progress indicator while work runs, and the empty black log area replaced with a summary of what Install will do

#### Fixed

- **Security: script injection via titles** — the UI's HTML escaping did not escape quotes, so a video title containing one (untrusted data from third-party sites) could break out of an HTML attribute and run script in the page. Quoted titles also broke tooltips
- **Existing files are no longer destroyed** — when re-downloading the same video, yt-dlp deleted the existing file *at the start* of the download, so a cancel, an HTTP 403, a dropped connection, or a crash left you with neither the new file nor the old one. The previous file is now moved aside and put back if the download doesn't finish (and recovered on next launch if the app crashed)
- **The ✕ button in the download panel** — the panel rebuilt itself every 800 ms, destroying and recreating the button; a click landing across a rebuild produced no `click` event at all, so the button silently did nothing. It was also drawn as a blue ellipse instead of a circle (the base `button` padding was never reset)
- **Hover colour on 11 buttons** — a specificity quirk let the base `button:hover` rule override each component's own hover colour, painting them all accent-blue
- **Header overflow on mobile** — at 375 px the header's content ran 33 px past its box, pushing the "EN" language button out of view
- **Turkish text shown in the English UI** — the server knew the language but still rendered the page in Turkish for JS to swap afterwards; the first paint is now in the right language
- **Confirmation before deleting a single file** — "Clear All" asked for confirmation but deleting one file (an unrecoverable action) did not. Removing a followed channel now asks too
- **Leftover partial downloads** — `.part` / `.ytdl` debris accumulated; it's now cleared on cancel and at startup

#### Changed

- **The history page is markedly faster** — every cover was re-extracted with ffprobe+ffmpeg on each page load (measured ~590 ms per request). Results are now cached and served with an `ETag` (~2 ms), and subtitle/transcript files no longer trigger a request at all
- **Accessibility** — descriptive labels on icon buttons and history-card actions, `aria-current` on navigation, `role="alert"` on error areas
- All colours moved to CSS variables (the prerequisite for the light theme); the dark theme renders identically to before
- UI strings now come from a single server-side source (`i18n.py`); 27 dead translation keys and 21 unused DOM references were removed from the JS
- Replaced FastAPI's deprecated `on_event` with `lifespan`

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
