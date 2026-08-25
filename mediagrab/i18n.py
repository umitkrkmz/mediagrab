"""Server-rendered UI strings.

NOTE: these are the strings that appear directly in Jinja templates, so the
very first paint is already in the right language. They are deliberately NOT
duplicated in static/app.js - switching language reloads the page (see
setLang() there), which makes the server the single source of truth for this
text. app.js's own I18N dictionary only covers strings it builds dynamically
at runtime (download states, error messages, format labels...).
"""

UI = {
    "tr": {
        "title_index": "MediaGrab — Video ve Ses İndirici",
        "title_history": "İndirme Geçmişi — MediaGrab",
        "title_settings": "Ayarlar — MediaGrab",
        "title_channels": "Kanallar — MediaGrab",
        "nav_home": "Ana Sayfa",
        "nav_history": "Geçmiş",
        "nav_channels": "Kanallar",
        "nav_sites": "Desteklenen Siteler",
        "nav_settings": "Ayarlar",
        "channels_page_title": "Kanal Takibi",
        "channels_page_intro": (
            "Kanal takibi şimdilik yalnızca YouTube kanallarını destekler."
        ),
        "settings_ffmpeg_title": "ffmpeg / ffprobe",
        "settings_ffmpeg_hint": (
            "Birleştirme, dönüştürme ve kapak/süre okuma için gereklidir. "
            "MediaGrab ile birlikte gelmez, sisteminize ayrıca kurulur."
        ),
        "settings_cookies_title": "Çerezler",
        "settings_cookies_hint": (
            "Yaş sınırlı, üyelere özel veya giriş gerektiren içerikler için tarayıcı "
            "oturumunuzun çerezleri kullanılabilir. Yalnızca kendi erişim hakkınız olan "
            "içerik için kullanın."
        ),
        "cookie_off": "Kapalı",
        "cookie_file": "cookies.txt dosyası",
        "cookie_browser": "Tarayıcıdan",
        "cookie_file_label": "Dosya yolu",
        "cookie_file_help": (
            "Tarayıcınıza bir \"cookies.txt export\" eklentisi kurup çerezleri Netscape "
            "biçiminde dışa aktarın, sonra dosyanın tam yolunu buraya yazın. Bu yöntem "
            "her tarayıcıda ve her işletim sisteminde çalışır."
        ),
        "cookie_browser_label": "Tarayıcı",
        "cookie_chrome_warning": (
            "Dikkat: Chrome 127'den itibaren Windows'ta çerezler yalnızca Chrome'un kendi "
            "süreci tarafından çözülebiliyor (app-bound encryption). Chrome, Edge, Brave gibi "
            "Chromium tabanlı tarayıcılarda bu yöntem Windows'ta çalışmaz — Firefox çalışır. "
            "Chromium kullanıyorsanız \"cookies.txt dosyası\" seçeneğini kullanın."
        ),
        "cookie_save": "Kaydet",
        "cookie_test": "Bağlantıyı sına",
        "cookie_saved": "Kaydedildi.",
        "cookie_test_ok": "Çalışıyor — {n} çerez okundu.",
        "cookie_test_none": "Çerez kaynağı ayarlanmamış.",
        "cookie_test_failed": "Çerezler okunamadı",
        "cookie_privacy": (
            "Çerezleriniz MediaGrab'a kopyalanmaz veya hiçbir yere gönderilmez; yalnızca "
            "kaynağın adı (tarayıcı adı ya da dosya yolu) bu bilgisayarda saklanır."
        ),
        "settings_deps_title": "Python Bağımlılıkları",
        "settings_deps_hint": (
            "Sanal ortamdaki paketler PyPI'daki güncel sürümlerle karşılaştırılır."
        ),
        "deps_update_btn": "Tümünü Güncelle",
        "footer_legal": (
            "Bu araç yalnızca kişisel kullanım içindir. İndirdiğiniz içeriğin telif durumundan "
            "ve ilgili platformun kullanım şartlarına uyumdan tamamen siz sorumlusunuz."
        ),
        "footer_note": (
            "MediaGrab, yt-dlp ile çalışır. Veritabanı ve hesap sistemi yoktur — "
            "sadece bu bilgisayarda çalışır."
        ),
        "lang_switch_label": "Dil",
        "theme_toggle": "Açık / koyu tema",
        "downloads_panel": "İndirmeler",
        "settings_theme_title": "Görünüm",
        "settings_theme_hint": "Sistem seçilirse, işletim sisteminizin açık/koyu ayarını takip eder.",
        "theme_system": "Sistem",
        "theme_light": "Açık",
        "theme_dark": "Koyu",
        "hero_title": "Link yapıştır, indir",
        "hero_sub": (
            "YouTube, YouTube Music ve yt-dlp'nin desteklediği diğer birçok siteden "
            "linki yapıştırın; ses veya video olarak indirin."
        ),
        "url_placeholder": "Video linkini yapıştır...",
        "paste_btn": "Panodan yapıştır",
        "resolve_btn": "Çözümle",
        "pending_title": "Takip Edilen Kanallarda Yeni Video",
        "pending_clear": "Temizle",
        "recent_title": "Son İndirilenler",
        "recent_see_all": "Tümünü gör →",
        "history_page_title": "İndirme Geçmişi",
        "history_clear": "Tümünü Sil",
        "history_search_placeholder": "Ara...",
        "history_all_channels": "Tüm kanallar",
        "settings_page_title": "Ayarlar",
        "settings_add_title": "Kanal Takip Et",
        "settings_add_hint": (
            "Uygulamayı her açtığınızda takip ettiğiniz kanallar yeni video için kontrol edilir."
        ),
        "channel_url_placeholder": "Kanal linki yapıştır (ör. youtube.com/@kanaladi)",
        "mode_notify": "Bildir",
        "mode_auto": "Otomatik indir",
        "choice_best_video": "En iyi video kalitesi",
        "channel_add_btn": "Ekle",
        "settings_list_title": "Takip Edilen Kanallar",
        "channel_empty": "Henüz takip edilen kanal yok.",
        "settings_ytdlp_title": "yt-dlp Sürümü",
    },
    "en": {
        "title_index": "MediaGrab — Video & Audio Downloader",
        "title_history": "Download History — MediaGrab",
        "title_settings": "Settings — MediaGrab",
        "title_channels": "Channels — MediaGrab",
        "nav_home": "Home",
        "nav_history": "History",
        "nav_channels": "Channels",
        "nav_sites": "Supported Sites",
        "nav_settings": "Settings",
        "channels_page_title": "Channel Following",
        "channels_page_intro": "Channel following currently supports YouTube channels only.",
        "settings_ffmpeg_title": "ffmpeg / ffprobe",
        "settings_ffmpeg_hint": (
            "Required for merging, converting, and reading cover art/duration. "
            "Not bundled with MediaGrab - you install it on your system separately."
        ),
        "settings_cookies_title": "Cookies",
        "settings_cookies_hint": (
            "Your browser session's cookies can be used for age-restricted, members-only "
            "or sign-in-required content. Only use this for content you already have "
            "access to."
        ),
        "cookie_off": "Off",
        "cookie_file": "cookies.txt file",
        "cookie_browser": "From browser",
        "cookie_file_label": "File path",
        "cookie_file_help": (
            "Install a \"cookies.txt export\" extension in your browser, export your cookies "
            "in Netscape format, then put the full path to that file here. This method works "
            "in every browser and on every operating system."
        ),
        "cookie_browser_label": "Browser",
        "cookie_chrome_warning": (
            "Note: since Chrome 127, cookies on Windows can only be decrypted by Chrome's own "
            "process (app-bound encryption). This method therefore does NOT work on Windows for "
            "Chromium-based browsers such as Chrome, Edge or Brave — Firefox does work. If you "
            "use a Chromium browser, choose the \"cookies.txt file\" option instead."
        ),
        "cookie_save": "Save",
        "cookie_test": "Test",
        "cookie_saved": "Saved.",
        "cookie_test_ok": "Working — {n} cookie(s) loaded.",
        "cookie_test_none": "No cookie source configured.",
        "cookie_test_failed": "Could not read cookies",
        "cookie_privacy": (
            "Your cookies are never copied into MediaGrab or sent anywhere; only the name of "
            "the source (a browser name or a file path) is stored on this computer."
        ),
        "settings_deps_title": "Python Dependencies",
        "settings_deps_hint": "Packages in the virtual environment, compared against the latest on PyPI.",
        "deps_update_btn": "Update All",
        "footer_legal": (
            "This tool is for personal use only. You are solely responsible for the copyright "
            "status of downloaded content and compliance with the relevant platform's terms of service."
        ),
        "footer_note": (
            "MediaGrab runs on yt-dlp. No database or account system — it only runs on this computer."
        ),
        "lang_switch_label": "Language",
        "theme_toggle": "Light / dark theme",
        "downloads_panel": "Downloads",
        "settings_theme_title": "Appearance",
        "settings_theme_hint": "With System selected, it follows your operating system's light/dark setting.",
        "theme_system": "System",
        "theme_light": "Light",
        "theme_dark": "Dark",
        "hero_title": "Paste a link, download",
        "hero_sub": (
            "Paste a link from YouTube, YouTube Music, or many other sites supported by yt-dlp; "
            "download it as audio or video."
        ),
        "url_placeholder": "Paste a video link...",
        "paste_btn": "Paste from clipboard",
        "resolve_btn": "Resolve",
        "pending_title": "New Videos From Followed Channels",
        "pending_clear": "Clear",
        "recent_title": "Recent Downloads",
        "recent_see_all": "View all →",
        "history_page_title": "Download History",
        "history_clear": "Clear All",
        "history_search_placeholder": "Search...",
        "history_all_channels": "All channels",
        "settings_page_title": "Settings",
        "settings_add_title": "Follow a Channel",
        "settings_add_hint": (
            "Every time you open the app, followed channels are checked for new videos."
        ),
        "channel_url_placeholder": "Paste a channel link (e.g. youtube.com/@channelname)",
        "mode_notify": "Notify",
        "mode_auto": "Auto-download",
        "choice_best_video": "Best video quality",
        "channel_add_btn": "Add",
        "settings_list_title": "Followed Channels",
        "channel_empty": "No followed channels yet.",
        "settings_ytdlp_title": "yt-dlp Version",
    },
}


def ui_text(lang: str) -> dict:
    return UI.get(lang, UI["tr"])
