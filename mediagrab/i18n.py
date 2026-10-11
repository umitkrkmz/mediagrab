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
        "nav_about": "Hakkında",
        "nav_toggle": "Menü",
        "channels_page_title": "Kanal Takibi",
        "channels_page_intro": (
            "Kanal takibi şimdilik yalnızca YouTube kanallarını destekler."
        ),
        "settings_ffmpeg_title": "ffmpeg / ffprobe",
        "settings_ffmpeg_hint": (
            "Birleştirme, dönüştürme ve kapak/süre okuma için gereklidir. "
            "MediaGrab ile birlikte gelmez, sisteminize ayrıca kurulur."
        ),
        "settings_audio_lang_title": "Varsayılan Ses Parçası",
        "settings_audio_lang_hint": (
            "Birden fazla dilde dublajı olan bir video indirdiğinizde, mevcutsa bu dil otomatik "
            "seçili gelir. Boş bırakırsanız videonun orijinal dili kullanılır. Kanal otomatik "
            "indirmesi de bu ayarı kullanır."
        ),
        "settings_audio_lang_label": "Dil kodu",
        "settings_audio_lang_placeholder": "örn. tr, en, de",
        "settings_audio_lang_codes_url": "https://github.com/umitkrkmz/mediagrab/blob/master/docs/language-codes.tr.md",
        "settings_audio_lang_codes_link": "Dil kodlarını görüntüle →",
        "settings_downloads_title": "İndirme Ayarları",
        "settings_download_dir_title": "İndirme Klasörü",
        "settings_download_dir_hint": (
            "İndirdiğiniz videolar ve sesler bu klasöre kaydedilir. Değiştirirseniz yalnızca yeni indirmeler "
            "yeni klasöre gider; önceki dosyalar eski yerinde kalır, silinmez."
        ),
        "settings_download_dir_browse": "Klasör Seç…",
        "settings_download_dir_reset": "Varsayılana Dön",
        "settings_download_dir_input_label": "Ya da klasör yolunu yazın:",
        "settings_download_dir_picker_title": "MediaGrab: İndirilen videolar nereye kaydedilsin?",
        "settings_download_dir_readonly": "Bu klasör yalnızca MediaGrab'ın kurulu olduğu bilgisayardan değiştirilebilir.",
        "settings_download_dir_docker": (
            "Docker'da indirme klasörünü docker-compose.yml'deki ./data/indirilenler bağlantısı belirler."
        ),
        "settings_speed_limit_title": "Hız Sınırlama",
        "settings_speed_limit_hint": "İndirmelerin ev ağınızın tüm bant genişliğini kullanmasını önlemek için bir üst sınır koyun.",
        "settings_speed_limit_unlimited": "Sınırsız",
        "settings_speed_limit_custom_btn": "Özel",
        "settings_speed_limit_custom_label": "Özel hız (MB/s)",
        "settings_speed_limit_custom_placeholder": "örn. 2",
        "settings_speed_limit_table_title": "Hız karşılaştırması",
        "settings_speed_limit_table_hint": "Ev interneti genelde Mbps (megabit) olarak satılır, MB/s (megabayt) ile karıştırmayın - 1 MB/s = 8 Mbps.",
        "settings_speed_limit_table_custom_label": "Özel",
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
        "cookie_upload_label": "cookies.txt yükle",
        "cookie_howto_title": "cookies.txt nasıl alınır?",
        "cookie_step1": "Tarayıcınıza açık kaynaklı \"Get cookies.txt LOCALLY\" eklentisini kurun:",
        "cookie_step2": (
            "Eklenti ayarlarından gizli (özel) pencerede çalışmasına izin verin; sonra gizli "
            "bir pencere açıp youtube.com'da hesabınıza giriş yapın."
        ),
        "cookie_step3": (
            "Aynı sekmede youtube.com/robots.txt adresini açın ve eklentide \"Export\" "
            "düğmesine basın (\"Export All Cookies\" değil — o tüm sitelerin çerezlerini alır)."
        ),
        "cookie_step4": "Gizli pencereyi kapatın, sonra indirilen dosyayı yukarıdan yükleyin.",
        "cookie_howto_why": (
            "Neden gizli pencere? YouTube açık sekmelerdeki oturum çerezlerini sık sık yeniler; "
            "kapatılmış bir oturumdan alınan çerezler çok daha uzun süre geçerli kalır."
        ),
        "cookie_account_warning": (
            "yt-dlp'nin uyarısı: hesabınızla yapılan yoğun indirmeler hesabın geçici veya kalıcı "
            "olarak kısıtlanmasına yol açabilir. Mümkünse ikincil bir hesap kullanın."
        ),
        "cookie_path_advanced": "Gelişmiş: bilgisayardaki bir dosyanın yolunu girin",
        "cookie_browser_label": "Tarayıcı",
        "cookie_windows_browser_note": (
            "Windows'ta yalnızca Firefox listelenir: Chrome, Edge, Brave gibi Chromium tabanlı "
            "tarayıcıların çerezlerini Windows'ta yalnızca tarayıcının kendisi çözebiliyor "
            "(App-Bound Encryption). Bu tarayıcılar için \"cookies.txt dosyası\" seçeneğini kullanın."
        ),
        "cookie_save": "Kaydet",
        "cookie_test": "Bağlantıyı sına",
        "copy_btn": "Kopyala",
        "cookie_saved": "Kaydedildi.",
        "cookie_test_ok": "Çalışıyor — {n} çerez okundu.",
        "cookie_test_none": "Çerez kaynağı ayarlanmamış.",
        "cookie_test_failed": "Çerezler okunamadı",
        "cookie_privacy": (
            "Yüklediğiniz dosya yalnızca bu cihazdaki MediaGrab veri klasörüne kaydedilir; "
            "hiçbir yere gönderilmez, yedeğe girmez ve içeriği arayüzde gösterilmez. yt-dlp "
            "indirme sırasında yenilenen çerezleri bu dosyaya geri yazar."
        ),
        "settings_deps_title": "Python Bağımlılıkları",
        "settings_deps_hint": (
            "Sanal ortamdaki paketler PyPI'daki güncel sürümlerle karşılaştırılır."
        ),
        "deps_update_btn": "Tümünü Güncelle",
        "settings_deps_docker_hint": "Docker'da paketler imaja gömülü — güncellemek için yeni bir imaj çekip container'ı yeniden oluşturun (docker pull + docker compose up -d).",
        "settings_backup_title": "Yedekle",
        "settings_backup_hint": "Ayarlarınızı ve kanal takip listenizi tek bir dosyaya kaydedin; başka bir bilgisayara veya Raspberry Pi'ye geçerken bu dosyayı içe aktarın.",
        "settings_backup_password_warning": "Uzaktan erişim şifreniz yedeğe dahil edilmez - yeni cihazda şifreyi yeniden belirlemeniz gerekir.",
        "settings_backup_export_btn": "Dışa Aktar",
        "settings_backup_import_btn": "İçe Aktar",
        "settings_feedback_title": "Geri Bildirim",
        "settings_feedback_hint": (
            "Bir hata mı buldunuz, yoksa bir özellik mi önereceksiniz? GitHub üzerinden bildirin."
        ),
        "settings_feedback_btn": "Hata Bildir / Özellik Öner",
        "settings_diagnostics_btn": "Tanılama bilgisini kopyala",
        "settings_diagnostics_hint": (
            "Hata bildirirken bunu yapıştırın: MediaGrab, yt-dlp ve ffmpeg sürümleri, işletim sistemi, "
            "kurulum türü ve çerez modu. Dosya yolu, IP adresi, bilgisayar adı veya çerez içeriği içermez."
        ),
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
        "history_tab_files": "Dosyalar",
        "history_tab_stats": "İstatistikler",
        "stats_period_label": "Dönem",
        "stats_period_day": "Günlük",
        "stats_period_week": "Haftalık",
        "stats_period_month": "Aylık",
        "stats_reset": "İstatistikleri Sıfırla",
        "stats_downloads_title": "İndirmeler",
        "stats_sites_title": "Siteler",
        "stats_audio_title": "Ses biçimleri",
        "stats_video_title": "Video çözünürlükleri",
        "stats_disk_title": "Disk",
        "stats_privacy": (
            "Yalnızca sayılar tutulur: hangi siteden, hangi biçimde, kaç dosya ve ne kadar. Başlık, bağlantı, "
            "kanal ya da dosya adı kaydedilmez; hepsi bu bilgisayarda kalır."
        ),
        "history_search_placeholder": "Ara...",
        "history_all_channels": "Tüm kanallar",
        "history_type_filter_label": "Dosya türüne göre filtrele",
        "history_view_grid": "Izgara görünümü",
        "history_view_list": "Liste görünümü",
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
        "settings_mediagrab_title": "MediaGrab Sürümü",
        "settings_ytdlp_title": "yt-dlp Sürümü",
        "settings_environment_title": "Sürüm Kontrolleri",
        "title_login": "Giriş — MediaGrab",
        "login_heading": "MediaGrab'a Giriş",
        "login_password_label": "Şifre",
        "login_password_placeholder": "Şifrenizi girin",
        "login_submit_btn": "Giriş Yap",
        "login_wrong_password": "Şifre yanlış",
        "settings_remote_access_title": "Uzaktan Erişim",
        "settings_home_server_title": "Ev Sunucusu Modu",
        "settings_home_server_enable_label": "Bu cihazı sürekli açık tutuyorum",
        "settings_home_server_hint": (
            "Açıkken takip ettiğiniz kanallar sadece uygulamayı açtığınızda değil, arka planda periyodik olarak "
            "(birkaç saatte bir) kontrol edilir. Uzaktan erişimden bağımsızdır - ikisini ayrı ayrı açıp "
            "kapatabilirsiniz. Ayar değiştiğinde uygulama kendini bir kez yeniden başlatır."
        ),
        "settings_remote_access_hint": "Bunu açtığınızda, aynı ağdaki başka cihazlar (telefon, laptop) MediaGrab'a bağlanabilir — şifrenizi bilmeleri gerekir. Bağlantı adresi, etkinleştirdikten sonra aşağıda görünür.",
        "settings_remote_access_warning": "Bu şifreleme kullanmaz (HTTPS değildir) — yalnızca güvendiğiniz bir ev/ofis ağında kullanın, doğrudan internete açmayın.",
        "settings_remote_access_enable_label": "Yerel ağdan erişime izin ver",
        "settings_remote_access_need_password_first": "Etkinleştirmeden önce bir şifre belirleyin.",
        "settings_remote_access_current_password_label": "Mevcut Şifre",
        "settings_remote_access_password_label": "Yeni Şifre",
        "settings_remote_access_password_placeholder": "Yeni şifre (en az 8 karakter)",
        "settings_remote_access_confirm_password_label": "Yeni Şifre (Tekrar)",
        "settings_remote_access_show_passwords_label": "Şifreleri göster",
        "settings_remote_access_forgot_password_hint": "Şifrenizi unuttuysanız: bu bilgisayardaki settings.json dosyasında remote_access_password_salt ve remote_access_password_hash alanlarını silip MediaGrab'ı yeniden başlatın, buradan yeni bir şifre belirleyebilirsiniz.",
        "settings_remote_access_set_password_btn": "Şifreyi Kaydet",
        "settings_remote_access_update_password_btn": "Şifreyi Güncelle",
        "settings_remote_access_password_saved": "Şifre kaydedildi.",
        "settings_remote_access_password_too_short": "Şifre en az 8 karakter olmalı.",
        "settings_remote_access_restart_note": "Ayar uygulanıyor, sunucu yeniden başlatılıyor...",
        "settings_remote_access_logout_btn": "Bu Cihazdan Çıkış Yap",
        "settings_remote_access_logged_out": "Çıkış yapıldı.",
        "settings_remote_access_address_title": "Bağlantı Adresi",
        "settings_remote_access_address_hint": "Telefonunuzdan veya aynı ağdaki başka bir cihazdan bu adrese gidin:",
        "settings_remote_access_qr_hint": "Ya da telefonunuzun kamerasını bu kodun üzerine tutun.",
        "settings_remote_access_mdns_hint": "Bazı cihazlarda bu adres de işe yarayabilir:",
        "settings_remote_access_qr_ip_label": "IP Adresi",
        "settings_remote_access_devices_title": "Bağlı Cihazlar",
        "settings_remote_access_storage_title": "Depolama",
        "settings_remote_access_storage_hint": "İndirilen dosyalar bu bilgisayarda kalsın mı, yoksa cihaza gönderildikten sonra silinsin mi?",
        "settings_remote_access_storage_keep_label": "Bende Kalsın",
        "settings_remote_access_storage_keep_hint": "Kişisel bilgisayar için: dosyalar her zamanki gibi indirilenler/ klasöründe kalıcı olarak durur.",
        "item_resolution": "Çözünürlük",
        "item_video_codec": "Video",
        "item_audio": "Ses",
        "item_channels_mono": "mono",
        "item_channels_stereo": "stereo",
        "item_channels_n": "{n} kanal",
        "settings_remote_access_storage_relay_label": "Cihaza Aktar",
        "settings_remote_access_storage_relay_hint": (
            "Depolaması sınırlı cihazlar için (ör. Raspberry Pi): telefon gibi başka bir cihaz dosyayı tamamen "
            "indirdiğinde buradaki kopyası silinir. Docker'ı kendi bilgisayarınızda localhost ile açtıysanız "
            "\"Klasöre Kaydet\" çıkar; kopya yalnız dosya seçtiğiniz klasöre gerçekten kaydedildikten sonra silinir, "
            "pencereyi iptal ederseniz dosyaya dokunulmaz. Not: başka bir bilgisayarda tarayıcı \"nereye "
            "kaydedileceğini sor\" ayarıyla açıksa, tarayıcı dosyayı pencere açıkken indirdiği için iptal "
            "algılanamaz."
        ),
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
        "nav_about": "About",
        "nav_toggle": "Menu",
        "channels_page_title": "Channel Following",
        "channels_page_intro": "Channel following currently supports YouTube channels only.",
        "settings_ffmpeg_title": "ffmpeg / ffprobe",
        "settings_ffmpeg_hint": (
            "Required for merging, converting, and reading cover art/duration. "
            "Not bundled with MediaGrab - you install it on your system separately."
        ),
        "settings_audio_lang_title": "Default Audio Track",
        "settings_audio_lang_hint": (
            "When you download a video that has more than one dub, this language is preselected "
            "if it's available. Leave it blank to use the video's original language. Channel "
            "auto-download uses this setting too."
        ),
        "settings_audio_lang_label": "Language code",
        "settings_audio_lang_placeholder": "e.g. tr, en, de",
        "settings_audio_lang_codes_url": "https://github.com/umitkrkmz/mediagrab/blob/master/docs/language-codes.en.md",
        "settings_audio_lang_codes_link": "View language codes →",
        "settings_downloads_title": "Download Settings",
        "settings_download_dir_title": "Download Folder",
        "settings_download_dir_hint": (
            "Your downloaded videos and audio are saved here. If you change it, only new downloads go to the "
            "new folder; earlier files stay where they are and are not deleted."
        ),
        "settings_download_dir_browse": "Choose Folder…",
        "settings_download_dir_reset": "Back to Default",
        "settings_download_dir_input_label": "Or type the folder path:",
        "settings_download_dir_picker_title": "MediaGrab: Where should downloaded videos be saved?",
        "settings_download_dir_readonly": "This folder can only be changed on the computer MediaGrab is installed on.",
        "settings_download_dir_docker": (
            "In Docker, the download folder is set by the ./data/indirilenler mount in docker-compose.yml."
        ),
        "settings_speed_limit_title": "Speed Limit",
        "settings_speed_limit_hint": "Cap download speed so it doesn't use your whole home network's bandwidth.",
        "settings_speed_limit_unlimited": "Unlimited",
        "settings_speed_limit_custom_btn": "Custom",
        "settings_speed_limit_custom_label": "Custom speed (MB/s)",
        "settings_speed_limit_custom_placeholder": "e.g. 2",
        "settings_speed_limit_table_title": "Speed comparison",
        "settings_speed_limit_table_hint": "Home internet is usually sold in Mbps (megabits), not MB/s (megabytes) - 1 MB/s = 8 Mbps.",
        "settings_speed_limit_table_custom_label": "Custom",
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
        "cookie_upload_label": "Upload cookies.txt",
        "cookie_howto_title": "How do I get a cookies.txt?",
        "cookie_step1": "Install the open-source \"Get cookies.txt LOCALLY\" extension in your browser:",
        "cookie_step2": (
            "Allow it to run in private (incognito) windows in the extension's settings, then "
            "open a private window and sign in to your account on youtube.com."
        ),
        "cookie_step3": (
            "In that same tab, open youtube.com/robots.txt and click \"Export\" in the "
            "extension (not \"Export All Cookies\" - that takes every site's cookies)."
        ),
        "cookie_step4": "Close the private window, then upload the downloaded file above.",
        "cookie_howto_why": (
            "Why a private window? YouTube frequently rotates the session cookies of open "
            "tabs; cookies taken from a session that's then closed stay valid much longer."
        ),
        "cookie_account_warning": (
            "yt-dlp's own warning: heavy downloading with your account can get it temporarily "
            "or permanently restricted. Use a secondary account if you can."
        ),
        "cookie_path_advanced": "Advanced: enter the path of a file on this computer",
        "cookie_browser_label": "Browser",
        "cookie_windows_browser_note": (
            "Only Firefox is listed on Windows: there, cookies of Chromium-based browsers like "
            "Chrome, Edge and Brave can only be decrypted by the browser itself (App-Bound "
            "Encryption). Use the \"cookies.txt file\" option for those browsers."
        ),
        "cookie_save": "Save",
        "cookie_test": "Test",
        "copy_btn": "Copy",
        "cookie_saved": "Saved.",
        "cookie_test_ok": "Working — {n} cookie(s) loaded.",
        "cookie_test_none": "No cookie source configured.",
        "cookie_test_failed": "Could not read cookies",
        "cookie_privacy": (
            "An uploaded file is only saved in MediaGrab's data folder on this device; it is "
            "never sent anywhere, never included in backups, and its contents are never shown "
            "in the interface. yt-dlp writes refreshed cookies back into it while downloading."
        ),
        "settings_deps_title": "Python Dependencies",
        "settings_deps_hint": "Packages in the virtual environment, compared against the latest on PyPI.",
        "deps_update_btn": "Update All",
        "settings_deps_docker_hint": "In Docker, packages are baked into the image — to update, pull a new one and recreate the container (docker pull + docker compose up -d).",
        "settings_backup_title": "Backup",
        "settings_backup_hint": "Save your settings and followed-channel list to one file; import it when moving to another computer or a Raspberry Pi.",
        "settings_backup_password_warning": "Your remote-access password is not included in the backup - you'll need to set it again on the new device.",
        "settings_backup_export_btn": "Export",
        "settings_backup_import_btn": "Import",
        "settings_feedback_title": "Feedback",
        "settings_feedback_hint": "Found a bug, or have a feature to suggest? Report it on GitHub.",
        "settings_feedback_btn": "Report a Bug / Suggest a Feature",
        "settings_diagnostics_btn": "Copy diagnostic info",
        "settings_diagnostics_hint": (
            "Paste this into a bug report: MediaGrab, yt-dlp and ffmpeg versions, OS, install type and "
            "cookie mode. It contains no file paths, IP addresses, computer name or cookie contents."
        ),
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
        "history_tab_files": "Files",
        "history_tab_stats": "Statistics",
        "stats_period_label": "Period",
        "stats_period_day": "Daily",
        "stats_period_week": "Weekly",
        "stats_period_month": "Monthly",
        "stats_reset": "Reset Statistics",
        "stats_downloads_title": "Downloads",
        "stats_sites_title": "Sites",
        "stats_audio_title": "Audio formats",
        "stats_video_title": "Video resolutions",
        "stats_disk_title": "Disk",
        "stats_privacy": (
            "Only numbers are kept: which site, which format, how many files and how much. No titles, links, "
            "channels or file names are recorded, and it all stays on this computer."
        ),
        "history_search_placeholder": "Search...",
        "history_all_channels": "All channels",
        "history_type_filter_label": "Filter by file type",
        "history_view_grid": "Grid view",
        "history_view_list": "List view",
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
        "settings_mediagrab_title": "MediaGrab Version",
        "settings_ytdlp_title": "yt-dlp Version",
        "settings_environment_title": "Version Checks",
        "title_login": "Login — MediaGrab",
        "login_heading": "Log in to MediaGrab",
        "login_password_label": "Password",
        "login_password_placeholder": "Enter your password",
        "login_submit_btn": "Log In",
        "login_wrong_password": "Incorrect password",
        "settings_remote_access_title": "Remote Access",
        "settings_home_server_title": "Home Server Mode",
        "settings_home_server_enable_label": "I keep this device running continuously",
        "settings_home_server_hint": (
            "When on, followed channels are checked periodically in the background (every few hours) instead of "
            "only when you open the app. Independent of remote access - turn either on or off separately. "
            "The app restarts itself once when this setting changes."
        ),
        "settings_remote_access_hint": "Turning this on lets other devices on the same network (phone, laptop) reach MediaGrab — they'll need your password. The connection address shows up below once it's on.",
        "settings_remote_access_warning": "This has no encryption (it isn't HTTPS) — only use it on a home/office network you trust, never expose it directly to the internet.",
        "settings_remote_access_enable_label": "Allow access from your local network",
        "settings_remote_access_need_password_first": "Set a password before enabling this.",
        "settings_remote_access_current_password_label": "Current Password",
        "settings_remote_access_password_label": "New Password",
        "settings_remote_access_password_placeholder": "New password (min 8 characters)",
        "settings_remote_access_confirm_password_label": "New Password (again)",
        "settings_remote_access_show_passwords_label": "Show passwords",
        "settings_remote_access_forgot_password_hint": "Forgot your password? On this computer, delete the remote_access_password_salt and remote_access_password_hash fields from settings.json and restart MediaGrab - you can then set a new password from here.",
        "settings_remote_access_set_password_btn": "Save Password",
        "settings_remote_access_update_password_btn": "Update Password",
        "settings_remote_access_password_saved": "Password saved.",
        "settings_remote_access_password_too_short": "Password must be at least 8 characters.",
        "settings_remote_access_restart_note": "Applying the setting, restarting the server...",
        "settings_remote_access_logout_btn": "Log Out On This Device",
        "settings_remote_access_logged_out": "Logged out.",
        "settings_remote_access_address_title": "Connection Address",
        "settings_remote_access_address_hint": "Visit this address from your phone or another device on the same network:",
        "settings_remote_access_qr_hint": "Or point your phone's camera at this code.",
        "settings_remote_access_mdns_hint": "This address might also work on some devices:",
        "settings_remote_access_qr_ip_label": "IP Address",
        "settings_remote_access_devices_title": "Connected Devices",
        "settings_remote_access_storage_title": "Storage",
        "settings_remote_access_storage_hint": "Should downloaded files stay on this computer, or be deleted once they've been sent to a device?",
        "settings_remote_access_storage_keep_label": "Keep Here",
        "settings_remote_access_storage_keep_hint": "For a personal computer: files stay permanently in indirilenler/, same as always.",
        "item_resolution": "Resolution",
        "item_video_codec": "Video",
        "item_audio": "Audio",
        "item_channels_mono": "mono",
        "item_channels_stereo": "stereo",
        "item_channels_n": "{n} channels",
        "settings_remote_access_storage_relay_label": "Relay To Device",
        "settings_remote_access_storage_relay_hint": (
            "For storage-constrained devices (e.g. a Raspberry Pi): once another device, like a phone, fully "
            "downloads a file, the copy here is deleted. If you run Docker on your own computer and open it via "
            "localhost, you get \"Save to Folder\" instead: the copy is only deleted after the file is actually "
            "saved to the folder you picked - cancelling the dialog leaves it untouched. Note: on another computer "
            "whose browser asks where to save each file, a cancel can't be detected, because the browser downloads "
            "the file while that dialog is still open."
        ),
    },
}


def ui_text(lang: str) -> dict:
    return UI.get(lang, UI["tr"])
