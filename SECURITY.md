# Security Policy

**[🇹🇷 Türkçe](#türkçe) · [🇬🇧 English](#english)**

---

## Türkçe

### Kapsam

MediaGrab, kendi bilgisayarınızda çalışan yerel bir araçtır (varsayılan olarak `127.0.0.1`'e bağlanır, dışarıya açılmaz). Yine de dikkat edilmesi gereken yerler var:

- **Çerezler** (`/settings` → Çerezler) — yüklenen `cookies.txt`'den yalnızca kullanıcının seçtiği sitelerin çerezleri, yalnızca bu cihazdaki MediaGrab veri klasörüne yazılır; arayüz ve API çerez adlarını ya da değerlerini hiçbir zaman göstermez, Ayarlar yedeğine girmez, yt-dlp'nin ilgili siteye gönderdiği istekler dışında hiçbir yere gitmez. Tarayıcıdan okuma modunda yalnızca tarayıcının adı `settings.json`'da tutulur. Bu varsayımları bozan herhangi bir şey güvenlik açığıdır.
- **Yerel HTTP sunucusu** (FastAPI) — dosya yolları, indirme adları veya harici sitelerden gelen video/kanal başlıkları gibi güvenilmeyen veriyi işliyor. XSS, path traversal veya benzeri bir açık burada önemlidir (bkz. v1.4.0'da düzeltilen başlık kaçış açığı — [CHANGELOG.md](CHANGELOG.md)).
- **Uzaktan Erişim** — açıldığında sunucu yerel ağa açılır (`0.0.0.0`) ve parolayla korunur; Docker'da her zaman böyledir. Parolasız erişim, oturumun başka bir cihaza taşınabilmesi ya da yalnızca aynı bilgisayara ayrılmış işlemlerin (indirme klasörünü değiştirme, klasör seçme penceresi vb.) uzaktan yapılabilmesi güvenlik açığıdır.
- **Windows kurulum programı** (`packaging/`) — derlenirken indirilen her şey (Python, FFmpeg, Inno Setup) sabit sürüm ve SHA256 ile doğrulanır; kaldırıcı yalnızca MediaGrab'ın kendi dosyalarını siler. Kurulumun ya da kaldırıcının başka dosyalara dokunması veya beklenmedik bir yere yazması bildirilmeye değer.

### Bir açık bulursanız

**Lütfen herkese açık bir issue açmayın.** Bunun yerine [GitHub Security Advisories](https://github.com/umitkrkmz/mediagrab/security/advisories/new) üzerinden özel olarak bildirin (repo → Security sekmesi → "Report a vulnerability").

Mümkünse şunları ekleyin: etkilenen dosya/uç nokta, yeniden üretme adımları, potansiyel etki. Bu tek kişilik, gönüllü bir bakım altındaki bir proje — kesin bir yanıt süresi taahhüt edemem, ama bildirilen her açığı ciddiye alıyorum ve mümkün olan en kısa sürede bir düzeltme yayınlamayı hedefliyorum.

### Kapsam dışı

- yt-dlp'nin kendisindeki açıklar → [yt-dlp/yt-dlp](https://github.com/yt-dlp/yt-dlp/security)
- ffmpeg'deki açıklar → [FFmpeg güvenlik sayfası](https://ffmpeg.org/security.html)
- İndirdiğiniz içeriğin telif durumu (bkz. README'deki Yasal Uyarı)

---

## English

### Scope

MediaGrab is a local tool that runs on your own machine (binds to `127.0.0.1` by default, not exposed externally). Some areas still matter:

- **Cookies** (`/settings` → Cookies) — from an uploaded `cookies.txt`, only the cookies of the sites the user picks are written, and only to MediaGrab's data folder on that device; the UI and API never show cookie names or values, they're left out of the Settings backup, and they go nowhere except in yt-dlp's requests to the site concerned. In browser mode only the browser's name is kept in `settings.json`. Anything that breaks these assumptions is a vulnerability.
- **The local HTTP server** (FastAPI) — it handles untrusted data such as file paths, download names, or video/channel titles pulled from external sites. XSS, path traversal, or similar issues matter here (see the title-escaping fix in v1.4.0 — [CHANGELOG.md](CHANGELOG.md)).
- **Remote Access** — when it's on, the server listens on the local network (`0.0.0.0`) behind a password; on Docker it always does. Access without the password, a session that can be carried to another device, or same-computer-only actions (changing the downloads folder, the folder picker, etc.) working remotely are vulnerabilities.
- **The Windows installer** (`packaging/`) — everything downloaded to build it (Python, FFmpeg, Inno Setup) is checked against a pinned version and SHA256; the uninstaller deletes only MediaGrab's own files. The installer or uninstaller touching other files, or writing somewhere unexpected, is worth reporting.

### Reporting a vulnerability

**Please don't open a public issue.** Instead, report privately via [GitHub Security Advisories](https://github.com/umitkrkmz/mediagrab/security/advisories/new) (repo → Security tab → "Report a vulnerability").

Include, if possible: the affected file/endpoint, reproduction steps, and potential impact. This is a one-person, volunteer-maintained project, so I can't commit to a fixed response time — but every report is taken seriously and I aim to ship a fix as soon as I reasonably can.

### Out of scope

- Vulnerabilities in yt-dlp itself → [yt-dlp/yt-dlp](https://github.com/yt-dlp/yt-dlp/security)
- Vulnerabilities in ffmpeg → [FFmpeg security page](https://ffmpeg.org/security.html)
- The copyright status of content you download (see the Legal Notice in the README)
