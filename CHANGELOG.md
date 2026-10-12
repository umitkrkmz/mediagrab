# Changelog

Bu dosya MediaGrab'daki önemli değişiklikleri sürüm bazında listeler.
This file lists notable changes to MediaGrab, by release.

---

## [Türkçe](#türkçe) · [English](#english)

---

## Türkçe

### [2.4.0] — 2026-10-12

Kurulum ve güven sürümü: Windows'ta MediaGrab artık tek bir kurulum dosyasıyla, başka hiçbir şey kurmadan çalışıyor.

#### Eklenen

- **Yeni Windows kurulum programı** — `MediaGrabSetup.exe` artık her şeyi içinde getiriyor: Python, FFmpeg ve Deno. Python, Git ya da ffmpeg kurmak, internetten paket indirmek gerekmiyor; yönetici izni istemiyor. Windows'un diline göre Türkçe ya da İngilizce açılıyor, "Yüklü uygulamalar"da görünüyor, Başlat menüsüne ve isteğe bağlı olarak masaüstüne kısayol koyuyor. Program `%LOCALAPPDATA%\Programs\MediaGrab`'a, ayarlar ve kanallar `%LOCALAPPDATA%\MediaGrab`'a, indirilenler varsayılan olarak `İndirilenler\MediaGrab`'a gidiyor. Güncellemek için yeni kurulum dosyasını çalıştırmak yeterli; MediaGrab açıksa kurulum önce sorup onu kapatıyor
- **Bildirim alanı simgesi** — Windows kurulumunda MediaGrab konsol penceresi olmadan çalışıyor; saatin yanındaki **M** simgesine tıklayınca sayfa açılıyor, sağ tıklayıp **MediaGrab'ı kapat** ile kapanıyor. Görev Yöneticisi'nde "Python" yerine "MediaGrab" adıyla ve kendi simgesiyle görünüyor
- **Ayarlanabilir indirme klasörü** (Ayarlar → İndirme Ayarları → İndirme Klasörü) — kurulumda ya da sonradan seçiliyor; **Klasör Seç…** Windows'un kendi klasör seçme penceresini açıyor. Yazılamayan, MediaGrab'ın program klasörünün içinde kalan ya da göreli yollar reddediliyor; OneDrive gibi eşitlenen bir klasör seçilirse uyarı çıkıyor. Kaynak koddan kurulumda da çalışıyor; yalnızca MediaGrab'ın çalıştığı bilgisayardan değiştirilebiliyor (telefondan değil). Docker'da klasörü `docker-compose.yml` belirliyor
- **Eski indirmeleri taşıma** — indirme klasörü değişince Ayarlar'da eski klasör için bir kart çıkıyor: **Buraya taşı** ya da **Yerinde bırak**. Yalnızca MediaGrab'ın indirdiği dosyalar (ve `.json` bilgi dosyaları) kanal klasörleriyle birlikte taşınıyor, klasördeki başka dosyalara dokunulmuyor, hiçbir dosyanın üzerine yazılmıyor. Başka bir diske taşırken önce kopyalanıp boyut doğrulanıyor, sonra eskisi siliniyor; taşıma sürerken yeni indirmeler bekliyor
- **Docker ile kurulum, aynı kurulum programında** — kurulumun başında "Normal kurulum" ya da "Docker ile kurulum" seçiliyor. Docker Desktop'ın kurulu ve çalışır olduğu denetleniyor; Docker'da zaten bir MediaGrab varsa (eski kurulum aracıyla kurulmuş olanlar dahil) bulunuyor, sürümü gösteriliyor ve parolası ile verileri korunarak yerinde güncelleniyor. Yoksa klasör ve ilk parola sorulup imaj indiriliyor, başlatılıyor ve MediaGrab cevap verene kadar bekleniyor. İmaj kurulum programının sürümüne sabit (ör. `ghcr.io/umitkrkmz/mediagrab:2.4.0`). Kaldırınca konteyner siliniyor, veriler varsayılan olarak klasörde kalıyor
- **Eski kurulumdan geçiş** — v2.4.0'dan önceki kurulum aracıyla kurulmuş bir MediaGrab bulunursa ayarlar, kanallar, çerezler ve istatistikler yeni kuruluma aktarılıyor. Videolar yerinde kalıyor; Ayarlar'da **Buraya taşı** kartı ve Geçmiş'te bir not onları yeni klasöre taşımayı teklif ediyor. Eski kurulum silinmiyor
- **Kaldırırken verileriniz ne olsun?** — kaldırıcı soruyor: yalnızca MediaGrab'ı kaldır (varsayılan; ayarlar ve videolar kalır), ayarları da sil, ya da ek bir onayla indirilen videoları da sil. Videolar silinirken yalnızca MediaGrab'ın indirdiği dosyalar gidiyor, klasördeki başka dosyalar kalıyor
- **Üçüncü taraf lisans bildirimleri** — Windows paketindeki Python, FFmpeg ve Python paketlerinin sürümleri, lisansları ve kaynak bağlantıları kurulum klasöründeki `THIRD-PARTY-NOTICES.txt`'de ve Hakkında sayfasında. FFmpeg GPL lisanslı olduğu için her yayına o sürümdeki FFmpeg'in kaynak kodu ve derleme betikleri ek dosya olarak konuyor
- **README: "Güvenli mi?" ve "Telefondan kullanın"** — kurulum dosyasının nereden alınacağı, SmartScreen uyarısı, SHA256 ve VirusTotal ile doğrulama, MediaGrab'ın dışarıyla neden ve ne zaman konuştuğu; iPhone'da indirme uygulaması yerine MediaGrab'ı telefonun tarayıcısından kullanma

#### Değiştirilen

- **Eski kurulum aracı kaldırıldı** — v2.4.0'dan önceki `MediaGrabSetup.exe` (Python, Git ve ffmpeg'i bilgisayara kuran araç) yerini yeni kurulum programına bıraktı. İndirme bağlantısı ve dosya adı aynı
- **Ayarlar'daki güncelleme yönergesi** yeni kurulum türlerini tanıyor: Windows kurulum programıyla (normal ya da Docker) kurulanlara "yeni kurulum dosyasını çalıştırın", eski araçla kurulanlara "yeni kurulum programına geçin, verilerinizi aktarmayı teklif eder" diyor
- **Günlük dosyası şişmiyor** — konsol penceresi olmadan çalışırken (Windows kurulumu, Docker) yt-dlp'nin indirme ilerleme satırları artık `mediagrab.log`'a ya da `docker logs`'a yazılmıyor (tek bir indirme yüzlerce KB'lık satır bırakabiliyordu); hata ve uyarı satırları yazılmaya devam ediyor

#### Düzeltilen

- **Türkçe Windows'ta detay sayfasında bozuk karakterler** — ffprobe/ffmpeg çıktısı Windows'un eski kod sayfasıyla okunuyordu; artık UTF-8 okunuyor
- **Eski kurulum aracının Docker kurulumu `$` içeren bir parolayı bozuyordu** — Docker Compose `$`'ı değişken başlangıcı sayıyor; parola `docker-compose.yml`'e kaçışsız yazıldığı için ilk parola, girilenden farklı oluyordu. Yeni kurulum programı `$`'ı doğru kaçırıyor

#### Güncellerken

- **Eski Windows kurulum aracıyla kurduysanız:** yeni `MediaGrabSetup.exe`'yi indirip çalıştırın. Önceki kurulumu bulur ve verilerinizi aktarmayı teklif eder; videolarınızı sonra Ayarlar'dan yeni klasöre taşıyabilirsiniz. Her şeyin geldiğini gördükten sonra eski klasörü elle silebilirsiniz
- **Eski araçla Docker kurduysanız:** yeni kurulum programında **Docker ile kurulum**'u seçin; var olan kurulumu bulup yerinde günceller. Bundan sonra imaj kurulum programının sürümüne sabit olduğu için güncellemeler yeni kurulum dosyasıyla yapılır (`docker compose pull` sabit sürümü yeniden indirir)
- **Elle Docker / kaynak kod:** uygulamada yeni bağımlılık yok — `docker compose pull && docker compose up -d` ya da `git pull`

#### Geliştirici notu

- **Windows paketi** — `packaging/build_windows.py` gömülü Python'u, bütün paketleri ve FFmpeg'i (her indirme sabit sürüm + SHA256) hazırlıyor, `packaging/mediagrab.iss` (Inno Setup) tek bir kurulum dosyasına çeviriyor. PyInstaller ve Tkinter artık kullanılmıyor
- **CI** — `tests.yml`'e her push'ta ve PR'da koşan bir Windows işi eklendi (gerçek Win32 bildirim alanı simgesi, `MediaGrab.exe`, kurulum programının Pascal kodu gerçek ISCC ile). `release.yml` kurulum programını derleyip Windows'ta sessizce kurup başlatıyor, paketin kendi Python ve FFmpeg'iyle çalıştığını denetliyor, kaldırıyor; FFmpeg kaynak arşivlerini ve SHA256 değerini yayına ekliyor
- **Kurulum programı ile uygulama arasındaki devir adları** (`install-download-dir.txt`, `MediaGrabTrayWindow`, `MEDIAGRAB_INSTALLED_BY` vb.) iki tarafta da elle yazılı; testler eşleştiklerini denetliyor (bkz. `AGENTS.md`)

### [2.3.1] — 2026-10-10

#### Düzeltilen

- **Windows kurulum programının "Docker ile kur" seçeneği eski bir imajı kurabiliyordu** — bilgisayarda daha önceki bir kurulumdan kalma `latest` imajı varsa (container'ı ve klasörü silinmiş olsa bile), kurulum yeni sürümü indirmeden o eski imajı başlatıyordu; `docker compose up -d` yalnızca hiç olmayan bir imajı indiriyor. Kurulum artık önce `docker compose pull` ile güncel imajı indiriyor. İnternet yoksa ve bilgisayarda bir imaj varsa kurulum onunla devam ediyor ve bunu günlükte belirtiyor

#### Güncellerken

- **Uygulamanın kendisinde değişiklik yok** — yalnızca `MediaGrabSetup.exe` değişti. Docker kullanıyorsanız ve Ayarlar'da sürüm 2.3.0 görünüyorsa bir şey yapmanız gerekmiyor; v2.3.0'ı kurduğunuz halde 2.2.0 görünüyorsa `docker-compose.yml`'in bulunduğu klasörde `docker compose pull && docker compose up -d` çalıştırın

### [2.3.0] — 2026-10-10

#### Eklenen

- **İstatistikler** (Geçmiş → İstatistikler sekmesi) — ne kadar, hangi siteden ve hangi biçimde indirdiğinizi gösteren yerel bir panel: Günlük / Haftalık / Aylık görünüm, dönem ve tüm zamanlar özeti, zamana göre indirme çubukları, siteler, ses biçimleri (Opus / M4A / MP3) ve video çözünürlükleri, diskte MediaGrab'ın ve diğer dosyaların kapladığı yer ile boş alan. Her indirme bittiği anda sayılıyor; "Cihaza Aktar" ya da Geçmiş'ten silinen dosyalar sayılmaya devam ediyor. İlk açılışta indirme klasöründeki mevcut dosyalar bir kez içe aktarılıyor. Yalnızca sayılar tutuluyor (site, tür, biçim, adet, boyut): başlık, bağlantı, kanal ya da dosya adı kaydedilmiyor; "İstatistikleri Sıfırla" indirilen dosyalara dokunmuyor. Gün ve hafta sınırları tarayıcınızın saatine göre çiziliyor (Docker UTC'de çalışsa da gece yaptığınız bir indirme doğru güne düşüyor)
- **MediaGrab'e özgü oynatıcı** (Geçmiş → bir dosya → Oynat) — tarayıcının kendi kontrolleri yerine sade, YouTube/Drive tarzı bir oynatıcı: ilerleme çubuğu (üzerine gelince zamanı gösteriyor), ses, oynatma hızı (0.5× – 2×), pencere içinde pencere ve tam ekran. "İndir" menüsü ve sağ tıktaki "Farklı kaydet" yok. Klavye kısayolları YouTube'la aynı: boşluk/K, ←/→ (5 sn), J/L (10 sn), ↑/↓ ses, M sessiz, F tam ekran, 0–9 atlama. Ses düzeyi ve hız hatırlanıyor; telefonda ilk dokunuş yalnızca kontrolleri gösteriyor
- **Detay sayfasında dosyanın gerçek içeriği** — Çözünürlük (ör. `1920×1080 (1080p) · 30 fps`), video codec'i ve ses bilgisi (ör. `Opus · 48 kHz · stereo`) artık dosyanın kendisinden okunuyor; indirmeden önce hangi düğmeye basıldığına değil, gerçekte ne indiğine bakıyor. Müzik dosyalarındaki kapak resmi video sayılmıyor
- **Docker'da "Klasöre Kaydet"** — Docker'ı kendi bilgisayarınızda çalıştırıp `localhost` ile açtığınızda (Chrome/Edge), "Cihaza İndir" yerine dosyayı istediğiniz klasöre kaydeden bir pencere açılıyor. Pencereyi iptal ederseniz hiçbir şey olmuyor

#### Düzeltilen

- **Docker'da iptal edilen kaydetme dosyayı siliyordu** — Uzaktan Erişim'de "Cihaza Aktar" seçiliyken, Docker'ı kendi bilgisayarında kullananların tarayıcısı da "başka bir cihaz" sayılıyordu (Docker'da her istek aynı iç ağ adresinden geliyor). Chrome/Edge "Farklı Kaydet" penceresi açıkken dosyayı arka planda tamamen indirdiği için, pencere iptal edilse bile MediaGrab'daki tek kopya siliniyordu. Artık kendi bilgisayarınızdan yapılan indirmeler hiçbir zaman otomatik silinmiyor; "Klasöre Kaydet"te kopya yalnızca dosya seçtiğiniz klasöre gerçekten yazıldıktan sonra siliniyor. Telefon gibi diğer cihazlarda davranış aynı. Ayarlar'daki açıklama da buna göre güncellendi
- **Windows kurulum programının Onar/Kaldır işlemi yüklenen `cookies.txt`'yi siliyordu** (v2.2.0'dan beri) — korunan dosyalar listesinde yoktu. Artık `cookies.txt` ve yeni `stats.json` da korunuyor

#### Güncellerken

- **Docker:** `docker-compose.yml`'in `volumes:` bölümüne `- ./data/stats:/data/stats` satırını ekleyin (istatistikler container yenilenince sıfırlanmasın diye; yeni kurulumlarda zaten var). Ardından `docker compose pull && docker compose up -d`
- **Windows kurulum programı / kaynak kod:** yeni bağımlılık yok. Kurulum programında "Onar / Güncelle", kaynak kodda `git pull`
- **İstatistikler** ilk açılışta mevcut indirmelerden doldurulur; bu sürümden önce silinmiş dosyalar (ör. "Cihaza Aktar" ile) sayılamaz

#### Geliştirici notu

- **Testler her push'ta** — `master`'a her push'ta ve her PR'da tüm testler Linux'ta çalışıyor (`.github/workflows/tests.yml`); yayında Windows'ta çalışmaya devam ediyor. Linux'ta çalıştırınca iki test hatası ortaya çıktı ve düzeltildi: PATH testi Windows'a özgü bir sürücü harfi kullanıyordu; testler bir container içinde çalışınca kendini Docker'da sanıp ilk parolayı istiyordu
- **Daha derin Docker duman testi** (`.github/scripts/smoke-docker.sh`) — yalnızca "cevap veriyor mu" değil: ilk parolayla giriş, ffmpeg/ffprobe/Deno'nun varlığı, Geçmiş, detay sayfasındaki çözünürlük satırı ve istatistikler. Ağ gerektirmiyor, elle de çalıştırılabiliyor
- **Yayın öncesi elle deneme** — `CONTRIBUTING.md`'nin yayın listesine gerçek bir YouTube/başka site/telefon denemesi eklendi; otomatik testler bilerek internete çıkmıyor
- **app.js'de TR/EN anahtar eşitliği testi** — sunucu tarafındaki gibi; yalnızca İngilizcede kalmış iki kullanılmayan metni yakaladı

### [2.2.0] — 2026-10-07

#### Eklenen

- **MediaGrab güncelleme kontrolü** (Ayarlar → Sürüm Kontrolleri) — kurulu sürüm GitHub'daki son yayınla karşılaştırılıyor; yeni sürüm varsa sürüm notlarına bağlantı ve kurulum türüne göre doğru adımlar gösteriliyor (Docker: `docker compose pull`, Windows kurulum programı: "Onar / Güncelle", kaynak kod: `git pull` + `pip install`). Kendi kendini güncellemiyor, kontrol yalnızca Ayarlar açıldığında yapılıyor ve bir saat önbelleğe alınıyor. Kurulu sürüm Hakkında sayfasında da görünüyor
- **cookies.txt yükleme** (Ayarlar → Çerezler) — yaş sınırlı, üyelere özel veya giriş gerektiren videolar için hesabınızın çerezlerini içeren bir `cookies.txt` dosyasını artık doğrudan arayüzden yüklüyorsunuz; dosya yolu yazmak gerekmiyor. Docker ve Raspberry Pi dahil her kurulumda çalışıyor (önceden Docker'da çerez kullanmanın bir yolu yoktu). Dosya yt-dlp'nin kendi okuyucusuyla doğrulanıyor ve içindeki siteler listeleniyor: YouTube ve Google işaretli geliyor, yalnızca seçtiğiniz sitelerin çerezleri kaydediliyor, gerisi diske hiç yazılmıyor. Kayıttan sonra site/çerez sayısı, yükleme ve son güncelleme zamanı ve dosyada YouTube oturumu olup olmadığı gösteriliyor; "Çerezleri sil" ile kaldırılıyor
- **"cookies.txt nasıl alınır?" rehberi** — Ayarlar'da ve kılavuzda adım adım: Get cookies.txt LOCALLY eklentisi, gizli pencere, `youtube.com/robots.txt`, "Export" (Export All değil) ve yt-dlp'nin hesap güvenliği uyarısı. Kılavuza ayrı bir "Çerezler" bölümü eklendi
- **YouTube için JavaScript çalışma ortamı (Deno)** — yt-dlp, YouTube'un korumalarını çözmek için artık harici bir JS çalışma ortamı istiyor; olmadan bazı biçimler eksik kalabiliyor ve yaş sınırlı videolar çerezle bile inmeyebiliyor. Deno ve çözücü betikleri (`yt-dlp-ejs`) artık bağımlılıklarla birlikte kuruluyor (Windows, Linux x86_64/arm64, macOS, Docker). Ayarlar → Sürüm Kontrolleri'nde durumu görünüyor; eksikse "Şimdi Güncelle" kuruyor
- **"Tanılama bilgisini kopyala"** (Ayarlar → Geri Bildirim) — hata bildirimine yapıştırmak için MediaGrab/yt-dlp/ffmpeg sürümlerini, JS çalışma ortamını, işletim sistemini, kurulum türünü ve çerez modunu tek metinde topluyor. Dosya yolu, IP adresi, bilgisayar adı veya çerez içeriği içermiyor; panoya kopyalanamazsa metin seçili olarak gösteriliyor
- **Çerezle ilgili hatalarda yönlendirme** — yaş sınırı, bot doğrulaması, üyelere özel ve gizli video hatalarının altında doğrudan Ayarlar → Çerezler bağlantısı çıkıyor; çerez zaten ayarlıysa "yenisini yükleyin" diyor. yt-dlp'nin yalnızca yan mesaj olarak bildirdiği iki durum da artık ayrı ayrı açıklanıyor: çerezlerin geçersizleşmesi ve YouTube'un hesap için yaş doğrulaması istemesi (ikincisi YouTube hesabından yapılır, yeni bir cookies.txt çözmez)

#### Değiştirilen

- **Repodaki `docker-compose.yml` artık yayımlanan imajı kullanıyor** (`image: ghcr.io/umitkrkmz/mediagrab:latest`, `build: .` yerine) — güncelleme `docker compose pull && docker compose up -d` ile yapılıyor, yerel derleme gerekmiyor. Kendi değişikliklerinizi derlemek için `build: .` hâlâ kullanılabilir
- **Windows'ta "Tarayıcıdan" seçeneğinde yalnızca Firefox** — Chrome, Edge, Brave gibi Chromium tabanlı tarayıcıların çerezleri Windows'ta okunamıyor (App-Bound Encryption) ve bu tarayıcılardan biri seçiliyken **her** video "Could not copy Chrome cookie database" hatası veriyordu. Daha önce Windows'ta Chrome seçmiş olanlarda bu ayar artık yok sayılıyor (indirmeler çalışıyor) ve Ayarlar bunu bir uyarıyla gösteriyor. macOS ve Linux'ta değişiklik yok
- **Docker'da sürüm kontrolleri sadeleşti** — ffmpeg imajla birlikte geldiği için işletim sistemine göre kurulum komutları ("sisteminiz: Linux" dahil) artık gösterilmiyor; yt-dlp'nin "Şimdi Güncelle" butonu kalıyor, Docker'da işe yaramayan elle venv adımları gizleniyor. Docker'da "Tarayıcıdan" çerez seçeneği de gizli (container'da tarayıcı yok)
- **yt-dlp güncellemesi Deno'yu da güncelliyor** — "Şimdi Güncelle" ve kılavuzdaki komut artık `yt-dlp[default,deno]` kuruyor; düz `pip install -U yt-dlp` çözücü betiklerini geride bırakıp YouTube çözümlemesini sessizce bozabiliyordu

#### Düzeltilen

- **İndirme sürerken yüklenen çerezlerin üzerine yazılması** — yt-dlp, bitirdiği her indirmede çerezleri dosyaya geri yazıyor; indirme sürerken yeni bir cookies.txt yüklenirse biten indirme eski çerezleri yeni yüklemenin üzerine yazıyordu. Artık dosya o arada değiştiyse (yeni yükleme, silme, başka bir indirme) geri yazma atlanıyor ve silinen çerezler geri gelmiyor. Canlı bir kontrol deneyiyle doğrulandı
- **Yaş doğrulaması isteyen hesapla sessiz kalite düşüşü** — YouTube hesap için yaş doğrulaması istediğinde yalnızca 360p birleşik bir biçim geliyordu: Opus/M4A ham "Requested format is not available" hatasıyla düşüyor, MP3 ise uyarısız olarak 360p videonun sesinden yeniden kodlanıyordu. Artık analiz bunu bildiriyor: sarı bir uyarı nedenini söylüyor, ayrı ses akışı yoksa Opus/M4A devre dışı görünüyor ve "En İyi Ses" MP3'ü seçiyor. Biçim bulunamadı hatası da anlaşılır bir mesaja çevrildi
- **Süresi dolmuş bir oturum "YouTube oturumu var" görünüyordu** — YouTube geçersiz oturumu temizlerken bir çerezi geride bırakıyor; MediaGrab artık yt-dlp'nin kendi ölçütünü kullanıyor (`LOGIN_INFO` + SAPISID)

#### Güncellerken

- **Docker:** `docker-compose.yml`'in `volumes:` bölümüne `- ./data/cookies:/data/cookies` satırını ekleyin (yüklenen çerezler container yenilenince kaybolmasın diye; yeni kurulumlarda zaten var). Repodan elle kurduysanız `build: .` satırını `image: ghcr.io/umitkrkmz/mediagrab:latest` ile değiştirin. Ardından `docker compose pull && docker compose up -d`
- **Windows kurulum programı / kaynak kod:** Deno'nun gelmesi için bağımlılıkları yeniden kurun — kurulum programında "Onar / Güncelle", kaynak kodda `pip install -r requirements.txt`. Atlarsanız Ayarlar → Sürüm Kontrolleri "JavaScript çalışma ortamı: Eksik" gösterir ve oradaki "Şimdi Güncelle" de kurar

#### Geliştirici notu

- **CI:** GitHub Actions runner'ları sabitlendi (`ubuntu-24.04`, `windows-2025`; `ubuntu-latest` 19 Ekim 2026'da Ubuntu 26'ya geçiyor) ve tüm action'lar Node 24 kullanan ana sürümlere yükseltildi (Node 20 kullanımdan kalkıyor)
- **PyInstaller sabitlendi** (`6.22.3` + `pyinstaller-hooks-contrib 2026.7`, v2.1.0'ı derleyen sürümler) — her yayında exe'nin gereksiz yere değişip Windows Defender/SmartScreen itibarını sıfırdan başlatmasının önüne geçmek için
- **Yayın kontrol listesi** — `CONTRIBUTING.md`'ye "Yayın yaparken" bölümü eklendi: sürüm ve CHANGELOG, etiketten önce iş akışlarını elle deneme, Actions uyarılarını okuma, gerekirse Docker imajını etiketten elle yeniden yayımlama
- **Testler artık geliştiricinin gerçek verisine dokunmuyor** — uygulamaya istek atan testler açılışta kanal kontrolünü başlatıp projenin kendi `channels.json`'unu okuyor, YouTube'a gerçek istek atıyor ve sonucu geri yazıyordu; indirme klasöründe yarım dosya temizliği de çalışıyordu. `tests/conftest.py` artık her test için tüm kullanıcı verisi yollarını geçici bir klasöre yönlendiriyor

### [2.1.0] — 2026-09-18

#### Eklenen

- **Mobil uyumlu arayüz** — dar ekranlarda üst menü ve Ayarlar sayfasının kategori listesi artık ☰ simgesiyle açılıp kapanan dikey listeler; Ayarlar'da bir kategori seçilince menü kendiliğinden kapanıyor. Masaüstü görünüm değişmedi
- **Yeniden düzenlenen kılavuzlar ve ekran görüntüleri** — `docs/README.tr.md` / `README.en.md` baştan düzenlendi: "Hızlı başlangıç" tablosu, 5 adımlı örnek senaryolar, özelliklerin 5 gruba bölünmesi, yeni "Mobil Kullanım" bölümü; gerçek ekran görüntüleri (`docs/images/`) ve ana README'de bir hero görseli

#### Düzeltilen

- **Telefonda üst menü kırpılıyordu** — dar ekranda taşan menü satırı `justify-content: center` yüzünden iki tarafa eşit taşıyordu; ilk sekme ("Ana Sayfa") sola, son sekme sağa doğru görünmez oluyordu. Yerini açılır menü aldı
- **Telefonda "Panodan yapıştır" düğmesi hiçbir şey yapmıyordu** — tarayıcılar panoyu okuma API'sini yalnızca HTTPS/`localhost` üzerinde açar; uzaktan erişim düz HTTP olduğu için düğme LAN'daki hiçbir cihazda çalışamazdı. Bu durumda düğme artık gösterilmiyor (alana uzun basıp "Yapıştır" hâlâ çalışıyor ve linki yine otomatik çözümlüyor); `localhost`'ta davranış aynı
- **Kanallar sayfasında rozet, metnin üzerine biniyordu** — dar ekranda "Son kontrol" satırı çok satıra bölünüp satırı uzatıyor, dikey ortalanmış "BİLDİR/OTOMATİK" rozeti o bloğun ortasında yüzüyordu. Metin tek satırda kısaltılıyor, butonlar kendi satırına iniyor
- **Geçmiş sayfasının liste görünümü telefonda sıkışıyordu** — küçük resim, isim, tarih ve iki buton tek satıra sığmıyor, tarih kesiliyordu; artık iki satıra bölünüyor
- **Ayarlar'ın kategori menüsünde boşluk** — masaüstü için ayarlanmış boşluk mobilde de uygulanıp menü kapalıyken bile ~64px boş alan bırakıyordu
- **iPhone'da bazı alanlara dokununca sayfa yakınlaşıyordu** — Geçmiş arama/filtreleri, kanal linki, çerez ayarları ve playlist aralık kutusunun yazı boyutu 16px'in altındaydı (iOS Safari bu durumda otomatik yakınlaştırır); mobilde 16px'e çıkarıldı
- **Küçük simge butonları telefonda zor dokunuluyordu** — menü, tema ve dil butonları 24-37px'ti, mobilde 32-40px'e büyütüldü
- **"Video" sekmesinin üzerine gelince yazı okunmuyordu** — genel `button:hover` kuralı sekmenin şeffaf zeminini ezip aktif sekmede vurgu rengini vurgu rengi üzerine bindiriyordu

### [2.0.1] — 2026-09-18

#### Düzeltilen

- **Docker'da (Windows/Mac) Ayarlar → Uzaktan Erişim'deki bağlantı adresi ve QR kodları yanlış IP gösteriyordu** — `lan_ip()`, bridge ağlı bir container içinden çağrıldığında Windows/Mac host'un gerçek LAN IP'sini değil, container'ın kendi iç Docker bridge IP'sini (ör. `172.19.0.2`) döndürüyordu; bu adrese ne başka bir cihaz ne de host'un kendisi ulaşabiliyordu. Windows kurulum programının "Docker ile kur" akışı artık gerçek LAN IP'yi host üzerinde tespit edip `docker-compose.yml`'e otomatik gömüyor (`MEDIAGRAB_HOST_LAN_IP`); elle Docker kurulumu için de aynı değişken `docker-compose.yml`'e talimatıyla birlikte eklendi. Gerçek bir Android telefondan doğrulandı

### [2.0.0] — 2026-09-15

#### Eklenen

- **Ev Sunucusu Modu** (Ayarlar → Uzaktan Erişim) — bir Raspberry Pi gibi 7/24 açık bir makinede çalıştıranlar için: takip listeniz siz uygulamayı açmasanız bile her 3 saatte bir otomatik kontrol edilir, ve aynı ağdaki cihazlardan LAN IP'ye ek olarak `http://mediagrab.local:8420` gibi hatırlaması kolay bir mDNS adresiyle de erişilebilir. Uzaktan Erişim'den bağımsız bir ayar
- **İki ayrı, etiketli QR kod** — Ayarlar sayfası artık hem LAN IP hem de mDNS adresi için ayrı ayrı QR kod gösteriyor, hangisinin hangisi olduğu altlarında yazıyor
- **Disk alanı kalkanı** — tahmini boyutu kalan disk alanını aşacak bir indirme baştan reddedilir; hem indirme isteği anında hem de gerçek indirme başlamadan hemen önce tekrar kontrol edilir
- **İndirme hızı sınırlama** (Ayarlar) — isteğe bağlı bir üst hız sınırı belirlenebilir (hazır seçenekler veya özel Mbps değeri)
- **Ayarları yedekle / içe aktar** (Ayarlar) — tüm ayarlar ve takip listesi (şifre hariç) tek bir dosyaya dışa aktarılıp başka bir kuruluma aktarılabilir
- **Otomatik indirme kuyruğunda manuel indirmeye ayrılmış slot** — kanal otomatik indirmeleri artık manuel bir indirmeyi süresiz bekletmiyor; paylaşılan indirme havuzunda en az bir slot her zaman manuel indirme için ayrılıyor
- **Docker desteği** — MediaGrab artık Python veya Git kurmadan, doğrudan bir Docker imajından (`ghcr.io/umitkrkmz/mediagrab`) çalıştırılabilir. Bir container her zaman `0.0.0.0`'a bağlanır; ilk çalıştırmada `MEDIAGRAB_INITIAL_PASSWORD` ortam değişkeni zorunludur ve yoksa başlamayı reddeder — böylece bir container hiçbir zaman şifresiz, açık durumda kalmaz. yt-dlp güncellemesi kalıcı bir klasöre kurulur (image yeniden oluşturulsa bile kaybolmaz); diğer bağımlılıklar yalnızca yeni bir image çekilerek güncellenir
- **Windows kurulum programında "Docker ile kur"** — Docker/Compose/daemon hazırlığını kontrol eden, bir klasör ve ilk yönetici şifresi isteyen, gerekli `docker-compose.yml`'yi kendisi yazıp başlatan ayrı bir sihirbaz akışı

#### Docker paketleme (geliştirici notu)

- `Dockerfile`, `docker-compose.yml`, `.dockerignore` — bkz. [docs/README.tr.md](docs/README.tr.md#yöntem-c-docker-her-platform)
- `.github/workflows/docker.yml` — QEMU + Buildx ile amd64 build ve gerçek container smoke-test her zaman çalışır; `v*` etiketiyle push edilen sürümlerde ayrıca amd64+arm64 multi-arch build yapılıp `ghcr.io/umitkrkmz/mediagrab`'a gönderilir

### [1.10.0] — 2026-09-13

#### Eklenen

- **Uzaktan erişim (yerel ağdan)** — Ayarlar → Uzaktan Erişim: bir şifre belirleyip açtığınızda, aynı ağdaki başka bir cihaz (telefon, dizüstü) tarayıcıdan MediaGrab'e bağlanabilir. Bağlantı adresi etkinleştirildikten sonra aynı panelde görünür. HTTP üzerinden çalışır (HTTPS değildir) — yalnızca güvendiğiniz bir ev/ofis ağında kullanın, doğrudan internete açmayın
- **Bağlı cihazlar listesi ve tek tek çıkış yaptırma** — Ayarlar, o an oturum açmış her cihazı (tarayıcı + işletim sistemi tahmini, ör. "Chrome · Windows") ve bağlantı zamanını gösterir; herhangi birini tek tek çıkışa zorlayabilirsiniz, kendi cihazınız etkilenmez
- **Uzak bir cihazdan gerçek indirme** — bir telefon/dizüstü artık "klasörde göster" yerine dosyayı doğrudan kendi cihazına indirebiliyor; host'un kendi tarayıcısında davranış değişmedi (hâlâ klasörde gösterir)
- **Depolama modu: Bende Kalsın / Cihaza Aktar** — depolaması sınırlı bir cihazda (ör. Raspberry Pi) çalıştırıyorsanız "Cihaza Aktar" modu, bir dosya bir cihaza tam olarak gönderildikten hemen sonra host'taki kopyasını siler; kendi bilgisayarınızdan yaptığınız indirmeler bu ayardan hiçbir zaman etkilenmez. Varsayılan "Bende Kalsın" önceki davranışın (kalıcı saklama) tamamen aynısı
- **İndirme ilerlemesi artık anlık** — indirme kutusu her işi ayrı ayrı yoklamak yerine tek bir canlı bağlantı üzerinden güncelleniyor, arayüz daha akıcı

#### Düzeltilen

- **Bazı videolar çok nadiren sesi olmayan bir mp4 olarak inebiliyordu** — format seçici zincirinin en sonundaki "hiçbir tercihe uymasa da olsun" düşüşü, sesi olmayan bir formata da razı olabiliyordu; artık zincirin sonu bile ses içermeyen bir formatta karar kılmıyor
- **`python -m uvicorn ...` ile başlatılan sunucu, bir güncelleme (yt-dlp/bağımlılık/uzaktan erişim ayarı) sonrası kendini yeniden başlatırken çökebiliyordu** — yeniden başlatma artık orijinal komut satırını (`-m` bayrağı dahil) koruyor

### [1.9.0] — 2026-09-11

#### Eklenen

- **Birden fazla ses parçası tek dosyada** — bir video birden fazla dilde dublajlıysa artık sadece birini değil, birden fazlasını (ör. orijinal + Türkçe) aynı anda seçip tek dosyaya (`.mkv`) her biri ayrı, oynatıcıdan seçilebilir bir ses parçası olarak gömebilirsiniz. Yalnızca manuel indirmede geçerli; kanal otomatik indirmesi hâlâ tek dil seçiyor. Tek dil seçilirse davranış tamamen eskisi gibi (mp4, tek ses parçası)
- **Ana sayfa video açıklaması** — önizleme paneli boş kalmasın diye "En İyi Ses/Video" butonlarının altında yt-dlp'nin getirdiği video açıklaması gösteriliyor, uzun açıklamalar "Daha fazla göster" ile açılıp kapanıyor
- **Ana sayfada Ses/Video sekmeleri** — aynı anda ikisi birden indirilemeyeceği için format listeleri artık geçiş animasyonlu iki sekmeye ayrıldı; Ses Parçası (her ikisine de uygulandığı için) sekmelerin üstünde, Altyazı ve Transkript her zaman görünür
- **Ses parçası ve altyazı dillerinde hover tooltip** — "DE", "JA", "ES-419" gibi chip'lerin üzerine gelince dilin tam adı ("Almanca", "Japonca", "İspanyolca") çıkıyor
- **Yeni "Hakkında" sayfası** (`/about`) — proje ne yapar, GPL-3.0 lisansı, kaynak kod ve katkı/geri bildirim linkleri tek yerde
- **Ayarlar sayfası yeniden tasarlandı** — tek uzun sayfa yerine solda kategori listesi (Görünüm, Varsayılan Ses Parçası, Çerezler, Sürüm Kontrolleri, Geri Bildirim), sağda seçilenin detay paneli
- **Geçmiş sayfasında tür filtresi ve liste görünümü** — büyük kapak kartlarına ek olarak kompakt bir liste görünümü; dosya türüne göre filtre artık diskteki gerçek uzantılardan dinamik olarak oluşuyor (elle güncellenmesi gerekmiyor)
- **Desteklenen Siteler artık tıklanabilir** — her site chip'i kendi marka renginde/logosuyla, tıklanınca ilgili sitenin ana sayfasına gidiyor
- **Dil kodu sözlüğü** (`docs/language-codes.tr.md`, `docs/language-codes.en.md`) — ISO 639-1'deki 184 dilin tam adı ve kodu; Ayarlar → Varsayılan Ses Parçası alanının yanından linkleniyor

#### Kurulum aracı (`MediaGrabSetup.exe`)

- **Sihirbaz akışı** — her şeyin tek pencereye sığdırıldığı eski ekran yerine adım adım ilerleyen sayfalar: açılışta **Kur / Onar-Güncelle / Kaldır** seçilir; Kur ve Onar sırasıyla Gereksinimler (Git, Python, ffmpeg) → Klasör ve kısayollar → Özet → canlı günlük sayfalarından geçer, Kaldır ise doğrudan klasör → özet. Özet sayfası tıklamadan önce ne olacağını (klasör, bulunan araçlar, kısayollar, üzerine yazılacak mevcut başlatma dosyası/kısayol, ffmpeg eksikse uyarı) tek yerde gösterir
- **Son kurulum klasörü hatırlanıyor** — başarılı bir kurulum/onarım klasörü `%LOCALAPPDATA%\MediaGrab\installer.json` içine yazılır; **Onar** ve **Kaldır** bu klasörü kendiliğinden doldurur (değiştirilebilir). Exe'nin yanına değil kullanıcı profiline yazılır, çünkü kurulum programı çoğunlukla İndirilenler'den çalıştırılıp sonra siliniyor. Klasör elle silinmişse güvenilmez ve doldurulmaz; kaldırma işlemi de yalnızca hatırlanan klasör boşaltıldıysa kaydı siler
- **Açılış sayfasında TR/EN düğmesi** — dil sistem ayarından otomatik seçilir (Türkçe dışı her şey İngilizce), tek tıkla değiştirilir
- **"Docker ile kur" düğmesi** — henüz hazır değil, tıklanınca bunu söyler; Docker desteği sonraki bir sürüme bırakıldı

#### Düzeltilen

- **Video kalitesi boyut tahmini bazı formatlarda gerçek boyutun kat kat üzerinde gösteriyordu** (ör. gerçekte ~500 MB olan bir video için "~2.1 GB") — bazı format varyantlarının kendi bildirdiği ortalama bit hızı (`tbr`) güvenilmezdi. Tahmin artık aynı çözünürlükte, gerçek dosya boyutu bilinen bir kardeş formatla sınırlandırılıyor; hangi formatın indirileceğini etkilemiyor, yalnızca gösterilen tahmini düzeltiyor
- **Ana sayfada önizleme paneli aşağı kaydırırken navbar'ın üstüne çıkabiliyordu** — panelin nerede sabitleneceği artık sabit bir piksel değeri yerine üst menünün gerçek, ölçülen yüksekliğinden hesaplanıyor

#### Değiştirilen

- **`maps/` klasörü eklendi** — `project-map.md` (her dosyanın amacı, önemli işlevler, projenin değişmezleri) ve `site-map.md` (her rota, şablon, JS ve `/api/*` uçları). Yapay zeka araçları ve katkıcılar keşfe buradan başlasın diye; `AGENTS.md` yönlendiriyor. `tests/test_maps.py` haritaları koruyor: haritaya eklenmeden yeni bir dosya ya da rota eklenirse test kırmızıya döner, böylece harita bayatlayamaz
- **Ana sayfa yeniden tasarlandı** — çözümlenen video artık 1440px genişliğe kadar genişleyen, sol 1/3 önizleme + sağ 2/3 seçenekler şeklinde iki sütuna bölünmüş bir düzende; önizleme paneli kaydırırken üst menünün hemen altında sabit kalıyor
- **Lisans: v1.9.0'dan itibaren GPL-3.0-or-later.** v1.0.0 – v1.8.0 sürümleri kalıcı olarak **MIT** kalıyor (bkz. [LICENSE-MIT](LICENSE-MIT)) — bu hak geriye dönük değişmiyor, o sürümleri MIT şartlarıyla kullanmaya/fork'lamaya devam edebilirsiniz. v1.9.0 ve sonrası için lisans **GNU GPL-3.0-or-later** (bkz. [LICENSE](LICENSE), resmi metin gnu.org'dan alındı). Sebep: `mutagen` gibi GPL bağımlılıkları MIT kalarak kullanmak, onları hiç doğrudan import etmemeyi gerektiriyordu; GPL-3.0'a geçmek bu kısıtı kaldırıyor, ileride bir özellik GPL lisanslı bir kütüphaneyi doğrudan kullanmak isterse sorun olmaz. AGPL yerine GPL-3.0 seçildi çünkü MediaGrab bir ağ servisi değil, yerel bir araç.
- **README ikiye ayrıldı: kısa bir "beni oku" + ayrıntılı kılavuzlar.** Kök `README.md` artık sadece proje ne yapar, nasıl kurulur (linkli) ve lisans/yasal uyarı özeti içeren kısa bir sayfa. Özellik listesi, adım adım kurulum, sorun giderme ve proje yapısı gibi ayrıntılar `docs/README.tr.md` ve `docs/README.en.md`'ye taşındı — Türkçe/İngilizce artık aynı sayfada çapa (anchor) linkleriyle değil, **ayrı dosyalar** olarak birbirine bağlı; bazı görüntüleyicilerde Türkçe karakterli çapa bağlantıları güvenilir çalışmıyordu, ayrı dosya linki bunu ortadan kaldırıyor.

### [1.8.0] — 2026-09-09

#### Eklenen

- **İndirmede kalan süre (ETA)** — dock'taki ilerleme artık "İndiriliyor · 2.7 MB/s · kalan 0:13" şeklinde tahmini süreyi de gösteriyor. yt-dlp bu bilgiyi zaten hesaplıyordu, sadece arayüze hiç yansıtılmıyordu
- **Ayarlara Geri Bildirim düğmesi** — bir hata bulduğunuzda veya özellik önereceğinizde GitHub'daki hazır şablonlara (hata bildirimi / özellik önerisi) tek tıkla gidiyor
- **Varsayılan ses parçası ayarı** (`/settings`) — birden fazla dilde dublajı olan videolar için tercih ettiğiniz dili bir kere kaydedin, sonraki her indirmede (chip'e tıklamadan) o dil otomatik seçili gelsin. Kanal otomatik indirmesi de bu ayarı kullanıyor — takip ettiğiniz bir kanal kendiliğinden indirirken de tercih ettiğiniz dilde iniyor
- **Video kalitesi boyut tahmini** — YouTube'un pek çok video akışı için gerçek dosya boyutunu hiç vermediği durumlarda (`?` görünürdü), artık ortalama bit hızından tahmini bir boyut (`~1.2 GB` gibi) hesaplanıp gösteriliyor. `~` işareti bunun bir tahmin olduğunu, kesin değer olmadığını belirtiyor

#### Düzeltilen

- **Güncelleme sonrası tarayıcı eski sürümü göstermeye devam edebiliyordu** — `app.js`/`style.css` her zaman aynı adresten (`/static/app.js`) geldiği için, sunucuyu yeniden başlatmak açık bir sekmenin tarayıcı önbelleğini temizlemiyordu; yeni özellikler sert yenileme (Ctrl+Shift+R) yapılana kadar hiç görünmüyordu. Artık bu dosyalar `?v=<değişim-zamanı>` taşıyor — dosya gerçekten değiştiğinde adres de değişiyor, tarayıcı otomatik olarak tazesini çekiyor

### [1.7.0] — 2026-09-09

#### Eklenen

- **Ses parçası (dublaj) seçimi** — bir video birden fazla dilde seslendirilmişse (ör. 18 dile dublajlı bir belgesel), artık hangisini istediğinizi seçebilirsiniz. Video ile birlikte "Ses Parçası" bölümünde diller chip olarak listelenir; hiçbirini seçmezseniz videonun orijinal dili iner — önceki davranış aynen korunuyor. Aynı seçim tek başına ses indirirken (Opus/M4A/MP3) de geçerli. Bölüm yalnızca videoda gerçekten birden fazla dil varsa görünür, çoğu videoda hiç çıkmaz. Seçtiğiniz dil o indirme için mevcut değilse hata vermez, videonun orijinal sesine sessizce döner

### [1.6.1] — 2026-08-25

#### Düzeltilen

- **Kurulum aracı, açıkken kurulan araçları görmüyordu** — Windows'ta bir programın PATH'i açılış anında dondurulur. Kurulum penceresi açıkken Git veya Python kurarsanız yeni PATH kayıt defterine yazılır ama pencereye hiç ulaşmaz; **"Durumu yenile" düğmesi de aynı donmuş listeye tekrar baktığı için hiçbir zaman işe yaramıyordu.** Tek çare uygulamayı kapatıp açmaktı. Artık PATH kayıt defterinden yeniden okunuyor. (Python'un "kurulu" görünüp Git ve ffmpeg'in görünmemesi de bundandı: Python'un başlatıcısı açılıştan beri PATH'te olan bir klasörde durur, diğer ikisi ise PATH'e yeni eklenen klasörlerde.)
- **Birleştirilmemiş akış dosyaları birikiyordu** — yt-dlp videoyu ve sesi ayrı ayrı indirip (`video.f616.mp4`, `video.f251.webm`) ffmpeg ile birleştirdikten sonra siler. Birleştirme çalışmazsa (iptal, hata, süreç öldürülmesi) bu dosyalar kalıyordu; üzerlerinde `.part` veya `.ytdl` işareti olmadığı için mevcut temizlik onları hiç görmüyordu. Tek bir 1080p video akışı yüzlerce MB olabildiğinden sessizce disk doluyordu. Artık hem iptalde hem açılışta temizleniyorlar — yalnızca birleştirilmiş dosya yanlarında duruyorsa, yani artık oldukları kanıtlıysa
- **Çerez ayarı güncellemede siliniyordu** — v1.6.0'da eklenen `settings.json` kurulum aracının koruma listesinde değildi; **Onar** veya **Kaldır** işlemi çerez ayarınızı siliyordu. Listeye eklendi ve bir daha atlanmaması için koruma listesi artık uygulamanın kendi kodundan türetiliyor

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

### [2.4.0] — 2026-10-12

The install & trust release: on Windows, MediaGrab now runs from a single setup file, with nothing else to install.

#### Added

- **A new Windows installer** — `MediaGrabSetup.exe` now brings everything with it: Python, FFmpeg and Deno. No Python, Git or ffmpeg to install and no packages downloaded from the internet; no admin rights needed. It opens in Turkish or English following Windows' language, shows up in "Installed apps", and adds a Start-menu shortcut and, optionally, a desktop one. The program goes to `%LOCALAPPDATA%\Programs\MediaGrab`, settings and channels to `%LOCALAPPDATA%\MediaGrab`, downloads to `Downloads\MediaGrab` by default. To update, just run the new setup file; if MediaGrab is running, setup asks first and closes it
- **A notification-area icon** — in the Windows install MediaGrab runs without a console window; click the **M** icon next to the clock to open the page, right-click → **Quit MediaGrab** to close it. Task Manager shows it as "MediaGrab", with its own icon, instead of "Python"
- **A configurable downloads folder** (Settings → Download Settings → Download Folder) — chosen during setup or later; **Choose Folder…** opens Windows' own folder picker. Folders that can't be written to, folders inside MediaGrab's program folder and relative paths are refused; picking a synced folder such as OneDrive shows a warning. Works for source installs too; it can only be changed from the computer MediaGrab runs on (not from a phone). On Docker, `docker-compose.yml` decides the folder
- **Moving earlier downloads** — when the downloads folder changes, Settings shows a card for the old one: **Move here** or **Leave them there**. Only the files MediaGrab downloaded (and their `.json` info files) move, along with their channel folders; other files in the folder aren't touched and nothing is overwritten. Moving to another drive copies first, checks the size, then deletes the original; new downloads wait while a move runs
- **Install with Docker, in the same installer** — setup starts by asking "Normal install" or "Install with Docker". It checks that Docker Desktop is installed and running; if Docker already has a MediaGrab (including one set up by the old installer), it finds it, shows its version and updates it in place, keeping its password and data. Otherwise it asks for a folder and a first password, pulls the image, starts it and waits until MediaGrab answers. The image is pinned to the installer's version (e.g. `ghcr.io/umitkrkmz/mediagrab:2.4.0`). Uninstalling deletes the container; the data stays in its folder by default
- **Moving over from an earlier install** — if a MediaGrab set up with the pre-2.4.0 installer is found, its settings, channels, cookies and statistics are carried over. The videos stay where they are; a **Move here** card in Settings and a note in History offer to move them into the new folder. The old install isn't deleted
- **What should happen to your data on uninstall?** — the uninstaller asks: remove only MediaGrab (the default; settings and videos stay), also delete the settings, or, with an extra confirmation, also delete the downloaded videos. Deleting videos removes only the files MediaGrab downloaded; other files in the folder stay
- **Third-party notices** — the versions, licenses and source links of the Python, FFmpeg and Python packages in the Windows package are in `THIRD-PARTY-NOTICES.txt` in the install folder and on the About page. Since FFmpeg is GPL, every release attaches the source of that release's FFmpeg and its build scripts
- **README: "Is it safe?" and "Use it from your phone"** — where to get the setup file, the SmartScreen warning, checking it with SHA256 and VirusTotal, why and when MediaGrab talks to the outside world; on iPhone, using MediaGrab from the phone's browser instead of a downloader app

#### Changed

- **The old installer is gone** — the pre-2.4.0 `MediaGrabSetup.exe` (the tool that installed Python, Git and ffmpeg on the computer) has been replaced by the new installer. The download link and file name stay the same
- **Settings' update instructions** know the new install types: installs made by the Windows installer (normal or Docker) are told to run the new setup file, installs made by the old tool to switch to the new installer, which offers to bring their data over
- **The log no longer balloons** — running without a console window (the Windows install, Docker), yt-dlp's download progress lines are no longer written to `mediagrab.log` or `docker logs` (a single download could leave a line hundreds of KB long); error and warning lines still are

#### Fixed

- **Garbled characters on the detail page on Turkish Windows** — ffprobe/ffmpeg output was read with Windows' legacy code page; it's now read as UTF-8
- **The old installer's Docker install broke passwords containing `$`** — Docker Compose reads `$` as the start of a variable, and the password was written into `docker-compose.yml` unescaped, so the first password ended up different from the one typed. The new installer escapes `$` correctly

#### When updating

- **If you installed with the old Windows installer:** download and run the new `MediaGrabSetup.exe`. It finds the earlier install and offers to bring your data over; you can then move your videos to the new folder from Settings. Once you've seen everything arrive, you can delete the old folder by hand
- **If you set up Docker with the old installer:** choose **Install with Docker** in the new installer; it finds the existing install and updates it in place. From then on the image is pinned to the installer's version, so updates come with a new setup file (`docker compose pull` just fetches the same pinned version again)
- **Manual Docker / source:** no new dependencies in the app — `docker compose pull && docker compose up -d` or `git pull`

#### Developer notes

- **The Windows package** — `packaging/build_windows.py` stages the embedded Python, every package and FFmpeg (each download pinned + SHA256-checked), and `packaging/mediagrab.iss` (Inno Setup) turns that into one setup file. PyInstaller and Tkinter are no longer used
- **CI** — `tests.yml` gained a Windows job that runs on every push and PR (the real Win32 notification-area icon, `MediaGrab.exe`, the installer's Pascal code with real ISCC). `release.yml` builds the installer, silently installs and starts it on Windows, checks that it runs on the package's own Python and FFmpeg, uninstalls it, and attaches FFmpeg's source archives and the SHA256 to the release
- **The handoff names between the installer and the app** (`install-download-dir.txt`, `MediaGrabTrayWindow`, `MEDIAGRAB_INSTALLED_BY`, etc.) are spelled out on both sides; tests check that they match (see `AGENTS.md`)

### [2.3.1] — 2026-10-10

#### Fixed

- **The Windows installer's "Install with Docker" could install an old image** — if an older `latest` image from a previous install was still on the computer (even with its container and folder deleted), the installer started that old image instead of downloading the new release; `docker compose up -d` only downloads an image that's missing. The installer now runs `docker compose pull` first. Offline with an image already present, it carries on with that one and says so in the log

#### When updating

- **No change to the app itself** — only `MediaGrabSetup.exe` changed. If you use Docker and Settings shows version 2.3.0, there's nothing to do; if you installed v2.3.0 but it shows 2.2.0, run `docker compose pull && docker compose up -d` in the folder with your `docker-compose.yml`

### [2.3.0] — 2026-10-10

#### Added

- **Statistics** (History → Statistics tab) — a local panel showing how much you download, from which sites and in which formats: Daily / Weekly / Monthly views, period and all-time totals, downloads over time, sites, audio formats (Opus / M4A / MP3) and video resolutions, and how much of the disk MediaGrab and everything else take up, plus free space. Each download is counted the moment it finishes; files removed later (by "Relay To Device" or from History) still count. On first start, the files already in the downloads folder are imported once. Only numbers are kept (site, kind, format, count, size): no titles, links, channels or file names; "Reset Statistics" doesn't touch downloaded files. Day and week boundaries follow your browser's clock (a late-night download lands on the right day even though Docker runs on UTC)
- **MediaGrab's own player** (History → a file → Play) — a clean, YouTube/Drive-style player instead of the browser's built-in controls: a progress bar (shows the time on hover), volume, playback speed (0.5× – 2×), picture in picture and full screen. No "Download" menu and no right-click "Save video as". Keyboard shortcuts match YouTube: Space/K, ←/→ (5 s), J/L (10 s), ↑/↓ volume, M mute, F full screen, 0–9 to jump. Volume and speed are remembered; on phones the first tap only brings the controls back
- **What's actually in the file, on the detail page** — Resolution (e.g. `1920×1080 (1080p) · 30 fps`), the video codec and the audio (e.g. `Opus · 48 kHz · stereo`) are now read from the file itself - what really got downloaded, not which button was pressed. Cover art in music files isn't counted as video
- **"Save to Folder" in Docker** — when you run Docker on your own computer and open it via `localhost` (Chrome/Edge), "Download to Device" becomes a dialog that saves the file to the folder you pick. Cancelling it does nothing

#### Fixed

- **A cancelled save deleted the file in Docker** — with "Relay To Device" selected under Remote Access, the browser of someone running Docker on their own computer counted as "another device" too (in Docker every request comes from the same internal address). Chrome/Edge download the whole file in the background while the Save As dialog is still open, so even a cancelled dialog deleted MediaGrab's only copy. Downloads from your own computer are now never deleted automatically; with "Save to Folder" the copy is only removed after the file has actually been written to the folder you picked. Other devices (like phones) behave as before. The description in Settings was updated to match
- **The Windows installer's Repair/Remove deleted an uploaded `cookies.txt`** (since v2.2.0) — it wasn't on the list of kept files. `cookies.txt` and the new `stats.json` are now kept

#### When updating

- **Docker:** add `- ./data/stats:/data/stats` under `volumes:` in `docker-compose.yml` (so statistics survive the container being recreated; new installs already have it). Then `docker compose pull && docker compose up -d`
- **Windows installer / source:** no new dependencies. "Repair / Update" in the installer, `git pull` for source
- **Statistics** are filled from your existing downloads on first start; files deleted before this release (e.g. by "Relay To Device") can't be counted

#### Developer notes

- **Tests on every push** — the full suite now runs on Linux for every push to `master` and every PR (`.github/workflows/tests.yml`), and still on Windows at release time. Running it on Linux surfaced two test bugs, now fixed: the PATH test used a Windows drive letter, and inside a container the tests mistook themselves for Docker and demanded a first-run password
- **Deeper Docker smoke test** (`.github/scripts/smoke-docker.sh`) — not just "does it answer": logging in with the initial password, ffmpeg/ffprobe/Deno present, History, the detail page's resolution row and statistics. No network needed, runnable by hand
- **Manual check before releasing** — `CONTRIBUTING.md`'s release list gained a real YouTube / other site / phone try; the automated tests stay offline on purpose
- **TR/EN key parity test for app.js** — like the server-side one; it caught two unused strings left only in English

### [2.2.0] — 2026-10-07

#### Added

- **MediaGrab update check** (Settings → Version Checks) — the installed version is compared against the latest GitHub release; if there's a newer one, the release notes are linked and the right steps for your install type are shown (Docker: `docker compose pull`, Windows installer: "Repair / Update", from source: `git pull` + `pip install`). It never updates itself; the check only runs when Settings is opened and is cached for an hour. The installed version is also shown on the About page
- **cookies.txt upload** (Settings → Cookies) — for age-restricted, members-only or sign-in-only videos, you now upload a `cookies.txt` with your account's cookies straight from the interface; no file path to type. Works on every install, Docker and Raspberry Pi included (there was previously no way to use cookies on Docker). The file is validated with yt-dlp's own reader and the sites in it are listed: YouTube and Google come pre-ticked, only the sites you pick are saved, and the rest are never written to disk. After saving you see the site/cookie counts, upload and last-updated times, and whether the file holds a YouTube session; "Delete cookies" removes it
- **"How do I get a cookies.txt?" guide** — step by step in Settings and in the guide: the Get cookies.txt LOCALLY extension, a private window, `youtube.com/robots.txt`, "Export" (not Export All), and yt-dlp's account-safety warning. The guide gained its own "Cookies" section
- **JavaScript runtime for YouTube (Deno)** — yt-dlp now needs an external JS runtime to solve YouTube's protections; without one some formats can go missing and age-restricted videos may fail even with cookies. Deno and the solver scripts (`yt-dlp-ejs`) are now installed with the dependencies (Windows, Linux x86_64/arm64, macOS, Docker). Settings → Version Checks shows its status; "Update Now" installs it if missing
- **"Copy diagnostic info"** (Settings → Feedback) — gathers MediaGrab/yt-dlp/ffmpeg versions, the JS runtime, OS, install type and cookie mode into one text to paste into a bug report. It contains no file paths, IP addresses, computer name or cookie contents; if the clipboard isn't available, the text is shown selected instead
- **Pointers on cookie-related errors** — age-restricted, bot-check, members-only and private-video errors now link straight to Settings → Cookies, and say "upload a fresh one" when cookies are already set. Two cases yt-dlp only reports as side messages are now explained on their own: the cookies having gone stale, and YouTube requiring the account to be age-verified (done in the YouTube account; a new cookies.txt won't fix it)

#### Changed

- **The repo's `docker-compose.yml` now uses the published image** (`image: ghcr.io/umitkrkmz/mediagrab:latest` instead of `build: .`) — updating is `docker compose pull && docker compose up -d`, no local build. `build: .` still works for building your own changes
- **"From browser" lists only Firefox on Windows** — cookies of Chromium-based browsers like Chrome, Edge and Brave can't be read on Windows (App-Bound Encryption), and with one of them selected **every** video failed with "Could not copy Chrome cookie database". A Chrome choice saved earlier on Windows is now ignored (downloads keep working) and Settings shows a warning about it. No change on macOS and Linux
- **Simpler version checks on Docker** — ffmpeg ships with the image, so the per-OS install commands (including "your system: Linux") are no longer shown; yt-dlp's "Update Now" stays, and the manual venv steps that don't apply in a container are hidden. The "From browser" cookie option is hidden on Docker too (there's no browser in the container)
- **Updating yt-dlp updates Deno too** — "Update Now" and the command in the guide now install `yt-dlp[default,deno]`; a plain `pip install -U yt-dlp` could leave the solver scripts behind and quietly break YouTube extraction

#### Fixed

- **Cookies uploaded during a download getting overwritten** — yt-dlp writes cookies back to the file whenever a download finishes; uploading a new cookies.txt while one was running let the finishing download write its old cookies over the new upload. Now the write-back is skipped if the file changed in the meantime (a new upload, a delete, another download), and deleted cookies never come back. Verified with a live control experiment
- **Silent quality loss with an account that needs age verification** — when YouTube wanted the account age-verified, only a 360p muxed format came back: Opus/M4A failed with a raw "Requested format is not available", and MP3 was quietly re-encoded from the 360p video's audio. The probe now reports this: a yellow notice explains why, Opus/M4A are greyed out when there's no separate audio stream, and "Best Audio" picks MP3. The format-not-available error now has a plain-language message too
- **An expired session showed "YouTube session found"** — YouTube leaves one cookie behind when it clears a dead session; MediaGrab now uses yt-dlp's own rule (`LOGIN_INFO` + SAPISID)

#### When updating

- **Docker:** add `- ./data/cookies:/data/cookies` to the `volumes:` section of your `docker-compose.yml` (so uploaded cookies survive the container being recreated; new installs already have it). If you installed from the repo by hand, replace `build: .` with `image: ghcr.io/umitkrkmz/mediagrab:latest`. Then `docker compose pull && docker compose up -d`
- **Windows installer / from source:** reinstall the dependencies so Deno comes in — "Repair / Update" in the installer, `pip install -r requirements.txt` from source. If skipped, Settings → Version Checks shows "JavaScript runtime: Missing", and its "Update Now" installs it too

#### Developer note

- **CI:** GitHub Actions runners are pinned (`ubuntu-24.04`, `windows-2025`; `ubuntu-latest` moves to Ubuntu 26 on 2026-10-19) and every action moved to its Node 24 major (Node 20 is being retired)
- **PyInstaller pinned** (`6.22.3` + `pyinstaller-hooks-contrib 2026.7`, the versions that built v2.1.0) — so the exe doesn't change needlessly between releases and restart its Windows Defender/SmartScreen reputation from zero
- **Release checklist** — `CONTRIBUTING.md` gained a "Cutting a release" section: version and CHANGELOG, a manual dry run of the workflows before tagging, reading the Actions warnings, and re-publishing the Docker image from a tag by hand when needed
- **Tests no longer touch the developer's real data** — tests that sent requests to the app started the startup channel check, which read the project's own `channels.json`, made real requests to YouTube and wrote results back; the half-finished-download sweep ran on the downloads folder too. `tests/conftest.py` now redirects every user-data path to a temp folder for every test

### [2.1.0] — 2026-09-18

#### Added

- **A mobile-friendly interface** — on narrow screens the top menu and the Settings page's category list are now vertical lists that open and close with a ☰ icon; picking a category in Settings closes the menu by itself. The desktop layout is unchanged
- **Reworked guides and screenshots** — `docs/README.tr.md` / `README.en.md` were reorganized: a "Quick start" table, five step-by-step example scenarios, the features split into five groups, a new "Using It On Mobile" section; real screenshots (`docs/images/`) and a hero image in the main README

#### Fixed

- **The top menu was clipped on phones** — on a narrow screen the overflowing nav row spilled evenly off both edges because of `justify-content: center`, so the first tab ("Home") was cut off on the left and the last on the right. Replaced by the collapsible menu
- **The "Paste from clipboard" button did nothing on a phone** — browsers only expose the clipboard-reading API on HTTPS/`localhost`, and Remote Access is plain HTTP, so the button could never work on any device on the LAN. It's now hidden in that situation (long-pressing the field and choosing "Paste" still works, and still resolves the link automatically); behaviour on `localhost` is unchanged
- **On the Channels page the badge overlapped the text** — on a narrow screen the "Last checked" line wrapped over several lines, making the row tall, and the vertically-centered "NOTIFY/AUTO" badge floated in the middle of that block. The text is now truncated to one line and the buttons move to their own row
- **The History list view was cramped on phones** — thumbnail, name, date and two buttons couldn't fit on one row and the date was clipped; it now wraps onto two lines
- **Dead space in the Settings category menu** — the gap meant for desktop also applied on mobile, leaving ~64px of blank space even when the menu was closed
- **Tapping some fields zoomed the page on iPhone** — the History search/filters, the channel link box, the cookie settings and the playlist range box used a font size under 16px (iOS Safari auto-zooms in that case); raised to 16px on mobile
- **Small icon buttons were hard to tap on a phone** — the menu, theme and language buttons were 24-37px; enlarged to 32-40px on mobile
- **The "Video" tab's label was unreadable on hover** — the generic `button:hover` rule overrode the tab's transparent background, stacking the accent colour on the accent colour for the active tab

### [2.0.1] — 2026-09-18

#### Fixed

- **In Docker (Windows/Mac), the connection address and QR codes in Settings → Remote Access showed the wrong IP** — `lan_ip()`, called from inside a bridge-networked container, resolved to the container's own internal Docker bridge IP (e.g. `172.19.0.2`) instead of the Windows/Mac host's real LAN IP - unreachable from any other device, or even from the host itself. The Windows installer's "Install with Docker" flow now detects the real LAN IP on the host and bakes it into `docker-compose.yml` automatically (`MEDIAGRAB_HOST_LAN_IP`); a manual Docker install got the same variable added to `docker-compose.yml`, with instructions. Verified from a real Android phone

### [2.0.0] — 2026-09-15

#### Added

- **Home Server Mode** (Settings → Remote Access) — for anyone running MediaGrab on a machine that's on 24/7, like a Raspberry Pi: your followed list is checked automatically every 3 hours even if you never open the app, and other devices on the network can reach you at an easy-to-remember mDNS address, `http://mediagrab.local:8420`, alongside your LAN IP. Independent of Remote Access
- **Two separate, labeled QR codes** — the Settings page now shows a QR code for the LAN IP and another for the mDNS address, each labeled underneath
- **Disk-space shield** — a download whose estimated size would exceed the free disk space left is refused up front, checked both when the download is requested and again right before the real download starts
- **Download speed limiting** (Settings) — set an optional overall speed cap (preset options or a custom Mbps value)
- **Backup / restore settings** (Settings) — export all your settings and followed channels (minus your password) into one file and import them into another install
- **A reserved slot for manual downloads in the auto-download queue** — channel auto-downloads no longer indefinitely block a manual download; the shared download pool always keeps at least one slot free for a manual one
- **Docker support** — MediaGrab can now run straight from a Docker image (`ghcr.io/umitkrkmz/mediagrab`) with no Python or Git install needed. A container always binds to `0.0.0.0`; the first run requires a `MEDIAGRAB_INITIAL_PASSWORD` environment variable and refuses to start without one, so a container is never left open with no login. Updating yt-dlp installs into a folder that persists across image rebuilds; every other dependency only updates by pulling a new image
- **"Install with Docker" in the Windows installer** — a separate wizard flow that checks Docker/Compose/daemon readiness, asks for a folder and an initial admin password, and writes and starts the required `docker-compose.yml` itself

#### Docker packaging (developer note)

- `Dockerfile`, `docker-compose.yml`, `.dockerignore` — see [docs/README.en.md](docs/README.en.md#method-c-docker-any-platform)
- `.github/workflows/docker.yml` — always builds for amd64 with QEMU + Buildx and runs a real container smoke test; on a `v*` tag push, also builds a multi-arch (amd64+arm64) image and pushes it to `ghcr.io/umitkrkmz/mediagrab`

### [1.10.0] — 2026-09-13

#### Added

- **Remote access (from your local network)** — Settings → Remote Access: set a password and turn it on, and another device on the same network (phone, laptop) can connect to MediaGrab from its own browser. The connection address appears in the same panel once it's active. Runs over plain HTTP (not HTTPS) — only use this on a home/office network you trust, never expose it directly to the internet
- **A connected-devices list with per-device sign-out** — Settings shows every currently logged-in device (browser + OS guess, e.g. "Chrome · Windows") and when it connected; you can sign any one of them out individually without affecting your own
- **A real download from a remote device** — a phone/laptop now gets the actual file sent to it instead of "show in folder" (which only makes sense on the host itself); the host's own browser behaves exactly as before (still reveals the file in its folder)
- **Storage mode: Keep Here / Relay To Device** — if you're running this on a storage-constrained device (e.g. a Raspberry Pi), "Relay To Device" deletes the host's own copy right after a file has been fully sent to a device; downloads you make from the host itself are never affected by this setting either way. The default, "Keep Here", is identical to the previous (permanent) behaviour
- **Download progress is now pushed live** — the download dock updates over one shared live connection instead of polling every job separately, making progress feel smoother

#### Fixed

- **A downloaded mp4 could very rarely end up with no audio** — the very last fallback in the format-selector chain would settle for a format with no audio track at all if nothing else matched; the chain's last resort now never settles for a silent video
- **A server launched via `python -m uvicorn ...` could crash while restarting itself after an update** (yt-dlp, a dependency, or a remote-access setting change) — the restart now preserves the exact original command line (including the `-m` flag)

### [1.9.0] — 2026-09-11

#### Added

- **Multiple audio tracks in one file** — when a video is dubbed into more than one language, you can now pick more than one (e.g. original + Turkish) and get them embedded as separate, player-selectable audio tracks in a single `.mkv`, instead of only ever picking one. Manual downloads only — channel auto-download still picks a single language. Picking just one language behaves exactly as before (mp4, one audio track)
- **Video description on the home page** — so the preview column isn't left empty, the description yt-dlp fetches is now shown below the "Best Audio/Video" buttons, with a "Show more" toggle for long ones
- **Audio/Video tabs on the home page** — since you can't download both at once anyway, the format lists are now split into two tabs with a transition animation; the Audio Track picker (it applies to both) sits above the tabs, Subtitles and Transcript stay always visible
- **Hover tooltips on audio-track and subtitle chips** — hovering "DE", "JA", "ES-419" and similar codes now shows the full language name ("German", "Japanese", "Spanish")
- **A new "About" page** (`/about`) — what the project is, its GPL-3.0 license, and links to the source code and to filing feedback, all in one place
- **Settings page redesigned** — instead of one long page, a category list on the left (Appearance, Default Audio Track, Cookies, Version Checks, Feedback) with the selected section's detail panel on the right
- **A type filter and list view on the History page** — a compact list view alongside the existing large cover-card grid; the file-type filter is now built dynamically from what's actually on disk instead of a hardcoded list
- **Supported Sites chips are now clickable** — each one carries its site's brand color/logo and links to that site's homepage
- **A language code reference** (`docs/language-codes.tr.md`, `docs/language-codes.en.md`) — every ISO 639-1 language's name and code, linked from next to Settings → Default Audio Track

#### Installer (`MediaGrabSetup.exe`)

- **A wizard flow** — instead of the old everything-in-one-window screen, step-by-step pages: the welcome page offers **Install / Repair-Update / Remove**; Install and Repair go Requirements (Git, Python, ffmpeg) → Folder and shortcuts → Summary → live log, Remove goes straight to folder → summary. The summary page shows what's about to happen before you click (folder, tools found, shortcuts, an existing launcher/shortcut that will be overwritten, a warning if ffmpeg is missing)
- **The last install folder is remembered** — a successful install/repair writes its folder to `%LOCALAPPDATA%\MediaGrab\installer.json`, and **Repair** and **Remove** pre-fill it (still changeable). It's stored in the user profile rather than next to the exe, since the installer is usually run from Downloads and deleted afterwards. A folder that was deleted by hand is not trusted and not pre-filled; Remove only clears the record when it's the remembered folder that was emptied
- **A TR/EN toggle on the welcome page** — the language is picked from the system locale automatically (anything non-Turkish gets English) and switched with one click
- **An "Install with Docker" button** — not ready yet and says so when clicked; Docker support is left for a later version

#### Fixed

- **The estimated file size for some video qualities was several times the real size** (e.g. "~2.1 GB" for a video that was actually ~500 MB) — a handful of format variants reported an unreliable average bitrate (`tbr`) of their own. The estimate is now capped by a sibling format at the same resolution with a confirmed real file size; this only fixes the displayed number, not which format actually gets downloaded
- **The home page's preview panel could scroll above the navbar** — where the panel stops pinning is now computed from the header's real, measured height instead of a guessed fixed pixel value

#### Changed

- **A `maps/` folder** — `project-map.md` (what every file is for, key functions, the project's invariants) and `site-map.md` (every route, its template/JS, all `/api/*` endpoints), so AI tools and contributors start exploring there; `AGENTS.md` points to them. `tests/test_maps.py` guards them: a file or route added without a map entry turns the test red, so the maps can't go stale
- **Home page redesigned** — a resolved video now renders in a two-column layout (1440px max width) with a 1/3 preview column on the left and a 2/3 options column on the right; the preview stays pinned just below the header while scrolling
- **License: GPL-3.0-or-later starting with v1.9.0.** Versions v1.0.0 – v1.8.0 remain permanently **MIT** (see [LICENSE-MIT](LICENSE-MIT)) — that grant doesn't change retroactively, you can keep using or forking those releases under MIT terms. v1.9.0 and later are licensed under the **GNU GPL-3.0-or-later** (see [LICENSE](LICENSE), official text pulled from gnu.org). Reason: staying MIT while depending on a GPL package like `mutagen` meant never importing it directly; moving to GPL-3.0 removes that constraint, so a future feature can import a GPL-licensed library directly without issue. GPL-3.0 was chosen over AGPL because MediaGrab isn't a network service, only a local tool.
- **The README was split into a short "read me" plus detailed guides.** The root `README.md` is now a short page: what the project does, how to install (linked), and a license/legal summary. The feature list, step-by-step installation, troubleshooting, and project structure moved to `docs/README.tr.md` and `docs/README.en.md` — Turkish and English are now linked as **separate files** instead of same-page anchors, since anchor links with Turkish characters didn't reliably work in every viewer; separate files sidestep that entirely.

### [1.8.0] — 2026-09-09

#### Added

- **Download ETA** — the dock's progress now shows an estimated time remaining too, e.g. "Downloading · 2.7 MB/s · ETA 0:13". yt-dlp already computed this; it just never reached the UI
- **A Feedback button in Settings** — found a bug or have a feature idea? One click takes you to GitHub's ready-made templates (bug report / feature request)
- **A default audio track setting** (`/settings`) — save your preferred language once for videos with more than one dub, and it's preselected on every future download without clicking a chip. Channel auto-download uses this setting too - a channel you follow downloads in your preferred language on its own
- **Estimated file size for video qualities** — YouTube often reports no real filesize at all for a video stream (it showed `?`), so now an estimate (`~1.2 GB`) is computed from the average bitrate instead. The `~` makes clear it's an estimate, not a reported fact

#### Fixed

- **The browser could keep showing an old version after an update** — `app.js`/`style.css` always loaded from the same URL (`/static/app.js`), so restarting the server never cleared an already-open tab's cache; a shipped feature could stay invisible until a hard refresh (Ctrl+Shift+R). These files now carry `?v=<mtime>` - the URL changes exactly when the file actually does, so the browser fetches a fresh copy automatically

### [1.7.0] — 2026-09-09

#### Added

- **Audio track (dub) selection** — when a video carries more than one language track (e.g. a documentary dubbed into 18 languages), you can now pick which one you want. A new "Audio Track" section lists the available languages as chips alongside the video; pick nothing and you get the video's original language, exactly as before. The same choice applies to a standalone audio download (Opus/M4A/MP3) too. The section only appears when a video actually has more than one language — most videos won't show it at all. If your chosen language isn't available for a given download, it quietly falls back to the video's original audio instead of failing

### [1.6.1] — 2026-08-25

#### Fixed

- **The installer could not see tools installed while it was open** — on Windows a process's PATH is frozen at startup. Install Git or Python with the setup window open and the new PATH goes to the registry but never reaches the window; **the "Refresh" button re-checked that same frozen list, so it could never help.** Closing and reopening was the only cure. PATH is now re-read from the registry. (It also explains why Python looked "installed" while Git and ffmpeg did not: Python's launcher sits in a directory that has been on PATH since boot, the other two land in directories newly added to it.)
- **Unmerged stream files piled up** — yt-dlp downloads video and audio separately (`video.f616.mp4`, `video.f251.webm`) and deletes them once ffmpeg has merged the two. When the merge never runs — cancelled, failed, process killed — they survived, and since they carry neither `.part` nor `.ytdl` the existing cleanup never saw them. A single 1080p video stream runs to hundreds of MB, so disks filled up quietly. They are now cleared on cancel and at startup — but only when the merged file is sitting beside them, which is what proves them redundant
- **The cookie setting was wiped by an update** — `settings.json`, added in v1.6.0, was missing from the installer's keep list, so **Repair** or **Remove** deleted your cookie configuration. It is on the list now, and the list is derived from the app's own code so the next such file cannot be forgotten

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
