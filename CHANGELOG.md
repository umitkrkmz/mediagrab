# Changelog

Bu dosya MediaGrab'daki önemli değişiklikleri sürüm bazında listeler.
This file lists notable changes to MediaGrab, by release.

---

## [Türkçe](#türkçe-1) · [English](#english-1)

---

## Türkçe

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
