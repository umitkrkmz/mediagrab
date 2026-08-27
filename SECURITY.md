# Security Policy

**[🇹🇷 Türkçe](#türkçe) · [🇬🇧 English](#english)**

---

## Türkçe

### Kapsam

MediaGrab, kendi bilgisayarınızda çalışan yerel bir araçtır (varsayılan olarak `127.0.0.1`'e bağlanır, dışarıya açılmaz). Yine de dikkat edilmesi gereken iki yer var:

- **Çerezler** (`/settings` → Çerezler) — yalnızca kaynağın (tarayıcı adı veya dosya yolu) `settings.json`'da tutulduğunu, çerez *içeriğinin* hiçbir zaman diske yazılmadığını veya ağa gönderilmediğini varsayan bir tasarım. Bu varsayımı bozan herhangi bir şey güvenlik açığıdır.
- **Yerel HTTP sunucusu** (FastAPI) — dosya yolları, indirme adları veya harici sitelerden gelen video/kanal başlıkları gibi güvenilmeyen veriyi işliyor. XSS, path traversal veya benzeri bir açık burada önemlidir (bkz. v1.4.0'da düzeltilen başlık kaçış açığı — [CHANGELOG.md](CHANGELOG.md)).

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

MediaGrab is a local tool that runs on your own machine (binds to `127.0.0.1` by default, not exposed externally). Two areas still matter:

- **Cookies** (`/settings` → Cookies) — the design assumes only the *source* (a browser name or file path) is ever stored in `settings.json`, and cookie *content* is never written to disk or sent over the network. Anything that breaks that assumption is a vulnerability.
- **The local HTTP server** (FastAPI) — it handles untrusted data such as file paths, download names, or video/channel titles pulled from external sites. XSS, path traversal, or similar issues matter here (see the title-escaping fix in v1.4.0 — [CHANGELOG.md](CHANGELOG.md)).

### Reporting a vulnerability

**Please don't open a public issue.** Instead, report privately via [GitHub Security Advisories](https://github.com/umitkrkmz/mediagrab/security/advisories/new) (repo → Security tab → "Report a vulnerability").

Include, if possible: the affected file/endpoint, reproduction steps, and potential impact. This is a one-person, volunteer-maintained project, so I can't commit to a fixed response time — but every report is taken seriously and I aim to ship a fix as soon as I reasonably can.

### Out of scope

- Vulnerabilities in yt-dlp itself → [yt-dlp/yt-dlp](https://github.com/yt-dlp/yt-dlp/security)
- Vulnerabilities in ffmpeg → [FFmpeg security page](https://ffmpeg.org/security.html)
- The copyright status of content you download (see the Legal Notice in the README)
