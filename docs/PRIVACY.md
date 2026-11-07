# MediaGrab — Gizlilik Politikası / Privacy Policy

**[🇹🇷 Türkçe](#türkçe) · [🇬🇧 English](#english)**

Son güncelleme / Last updated: 2026-11-07

---

## Türkçe

MediaGrab, kendi bilgisayarınızda çalışan bir medya indirme ve arşivleme uygulamasıdır. Bu politika Microsoft Store sürümü, GitHub sürümü ve Docker sürümü için geçerlidir.

### Kısaca

- **Hesap yok, telemetri yok, reklam yok, analiz yok.** MediaGrab'ın, geliştiricinin işlettiği bir sunucusu yoktur; uygulama size ait hiçbir veriyi geliştiriciye göndermez.
- Tüm veriler **sizin cihazınızda** kalır.

### Cihazınızda tutulan veriler

Uygulama yalnızca çalışması için gereken şeyleri, kendi veri klasöründe saklar:

- **Ayarlar** (`settings.json`): dil, indirme klasörü, kalite tercihleri vb.
- **Takip ettiğiniz kanallar** (`channels.json`).
- **İndirme istatistikleri** (`stats.json`): sayılar ve boyutlar.
- **İndirdiğiniz dosyalar** ve yanlarındaki bilgi dosyaları (`.json`: başlık, kaynak bağlantısı, süre gibi) — seçtiğiniz indirme klasöründe.
- **Uzaktan erişim şifresi** (açarsanız): şifrenin kendisi değil, yalnızca geri çevrilemez bir özeti (PBKDF2) saklanır. Oturumlar yalnızca bellekte tutulur.
- **Çerezler** (açarsanız): yalnızca çerez *kaynağı* saklanır (tarayıcı adı ya da bir `cookies.txt` yolu). Bir `cookies.txt` yüklerseniz kopyası uygulamanın veri klasöründe durur. Çerezler yalnızca ilgili siteye istek yapılırken kullanılır; başka hiçbir yere gönderilmez.

Microsoft Store sürümünde bu veriler Windows'un uygulamaya ayırdığı klasördedir ve **uygulamayı kaldırdığınızda silinir**. İndirdiğiniz dosyalar seçtiğiniz klasörde kalır. Ayarlarınızı Ayarlar sayfasından dışa aktarıp yedekleyebilirsiniz.

### Uygulamanın kurduğu ağ bağlantıları

- **İndirmek istediğiniz siteler:** bir bağlantı yapıştırdığınızda veya kanal kontrol edildiğinde uygulama o siteye bağlanır (yt-dlp aracılığıyla). Önizleme küçük resimleri tarayıcınıza doğrudan o sitenin sunucularından yüklenir. Bu sitelerin kendi gizlilik politikaları geçerlidir.
- **Sürüm kontrolü:** yeni sürüm olup olmadığını öğrenmek için GitHub'a (`api.github.com`) ve Python paket dizinine (`pypi.org`) istek gönderilir. Bu isteklerde kişisel bilgi yoktur; her internet isteğinde olduğu gibi IP adresiniz bu hizmetler tarafından görülebilir.
- **Yerel ağ (yalnızca Uzaktan Erişim'i açarsanız):** uygulama, telefonunuz gibi aynı ağdaki cihazların bağlanabilmesi için yerel ağda dinler ve kendini yerel ağda (mDNS) duyurur. Bu, internete açılmak anlamına gelmez.

### Paylaşım

Geliştirici hiçbir veriyi toplamaz; dolayısıyla satmaz, kiralamaz veya üçüncü taraflarla paylaşmaz. Microsoft Store sürümünü satın aldığınızda ödeme ve lisans işlemlerini Microsoft yürütür; bu bilgiler Microsoft'un gizlilik bildirimine tabidir ve geliştiriciyle kişisel olarak paylaşılmaz.

### Çocuklar

MediaGrab çocuklara yönelik değildir ve kimseden bilerek kişisel veri toplamaz.

### Değişiklikler ve iletişim

Bu politika değişirse yeni hâli bu sayfada, tarihiyle yayımlanır. Sorularınız için: [GitHub üzerinden iletişim](https://github.com/umitkrkmz/mediagrab/issues/new/choose). Kaynak kodu açıktır; yukarıdakilerin hepsini [depoda](https://github.com/umitkrkmz/mediagrab) doğrulayabilirsiniz.

---

## English

MediaGrab is a media download and archiving app that runs on your own computer. This policy covers the Microsoft Store version, the GitHub version and the Docker version.

### In short

- **No account, no telemetry, no ads, no analytics.** MediaGrab has no server run by the developer; the app sends none of your data to the developer.
- All data stays **on your device**.

### Data kept on your device

The app stores only what it needs to work, in its own data folder:

- **Settings** (`settings.json`): language, download folder, quality preferences, etc.
- **Channels you follow** (`channels.json`).
- **Download statistics** (`stats.json`): counts and sizes.
- **The files you download** and the info files next to them (`.json`: title, source link, duration and the like) — in the download folder you choose.
- **Remote access password** (if you turn it on): never the password itself, only a one-way hash (PBKDF2). Sessions are kept in memory only.
- **Cookies** (if you turn them on): only the cookie *source* is stored (a browser name or a path to a `cookies.txt`). If you upload a `cookies.txt`, a copy is kept in the app's data folder. Cookies are used only for requests to the matching site and are sent nowhere else.

In the Microsoft Store version this data lives in the folder Windows sets aside for the app and **is deleted when you uninstall it**. Your downloaded files stay in the folder you chose. You can export your settings from the Settings page as a backup.

### Network connections the app makes

- **The sites you download from:** when you paste a link or a channel is checked, the app connects to that site (through yt-dlp). Preview thumbnails are loaded by your browser directly from that site's servers. Those sites' own privacy policies apply.
- **Version checks:** to find out whether a newer version exists, the app sends requests to GitHub (`api.github.com`) and the Python Package Index (`pypi.org`). These requests carry no personal information; as with any internet request, those services can see your IP address.
- **Local network (only if you turn on Remote Access):** the app listens on your local network so devices on the same network, such as your phone, can connect, and announces itself there (mDNS). This does not expose it to the internet.

### Sharing

The developer collects no data, so it is not sold, rented or shared with third parties. When you buy the Microsoft Store version, Microsoft handles payment and licensing; that information is covered by Microsoft's privacy statement and is not shared with the developer personally.

### Children

MediaGrab is not directed at children and does not knowingly collect personal data from anyone.

### Changes and contact

If this policy changes, the new version is published on this page with its date. Questions: [contact via GitHub](https://github.com/umitkrkmz/mediagrab/issues/new/choose). The source code is open; you can verify all of the above in the [repository](https://github.com/umitkrkmz/mediagrab).
