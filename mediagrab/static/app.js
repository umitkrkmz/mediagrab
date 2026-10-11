// NOTE: this script is loaded on the index/history/item pages alike (for the
// shared header/footer/language switcher), so every DOM element can be null -
// check it exists before using it.
const urlInput = document.getElementById("url-input");
const pasteBtn = document.getElementById("paste-btn");
const probeBtn = document.getElementById("probe-btn");
const card = document.getElementById("card");
const downloadDock = document.getElementById("download-dock");
const recentSection = document.getElementById("recent-section");
const recentList = document.getElementById("recent-list");
const historyList = document.getElementById("history-list");
const historyError = document.getElementById("history-error");
const historyClearBtn = document.getElementById("history-clear-btn");
const historySearchInput = document.getElementById("history-search");
const historyChannelFilter = document.getElementById("history-channel-filter");
const historyTypeFilter = document.getElementById("history-type-filter");
const historyViewGridBtn = document.getElementById("history-view-grid");
const historyViewListBtn = document.getElementById("history-view-list");
const langSwitch = document.getElementById("lang-switch");
const themeToggle = document.getElementById("theme-toggle");
const themeChoice = document.getElementById("theme-choice");
const itemRevealBtn = document.getElementById("item-reveal-btn");
const itemPreviewBtn = document.getElementById("item-preview-btn");
const itemPreviewPlayer = document.getElementById("item-preview-player");

const pendingBanner = document.getElementById("pending-banner");
const pendingClearBtn = document.getElementById("pending-clear-btn");
const pendingList = document.getElementById("pending-list");

const channelUrlInput = document.getElementById("channel-url-input");
const channelChoiceSelect = document.getElementById("channel-choice-select");
const channelAddBtn = document.getElementById("channel-add-btn");
const channelError = document.getElementById("channel-error");
const channelList = document.getElementById("channel-list");
const channelEmpty = document.getElementById("channel-empty");
const channelModeRadios = document.querySelectorAll('input[name="channel-mode"]');
const ytdlpStatus = document.getElementById("ytdlp-status");
const ytdlpJsStatus = document.getElementById("ytdlp-js-status");
const ytdlpInstructions = document.getElementById("ytdlp-instructions");
const ytdlpCredit = document.getElementById("ytdlp-credit");
const ffmpegStatus = document.getElementById("ffmpeg-status");
const ffmpegInstructions = document.getElementById("ffmpeg-instructions");
const ffmpegHint = document.getElementById("ffmpeg-hint");
const depsStatus = document.getElementById("deps-status");
const depsList = document.getElementById("deps-list");
const depsActions = document.getElementById("deps-actions");
const depsUpdateBtn = document.getElementById("deps-update-btn");
const depsDockerHint = document.getElementById("deps-docker-hint");
const depsUpdateStatus = document.getElementById("deps-update-status");

const LANG_KEY = "mediagrab_lang";
const THEME_KEY = "mediagrab_theme";

// --- Tema (acik/koyu) ---

// NOTE: three preferences - "system" (the default: no data-theme attribute,
// so the CSS follows prefers-color-scheme) plus the two explicit overrides.
// currentTheme() is what's actually on screen, which for "system" depends on
// the OS right now; themePreference() is what the user chose.
function themePreference() {
  try {
    const stored = localStorage.getItem(THEME_KEY);
    if (stored === "light" || stored === "dark") return stored;
  } catch (err) {
    // NOTE: storage blocked (private mode) - fall through to "system".
  }
  return "system";
}

function currentTheme() {
  const explicit = document.documentElement.dataset.theme;
  if (explicit === "light" || explicit === "dark") return explicit;
  return window.matchMedia("(prefers-color-scheme: light)").matches ? "light" : "dark";
}

function renderThemeControls() {
  if (themeToggle) {
    // NOTE: shows where the button will take you, not where you are.
    themeToggle.textContent = currentTheme() === "dark" ? "☀" : "☾";
  }
  const pref = themePreference();
  themeChoice?.querySelectorAll("[data-theme-choice]").forEach((btn) => {
    const active = btn.dataset.themeChoice === pref;
    btn.classList.toggle("active", active);
    btn.setAttribute("aria-checked", active ? "true" : "false");
  });
}

function setThemePreference(pref) {
  if (pref === "system") {
    // NOTE: removing the attribute is what hands control back to the
    // prefers-color-scheme media query in the stylesheet.
    delete document.documentElement.dataset.theme;
  } else {
    document.documentElement.dataset.theme = pref;
  }
  try {
    if (pref === "system") {
      localStorage.removeItem(THEME_KEY);
    } else {
      localStorage.setItem(THEME_KEY, pref);
    }
  } catch (err) {
    // NOTE: storage can be blocked (private mode) - the theme still applies
    // for this page, it just won't be remembered.
  }
  renderThemeControls();
}

function toggleTheme() {
  setThemePreference(currentTheme() === "dark" ? "light" : "dark");
}

// NOTE: error messages from the server (yt-dlp/downloader) are dynamic and
// mostly already English/technical, so there's no translation layer for
// them; only the client-side strings defined here change with the language.
const I18N = {
  tr: {
    resolveBtn: "Çözümle",
    resolveBtnBusy: "...",
    sectionAudio: "Ses",
    sectionAudioTrack: "Ses Parçası",
    audioTrackHint: "Bu videoda birden fazla dil/dublaj var. Birden fazlasını seçerseniz videoya hepsi ayrı ayrı seçilebilir ses parçası olarak eklenir (dosya .mkv olur)",
    audioTrackDefaultSuffix: "(orijinal)",
    // NOTE: ISO 639-1 code -> Turkish language name, sourced from pycountry +
    // Babel (see docs/language-codes.tr.md) for the audio-track chip tooltip.
    audioTrackNames: {
      aa: "Afar",
      ab: "Abhazca",
      ae: "Avestçe",
      af: "Afrikaanca",
      ak: "Akan",
      am: "Amharca",
      an: "Aragonca",
      ar: "Arapça",
      as: "Assamca",
      av: "Avar dili",
      ay: "Aymara",
      az: "Azerbaycan dili",
      ba: "Başkırtça",
      be: "Belarusça",
      bg: "Bulgarca",
      bi: "Bislama",
      bm: "Bambara",
      bn: "Bengalce",
      bo: "Tibetçe",
      br: "Bretonca",
      bs: "Boşnakça",
      ca: "Katalanca",
      ce: "Çeçence",
      ch: "Çamorro dili",
      co: "Korsikaca",
      cr: "Krice",
      cs: "Çekçe",
      cu: "Kilise Slavcası",
      cv: "Çuvaşça",
      cy: "Galce",
      da: "Danca",
      de: "Almanca",
      dv: "Divehi dili",
      dz: "Dzongkha",
      ee: "Ewe",
      el: "Yunanca",
      en: "İngilizce",
      eo: "Esperanto",
      es: "İspanyolca",
      et: "Estonca",
      eu: "Baskça",
      fa: "Farsça",
      ff: "Fula dili",
      fi: "Fince",
      fj: "Fiji dili",
      fo: "Faroe dili",
      fr: "Fransızca",
      fy: "Batı Frizcesi",
      ga: "İrlandaca",
      gd: "İskoç Gaelcesi",
      gl: "Galiçyaca",
      gn: "Guarani dili",
      gu: "Güceratça",
      gv: "Man dili",
      ha: "Hausa dili",
      he: "İbranice",
      hi: "Hintçe",
      ho: "Hiri Motu",
      hr: "Hırvatça",
      ht: "Haiti Kreyolu",
      hu: "Macarca",
      hy: "Ermenice",
      hz: "Herero dili",
      ia: "İnterlingua",
      id: "Endonezce",
      ie: "Interlingue",
      ig: "İbo dili",
      ii: "Sichuan Yi",
      ik: "İnyupikçe",
      io: "Ido",
      is: "İzlandaca",
      it: "İtalyanca",
      iu: "İnuktitut dili",
      ja: "Japonca",
      jv: "Cava dili",
      ka: "Gürcüce",
      kg: "Kongo dili",
      ki: "Kikuyu",
      kj: "Kuanyama",
      kk: "Kazakça",
      kl: "Grönland dili",
      km: "Khmer dili",
      kn: "Kannada dili",
      ko: "Korece",
      kr: "Kanuri dili",
      ks: "Keşmir dili",
      ku: "Kürtçe",
      kv: "Komi",
      kw: "Kernevekçe",
      ky: "Kırgızca",
      la: "Latince",
      lb: "Lüksemburgca",
      lg: "Ganda",
      li: "Limburgca",
      ln: "Lingala",
      lo: "Lao dili",
      lt: "Litvanca",
      lu: "Luba-Katanga",
      lv: "Letonca",
      mg: "Malgaşça",
      mh: "Marshall Adaları dili",
      mi: "Maori dili",
      mk: "Makedonca",
      ml: "Malayalam dili",
      mn: "Moğolca",
      mr: "Marathi dili",
      ms: "Malayca",
      mt: "Maltaca",
      my: "Birman dili",
      na: "Nauru dili",
      nb: "Norveççe Bokmål",
      nd: "Kuzey Ndebele",
      ne: "Nepalce",
      ng: "Ndonga",
      nl: "Felemenkçe",
      nn: "Norveççe Nynorsk",
      no: "Norveççe",
      nr: "Güney Ndebele",
      nv: "Navaho dili",
      ny: "Nyanja",
      oc: "Oksitan dili",
      oj: "Ojibva dili",
      om: "Oromo dili",
      or: "Oriya dili",
      os: "Osetçe",
      pa: "Pencapça",
      pi: "Pali",
      pl: "Lehçe",
      ps: "Peştuca",
      pt: "Portekizce",
      qu: "Keçuva dili",
      rm: "Romanşça",
      rn: "Kirundi",
      ro: "Rumence",
      ru: "Rusça",
      rw: "Kinyarwanda",
      sa: "Sanskrit",
      sc: "Sardunya dili",
      sd: "Sindhi dili",
      se: "Kuzey Laponcası",
      sg: "Sango",
      sh: "Sırp-Hırvat Dili",
      si: "Sinhali dili",
      sk: "Slovakça",
      sl: "Slovence",
      sm: "Samoa dili",
      sn: "Şona dili",
      so: "Somalice",
      sq: "Arnavutça",
      sr: "Sırpça",
      ss: "Sisvati",
      st: "Güney Sotho dili",
      su: "Sunda dili",
      sv: "İsveççe",
      sw: "Svahili dili",
      ta: "Tamilce",
      te: "Telugu dili",
      tg: "Tacikçe",
      th: "Tayca",
      ti: "Tigrinya dili",
      tk: "Türkmence",
      tl: "Tagalogca",
      tn: "Setsvana",
      to: "Tonga dili",
      tr: "Türkçe",
      ts: "Tsonga",
      tt: "Tatarca",
      tw: "Tvi",
      ty: "Tahiti dili",
      ug: "Uygurca",
      uk: "Ukraynaca",
      ur: "Urduca",
      uz: "Özbekçe",
      ve: "Venda dili",
      vi: "Vietnamca",
      vo: "Volapük",
      wa: "Valonca",
      wo: "Volofça",
      xh: "Zosa dili",
      yi: "Yidiş",
      yo: "Yorubaca",
      za: "Zhuangca",
      zh: "Çince",
      zu: "Zuluca",
    },
    sectionVideo: "Video",
    sectionSubtitle: "Altyazı",
    subtitleHint: "Seçtiğiniz video ile birlikte, aynı dosya adıyla iner",
    subtitleAutoSuffix: "(otomatik)",
    noVideoFormats: "Video seçeneği bulunamadı",
    sectionTranscript: "Transkript",
    transcriptDownload: "Transkript indir (.txt)",
    transcriptManual: "elle eklenmiş altyazıdan",
    transcriptAuto: "otomatik altyazıdan",
    transcriptTimestamps: "Zaman damgalı",
    transcriptBundleWithMedia: "Video/ses ile birlikte indir",
    quickBestAudio: "♪ En İyi Ses",
    audioUnavailableDesc: "bu video için ayrı ses akışı alınamadı",
    noticeAgeVerification:
      "YouTube bu hesap için yaş doğrulaması istiyor; bu yüzden yalnızca sınırlı, düşük kaliteli biçimler alınabildi. Önce videoyu YouTube'da aynı hesapla açıp içerik uyarısını onaylamayı deneyin; olmazsa hesabın yaşını YouTube/Google'da doğrulayın ya da yaşı doğrulanmış bir hesabın çerezlerini yükleyin.",
    quickBestVideo: "▶ En İyi Video",
    descriptionTitle: "Açıklama",
    descriptionShowMore: "Daha fazla göster",
    descriptionShowLess: "Daha az göster",
    sectionOptions: "Seçenekler",
    audio: {
      opus: { label: "Opus", desc: "en iyi kalite · yeniden kodlanmaz" },
      m4a: { label: "M4A", desc: "AAC · Apple uyumlu · yeniden kodlanmaz" },
      mp3: { label: "MP3", desc: "her yerde çalışır · kalite kaybı var" },
    },
    states: {
      basliyor: "Başlıyor...",
      indiriliyor: "İndiriliyor...",
      isleniyor: "İşleniyor (ffmpeg)...",
      bitti: "Tamamlandı",
      hata: "Hata",
      iptal: "İptal edildi",
    },
    downloadBtn: "Klasörde göster",
    downloadToDeviceBtn: "Cihaza İndir",
    saveToFolderBtn: "Klasöre Kaydet",
    savedToFolder: "Kaydedildi ✓",
    savedAndRemoved: "Kaydedildi — MediaGrab'daki kopyası silindi",
    saveToFolderFailed: "Kaydedilemedi: ",
    downloadStartedNote: "İndirme başladı — altta ilerlemesini takip edebilirsiniz.",
    dockDismiss: "Kapat",
    dockCancel: "İndirmeyi iptal et",
    etaLabel: "kalan",
    cookieSaved: "Kaydedildi.",
    cookieTestOk: "Çalışıyor — {n} çerez okundu.",
    cookieTestNone: "Çerez kaynağı ayarlanmamış.",
    cookieTestUnsupported:
      "Kayıtlı tarayıcı ({browser}) bu sistemde okunamıyor, çerezler şu an kullanılmıyor. Firefox'u seçip kaydedin ya da cookies.txt yükleyin.",
    cookieBrowserUnsupported:
      "Kayıtlı tarayıcı ({browser}) bu sistemde desteklenmiyor, bu yüzden çerezler şu an kullanılmıyor. Firefox'u seçip kaydedin ya da \"cookies.txt dosyası\" seçeneğini kullanın.",
    cookieTestFailed: "Çerezler okunamadı",
    diagCopied: "Kopyalandı ✓ — hata bildirimine yapıştırabilirsiniz.",
    diagCopyManual: "Panoya otomatik kopyalanamadı — metin aşağıda seçili, Ctrl+C (Mac'te ⌘C) ile kopyalayın.",
    cookieReviewTitle: "Bu dosyada {n} sitenin çerezleri var. Kaydedilecekleri seçin:",
    cookieReviewHint: "Yalnızca işaretli sitelerin çerezleri kaydedilir; gerisi diske hiç yazılmaz.",
    cookieCount: "{n} çerez",
    cookieUploadSaveBtn: "Seçilenleri kaydet",
    cookieUploadCancelBtn: "Vazgeç",
    cookieUploaded: "Kaydedildi — {n} çerez. İndirmelerde artık bu çerezler kullanılıyor.",
    cookieCurrentUploaded: "Yüklü dosya: {sites} site, {n} çerez",
    cookieCurrentPath: "Dosya: {path} — {sites} site, {n} çerez",
    cookieUploadedAt: "yüklendi {date}",
    cookieUpdatedAt: "son güncelleme {date}",
    cookieCurrentUnreadable: "Ayarlı dosya okunamıyor: {path}",
    cookieYoutubeOk: "YouTube oturumu var ✓",
    cookieYoutubeMissing:
      "Bu dosyada YouTube oturumu görünmüyor — youtube.com'da giriş yapmışken dışa aktardığınızdan emin olun.",
    cookieDeleteBtn: "Çerezleri sil",
    cookieDeleteConfirm: "Yüklenen çerez dosyası silinsin mi?",
    cookieDeleted: "Çerezler silindi.",
    cookieReadFailed: "Dosya okunamadı.",
    cookieErrors: {
      too_large: "Dosya çok büyük (en fazla 5 MB).",
      empty: "Dosya boş.",
      json: "Bu dosya JSON biçiminde — eklentide Netscape (cookies.txt) biçimini seçin.",
      not_netscape: "Bu bir cookies.txt (Netscape biçimi) dosyası değil.",
      no_cookies: "Dosyada hiç çerez bulunamadı.",
      nothing_selected: "En az bir site seçin.",
    },
    queuePosition: "Sırada {n}. — diğer indirmeler bekleniyor",
    itemPreviewPlay: "▶ Oynat",
    itemPreviewClose: "✕ Kapat",
    playerPlay: "Oynat (k)",
    playerPause: "Duraklat (k)",
    playerMute: "Sesi kapat (m)",
    playerUnmute: "Sesi aç (m)",
    playerVolume: "Ses düzeyi",
    playerSeek: "İlerleme",
    playerSpeed: "Oynatma hızı",
    playerSpeedNormal: "Normal",
    playerPip: "Pencere içinde pencere",
    playerFullscreen: "Tam ekran (f)",
    playerExitFullscreen: "Tam ekrandan çık (f)",
    playerSeconds: "sn",
    statsFileOne: "{n} dosya",
    statsFiles: "{n} dosya",
    statsUnknownSite: "Bilinmiyor",
    statsGenericSite: "Doğrudan bağlantı",
    statsOther: "Diğer",
    statsOtherFormat: "Diğer / bilinmiyor",
    statsWindowDay: "Son 14 gün",
    statsWindowWeek: "Son 12 hafta",
    statsWindowMonth: "Son 12 ay",
    statsTotal: "Toplam",
    statsSince: "{date} tarihinden beri",
    statsDiskFree: "Boş alan",
    statsDiskOf: "Disk: {total}",
    statsDiskDownloads: "MediaGrab indirmeleri",
    statsDiskOther: "Diğer dosyalar",
    statsDiskUnavailable: "Disk bilgisi okunamadı.",
    statsEmpty: "Bu dönemde indirme yok.",
    statsBackfilling: "Mevcut indirmeler sayılıyor…",
    statsNote: "Sonradan silinen dosyalar da sayılmaya devam eder. Bu özellik gelmeden önce silinmiş olanlar sayılamadı.",
    statsResetConfirm: "Tüm istatistikler silinsin mi? İndirilen dosyalara dokunulmaz.",
    statsLoadFailed: "İstatistikler yüklenemedi: ",
    errProbeFailed: "Çözümlenemedi",
    errDownloadFailed: "İndirme başlatılamadı",
    errNetwork: "Ağ hatası: ",
    errStatusFailed: "Durum alınamadı",
    errUnknown: "Bilinmeyen hata",
    errTechnicalDetail: "Teknik detay",
    errAgeRestricted: "Bu video yaş kısıtlı, giriş yapılmış bir hesap gerektiriyor.",
    errFormatUnavailable: "Seçtiğiniz biçim bu video için alınamadı. MP3'ü veya bir video seçeneğini deneyin.",
    errCookiesExpired:
      "YouTube çerezleriniz artık geçersiz — büyük ihtimalle tarayıcıda yenilendiler. Gizli pencere yöntemiyle yeni bir cookies.txt alıp yükleyin.",
    errAgeVerification:
      "Çerezleriniz çalışıyor, ama YouTube bu hesap için yaş doğrulaması istiyor. Bunu YouTube/Google hesabınızdan yapmanız gerekiyor; yeni bir cookies.txt bunu çözmez.",
    errCookieHintOff: "Giriş yapılmış bir hesabın çerezleriyle indirilebilir:",
    errCookieHintOn:
      "Çerezleriniz ayarlı ama işe yaramadı: süreleri dolmuş olabilir ya da bu hesap içeriğe erişemiyor. Yeni bir cookies.txt yüklemeyi deneyin:",
    errCookieSettingsLink: "Ayarlar → Çerezler",
    errBrowserCookies: "Çerezler tarayıcıdan okunamadı.",
    errBotCheck: "Site bot doğrulaması istiyor, bu video şu an indirilemiyor.",
    errPrivate: "Bu video gizli/özel — herkese açık değil.",
    errMembersOnly: "Bu içerik yalnızca kanal üyelerine özel.",
    errGeoRestricted: "Bu içerik bulunduğunuz ülkede kullanılamıyor (bölgesel kısıtlama).",
    errBlocked: "Site isteği reddetti (muhtemelen bot koruması).",
    errRemoved: "Bu video artık mevcut değil veya kaldırılmış.",
    errUnsupportedSite: "Bu link tanınan bir siteden değil ya da desteklenmiyor.",
    errInsufficientDisk: "Diskte yeterli boş alan yok. Yer açıp tekrar deneyin.",
    errNetworkIssue: "Ağ bağlantısı sorunu — internet bağlantınızı kontrol edip tekrar deneyin.",
    historyEmpty: "Henüz indirme yok",
    historyNoMatches: "Aramayla eşleşen indirme yok",
    historyAllChannels: "Tüm kanallar",
    historyAllTypes: "Tüm türler",
    historyDownload: "Klasörde göster",
    historyDelete: "Sil",
    historyDeleteFailed: "Silinemedi",
    historyClearConfirm: "Tüm indirme geçmişi diskten kalıcı olarak silinsin mi?",
    historyDeleteConfirm: "Bu dosya diskten kalıcı olarak silinsin mi?",
    channelRemoveConfirm: "Bu kanal takipten çıkarılsın mı?",
    historyClearFailed: "Geçmiş temizlenemedi",
    videoWord: "video",
    playlistRange: "Aralık:",
    playlistBulkHint: "Toplu indirmede her video için en iyi kalite seçilir; tek tek tıklayarak kalite seçebilirsiniz.",
    playlistConfirm: "{n} video kuyruğa eklenecek. Devam edilsin mi?",
    playlistQueued: "{n} video kuyruğa eklendi — altta ilerlemelerini takip edebilirsiniz.",
    backToPlaylist: "← Playlist'e dön",
    locale: "tr-TR",
    channelCheckNow: "Şimdi kontrol et",
    channelRemove: "Kaldır",
    channelAddFailed: "Kanal eklenemedi",
    channelModeAutoBadge: "OTOMATİK",
    channelModeNotifyBadge: "BİLDİR",
    channelLastChecked: "Son kontrol",
    channelNeverChecked: "Henüz kontrol edilmedi",
    channelCheckFailed: "Son kontrol başarısız",
    ytdlpChecking: "Kontrol ediliyor...",
    ytdlpCheckFailed: "Sürüm bilgisi alınamadı (internet bağlantınızı kontrol edin)",
    mgReleaseNotes: "Sürüm notları →",
    mgUpdateDocker:
      "docker-compose.yml dosyanızın bulunduğu klasörde şu iki komutu çalıştırın. Ayarlarınız, çerezleriniz ve indirdikleriniz ./data/ klasöründe kalır.",
    mgUpdateDockerBuild:
      "Compose dosyanız image: yerine build: . kullanıyorsa (repodan elle kurulum) bunun yerine:",
    mgUpdateInstaller: "MediaGrabSetup.exe'yi çalıştırıp \"Onar / Güncelle\"yi seçin. Elinizde yoksa son sürümü indirin:",
    mgDownloadInstaller: "MediaGrabSetup.exe (son sürüm)",
    mgUpdateSource:
      "Proje klasöründe, sanal ortam etkinken şunları çalıştırın, sonra MediaGrab'ı yeniden başlatın:",
    ytdlpUpToDate: "Güncel",
    ytdlpUpdateAvailable: "Güncelleme mevcut",
    ytdlpInstalledLabel: "Kurulu sürüm",
    ytdlpLatestLabel: "Güncel sürüm",
    ytdlpUpdateNowBtn: "Şimdi Güncelle",
    ytdlpUpdating: "Güncelleniyor...",
    ytdlpUpdateSuccess: "Güncellendi, sunucu yeniden başlatılıyor...",
    ytdlpUpdateFailed: "Güncelleme başarısız oldu",
    ytdlpManualToggle: "veya elle güncelleyin",
    ytdlpInstructionsTitle: "Nasıl güncellenir?",
    ytdlpStep1: "1. Proje klasöründe bir terminal açın",
    ytdlpStep2: "2. Sanal ortamı etkinleştirin",
    ytdlpStep2Win: "Windows (PowerShell):",
    ytdlpStep2Unix: "macOS / Linux:",
    ytdlpStep3: "3. Şu komutu çalıştırın:",
    ytdlpStep4: "4. MediaGrab'ı kapatıp yeniden başlatın",
    ytdlpCopyBtn: "Kopyala",
    ytdlpCopied: "Kopyalandı ✓",
    ffmpegInstalled: "Kurulu",
    ffmpegNotFound: "Bulunamadı",
    ffmpegMissing: "yok",
    ffmpegInstallTitle: "Nasıl kurulur?",
    ffmpegUpdateTitle: "Nasıl güncellenir?",
    ffmpegYourSystem: "sisteminiz",
    ffmpegRestartNote: "Kurulumdan sonra MediaGrab'ı kapatıp yeniden açın (PATH güncellemesi için).",
    ffmpegDockerNote: "Docker imajıyla birlikte gelir; imaj güncellendiğinde o da güncellenir.",
    ffmpegBundledNote: "MediaGrab ile birlikte gelir; MediaGrab güncellendiğinde o da güncellenir.",
    downloadDirDefaultTag: "(varsayılan)",
    downloadDirSaved: "Kaydedildi. Yeni indirmeler bu klasöre gidecek; öncekiler eski yerinde kaldı.",
    downloadDirResetDone: "Varsayılan klasöre dönüldü. Yeni indirmeler oraya gidecek.",
    downloadDirPickerOpen: "Klasör seçme penceresi açıldı (tarayıcının arkasında kalmış olabilir)…",
    downloadDirCloud: "Uyarı: bu klasör {service} ile eşitleniyor gibi görünüyor. İndirdiğiniz her video internete yüklenir ve indirme sırasında dosya kilitlenmeleri olabilir.",
    downloadDirErrRelative: "Tam bir klasör yolu girin (ör. D:\\Videolar).",
    downloadDirErrInsideApp: "Bu klasör MediaGrab'ın kendi program klasörünün içinde; güncellemede ya da kaldırmada silinebilir. Başka bir klasör seçin.",
    downloadDirErrNotFolder: "Bu yol bir dosyayı gösteriyor, klasörü değil.",
    downloadDirErrNotWritable: "Bu klasöre yazılamıyor (izin yok, disk dolu ya da sürücü çıkarılmış olabilir).",
    downloadDirErrNotAllowed: "Bu klasör yalnızca MediaGrab'ın kurulu olduğu bilgisayardan değiştirilebilir.",
    downloadDirErrPicker: "Klasör seçme penceresi açılamadı. Yolu elle yazabilirsiniz.",
    depsUpdatesAvailable: "paket güncellenebilir",
    depsUpdateBtn: "Tümünü Güncelle",
    ytdlpCreditText: "yt-dlp, açık kaynak katkıda bulunanlar tarafından geliştirilip sürdürülüyor.",
    ytdlpCreditLink: "GitHub'da teşekkür edin →",
    jsRuntimeLabel: "JavaScript çalışma ortamı (YouTube için)",
    jsRuntimeOk: "Hazır",
    jsRuntimeMissing: "Eksik",
    jsRuntimeMissingHint:
      "Bu olmadan YouTube'da bazı biçimler eksik kalabilir; yaş sınırlı veya giriş gerektiren videolar çerezlerle bile inmeyebilir. Aşağıdaki \"Şimdi Güncelle\" ile kurulur.",
    jsRuntimeMissingHintDocker:
      "Bu olmadan YouTube'da bazı biçimler eksik kalabilir; yaş sınırlı veya giriş gerektiren videolar çerezlerle bile inmeyebilir. Düzeltmek için Docker imajını güncelleyin.",
    settingsRemoteAccessRestartNote: "Ayar uygulanıyor, sunucu yeniden başlatılıyor...",
    settingsHomeServerRestartNote: "Ayar uygulanıyor, sunucu yeniden başlatılıyor...",
    settingsRemoteAccessPasswordTooShort: "Şifre en az 8 karakter olmalı.",
    settingsRemoteAccessPasswordsDontMatch: "Yeni şifreler eşleşmiyor.",
    settingsRemoteAccessCurrentPasswordRequired: "Mevcut şifrenizi girin.",
    settingsRemoteAccessWrongCurrentPassword: "Mevcut şifre yanlış.",
    settingsRemoteAccessPasswordSaved: "Şifre kaydedildi.",
    settingsRemoteAccessStorageSaved: "Depolama ayarı kaydedildi.",
    settingsSpeedLimitInvalid: "Geçerli bir hız girin (en az 1 MB/s).",
    settingsBackupImported: "İçe aktarıldı. Sayfa yenileniyor...",
    settingsBackupInvalidFile: "Bu dosya okunamadı - geçerli bir MediaGrab yedek dosyası olduğundan emin olun.",
    settingsRemoteAccessLoggedOut: "Çıkış yapıldı.",
    settingsRemoteAccessThisDevice: "Bu cihaz",
    settingsRemoteAccessSetPasswordBtn: "Şifreyi Kaydet",
    settingsRemoteAccessUpdatePasswordBtn: "Şifreyi Güncelle",
    settingsRemoteAccessRevokeBtn: "Çıkış yaptır",
    settingsRemoteAccessCopied: "Kopyalandı ✓",
  },
  en: {
    resolveBtn: "Resolve",
    resolveBtnBusy: "...",
    sectionAudio: "Audio",
    sectionAudioTrack: "Audio Track",
    audioTrackHint: "This video has more than one language/dub. Pick more than one and they're all added as separate, selectable audio tracks in the file (which becomes .mkv)",
    audioTrackDefaultSuffix: "(original)",
    // NOTE: ISO 639-1 code -> English language name, sourced from pycountry +
    // Babel (see docs/language-codes.en.md) for the audio-track chip tooltip.
    audioTrackNames: {
      aa: "Afar",
      ab: "Abkhazian",
      ae: "Avestan",
      af: "Afrikaans",
      ak: "Akan",
      am: "Amharic",
      an: "Aragonese",
      ar: "Arabic",
      as: "Assamese",
      av: "Avaric",
      ay: "Aymara",
      az: "Azerbaijani",
      ba: "Bashkir",
      be: "Belarusian",
      bg: "Bulgarian",
      bi: "Bislama",
      bm: "Bambara",
      bn: "Bangla",
      bo: "Tibetan",
      br: "Breton",
      bs: "Bosnian",
      ca: "Catalan",
      ce: "Chechen",
      ch: "Chamorro",
      co: "Corsican",
      cr: "Cree",
      cs: "Czech",
      cu: "Church Slavic",
      cv: "Chuvash",
      cy: "Welsh",
      da: "Danish",
      de: "German",
      dv: "Divehi",
      dz: "Dzongkha",
      ee: "Ewe",
      el: "Greek",
      en: "English",
      eo: "Esperanto",
      es: "Spanish",
      et: "Estonian",
      eu: "Basque",
      fa: "Persian",
      ff: "Fula",
      fi: "Finnish",
      fj: "Fijian",
      fo: "Faroese",
      fr: "French",
      fy: "Western Frisian",
      ga: "Irish",
      gd: "Scottish Gaelic",
      gl: "Galician",
      gn: "Guarani",
      gu: "Gujarati",
      gv: "Manx",
      ha: "Hausa",
      he: "Hebrew",
      hi: "Hindi",
      ho: "Hiri Motu",
      hr: "Croatian",
      ht: "Haitian Creole",
      hu: "Hungarian",
      hy: "Armenian",
      hz: "Herero",
      ia: "Interlingua",
      id: "Indonesian",
      ie: "Interlingue",
      ig: "Igbo",
      ii: "Sichuan Yi",
      ik: "Inupiaq",
      io: "Ido",
      is: "Icelandic",
      it: "Italian",
      iu: "Inuktitut",
      ja: "Japanese",
      jv: "Javanese",
      ka: "Georgian",
      kg: "Kongo",
      ki: "Kikuyu",
      kj: "Kuanyama",
      kk: "Kazakh",
      kl: "Kalaallisut",
      km: "Khmer",
      kn: "Kannada",
      ko: "Korean",
      kr: "Kanuri",
      ks: "Kashmiri",
      ku: "Kurdish",
      kv: "Komi",
      kw: "Cornish",
      ky: "Kyrgyz",
      la: "Latin",
      lb: "Luxembourgish",
      lg: "Ganda",
      li: "Limburgish",
      ln: "Lingala",
      lo: "Lao",
      lt: "Lithuanian",
      lu: "Luba-Katanga",
      lv: "Latvian",
      mg: "Malagasy",
      mh: "Marshallese",
      mi: "Māori",
      mk: "Macedonian",
      ml: "Malayalam",
      mn: "Mongolian",
      mr: "Marathi",
      ms: "Malay",
      mt: "Maltese",
      my: "Burmese",
      na: "Nauru",
      nb: "Norwegian Bokmål",
      nd: "North Ndebele",
      ne: "Nepali",
      ng: "Ndonga",
      nl: "Dutch",
      nn: "Norwegian Nynorsk",
      no: "Norwegian",
      nr: "South Ndebele",
      nv: "Navajo",
      ny: "Nyanja",
      oc: "Occitan",
      oj: "Ojibwa",
      om: "Oromo",
      or: "Odia",
      os: "Ossetic",
      pa: "Punjabi",
      pi: "Pali",
      pl: "Polish",
      ps: "Pashto",
      pt: "Portuguese",
      qu: "Quechua",
      rm: "Romansh",
      rn: "Rundi",
      ro: "Romanian",
      ru: "Russian",
      rw: "Kinyarwanda",
      sa: "Sanskrit",
      sc: "Sardinian",
      sd: "Sindhi",
      se: "Northern Sami",
      sg: "Sango",
      sh: "Serbo-Croatian",
      si: "Sinhala",
      sk: "Slovak",
      sl: "Slovenian",
      sm: "Samoan",
      sn: "Shona",
      so: "Somali",
      sq: "Albanian",
      sr: "Serbian",
      ss: "Swati",
      st: "Southern Sotho",
      su: "Sundanese",
      sv: "Swedish",
      sw: "Swahili",
      ta: "Tamil",
      te: "Telugu",
      tg: "Tajik",
      th: "Thai",
      ti: "Tigrinya",
      tk: "Turkmen",
      tl: "Tagalog",
      tn: "Tswana",
      to: "Tongan",
      tr: "Turkish",
      ts: "Tsonga",
      tt: "Tatar",
      tw: "Twi",
      ty: "Tahitian",
      ug: "Uyghur",
      uk: "Ukrainian",
      ur: "Urdu",
      uz: "Uzbek",
      ve: "Venda",
      vi: "Vietnamese",
      vo: "Volapük",
      wa: "Walloon",
      wo: "Wolof",
      xh: "Xhosa",
      yi: "Yiddish",
      yo: "Yoruba",
      za: "Zhuang",
      zh: "Chinese",
      zu: "Zulu",
    },
    sectionVideo: "Video",
    sectionSubtitle: "Subtitles",
    subtitleHint: "Downloads together with the video you pick, using the same filename",
    subtitleAutoSuffix: "(auto)",
    noVideoFormats: "No video options found",
    sectionTranscript: "Transcript",
    transcriptDownload: "Download transcript (.txt)",
    transcriptManual: "from manual subtitles",
    transcriptAuto: "from auto-generated captions",
    transcriptTimestamps: "With timestamps",
    transcriptBundleWithMedia: "Include with video/audio download",
    quickBestAudio: "♪ Best Audio",
    audioUnavailableDesc: "no separate audio stream available for this video",
    noticeAgeVerification:
      "YouTube wants this account to be age-verified, so only limited, low-quality formats were available. First try opening the video on YouTube with the same account and confirming the content warning; if that doesn't help, verify the account's age on YouTube/Google or upload cookies from an age-verified account.",
    quickBestVideo: "▶ Best Video",
    descriptionTitle: "Description",
    descriptionShowMore: "Show more",
    descriptionShowLess: "Show less",
    sectionOptions: "Options",
    audio: {
      opus: { label: "Opus", desc: "best quality · not re-encoded" },
      m4a: { label: "M4A", desc: "AAC · Apple-compatible · not re-encoded" },
      mp3: { label: "MP3", desc: "plays everywhere · quality loss" },
    },
    states: {
      basliyor: "Starting...",
      indiriliyor: "Downloading...",
      isleniyor: "Processing (ffmpeg)...",
      bitti: "Done",
      hata: "Error",
      iptal: "Cancelled",
    },
    downloadBtn: "Show in folder",
    downloadToDeviceBtn: "Download to Device",
    saveToFolderBtn: "Save to Folder",
    savedToFolder: "Saved ✓",
    savedAndRemoved: "Saved — MediaGrab's copy was removed",
    saveToFolderFailed: "Could not save: ",
    downloadStartedNote: "Download started — track its progress below.",
    dockDismiss: "Dismiss",
    dockCancel: "Cancel download",
    etaLabel: "ETA",
    cookieSaved: "Saved.",
    cookieTestOk: "Working — {n} cookie(s) loaded.",
    cookieTestNone: "No cookie source configured.",
    cookieTestUnsupported:
      "The saved browser ({browser}) can't be read on this system, so cookies aren't being used. Choose Firefox and save, or upload a cookies.txt.",
    cookieBrowserUnsupported:
      "The saved browser ({browser}) isn't supported on this system, so cookies aren't being used right now. Choose Firefox and save, or use the \"cookies.txt file\" option.",
    cookieTestFailed: "Could not read cookies",
    diagCopied: "Copied ✓ — paste it into your bug report.",
    diagCopyManual: "Couldn't copy automatically — the text below is selected, press Ctrl+C (⌘C on a Mac) to copy it.",
    cookieReviewTitle: "This file has cookies for {n} site(s). Choose which to keep:",
    cookieReviewHint: "Only the ticked sites' cookies are saved; the rest are never written to disk.",
    cookieCount: "{n} cookie(s)",
    cookieUploadSaveBtn: "Save selected",
    cookieUploadCancelBtn: "Cancel",
    cookieUploaded: "Saved — {n} cookie(s). Downloads now use these cookies.",
    cookieCurrentUploaded: "Uploaded file: {sites} site(s), {n} cookie(s)",
    cookieCurrentPath: "File: {path} — {sites} site(s), {n} cookie(s)",
    cookieUploadedAt: "uploaded {date}",
    cookieUpdatedAt: "last updated {date}",
    cookieCurrentUnreadable: "The configured file can't be read: {path}",
    cookieYoutubeOk: "YouTube session found ✓",
    cookieYoutubeMissing:
      "No YouTube session in this file — make sure you exported it while signed in on youtube.com.",
    cookieDeleteBtn: "Delete cookies",
    cookieDeleteConfirm: "Delete the uploaded cookie file?",
    cookieDeleted: "Cookies deleted.",
    cookieReadFailed: "Couldn't read the file.",
    cookieErrors: {
      too_large: "The file is too large (5 MB max).",
      empty: "The file is empty.",
      json: "This file is JSON — choose the Netscape (cookies.txt) format in the extension.",
      not_netscape: "This isn't a cookies.txt (Netscape format) file.",
      no_cookies: "No cookies found in the file.",
      nothing_selected: "Select at least one site.",
    },
    queuePosition: "{n}. in queue — waiting for other downloads",
    itemPreviewPlay: "▶ Play",
    itemPreviewClose: "✕ Close",
    playerPlay: "Play (k)",
    playerPause: "Pause (k)",
    playerMute: "Mute (m)",
    playerUnmute: "Unmute (m)",
    playerVolume: "Volume",
    playerSeek: "Seek",
    playerSpeed: "Playback speed",
    playerSpeedNormal: "Normal",
    playerPip: "Picture in picture",
    playerFullscreen: "Full screen (f)",
    playerExitFullscreen: "Exit full screen (f)",
    playerSeconds: "s",
    statsFileOne: "{n} file",
    statsFiles: "{n} files",
    statsUnknownSite: "Unknown",
    statsGenericSite: "Direct link",
    statsOther: "Other",
    statsOtherFormat: "Other / unknown",
    statsWindowDay: "Last 14 days",
    statsWindowWeek: "Last 12 weeks",
    statsWindowMonth: "Last 12 months",
    statsTotal: "All time",
    statsSince: "since {date}",
    statsDiskFree: "Free space",
    statsDiskOf: "Disk: {total}",
    statsDiskDownloads: "MediaGrab downloads",
    statsDiskOther: "Other files",
    statsDiskUnavailable: "Couldn't read disk information.",
    statsEmpty: "No downloads in this period.",
    statsBackfilling: "Counting the downloads already on disk…",
    statsNote: "Files deleted later still count. Files deleted before this feature existed couldn't be counted.",
    statsResetConfirm: "Delete all statistics? Downloaded files are not touched.",
    statsLoadFailed: "Couldn't load statistics: ",
    errProbeFailed: "Could not resolve",
    errDownloadFailed: "Could not start download",
    errNetwork: "Network error: ",
    errStatusFailed: "Could not get status",
    errUnknown: "Unknown error",
    errTechnicalDetail: "Technical detail",
    errAgeRestricted: "This video is age-restricted and requires a signed-in account.",
    errFormatUnavailable: "The format you picked isn't available for this video. Try MP3 or one of the video options.",
    errCookiesExpired:
      "Your YouTube cookies are no longer valid — most likely the browser rotated them. Get a fresh cookies.txt using the private-window method and upload it.",
    errAgeVerification:
      "Your cookies work, but YouTube wants this account to be age-verified. That has to be done in your YouTube/Google account; a new cookies.txt won't fix it.",
    errCookieHintOff: "It can be downloaded with a signed-in account's cookies:",
    errCookieHintOn:
      "Your cookies are set but didn't help: they may have expired, or this account can't access the content. Try uploading a fresh cookies.txt:",
    errCookieSettingsLink: "Settings → Cookies",
    errBrowserCookies: "Couldn't read cookies from the browser.",
    errBotCheck: "The site is asking for bot verification - this video can't be downloaded right now.",
    errPrivate: "This video is private and not publicly accessible.",
    errMembersOnly: "This content is members-only.",
    errGeoRestricted: "This content isn't available in your country (geo-restricted).",
    errBlocked: "The site refused the request (likely bot protection).",
    errRemoved: "This video is no longer available or has been removed.",
    errUnsupportedSite: "This link isn't from a recognized or supported site.",
    errInsufficientDisk: "Not enough free disk space. Make some room and try again.",
    errNetworkIssue: "Network connection issue — check your internet connection and try again.",
    historyEmpty: "No downloads yet",
    historyNoMatches: "No downloads match your search",
    historyAllChannels: "All channels",
    historyAllTypes: "All types",
    historyDownload: "Show in folder",
    historyDelete: "Delete",
    historyDeleteFailed: "Could not delete",
    historyClearConfirm: "Permanently delete all download history from disk?",
    historyDeleteConfirm: "Permanently delete this file from disk?",
    channelRemoveConfirm: "Stop following this channel?",
    historyClearFailed: "Could not clear history",
    videoWord: "videos",
    playlistRange: "Range:",
    playlistBulkHint: "Bulk downloads always take the best quality; click a single video to choose a specific one.",
    playlistConfirm: "{n} video(s) will be queued. Continue?",
    playlistQueued: "Queued {n} video(s) — follow their progress below.",
    backToPlaylist: "← Back to playlist",
    locale: "en-US",
    channelCheckNow: "Check now",
    channelRemove: "Remove",
    channelAddFailed: "Could not add channel",
    channelModeAutoBadge: "AUTO",
    channelModeNotifyBadge: "NOTIFY",
    channelLastChecked: "Last checked",
    channelNeverChecked: "Not checked yet",
    channelCheckFailed: "Last check failed",
    ytdlpChecking: "Checking...",
    ytdlpCheckFailed: "Couldn't check the version (check your internet connection)",
    mgReleaseNotes: "Release notes →",
    mgUpdateDocker:
      "Run these two commands in the folder that has your docker-compose.yml. Your settings, cookies and downloads stay in ./data/.",
    mgUpdateDockerBuild: "If your compose file uses build: . instead of image: (a manual install from the repo), run this instead:",
    mgUpdateInstaller: "Run MediaGrabSetup.exe and choose \"Repair / Update\". If you don't have it anymore, download the latest:",
    mgDownloadInstaller: "MediaGrabSetup.exe (latest)",
    mgUpdateSource: "In the project folder, with the virtual environment active, run these, then restart MediaGrab:",
    ytdlpUpToDate: "Up to date",
    ytdlpUpdateAvailable: "Update available",
    ytdlpInstalledLabel: "Installed version",
    ytdlpLatestLabel: "Latest version",
    ytdlpUpdateNowBtn: "Update Now",
    ytdlpUpdating: "Updating...",
    ytdlpUpdateSuccess: "Updated, restarting the server...",
    ytdlpUpdateFailed: "Update failed",
    ytdlpManualToggle: "or update manually",
    ytdlpInstructionsTitle: "How to update",
    ytdlpStep1: "1. Open a terminal in the project folder",
    ytdlpStep2: "2. Activate the virtual environment",
    ytdlpStep2Win: "Windows (PowerShell):",
    ytdlpStep2Unix: "macOS / Linux:",
    ytdlpStep3: "3. Run this command:",
    ytdlpStep4: "4. Close and restart MediaGrab",
    ytdlpCopyBtn: "Copy",
    ytdlpCopied: "Copied ✓",
    ffmpegInstalled: "Installed",
    ffmpegNotFound: "Not found",
    ffmpegMissing: "missing",
    ffmpegInstallTitle: "How to install",
    ffmpegUpdateTitle: "How to update",
    ffmpegYourSystem: "your system",
    ffmpegRestartNote: "Restart MediaGrab after installing, so it picks up the updated PATH.",
    ffmpegDockerNote: "Bundled with the Docker image; it's updated whenever the image is.",
    ffmpegBundledNote: "Comes with MediaGrab; it's updated whenever MediaGrab is.",
    downloadDirDefaultTag: "(default)",
    downloadDirSaved: "Saved. New downloads will go to this folder; earlier ones stay where they were.",
    downloadDirResetDone: "Back to the default folder. New downloads will go there.",
    downloadDirPickerOpen: "The folder picker is open (it may be behind your browser)…",
    downloadDirCloud: "Warning: this folder seems to be synced by {service}. Every video you download gets uploaded, and files can get locked mid-download.",
    downloadDirErrRelative: "Enter a full folder path (e.g. D:\\Videos).",
    downloadDirErrInsideApp: "This folder is inside MediaGrab's own program folder; an update or uninstall could delete it. Choose another folder.",
    downloadDirErrNotFolder: "This path points to a file, not a folder.",
    downloadDirErrNotWritable: "Can't write to this folder (no permission, disk full, or the drive was removed).",
    downloadDirErrNotAllowed: "This folder can only be changed on the computer MediaGrab is installed on.",
    downloadDirErrPicker: "Couldn't open the folder picker. You can type the path instead.",
    depsUpdatesAvailable: "packages can be updated",
    depsUpdateBtn: "Update All",
    ytdlpCreditText: "yt-dlp is built and maintained by its open-source contributors.",
    ytdlpCreditLink: "Say thanks on GitHub →",
    jsRuntimeLabel: "JavaScript runtime (for YouTube)",
    jsRuntimeOk: "Ready",
    jsRuntimeMissing: "Missing",
    jsRuntimeMissingHint:
      "Without it some YouTube formats may be missing, and age-restricted or sign-in-only videos may fail even with cookies. \"Update Now\" below installs it.",
    jsRuntimeMissingHintDocker:
      "Without it some YouTube formats may be missing, and age-restricted or sign-in-only videos may fail even with cookies. Update the Docker image to fix this.",
    settingsRemoteAccessRestartNote: "Applying the setting, restarting the server...",
    settingsHomeServerRestartNote: "Applying the setting, restarting the server...",
    settingsRemoteAccessPasswordTooShort: "Password must be at least 8 characters.",
    settingsRemoteAccessPasswordsDontMatch: "The new passwords don't match.",
    settingsRemoteAccessCurrentPasswordRequired: "Enter your current password.",
    settingsRemoteAccessWrongCurrentPassword: "Current password is incorrect.",
    settingsRemoteAccessPasswordSaved: "Password saved.",
    settingsRemoteAccessStorageSaved: "Storage setting saved.",
    settingsSpeedLimitInvalid: "Enter a valid speed (at least 1 MB/s).",
    settingsBackupImported: "Imported. Reloading...",
    settingsBackupInvalidFile: "Couldn't read this file - make sure it's a valid MediaGrab backup file.",
    settingsRemoteAccessLoggedOut: "Logged out.",
    settingsRemoteAccessThisDevice: "This device",
    settingsRemoteAccessSetPasswordBtn: "Save Password",
    settingsRemoteAccessUpdatePasswordBtn: "Update Password",
    settingsRemoteAccessRevokeBtn: "Sign out",
    settingsRemoteAccessCopied: "Copied ✓",
  },
};

// NOTE: read straight off the server-rendered <html lang> attribute. The
// server already resolved the language (?lang= > cookie > system locale) and
// rendered the page's static text in it, so this is both synchronous - no
// race with an async /api/locale fetch, which used to leave t() undefined -
// and guaranteed to agree with what's on screen.
let lang = document.documentElement.lang === "en" ? "en" : "tr";
let lastProbe = null; // { url, info } - currently shown single-video detail
let lastPlaylist = null; // { url, data } - currently shown playlist listing
let lastHistory = [];
let selectedSubtitles = new Set(); // checked subtitle language codes - go along with the next video download
// NOTE: a Set, not a single value - picking more than one language embeds all
// of them as separate, selectable audio tracks in one file (video only; see
// downloader.py). Empty means yt-dlp's own default (the original track).
let selectedAudioLangs = new Set();
let defaultAudioLang = ""; // the user's saved preference from /settings - applied when a video actually has that language
let transcriptBundleSelected = false; // whether the transcript should also download alongside the next audio/video download
let lastPending = [];
let lastChannels = [];

function t() {
  return I18N[lang];
}

function setLang(newLang) {
  if (newLang === lang) return;
  // NOTE: every page's static text is rendered server-side now, so switching
  // language reloads rather than re-translating in place. That keeps ONE copy
  // of those strings (in i18n.py) instead of a second JS copy that could
  // drift, and it's what makes the first paint correct - the cookie is what
  // a later bare-URL visit (bookmark, PWA launch) reads to pick the language
  // before any JS runs.
  document.cookie = `${LANG_KEY}=${newLang};path=/;max-age=31536000;samesite=lax`;
  const url = new URL(window.location.href);
  url.searchParams.set("lang", newLang);
  window.location.href = url.toString();
}

function withLang(path) {
  return `${path}${path.includes("?") ? "&" : "?"}lang=${lang}`;
}

function fmtDuration(seconds) {
  seconds = Math.floor(seconds || 0);
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${m}:${String(s).padStart(2, "0")}`;
}

// NOTE: yt-dlp's own error messages are raw and technical (English, often
// site-internal wording like "Sign in to confirm your age"). This maps
// common patterns to a short, actionable message in the user's language;
// the original raw message is still shown as a collapsible detail so power
// users/bug reports keep the specifics.
// NOTE: cookieFix marks the errors a signed-in account's cookies can solve -
// those get a pointer to Settings -> Cookies (see cookieHintHtml). The first
// two are yt-dlp's own side messages, which downloader.probe() appends to the
// error when it saw them: they're listed FIRST because they arrive together
// with the generic "sign in to confirm your age", and are the more precise
// explanation of the two.
const ERROR_PATTERNS = [
  { patterns: ["account cookies are no longer valid"], key: "errCookiesExpired" },
  {
    // NOTE: a broken "From browser" source fails EVERY video, not just the
    // sign-in ones - the first message is Chrome on Windows (seen on a real
    // machine), the rest are the other "couldn't read the browser" failures.
    patterns: [
      "could not copy chrome cookie database",
      "failed to decrypt with dpapi",
      // NOTE: yt-dlp's "could not find <browser> cookies database in <path>"
      // (cookies.py) - one substring covers every browser it names.
      "cookies database in",
      "could not find safari cookies database",
    ],
    key: "errBrowserCookies",
    cookieFix: true,
  },
  { patterns: ["requiring account age-verification"], key: "errAgeVerification" },
  { patterns: ["sign in to confirm your age", "inappropriate for some users"], key: "errAgeRestricted", cookieFix: true },
  { patterns: ["confirm you're not a bot", "confirm you are not a bot"], key: "errBotCheck", cookieFix: true },
  { patterns: ["private video", "this video is private"], key: "errPrivate", cookieFix: true },
  { patterns: ["requested format is not available"], key: "errFormatUnavailable" },
  { patterns: ["members-only", "join this channel"], key: "errMembersOnly", cookieFix: true },
  { patterns: ["not available in your country", "not made this video available in your country", "geo restrict"], key: "errGeoRestricted" },
  { patterns: ["cloudflare", "http error 403"], key: "errBlocked" },
  { patterns: ["video unavailable", "has been removed"], key: "errRemoved" },
  { patterns: ["unsupported url", "no extractor"], key: "errUnsupportedSite" },
  { patterns: ["yetersiz disk alani"], key: "errInsufficientDisk" },
  {
    // NOTE: "unable to download webpage" alone is yt-dlp's generic wrapper
    // for ANY fetch failure (DNS, timeout, refused, actual 403s, actual
    // Cloudflare blocks...) - it's not itself evidence of bot-blocking, so
    // it must NOT be in errBlocked's list above (that produced a false
    // "site is blocking you" message for a plain DNS failure in testing).
    // It only lands here, paired with genuine network-failure indicators.
    patterns: [
      "timed out",
      "connection refused",
      "failed to establish a new connection",
      "name or service not known",
      "getaddrinfo failed",
      "network is unreachable",
      "no address associated with hostname",
    ],
    key: "errNetworkIssue",
  },
];

function friendlyErrorEntry(raw) {
  if (!raw) return null;
  const lowered = raw.toLowerCase();
  return ERROR_PATTERNS.find((entry) => entry.patterns.some((p) => lowered.includes(p))) || null;
}

function friendlyError(raw) {
  const match = friendlyErrorEntry(raw);
  return match ? t()[match.key] : null;
}

// NOTE: set by loadSettings() on every page - whether ANY cookie source is
// configured decides which hint makes sense ("add cookies" vs "yours didn't
// work"). Pure helper below so the wording logic can be tested under Node.
let cookiesConfigured = false;

function cookieHintHtml(entry, configured, settingsHref) {
  if (!entry || !entry.cookieFix) return "";
  const text = configured ? t().errCookieHintOn : t().errCookieHintOff;
  return `<p class="error-hint">${text} <a href="${escapeHtml(settingsHref)}">${t().errCookieSettingsLink}</a></p>`;
}

function showError(message, raw) {
  // NOTE: back to the simple, page-local inline error in the resolve card
  // (the cross-page toast was removed - it fought a CSS specificity bug
  // that made "hidden" not actually hide it, and was more complexity than
  // this needed). Resolve/download-start errors always happen on the home
  // page where `card` exists; background job failures still show in the
  // dock row itself (see dockRowHtml), just without a separate popup.
  if (!card) return;
  const entry = friendlyErrorEntry(raw || message);
  const friendly = entry ? t()[entry.key] : null;
  const displayMessage = friendly || message;
  if (!displayMessage) return;
  const showDetail = raw && raw !== displayMessage;
  card.classList.remove("hidden");
  card.innerHTML = `
    <div class="error">${escapeHtml(displayMessage)}</div>
    ${cookieHintHtml(entry, cookiesConfigured, `${withLang("/settings")}#cookies`)}
    ${
      showDetail
        ? `<details class="error-detail"><summary>${t().errTechnicalDetail}</summary><pre>${escapeHtml(raw)}</pre></details>`
        : ""
    }`;
}

// NOTE: this escapes quotes too, which the previous textContent/innerHTML
// trick did NOT - innerHTML only escapes & < > when serializing a text node,
// since quotes are harmless in text. But nearly every caller here interpolates
// into an ATTRIBUTE (title="...", data-filename="...", src="..."), where an
// unescaped " closes the attribute early: a video titled 'x" onmouseover="..."'
// injected a live event handler (confirmed in-browser). Titles come from
// arbitrary third-party sites, so they're untrusted input.
const HTML_ESCAPES = { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" };

function escapeHtml(str) {
  return String(str ?? "").replace(/[&<>"']/g, (ch) => HTML_ESCAPES[ch]);
}

// NOTE: subtitle codes can carry a region tag (e.g. "es-419", "pt-BR") that
// audioTrackNames (plain ISO 639-1) doesn't have an entry for - only the
// base language part before the dash is looked up, so the tooltip still
// shows a name instead of nothing.
function languageNameForCode(code) {
  const base = String(code || "").split(/[-_]/)[0].toLowerCase();
  return t().audioTrackNames[base] || "";
}

// NOTE: whether THIS browser is talking to the app from the host machine
// itself (127.0.0.1/::1) or from another device on the LAN - decides whether
// "reveal in explorer" (host-only; opening an OS file explorer on some OTHER
// device's screen would help nobody) or a real file download is the right
// action. Defaults to true (today's only behaviour) until loadClientInfo()
// resolves, and again if it ever fails - the safe fallback either way.
let isLocalClient = true;
// NOTE: true for the host's own browser even in Docker, where isLocalClient
// is false (see _is_same_machine in app.py) - that's the case "Save to
// folder" exists for.
let isSameMachine = false;

async function loadClientInfo() {
  try {
    const res = await fetch("/api/client-info");
    const data = await res.json();
    isLocalClient = data.is_local !== false;
    isSameMachine = data.same_machine === true;
  } catch (err) {
    // NOTE: same tolerance as the rest of this file's best-effort fetches -
    // isLocalClient just stays at its safe default.
  }
}

// NOTE: the File System Access API exists only in Chromium browsers and only
// in a secure context - which plain-HTTP localhost counts as, but a LAN IP
// does not. So this is offered exactly where it's needed (the host's own
// browser in Docker) and nowhere else; Firefox there falls back to a normal
// download, which the server never auto-deletes for the same machine.
function canSaveToFolder() {
  return !isLocalClient && isSameMachine && typeof window.showSaveFilePicker === "function";
}

// NOTE: unlike a plain download link, the picker tells us what the user did:
// cancelling (or closing) it rejects with AbortError and nothing else
// happens. Only after the bytes are fully written to the chosen file does
// the server hear "/saved" - which is the one point where relay mode may
// remove MediaGrab's own copy. A failed or interrupted write never gets
// there (pipeTo rejects, and aborts the half-written file). Dependencies are
// passed in so this can be tested outside a browser.
async function saveFileToFolder(pickSaveFile, fetchFn, url, suggestedName) {
  let handle;
  try {
    handle = await pickSaveFile(suggestedName ? { suggestedName } : {});
  } catch (err) {
    if (err && err.name === "AbortError") return "cancelled";
    throw err;
  }
  const res = await fetchFn(`${url}/download`);
  if (!res.ok || !res.body) throw new Error(String(res.status));
  const writable = await handle.createWritable();
  await res.body.pipeTo(writable);
  const ack = await fetchFn(`${url}/saved`, { method: "POST" });
  const data = ack.ok ? await ack.json().catch(() => ({})) : {};
  return data.deleted ? "removed" : "saved";
}

// NOTE: resolves to what happened - "revealed", "downloaded", or (Save to
// folder) "cancelled" / "saved" / "removed" / "failed" - so callers can
// update their own button or list.
async function revealFile(url, suggestedName) {
  if (isLocalClient) {
    // NOTE: fetch() rather than a plain <a href> navigation - the endpoint
    // just opens the OS file explorer server-side and returns {"ok": true};
    // navigating to it directly would have shown raw JSON in the tab.
    try {
      await fetch(url);
    } catch (err) {
      // best-effort - revealing the file in explorer is a nice-to-have here.
    }
    return "revealed";
  }
  if (canSaveToFolder()) {
    try {
      return await saveFileToFolder((opts) => window.showSaveFilePicker(opts), fetch, url, suggestedName);
    } catch (err) {
      window.alert(t().saveToFolderFailed + (err?.message || err));
      return "failed";
    }
  }
  // NOTE: a real download needs a native browser navigation - fetch() would
  // receive the bytes into JS and just discard them, triggering nothing on
  // screen. The matching /download route (see app.py) sets
  // Content-Disposition: attachment, which is what makes the browser save
  // the file instead of trying to navigate to it inline.
  window.location.href = `${url}/download`;
  return "downloaded";
}

function revealOrDownloadLabel() {
  if (isLocalClient) return t().downloadBtn;
  return canSaveToFolder() ? t().saveToFolderBtn : t().downloadToDeviceBtn;
}

// NOTE: shared by the three places that offer the button (History cards,
// the download dock, the item page) - shows the outcome on the button itself.
function showSaveOutcome(btn, outcome) {
  if (!btn || (outcome !== "saved" && outcome !== "removed")) return;
  btn.textContent = outcome === "removed" ? t().savedAndRemoved : t().savedToFolder;
  btn.disabled = outcome === "removed";
}

async function fetchProbe(url) {
  const res = await fetch("/api/probe", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url }),
  });
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data.detail || t().errProbeFailed);
  }
  return data;
}

function applyDefaultAudioLang(info) {
  // NOTE: only pre-selects when the video actually HAS the saved language -
  // otherwise selectedAudioLangs stays empty and the original plays, exactly
  // as if no default were configured at all.
  if (defaultAudioLang && info.audio_tracks?.some((t) => t.code === defaultAudioLang)) {
    selectedAudioLangs = new Set([defaultAudioLang]);
  }
}

async function probe() {
  const url = urlInput.value.trim();
  if (!url) return;

  probeBtn.disabled = true;
  probeBtn.textContent = t().resolveBtnBusy;
  lastProbe = null;
  lastPlaylist = null;
  selectedSubtitles = new Set();
  selectedAudioLangs = new Set();
  transcriptBundleSelected = false;

  try {
    const data = await fetchProbe(url);
    if (data.type === "playlist") {
      lastPlaylist = { url, data };
      renderPlaylist();
    } else {
      applyDefaultAudioLang(data);
      lastProbe = { url, info: data };
      renderCard(url, data);
    }
  } catch (err) {
    showError(err.message, err.message);
  } finally {
    probeBtn.disabled = false;
    probeBtn.textContent = t().resolveBtn;
  }
}

async function selectPlaylistEntry(entry) {
  card.classList.remove("hidden");
  card.innerHTML = `<div class="progress-status">${t().resolveBtnBusy}</div>`;
  selectedSubtitles = new Set();
  selectedAudioLangs = new Set();
  transcriptBundleSelected = false;
  try {
    const data = await fetchProbe(entry.url);
    applyDefaultAudioLang(data);
    lastProbe = { url: entry.url, info: data };
    renderCard(entry.url, data);
  } catch (err) {
    lastProbe = null;
    showError(err.message, err.message);
  }
}

// NOTE: Opus and M4A keep YouTube's own audio stream as-is, so they need a
// separate audio-only format; MP3 can also be made from a muxed (audio+video)
// one. info.audio_only is false when the probe found no audio-only format at
// all (seen with an age-restricted video and a not-age-verified account) -
// undefined from an older server means "assume yes", today's behaviour.
function audioChoiceAvailable(info, choice) {
  return choice === "mp3" || info.audio_only !== false;
}

function bestAudioChoice(info) {
  return audioChoiceAvailable(info, "opus") ? "opus" : "mp3";
}

function probeNoticesHtml(info) {
  const notices = info.notices || [];
  if (!notices.includes("account_age_verification")) return "";
  return `<p class="cookie-warning preview-notice">${t().noticeAgeVerification}</p>`;
}

function renderCard(url, info) {
  card.classList.remove("hidden");

  const backLink = lastPlaylist
    ? `<a href="#" class="back-to-playlist" id="back-to-playlist">${t().backToPlaylist}</a>`
    : "";

  const thumb = info.thumbnail
    ? `<img src="${escapeHtml(info.thumbnail)}" alt="">`
    : "";

  const audioHtml = ["opus", "m4a", "mp3"]
    .map((choice) => {
      const opt = t().audio[choice];
      const available = audioChoiceAvailable(info, choice);
      return `
    <button class="option" data-kind="audio" data-choice="${choice}"${available ? "" : " disabled"}>
      <span>
        <span class="opt-label">${opt.label}</span><br>
        <span class="opt-desc">${available ? opt.desc : t().audioUnavailableDesc}</span>
      </span>
    </button>`;
    })
    .join("");

  let audioTrackHtml = "";
  if (info.audio_tracks && info.audio_tracks.length > 0) {
    const chipsHtml = info.audio_tracks
      .map((track) => {
        // NOTE: multi-select, like the subtitle chips - but when NOTHING has
        // been explicitly picked yet, the default track is shown as selected
        // anyway, since that's exactly what happens on the backend when
        // audio_langs is empty.
        const isSelected = selectedAudioLangs.size > 0 ? selectedAudioLangs.has(track.code) : track.is_default;
        const suffix = track.is_default ? ` ${t().audioTrackDefaultSuffix}` : "";
        const langName = languageNameForCode(track.code);
        return `<button type="button" class="subtitle-chip audio-track-chip${isSelected ? " selected" : ""}" data-lang="${escapeHtml(track.code)}" data-default="${track.is_default ? "1" : ""}"${langName ? ` title="${escapeHtml(langName)}"` : ""}>${escapeHtml(track.code.toUpperCase())}${suffix}</button>`;
      })
      .join("");
    audioTrackHtml = `
    <div class="section-subtitle">${t().sectionAudioTrack}</div>
    <div class="subtitle-hint">${t().audioTrackHint}</div>
    <div class="subtitle-grid" id="audio-track-grid">${chipsHtml}</div>`;
  }

  let videoHtml = info.video
    .map(
      (f) => `
    <button class="option" data-kind="video" data-choice="${f.format_id}">
      <span>
        <span class="opt-label">${f.label}</span>
      </span>
      <span class="opt-right">${f.vcodec} · ${f.ext} · ${f.size}</span>
    </button>`
    )
    .join("");

  if (!videoHtml) {
    videoHtml = `<div class="opt-desc">${t().noVideoFormats}</div>`;
  }

  let subtitleHtml = "";
  if (info.subtitles && info.subtitles.length > 0) {
    const chipsHtml = info.subtitles
      .map((s) => {
        const choiceVal = `${s.code}:${s.source}`;
        const selected = selectedSubtitles.has(choiceVal) ? " selected" : "";
        const suffix = s.source === "auto" ? ` ${t().subtitleAutoSuffix}` : "";
        const langName = languageNameForCode(s.code);
        return `<button type="button" class="subtitle-chip${selected}" data-choice="${escapeHtml(choiceVal)}"${langName ? ` title="${escapeHtml(langName)}"` : ""}>${escapeHtml(s.code.toUpperCase())}${suffix}</button>`;
      })
      .join("");
    subtitleHtml = `
    <div class="section-subtitle">${t().sectionSubtitle}</div>
    <div class="subtitle-hint">${t().subtitleHint}</div>
    <div class="subtitle-grid">${chipsHtml}</div>`;
  }

  let transcriptHtml = "";
  if (info.transcript) {
    const sourceLabel = info.transcript.source === "auto" ? t().transcriptAuto : t().transcriptManual;
    transcriptHtml = `
    <div class="section-subtitle">${t().sectionTranscript}</div>
    <label class="transcript-timestamp-check">
      <input type="checkbox" id="transcript-timestamps">
      ${t().transcriptTimestamps}
    </label>
    <button type="button" class="option" data-kind="transcript" data-choice="${escapeHtml(info.transcript.code)}:${info.transcript.source}">
      <span>
        <span class="opt-label">${t().transcriptDownload}</span><br>
        <span class="opt-desc">${escapeHtml(info.transcript.code.toUpperCase())} · ${sourceLabel}</span>
      </span>
    </button>
    <button type="button" class="subtitle-chip transcript-bundle-chip${transcriptBundleSelected ? " selected" : ""}" id="transcript-bundle-toggle">
      ${t().transcriptBundleWithMedia}
    </button>`;
  }

  // NOTE: info.video is already sorted best-first (highest height first) by
  // the server, so info.video[0] is exactly "best available quality" without
  // needing to re-sort here.
  const bestVideo = info.video && info.video.length > 0 ? info.video[0] : null;
  const quickHtml = `
    <div class="quick-actions">
      <button type="button" class="quick-btn" data-kind="audio" data-choice="${bestAudioChoice(info)}">${t().quickBestAudio}</button>
      ${
        bestVideo
          ? `<button type="button" class="quick-btn" data-kind="video" data-choice="${bestVideo.format_id}">${t().quickBestVideo}</button>`
          : ""
      }
    </div>`;

  let descriptionHtml = "";
  if (info.description && info.description.trim()) {
    descriptionHtml = `
    <div class="preview-description">
      <div class="section-subtitle">${t().descriptionTitle}</div>
      <div class="description-text" id="description-text">${escapeHtml(info.description)}</div>
      <button type="button" class="description-toggle hidden" id="description-toggle">${t().descriptionShowMore}</button>
    </div>`;
  }

  card.innerHTML = `
    ${backLink}
    <div class="result-layout">
      <div class="result-preview">
        <div class="info-row">
          ${thumb}
          <div class="info-meta">
            <div class="title">${escapeHtml(info.title)}</div>
            <div class="sub">${escapeHtml(info.uploader)} · ${fmtDuration(info.duration)}</div>
          </div>
        </div>
        ${quickHtml}
        ${descriptionHtml}
      </div>
      <div class="result-options">
        <div class="section-title">${t().sectionOptions}</div>
        ${probeNoticesHtml(info)}
        ${audioTrackHtml}
        <div class="format-tabs" id="format-tabs" role="tablist">
          <button type="button" class="format-tab active" data-tab="audio" role="tab" aria-selected="true">${t().sectionAudio}</button>
          <button type="button" class="format-tab" data-tab="video" role="tab" aria-selected="false">${t().sectionVideo}</button>
        </div>
        <div class="format-tab-panels">
          <div class="format-tab-panel active" data-tab-panel="audio">${audioHtml}</div>
          <div class="format-tab-panel" data-tab-panel="video" hidden>${videoHtml}</div>
        </div>
        ${subtitleHtml}
        ${transcriptHtml}
      </div>
    </div>
  `;

  const formatTabs = card.querySelector("#format-tabs");
  if (formatTabs) {
    formatTabs.querySelectorAll(".format-tab").forEach((tabBtn) => {
      tabBtn.addEventListener("click", () => {
        const targetTab = tabBtn.dataset.tab;
        formatTabs.querySelectorAll(".format-tab").forEach((btn) => {
          const active = btn.dataset.tab === targetTab;
          btn.classList.toggle("active", active);
          btn.setAttribute("aria-selected", active ? "true" : "false");
        });
        card.querySelectorAll(".format-tab-panel").forEach((panel) => {
          const active = panel.dataset.tabPanel === targetTab;
          panel.hidden = !active;
          panel.classList.toggle("active", active);
        });
      });
    });
  }

  const descText = card.querySelector("#description-text");
  const descToggle = card.querySelector("#description-toggle");
  if (descText && descToggle) {
    // NOTE: the toggle is only shown when the clamped text actually
    // overflows - a short description has nothing to expand, so the button
    // would just be dead UI.
    if (descText.scrollHeight > descText.clientHeight + 1) {
      descToggle.classList.remove("hidden");
    }
    descToggle.addEventListener("click", () => {
      const expanded = descText.classList.toggle("expanded");
      descToggle.textContent = expanded ? t().descriptionShowLess : t().descriptionShowMore;
    });
  }

  card.querySelectorAll(".option, .quick-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      const subs = btn.dataset.kind === "video" ? Array.from(selectedSubtitles) : [];
      const audioLangs =
        btn.dataset.kind === "video" || btn.dataset.kind === "audio" ? Array.from(selectedAudioLangs) : [];
      let choice = btn.dataset.choice;
      if (btn.dataset.kind === "transcript") {
        const tsCheck = document.getElementById("transcript-timestamps");
        choice = `${choice}:${tsCheck && tsCheck.checked ? "ts" : "plain"}`;
      }
      startDownload(url, btn.dataset.kind, choice, subs, info.title, audioLangs);

      // NOTE: transcript has no yt-dlp-level way to bundle into the same
      // download as audio/video (it needs skip_download: True, the opposite
      // of what a media download needs) - so "bundle" here just means firing
      // a second, independent download job right after the first one, both
      // tracked in the dock. Avoids the user having to re-resolve the link
      // just to grab the transcript too.
      if (transcriptBundleSelected && info.transcript && (btn.dataset.kind === "audio" || btn.dataset.kind === "video")) {
        const tsCheck = document.getElementById("transcript-timestamps");
        const tChoice = `${info.transcript.code}:${info.transcript.source}:${tsCheck && tsCheck.checked ? "ts" : "plain"}`;
        startDownload(url, "transcript", tChoice, [], info.title);
      }
    });
  });

  card.querySelectorAll(".subtitle-chip:not(.transcript-bundle-chip):not(.audio-track-chip)").forEach((chip) => {
    chip.addEventListener("click", () => {
      const code = chip.dataset.choice;
      if (selectedSubtitles.has(code)) {
        selectedSubtitles.delete(code);
        chip.classList.remove("selected");
      } else {
        selectedSubtitles.add(code);
        chip.classList.add("selected");
      }
    });
  });

  // NOTE: multi-select, like the subtitle chips above - picking Turkish and
  // English both embeds two selectable audio tracks in one file instead of
  // replacing one choice with another.
  card.querySelectorAll(".audio-track-chip").forEach((chip) => {
    chip.addEventListener("click", () => {
      const lang = chip.dataset.lang;
      if (selectedAudioLangs.has(lang)) {
        selectedAudioLangs.delete(lang);
      } else {
        selectedAudioLangs.add(lang);
      }
      // NOTE: re-derive every chip's state from the Set, not just the one
      // clicked - once anything is explicitly picked, the implicit
      // "is_default" highlight no longer applies to the others.
      card.querySelectorAll(".audio-track-chip").forEach((c) => {
        const isSelected = selectedAudioLangs.size > 0 ? selectedAudioLangs.has(c.dataset.lang) : !!c.dataset.default;
        c.classList.toggle("selected", isSelected);
      });
    });
  });

  const transcriptBundleToggle = document.getElementById("transcript-bundle-toggle");
  if (transcriptBundleToggle) {
    transcriptBundleToggle.addEventListener("click", () => {
      transcriptBundleSelected = !transcriptBundleSelected;
      transcriptBundleToggle.classList.toggle("selected", transcriptBundleSelected);
    });
  }

  const backBtn = document.getElementById("back-to-playlist");
  if (backBtn) {
    backBtn.addEventListener("click", (e) => {
      e.preventDefault();
      lastProbe = null;
      renderPlaylist();
    });
  }
}

function renderPlaylist() {
  if (!lastPlaylist) return;
  card.classList.remove("hidden");
  const { data } = lastPlaylist;

  const itemsHtml = data.entries
    .map((entry, i) => {
      const thumb = entry.thumbnail
        ? `<img src="${escapeHtml(entry.thumbnail)}" alt="" loading="lazy">`
        : `<span class="placeholder">▶</span>`;
      const meta = [fmtDuration(entry.duration), entry.uploader ? escapeHtml(entry.uploader) : null]
        .filter(Boolean)
        .join(" · ");
      return `
    <button type="button" class="playlist-item" data-index="${i}">
      <div class="playlist-thumb">${thumb}</div>
      <div class="playlist-info">
        <div class="name">${escapeHtml(entry.title)}</div>
        <div class="meta">${meta}</div>
      </div>
    </button>`;
    })
    .join("");

  // NOTE: without this, a playlist meant clicking every video one at a time
  // and re-picking the format for each - 50 videos, 50 round trips. "best
  // audio"/"best video" are the only formats offered in bulk on purpose: the
  // per-video format ids differ between videos, so there is no single
  // resolution that can be promised across a whole playlist.
  const bulkHtml = `
    <div class="playlist-bulk">
      <div class="playlist-bulk-row">
        <label class="playlist-range-label">${t().playlistRange}</label>
        <input type="number" id="playlist-from" min="1" max="${data.entries.length}" value="1">
        <span class="playlist-range-dash">–</span>
        <input type="number" id="playlist-to" min="1" max="${data.entries.length}" value="${data.entries.length}">
      </div>
      <div class="playlist-bulk-row">
        <button type="button" class="quick-btn" id="playlist-all-audio">${t().quickBestAudio}</button>
        <button type="button" class="quick-btn" id="playlist-all-video">${t().quickBestVideo}</button>
      </div>
      <div class="playlist-bulk-hint">${t().playlistBulkHint}</div>
    </div>`;

  card.innerHTML = `
    <div class="playlist-title">${escapeHtml(data.title)}</div>
    <div class="playlist-count">${data.entries.length} ${t().videoWord}</div>
    ${bulkHtml}
    <div class="playlist-list">${itemsHtml}</div>
  `;

  card.querySelectorAll(".playlist-item").forEach((btn) => {
    btn.addEventListener("click", () => {
      selectPlaylistEntry(data.entries[Number(btn.dataset.index)]);
    });
  });

  document
    .getElementById("playlist-all-audio")
    ?.addEventListener("click", () => queuePlaylistRange("audio", "opus"));
  document
    .getElementById("playlist-all-video")
    ?.addEventListener("click", () => queuePlaylistRange("video", "best"));
}

function queuePlaylistRange(kind, choice) {
  if (!lastPlaylist) return;
  const entries = lastPlaylist.data.entries;
  const fromInput = document.getElementById("playlist-from");
  const toInput = document.getElementById("playlist-to");

  // NOTE: clamped rather than validated-and-rejected - a range the user typed
  // slightly wrong should still do the obvious thing.
  let from = parseInt(fromInput?.value, 10) || 1;
  let to = parseInt(toInput?.value, 10) || entries.length;
  from = Math.max(1, Math.min(from, entries.length));
  to = Math.max(1, Math.min(to, entries.length));
  if (from > to) [from, to] = [to, from];

  const selected = entries.slice(from - 1, to);
  if (selected.length === 0) return;
  if (!confirm(t().playlistConfirm.replace("{n}", selected.length))) return;

  // NOTE: "best" for video is a sentinel the downloader maps to a generic
  // bestvideo+bestaudio selector - the same one channel auto-download uses.
  // Per-video format ids can't be reused across a playlist.
  selected.forEach((entry) => startDownload(entry.url, kind, choice, [], entry.title));

  if (card) {
    card.innerHTML = `<div class="progress-status">${t().playlistQueued.replace("{n}", selected.length)}</div>`;
  }
}

async function startDownload(url, kind, choice, subtitleLangs, title, audioLangs) {
  // NOTE: only ever known for a probed VIDEO format - lastProbe.info.video is
  // absent for a playlist (no format list at all) and irrelevant for
  // audio/subtitle/transcript kinds (no size estimate exists for those).
  // Left undefined otherwise, which JSON.stringify simply omits from the
  // request body - the server then falls back to its own absolute floor.
  const matchedFormat =
    kind === "video" && lastProbe?.info?.video ? lastProbe.info.video.find((f) => f.format_id === choice) : null;
  try {
    const res = await fetch("/api/download", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        url,
        kind,
        choice,
        subtitle_langs: subtitleLangs || [],
        audio_langs: audioLangs || [],
        estimated_size_bytes: matchedFormat?.size_bytes,
      }),
    });
    const data = await res.json();
    if (!res.ok) {
      showError(data.detail || t().errDownloadFailed, data.detail);
      return;
    }
    // NOTE: progress now lives in the dock (visible on every page, and
    // resumed across navigation via localStorage) instead of a duplicate
    // progress bar inline in this card - one source of truth.
    if (card) {
      card.innerHTML = `<div class="progress-status">${t().downloadStartedNote}</div>`;
    }
    trackDockJob(data.job_id, title || url);
  } catch (err) {
    showError(t().errNetwork + err.message, err.message);
  }
}

// --- Indirme dock'u: sayfa gecislerinde de takip edilebilen ilerleme cubugu ---

const DOCK_JOBS_KEY = "mediagrab_active_jobs";
let dockJobs = []; // in-memory: [{jobId, title, state, percent, speed, ready, error}]

function loadTrackedJobIds() {
  try {
    return JSON.parse(localStorage.getItem(DOCK_JOBS_KEY) || "[]");
  } catch (err) {
    return [];
  }
}

function saveTrackedJobIds() {
  const stillActive = dockJobs.filter((j) => !isJobFinished(j));
  localStorage.setItem(DOCK_JOBS_KEY, JSON.stringify(stillActive.map((j) => ({ jobId: j.jobId, title: j.title }))));
}

function trackDockJob(jobId, title) {
  dockJobs.push({ jobId, title, state: "basliyor", percent: 0, speed: null, ready: false, error: null });
  saveTrackedJobIds();
  renderDock();
  ensureJobEventStream();
  // NOTE: the live stream only pushes on the NEXT change - this fetches the
  // current snapshot once immediately, so the row doesn't sit blank until
  // the download's first progress tick (which can be seconds away).
  refreshJobOnce(jobId);
}

function dismissDockJob(jobId) {
  dockJobs = dockJobs.filter((j) => j.jobId !== jobId);
  saveTrackedJobIds();
  renderDock();
}

function isJobFinished(job) {
  return job.state === "hata" || job.state === "iptal" || (job.state === "bitti" && job.ready);
}

// NOTE: shared by the one-shot fetch below AND by incoming SSE messages -
// either way, a job update ends up applied exactly the same way.
function applyJobUpdate(jobId, data) {
  const job = dockJobs.find((j) => j.jobId === jobId);
  if (!job) return;
  Object.assign(job, data);
  if (isJobFinished(data)) {
    saveTrackedJobIds();
    if (data.state === "bitti" && data.ready) loadHistory();
  }
  renderDock();
}

async function refreshJobOnce(jobId) {
  const job = dockJobs.find((j) => j.jobId === jobId);
  if (!job) return;
  try {
    const res = await fetch(`/api/status/${jobId}`);
    if (res.status === 404) {
      // NOTE: the server has no record of this job at all - almost always
      // because it restarted since this job was tracked (its jobs dict is
      // in-memory only) and a stale entry survived in this browser's
      // localStorage. That's infrastructure noise, not a real download
      // failure the user did anything to cause, so this cleans it up
      // silently instead of popping an alarming, unexplained error toast.
      dismissDockJob(jobId);
      return;
    }
    const data = await res.json();
    if (!res.ok) {
      job.state = "hata";
      job.error = data.detail || t().errStatusFailed;
      saveTrackedJobIds();
      renderDock();
      return;
    }
    applyJobUpdate(jobId, data);
  } catch (err) {
    // NOTE: transient network hiccup - the live event stream below will
    // catch up once it's connected, same tolerance the old poll loop had.
  }
}

// NOTE: ONE shared connection for every tracked job, replacing what used to
// be an 800ms setInterval PER job - see /api/events in app.py. A page with
// no downloads yet still opens this eagerly (see resumeTrackedDockJobs/
// trackDockJob) so it's already live the moment a job needs it.
let jobEventSource = null;

function ensureJobEventStream() {
  if (jobEventSource) return;
  jobEventSource = new EventSource("/api/events");
  jobEventSource.onmessage = (event) => {
    let data;
    try {
      data = JSON.parse(event.data);
    } catch (err) {
      return; // NOTE: not job JSON (shouldn't happen - onmessage never fires for ":" comment lines) - ignore.
    }
    if (data && data.job_id) applyJobUpdate(data.job_id, data);
  };
  // NOTE: the browser's EventSource reconnects on its own after a drop -
  // nothing to do here beyond letting it keep trying, the same tolerance
  // the old polling loop had for a transient network hiccup.
}

function dockMetaText(job) {
  // NOTE: only 3 downloads run at once. A queued job used to sit on
  // "Starting..." forever, looking stuck - showing its place in the queue
  // makes the wait explainable.
  // NOTE: position 1 counts too - it still means "waiting for a free slot",
  // not "running". It just happens to be next in line.
  if (job.state === "basliyor" && job.queue_position >= 1) {
    return `${t().queuePosition.replace("{n}", job.queue_position)}`;
  }
  const label = t().states[job.state] || job.state;
  const speedPart = job.speed ? ` · ${job.speed}` : "";
  const etaPart = job.eta ? ` · ${t().etaLabel} ${job.eta}` : "";
  return `${label}${speedPart}${etaPart}`;
}

function dockRowHtml(job) {
  const percent = job.percent || 0;
  let statusHtml;
  if (job.state === "hata") {
    const friendly = friendlyError(job.error) || job.error || t().errUnknown;
    statusHtml = `<div class="dock-row-error">${escapeHtml(friendly)}</div>`;
  } else if (job.state === "iptal") {
    statusHtml = `<div class="dock-row-meta">${t().states.iptal}</div>`;
  } else if (job.state === "bitti" && job.ready) {
    statusHtml = `<button type="button" class="dock-reveal-btn" data-job-id="${job.jobId}">${revealOrDownloadLabel()}</button>`;
  } else {
    statusHtml = `
      <div class="dock-row-bar-bg"><div class="dock-row-bar-fg" style="width:${percent}%"></div></div>
      <div class="dock-row-meta">${dockMetaText(job)}</div>`;
  }
  // NOTE: while a job is still running the ✕ cancels it (and it stays on
  // screen showing "cancelled"); once it's finished the same ✕ just clears
  // the row. Previously ✕ only ever hid the row while the download kept
  // going server-side, which looked like a cancel but wasn't one.
  const finished = isJobFinished(job);
  const closeLabel = finished ? t().dockDismiss : t().dockCancel;
  return `
    <div class="dock-row" data-job-id="${job.jobId}">
      <div class="dock-row-title" title="${escapeHtml(job.title)}">${escapeHtml(job.title)}</div>
      <div class="dock-row-status">${statusHtml}</div>
      <button type="button" class="dock-dismiss-btn" data-job-id="${job.jobId}"
        data-action="${finished ? "dismiss" : "cancel"}"
        title="${escapeHtml(closeLabel)}" aria-label="${escapeHtml(closeLabel)}">✕</button>
    </div>`;
}

async function cancelDockJob(jobId) {
  const job = dockJobs.find((j) => j.jobId === jobId);
  if (job) {
    // NOTE: optimistic - the poll below will confirm it, but the button
    // shouldn't sit there looking unresponsive while the request is in flight.
    job.state = "iptal";
    job.speed = null;
    job.eta = null;
    renderDock();
  }
  try {
    await fetch(`/api/cancel/${jobId}`, { method: "POST" });
  } catch (err) {
    // NOTE: the flag may still have been set server-side; the poll decides.
  }
}

// NOTE: identifies what the dock's MARKUP depends on. Progress and speed
// change constantly but don't alter the structure, so they're deliberately
// not part of this - see renderDock().
function dockLayoutSignature() {
  return dockJobs.map((j) => `${j.jobId}:${j.state}:${j.ready ? 1 : 0}`).join("|");
}

let dockLayoutKey = "";

function updateDockRowProgress(job) {
  const row = downloadDock.querySelector(`.dock-row[data-job-id="${job.jobId}"]`);
  if (!row) return;
  const bar = row.querySelector(".dock-row-bar-fg");
  if (bar) bar.style.width = `${job.percent || 0}%`;
  const meta = row.querySelector(".dock-row-meta");
  if (meta) {
    // NOTE: textContent, so no escaping needed (and no HTML re-parse).
    meta.textContent = dockMetaText(job);
  }
}

function renderDock() {
  if (!downloadDock) return;
  if (dockJobs.length === 0) {
    downloadDock.classList.add("hidden");
    downloadDock.innerHTML = "";
    dockLayoutKey = "";
    return;
  }
  downloadDock.classList.remove("hidden");

  // NOTE: this used to rebuild innerHTML on every 800ms poll tick, which threw
  // away and recreated the ✕ button ~1.25x/second. A real mouse click needs
  // mousedown and mouseup on the SAME node - if a rebuild landed in between
  // (a large chance during an active download), the browser fired no click at
  // all and the button silently did nothing. Now the markup is only rebuilt
  // when the rows actually change shape; a plain progress update just patches
  // the numbers in place, so the button node survives and stays clickable.
  const key = dockLayoutSignature();
  if (key !== dockLayoutKey) {
    dockLayoutKey = key;
    downloadDock.innerHTML = dockJobs.map(dockRowHtml).join("");
    return;
  }
  dockJobs.forEach(updateDockRowProgress);
}

function resumeTrackedDockJobs() {
  const stored = loadTrackedJobIds();
  if (stored.length === 0) return;
  dockJobs = stored.map((j) => ({ ...j, state: "indiriliyor", percent: 0, speed: null, ready: false, error: null }));
  renderDock();
  ensureJobEventStream();
  dockJobs.forEach((j) => refreshJobOnce(j.jobId));
}

async function loadHistory() {
  if (!historyList && !recentList) return;
  try {
    const res = await fetch("/api/history");
    const data = await res.json();
    if (!res.ok) return;
    lastHistory = data;
    if (historyList) {
      populateChannelFilter();
      populateTypeFilter();
      applyHistoryFilters();
    }
    if (recentList) renderRecent(lastHistory);
  } catch (err) {
    // NOTE: if history fails to load, give up silently - don't break the main flow.
  }
}

function populateChannelFilter() {
  if (!historyChannelFilter) return;
  const channels = Array.from(new Set(lastHistory.map((i) => i.folder).filter(Boolean))).sort();
  const current = historyChannelFilter.value;
  historyChannelFilter.innerHTML =
    `<option value="">${t().historyAllChannels}</option>` +
    channels.map((c) => `<option value="${escapeHtml(c)}">${escapeHtml(c)}</option>`).join("");
  historyChannelFilter.value = channels.includes(current) ? current : "";
}

function populateTypeFilter() {
  if (!historyTypeFilter) return;
  // NOTE: built from whatever extensions actually exist in the downloads
  // folder right now, not a hand-kept list here - a new download kind (like
  // .mkv from multi-track audio) shows up on its own, nothing to remember.
  const types = Array.from(new Set(lastHistory.map((i) => i.ext).filter(Boolean))).sort();
  const current = historyTypeFilter.value;
  historyTypeFilter.innerHTML =
    `<option value="">${t().historyAllTypes}</option>` +
    types.map((ext) => `<option value="${escapeHtml(ext)}">${escapeHtml(ext.toUpperCase())}</option>`).join("");
  historyTypeFilter.value = types.includes(current) ? current : "";
}

function applyHistoryFilters() {
  if (!historyList) return;
  const q = (historySearchInput?.value || "").trim().toLowerCase();
  const channel = historyChannelFilter?.value || "";
  const type = historyTypeFilter?.value || "";
  const filtered = lastHistory.filter((item) => {
    const matchesQuery = !q || item.filename.toLowerCase().includes(q);
    const matchesChannel = !channel || item.folder === channel;
    const matchesType = !type || item.ext === type;
    return matchesQuery && matchesChannel && matchesType;
  });
  renderHistory(filtered);
}

const VIDEO_EXTS = new Set(["mp4", "mkv"]);
const SUBTITLE_EXTS = new Set(["srt"]);
const TRANSCRIPT_EXTS = new Set(["txt"]);
// NOTE: only media containers can carry an embedded cover. Subtitles and
// transcripts are plain text, so requesting a thumbnail for them was a
// guaranteed 404 that still cost the server an ffprobe spawn per card.
const THUMBNAILABLE_EXTS = new Set(["mp4", "mkv", "mp3", "m4a", "opus"]);

function encodePath(relPath) {
  // NOTE: encodes each "/"-separated segment individually so the slash stays
  // a literal path separator (matches the server's {..:path} routes) instead
  // of becoming "%2F", which plain encodeURIComponent would do.
  return relPath.split("/").map(encodeURIComponent).join("/");
}

function historyCardHtml(item, withActions) {
  const date = new Date(item.downloaded_at).toLocaleString(t().locale, {
    dateStyle: "medium",
    timeStyle: "short",
  });
  const placeholder = VIDEO_EXTS.has(item.ext)
    ? "▶"
    : SUBTITLE_EXTS.has(item.ext)
      ? "CC"
      : TRANSCRIPT_EXTS.has(item.ext)
        ? "📄"
        : "♪";
  const encodedPath = encodePath(item.filename);
  const fileUrl = `/api/history/file/${encodedPath}`;
  const thumbHtml = THUMBNAILABLE_EXTS.has(item.ext)
    ? `<img src="/api/history/thumb/${encodedPath}" alt="" loading="lazy" onerror="this.remove()">`
    : "";
  const itemUrl = withLang(`/item/${encodedPath}`);
  const baseName = item.filename.includes("/") ? item.filename.split("/").pop() : item.filename;
  const folderBadge = item.folder ? `<div class="folder-badge">${escapeHtml(item.folder)}</div>` : "";
  // NOTE: every card repeats the same two button labels, so on their own
  // ("Delete", "Delete", "Delete"...) they tell a screen reader nothing about
  // WHICH file they act on - aria-label pins each one to its filename.
  const actions = withActions
    ? `
      <div class="history-actions">
        <button type="button" class="reveal-btn" data-reveal-url="${fileUrl}"
          aria-label="${escapeHtml(`${revealOrDownloadLabel()}: ${baseName}`)}">${revealOrDownloadLabel()}</button>
        <button type="button" class="delete-btn"
          aria-label="${escapeHtml(`${t().historyDelete}: ${baseName}`)}">${t().historyDelete}</button>
      </div>`
    : "";
  return `
    <div class="history-card" data-filename="${escapeHtml(item.filename)}">
      <a class="history-card-link" href="${itemUrl}">
        <div class="history-thumb">
          <span class="placeholder">${placeholder}</span>
          ${thumbHtml}
        </div>
        <div class="history-body">
          ${folderBadge}
          <div class="name" title="${escapeHtml(baseName)}">${escapeHtml(baseName)}</div>
          <div class="meta">${item.size} · ${date}</div>
        </div>
      </a>${actions}
    </div>`;
}

function renderHistory(items) {
  if (!historyList) return;
  // NOTE: "Clear All" reflects whether ANY history exists (lastHistory),
  // not just the currently filtered/searched subset in `items` - otherwise
  // a search with zero matches would hide the button even though there's
  // plenty of history to clear.
  historyClearBtn?.classList.toggle("hidden", lastHistory.length === 0);

  if (!items || items.length === 0) {
    const message = lastHistory.length === 0 ? t().historyEmpty : t().historyNoMatches;
    historyList.innerHTML = `<div class="history-empty">${message}</div>`;
    return;
  }

  historyList.innerHTML = items.map((item) => historyCardHtml(item, true)).join("");

  historyList.querySelectorAll(".history-card").forEach((row) => {
    const filename = row.dataset.filename;
    row.querySelector(".reveal-btn")?.addEventListener("click", async (e) => {
      e.preventDefault();
      const btn = row.querySelector(".reveal-btn");
      const outcome = await revealFile(btn.dataset.revealUrl, filename.split("/").pop());
      if (outcome === "removed") loadHistory();
      else showSaveOutcome(btn, outcome);
    });
    row.querySelector(".delete-btn").addEventListener("click", () => deleteHistoryItem(filename));
  });
}

function renderRecent(items) {
  if (!recentList || !recentSection) return;
  const recent = (items || []).slice(0, 3);
  recentSection.classList.toggle("hidden", recent.length === 0);
  recentList.innerHTML = recent.map((item) => historyCardHtml(item, false)).join("");
}

async function deleteHistoryItem(filename) {
  // NOTE: this is an unrecoverable os.remove() on the server (no trash/undo),
  // and the button sits right next to "show in folder" - "Clear all" has
  // always asked for confirmation, so a single delete should too.
  if (!confirm(`${t().historyDeleteConfirm}\n\n${filename}`)) return;
  historyError?.classList.add("hidden");
  try {
    const res = await fetch(`/api/history/${encodePath(filename)}`, { method: "DELETE" });
    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      if (historyError) {
        historyError.textContent = data.detail || t().historyDeleteFailed;
        historyError.classList.remove("hidden");
      }
      return;
    }
    loadHistory();
  } catch (err) {
    if (historyError) {
      historyError.textContent = t().errNetwork + err.message;
      historyError.classList.remove("hidden");
    }
  }
}

async function clearAllHistory() {
  if (!confirm(t().historyClearConfirm)) return;
  historyError?.classList.add("hidden");
  try {
    const res = await fetch("/api/history", { method: "DELETE" });
    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      if (historyError) {
        historyError.textContent = data.detail || t().historyClearFailed;
        historyError.classList.remove("hidden");
      }
      return;
    }
    loadHistory();
  } catch (err) {
    if (historyError) {
      historyError.textContent = t().errNetwork + err.message;
      historyError.classList.remove("hidden");
    }
  }
}

// --- Ayarlar sayfasi: kanal takibi ---

function updateChannelChoiceVisibility() {
  if (!channelChoiceSelect) return;
  const mode = document.querySelector('input[name="channel-mode"]:checked')?.value;
  channelChoiceSelect.classList.toggle("hidden", mode !== "auto");
}

async function loadChannels() {
  if (!channelList) return;
  try {
    const res = await fetch("/api/channels");
    const data = await res.json();
    lastChannels = data;
    renderChannelList(lastChannels);
  } catch (err) {
    // NOTE: silent - settings page just shows an empty list on failure.
  }
}

function renderChannelList(items) {
  if (!channelList) return;
  channelEmpty?.classList.toggle("hidden", items.length > 0);

  channelList.innerHTML = items
    .map((c) => {
      const thumb = c.thumbnail ? `<img src="${escapeHtml(c.thumbnail)}" alt="">` : "";
      const modeLabel = c.mode === "auto" ? t().channelModeAutoBadge : t().channelModeNotifyBadge;
      const lastChecked = c.last_checked_at
        ? new Date(c.last_checked_at).toLocaleString(t().locale, { dateStyle: "medium", timeStyle: "short" })
        : t().channelNeverChecked;
      return `
    <div class="channel-item" data-id="${c.id}">
      <div class="channel-thumb">${thumb}</div>
      <div class="channel-info">
        <div class="name">${escapeHtml(c.name)}</div>
        <div class="meta">${t().channelLastChecked}: ${lastChecked}</div>
        ${
          c.last_error
            ? `<div class="channel-error" title="${escapeHtml(c.last_error)}">${t().channelCheckFailed}: ${escapeHtml(friendlyError(c.last_error) || c.last_error)}</div>`
            : ""
        }
      </div>
      <span class="channel-mode-badge ${c.mode}">${modeLabel}</span>
      <div class="channel-actions">
        <button type="button" class="check-now-btn">${t().channelCheckNow}</button>
        <button type="button" class="remove-btn">${t().channelRemove}</button>
      </div>
    </div>`;
    })
    .join("");

  channelList.querySelectorAll(".channel-item").forEach((row) => {
    const id = row.dataset.id;
    row.querySelector(".check-now-btn").addEventListener("click", async (e) => {
      e.target.disabled = true;
      try {
        await fetch(`/api/channels/${id}/check`, { method: "POST" });
        await loadChannels();
        await loadPending();
      } finally {
        e.target.disabled = false;
      }
    });
    row.querySelector(".remove-btn").addEventListener("click", async () => {
      const name = lastChannels.find((c) => c.id === id)?.name || "";
      if (!confirm(`${t().channelRemoveConfirm}\n\n${name}`)) return;
      await fetch(`/api/channels/${id}`, { method: "DELETE" });
      loadChannels();
    });
  });
}

async function addChannel() {
  if (!channelUrlInput) return;
  const url = channelUrlInput.value.trim();
  if (!url) return;
  channelError?.classList.add("hidden");

  const mode = document.querySelector('input[name="channel-mode"]:checked')?.value || "notify";
  let choiceKind = "audio";
  let choice = "opus";
  if (mode === "auto") {
    const [kind, val] = (channelChoiceSelect.value || "audio:opus").split(":");
    choiceKind = kind;
    choice = val;
  }

  channelAddBtn.disabled = true;
  try {
    const res = await fetch("/api/channels", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url, mode, choice_kind: choiceKind, choice }),
    });
    const data = await res.json();
    if (!res.ok) {
      if (channelError) {
        channelError.textContent = data.detail || t().channelAddFailed;
        channelError.classList.remove("hidden");
      }
      return;
    }
    channelUrlInput.value = "";
    loadChannels();
  } catch (err) {
    if (channelError) {
      channelError.textContent = t().errNetwork + err.message;
      channelError.classList.remove("hidden");
    }
  } finally {
    channelAddBtn.disabled = false;
  }
}

// --- Ana sayfa: takip edilen kanallardan yeni video banner'i ---

async function loadPending() {
  if (!pendingBanner) return;
  try {
    const res = await fetch("/api/channels/pending");
    const data = await res.json();
    lastPending = data;
    renderPending();
  } catch (err) {
    // NOTE: silent - the banner just stays hidden on failure.
  }
}

function renderPending() {
  if (!pendingBanner) return;
  pendingBanner.classList.toggle("hidden", lastPending.length === 0);
  if (lastPending.length === 0) return;

  pendingList.innerHTML = lastPending
    .map((v, i) => {
      const thumb = v.thumbnail
        ? `<img src="${escapeHtml(v.thumbnail)}" alt="" loading="lazy">`
        : `<span class="placeholder">▶</span>`;
      const meta = [escapeHtml(v.channel_name), fmtDuration(v.duration)].filter(Boolean).join(" · ");
      return `
    <button type="button" class="playlist-item" data-index="${i}">
      <div class="playlist-thumb">${thumb}</div>
      <div class="playlist-info">
        <div class="name">${escapeHtml(v.title)}</div>
        <div class="meta">${meta}</div>
      </div>
    </button>`;
    })
    .join("");

  pendingList.querySelectorAll(".playlist-item").forEach((btn) => {
    btn.addEventListener("click", () => {
      const v = lastPending[Number(btn.dataset.index)];
      selectPlaylistEntry(v);
      card.scrollIntoView({ behavior: "smooth", block: "start" });
    });
  });
}

async function clearPending() {
  try {
    const res = await fetch("/api/channels/pending", { method: "DELETE" });
    if (!res.ok) return;
    lastPending = [];
    renderPending();
  } catch (err) {
    // NOTE: silent - user can just try the button again.
  }
}

// --- Ayarlar sayfasi: tanilama bilgisi (Geri Bildirim) ---

const diagnosticsBtn = document.getElementById("diagnostics-btn");
const diagnosticsText = document.getElementById("diagnostics-text");
const diagnosticsStatus = document.getElementById("diagnostics-status");

async function copyDiagnostics() {
  if (!diagnosticsBtn || !diagnosticsText) return;
  diagnosticsBtn.disabled = true;
  try {
    const data = await (await fetch("/api/diagnostics")).json();
    // NOTE: always shown as selectable text too - the clipboard API only
    // exists on HTTPS/localhost, so on a plain-HTTP LAN device copying by
    // hand is the only way (same reason the paste button hides there).
    diagnosticsText.value = data.text;
    diagnosticsText.classList.remove("hidden");
    let copied = false;
    try {
      if (window.isSecureContext && navigator.clipboard) {
        await navigator.clipboard.writeText(data.text);
        copied = true;
      }
    } catch (err) {
      copied = false;
    }
    if (!copied) diagnosticsText.select();
    diagnosticsStatus.textContent = copied ? t().diagCopied : t().diagCopyManual;
    diagnosticsStatus.classList.remove("hidden", "ok", "bad");
    diagnosticsStatus.classList.add(copied ? "ok" : "bad");
  } catch (err) {
    diagnosticsStatus.textContent = t().errNetwork + err.message;
    diagnosticsStatus.classList.remove("hidden", "ok");
    diagnosticsStatus.classList.add("bad");
  } finally {
    diagnosticsBtn.disabled = false;
  }
}

diagnosticsBtn?.addEventListener("click", copyDiagnostics);

// --- Ayarlar sayfasi: MediaGrab surum kontrolu ---

const mediagrabStatus = document.getElementById("mediagrab-status");
const mediagrabInstructions = document.getElementById("mediagrab-instructions");

// NOTE: MediaGrab never updates itself - each install type updates a
// different way, so this only shows the right steps for the one in use.
// Pure (no DOM) so every branch can be tested under Node.
function mediagrabUpdateHtml(info) {
  const cmd = (command) => `
    <div class="ytdlp-cmd-row">
      <code>${escapeHtml(command)}</code>
      <button type="button" class="mg-copy-btn" data-command="${escapeHtml(command)}">${t().ytdlpCopyBtn}</button>
    </div>`;
  let steps;
  if (info.install_type === "docker") {
    steps = `
      <p class="settings-hint">${t().mgUpdateDocker}</p>
      ${cmd("docker compose pull")}
      ${cmd("docker compose up -d")}
      <p class="settings-hint">${t().mgUpdateDockerBuild}</p>
      ${cmd("git pull && docker compose up -d --build")}`;
  } else if (info.install_type === "installer") {
    steps = `
      <p class="settings-hint">${t().mgUpdateInstaller}
        <a href="https://github.com/umitkrkmz/mediagrab/releases/latest" target="_blank" rel="noopener noreferrer">${t().mgDownloadInstaller}</a>
      </p>`;
  } else {
    steps = `
      <p class="settings-hint">${t().mgUpdateSource}</p>
      ${cmd("git pull")}
      ${cmd("pip install -r requirements.txt")}`;
  }
  return `
    <div class="ytdlp-instructions-title">${t().ytdlpInstructionsTitle}</div>
    ${steps}`;
}

async function loadMediagrabVersion() {
  if (!mediagrabStatus) return;
  mediagrabStatus.textContent = t().ytdlpChecking;
  let info;
  try {
    info = await (await fetch("/api/mediagrab-version")).json();
  } catch (err) {
    mediagrabStatus.innerHTML = `<span class="ytdlp-badge unknown">${t().ytdlpCheckFailed}</span>`;
    return;
  }
  const notes = `<a href="${escapeHtml(info.release_url)}" target="_blank" rel="noopener noreferrer">${t().mgReleaseNotes}</a>`;
  if (info.update_available === null) {
    mediagrabStatus.innerHTML = `
      <span class="ytdlp-badge unknown">${t().ytdlpCheckFailed}</span>
      <span class="ytdlp-version-row">${t().ytdlpInstalledLabel}: ${escapeHtml(info.installed)}</span>`;
    mediagrabInstructions?.classList.add("hidden");
    return;
  }
  if (!info.update_available) {
    mediagrabStatus.innerHTML = `
      <span class="ytdlp-badge uptodate">${t().ytdlpUpToDate}</span>
      <span class="ytdlp-version-row">${t().ytdlpInstalledLabel}: ${escapeHtml(info.installed)}</span>`;
    mediagrabInstructions?.classList.add("hidden");
    return;
  }
  mediagrabStatus.innerHTML = `
    <span class="ytdlp-badge outdated">${t().ytdlpUpdateAvailable}</span>
    <span class="ytdlp-version-row">${t().ytdlpInstalledLabel}: ${escapeHtml(info.installed)} &rarr; ${t().ytdlpLatestLabel}: ${escapeHtml(info.latest)}</span>
    <span class="ytdlp-version-row">${notes}</span>`;
  if (!mediagrabInstructions) return;
  mediagrabInstructions.innerHTML = mediagrabUpdateHtml(info);
  mediagrabInstructions.classList.remove("hidden");
  mediagrabInstructions.querySelectorAll(".mg-copy-btn").forEach((btn) => {
    btn.addEventListener("click", async () => {
      try {
        await navigator.clipboard.writeText(btn.dataset.command);
        const original = btn.textContent;
        btn.textContent = t().ytdlpCopied;
        setTimeout(() => {
          btn.textContent = original;
        }, 1500);
      } catch (err) {
        // NOTE: clipboard can be blocked (plain-HTTP LAN) - the command is
        // visible to copy by hand.
      }
    });
  });
}

// --- Ayarlar sayfasi: yt-dlp surum kontrolu ---

// NOTE: same spec as downloader.YTDLP_PIP_SPEC (test_frontend checks this) -
// quoted, because PowerShell splits an unquoted "a[b,c]" at the comma and zsh
// treats the brackets as a glob.
const YTDLP_PIP_CMD = 'pip install --upgrade "yt-dlp[default,deno]"';
let lastYtdlpInfo = null;

async function loadYtdlpVersion() {
  if (!ytdlpStatus) return;
  ytdlpStatus.textContent = t().ytdlpChecking;
  try {
    const res = await fetch("/api/ytdlp-version");
    lastYtdlpInfo = await res.json();
  } catch (err) {
    lastYtdlpInfo = { installed: null, latest: null, update_available: null };
  }
  renderYtdlpVersion();
}

// NOTE: the "Update Now" button works in Docker too (update_ytdlp installs
// with --user into the volume-mounted PYTHONUSERBASE, so it survives the
// container being recreated) - only the manual venv/pip steps are dropped
// there, since a container has no venv to activate.
function ytdlpInstructionsHtml(isDocker) {
  const button = `
    <button type="button" id="ytdlp-update-now-btn" class="ytdlp-update-btn">${t().ytdlpUpdateNowBtn}</button>
    <div id="ytdlp-update-status" class="ytdlp-update-status hidden"></div>`;
  if (isDocker) return button;
  return `${button}
    <details class="ytdlp-manual">
      <summary>${t().ytdlpManualToggle}</summary>
      <div class="ytdlp-instructions-title">${t().ytdlpInstructionsTitle}</div>
      <ol class="ytdlp-steps">
        <li>${t().ytdlpStep1}</li>
        <li>
          ${t().ytdlpStep2}
          <div class="ytdlp-substep">${t().ytdlpStep2Win} <code>.venv\\Scripts\\Activate.ps1</code></div>
          <div class="ytdlp-substep">${t().ytdlpStep2Unix} <code>source .venv/bin/activate</code></div>
        </li>
        <li>
          ${t().ytdlpStep3}
          <div class="ytdlp-cmd-row">
            <code>${escapeHtml(YTDLP_PIP_CMD)}</code>
            <button type="button" id="ytdlp-copy-btn">${t().ytdlpCopyBtn}</button>
          </div>
        </li>
        <li>${t().ytdlpStep4}</li>
      </ol>
    </details>`;
}

function wireYtdlpCopyBtn() {
  const btn = document.getElementById("ytdlp-copy-btn");
  if (!btn) return;
  btn.addEventListener("click", async () => {
    try {
      await navigator.clipboard.writeText(YTDLP_PIP_CMD);
      const original = btn.textContent;
      btn.textContent = t().ytdlpCopied;
      setTimeout(() => {
        btn.textContent = original;
      }, 1500);
    } catch (err) {
      // NOTE: clipboard access can fail (permissions) - the command is
      // already visible as selectable text, so this is a nice-to-have.
    }
  });
}

async function waitForServerAndReload() {
  // NOTE: polls a lightweight endpoint until the restarted process (which
  // briefly goes away mid-restart) answers again, then reloads so the page
  // picks up the freshly-updated yt-dlp version instead of stale JS state.
  for (let i = 0; i < 30; i++) {
    await new Promise((r) => setTimeout(r, 1000));
    try {
      const res = await fetch("/api/locale");
      if (res.ok) {
        window.location.reload();
        return;
      }
    } catch (err) {
      // NOTE: expected while the process is mid-restart - keep polling.
    }
  }
}

function wireYtdlpUpdateBtn() {
  const btn = document.getElementById("ytdlp-update-now-btn");
  const statusEl = document.getElementById("ytdlp-update-status");
  if (!btn) return;
  btn.addEventListener("click", async () => {
    btn.disabled = true;
    btn.textContent = t().ytdlpUpdating;
    statusEl?.classList.add("hidden");
    try {
      const res = await fetch("/api/ytdlp-update", { method: "POST" });
      const data = await res.json();
      if (data.ok) {
        if (statusEl) {
          statusEl.textContent = t().ytdlpUpdateSuccess;
          statusEl.classList.remove("hidden", "error");
        }
        waitForServerAndReload();
      } else {
        btn.disabled = false;
        btn.textContent = t().ytdlpUpdateNowBtn;
        if (statusEl) {
          statusEl.textContent = `${t().ytdlpUpdateFailed}: ${data.output || ""}`;
          statusEl.classList.remove("hidden");
          statusEl.classList.add("error");
        }
      }
    } catch (err) {
      btn.disabled = false;
      btn.textContent = t().ytdlpUpdateNowBtn;
      if (statusEl) {
        statusEl.textContent = t().errNetwork + err.message;
        statusEl.classList.remove("hidden");
        statusEl.classList.add("error");
      }
    }
  });
}

// NOTE: undefined (not null) when /api/ytdlp-version itself failed - then
// nothing is known either way and no warning should be shown.
function jsRuntimeMissing(info) {
  if (info.js_runtime === undefined) return false;
  return !info.js_runtime || !info.js_solver;
}

// NOTE: the update button also installs a missing JS runtime (YTDLP_PIP_CMD's
// extras), so it's offered then too - but NOT in Docker, where the image
// already ships Deno and a --user install's deno binary would land outside
// the paths yt-dlp searches. There, the fix is updating the image.
function shouldOfferYtdlpUpdate(info) {
  if (info.update_available) return true;
  return jsRuntimeMissing(info) && !info.is_docker;
}

function renderJsRuntime(info) {
  if (!ytdlpJsStatus) return;
  if (info.js_runtime === undefined) {
    ytdlpJsStatus.innerHTML = "";
    return;
  }
  if (jsRuntimeMissing(info)) {
    ytdlpJsStatus.innerHTML = `
      <span class="ytdlp-badge outdated">${t().jsRuntimeMissing}</span>
      <span class="ytdlp-version-row">${t().jsRuntimeLabel}</span>
      <p class="settings-hint">${info.is_docker ? t().jsRuntimeMissingHintDocker : t().jsRuntimeMissingHint}</p>`;
    return;
  }
  ytdlpJsStatus.innerHTML = `
    <span class="ytdlp-badge uptodate">${t().jsRuntimeOk}</span>
    <span class="ytdlp-version-row">${t().jsRuntimeLabel}: ${escapeHtml(info.js_runtime)} ${escapeHtml(info.js_runtime_version || "")}</span>`;
}

function renderYtdlpVersion() {
  if (!ytdlpStatus || !lastYtdlpInfo) return;
  const info = lastYtdlpInfo;
  renderJsRuntime(info);
  const showInstructions = () => {
    if (!ytdlpInstructions) return;
    ytdlpInstructions.classList.remove("hidden");
    ytdlpInstructions.innerHTML = ytdlpInstructionsHtml(info.is_docker);
    wireYtdlpCopyBtn();
    wireYtdlpUpdateBtn();
  };

  if (info.update_available === null) {
    ytdlpStatus.innerHTML = `<span class="ytdlp-badge unknown">${t().ytdlpCheckFailed}</span>`;
    ytdlpInstructions?.classList.add("hidden");
  } else if (info.update_available) {
    ytdlpStatus.innerHTML = `
      <span class="ytdlp-badge outdated">${t().ytdlpUpdateAvailable}</span>
      <span class="ytdlp-version-row">${t().ytdlpInstalledLabel}: ${escapeHtml(info.installed)} &rarr; ${t().ytdlpLatestLabel}: ${escapeHtml(info.latest)}</span>`;
    showInstructions();
  } else {
    ytdlpStatus.innerHTML = `
      <span class="ytdlp-badge uptodate">${t().ytdlpUpToDate}</span>
      <span class="ytdlp-version-row">${t().ytdlpInstalledLabel}: ${escapeHtml(info.installed)}</span>`;
    if (shouldOfferYtdlpUpdate(info)) showInstructions();
    else ytdlpInstructions?.classList.add("hidden");
  }

  if (ytdlpCredit) {
    ytdlpCredit.innerHTML = `${t().ytdlpCreditText} <a href="https://github.com/yt-dlp/yt-dlp" target="_blank" rel="noopener noreferrer">${t().ytdlpCreditLink}</a>`;
  }
}

// --- Ayarlar: ffmpeg / ffprobe ---

async function loadFfmpegVersion() {
  if (!ffmpegStatus) return;
  ffmpegStatus.textContent = t().ytdlpChecking;
  let info;
  try {
    const res = await fetch("/api/ffmpeg-version");
    info = await res.json();
  } catch (err) {
    ffmpegStatus.innerHTML = `<span class="ytdlp-badge unknown">${t().ytdlpCheckFailed}</span>`;
    return;
  }

  const versions = [
    info.ffmpeg ? `ffmpeg ${escapeHtml(info.ffmpeg)}` : `ffmpeg: ${t().ffmpegMissing}`,
    info.ffprobe ? `ffprobe ${escapeHtml(info.ffprobe)}` : `ffprobe: ${t().ffmpegMissing}`,
  ].join(" · ");

  ffmpegStatus.innerHTML = `
    <span class="ytdlp-badge ${info.ok ? "uptodate" : "outdated"}">${info.ok ? t().ffmpegInstalled : t().ffmpegNotFound}</span>
    <span class="ytdlp-version-row">${versions}</span>`;

  // NOTE: in Docker ffmpeg comes with the image, and the Windows installer
  // ships its own copy - per-OS install commands (and the "not bundled,
  // install it yourself" hint) would be wrong in both.
  if (info.is_docker || info.bundled) {
    ffmpegHint?.classList.add("hidden");
    ffmpegInstructions?.classList.add("hidden");
    const note = info.is_docker ? t().ffmpegDockerNote : t().ffmpegBundledNote;
    ffmpegStatus.insertAdjacentHTML("beforeend", `<p class="settings-hint">${note}</p>`);
    return;
  }
  ffmpegHint?.classList.remove("hidden");

  // NOTE: unlike yt-dlp there's no reliable "latest ffmpeg" to compare
  // against (every platform ships its own build and numbering), so this
  // offers the install/update command rather than claiming an update exists.
  // All platforms are listed, with the one you're on marked.
  if (ffmpegInstructions) {
    ffmpegInstructions.classList.remove("hidden");
    const rows = (info.install_commands || [])
      .map((entry) => {
        const isCurrent = entry.key === info.platform;
        return `
        <div class="ffmpeg-platform${isCurrent ? " current" : ""}">
          <div class="ffmpeg-platform-label">
            ${escapeHtml(entry.label)}${isCurrent ? ` <span class="ffmpeg-current-tag">${t().ffmpegYourSystem}</span>` : ""}
          </div>
          <div class="ytdlp-cmd-row">
            <code>${escapeHtml(entry.command)}</code>
            <button type="button" class="ffmpeg-copy-btn" data-command="${escapeHtml(entry.command)}">${t().ytdlpCopyBtn}</button>
          </div>
        </div>`;
      })
      .join("");

    ffmpegInstructions.innerHTML = `
      <div class="ytdlp-instructions-title">${info.ok ? t().ffmpegUpdateTitle : t().ffmpegInstallTitle}</div>
      ${rows}
      <p class="settings-hint">${t().ffmpegRestartNote}</p>`;

    ffmpegInstructions.querySelectorAll(".ffmpeg-copy-btn").forEach((copyBtn) => {
      copyBtn.addEventListener("click", async () => {
        try {
          await navigator.clipboard.writeText(copyBtn.dataset.command);
          const original = copyBtn.textContent;
          copyBtn.textContent = t().ytdlpCopied;
          setTimeout(() => {
            copyBtn.textContent = original;
          }, 1500);
        } catch (err) {
          // NOTE: clipboard can be blocked - the command is visible to copy by hand.
        }
      });
    });
  }
}

// --- Ayarlar: Python bagimliliklari ---

async function loadDependencies() {
  if (!depsStatus) return;
  depsStatus.textContent = t().ytdlpChecking;
  let info;
  try {
    const res = await fetch("/api/dependencies");
    info = await res.json();
  } catch (err) {
    depsStatus.innerHTML = `<span class="ytdlp-badge unknown">${t().ytdlpCheckFailed}</span>`;
    return;
  }

  if (!info.reachable) {
    depsStatus.innerHTML = `<span class="ytdlp-badge unknown">${t().ytdlpCheckFailed}</span>`;
    depsList && (depsList.innerHTML = "");
    depsActions?.classList.add("hidden");
    return;
  }

  const outdated = info.update_count > 0;
  depsStatus.innerHTML = `
    <span class="ytdlp-badge ${outdated ? "outdated" : "uptodate"}">
      ${outdated ? `${info.update_count} ${t().depsUpdatesAvailable}` : t().ytdlpUpToDate}
    </span>`;

  if (depsList) {
    depsList.innerHTML = info.packages
      .map((p) => {
        const current = p.installed || "-";
        const right = p.update_available
          ? `<span class="deps-arrow">${escapeHtml(current)} &rarr; ${escapeHtml(p.latest)}</span>`
          : `<span class="deps-current">${escapeHtml(current)}</span>`;
        return `
        <div class="deps-row${p.update_available ? " outdated" : ""}">
          <span class="deps-name">${escapeHtml(p.name)}</span>
          ${right}
        </div>`;
      })
      .join("");
  }

  // NOTE: the update button installs packages into the container's own
  // (ephemeral) filesystem in Docker - gone the next time the image is
  // recreated, so it's replaced with a "docker pull" pointer instead. yt-dlp
  // is the one exception (see downloader.update_ytdlp's PYTHONUSERBASE
  // override) and keeps its own always-shown button elsewhere on this page.
  if (info.is_docker) {
    depsActions?.classList.add("hidden");
    depsDockerHint?.classList.toggle("hidden", !outdated);
    return;
  }
  depsDockerHint?.classList.add("hidden");
  depsActions?.classList.toggle("hidden", !outdated);
}

function wireDepsUpdateBtn() {
  if (!depsUpdateBtn) return;
  depsUpdateBtn.addEventListener("click", async () => {
    depsUpdateBtn.disabled = true;
    depsUpdateBtn.textContent = t().ytdlpUpdating;
    depsUpdateStatus?.classList.add("hidden");
    try {
      const res = await fetch("/api/dependencies-update", { method: "POST" });
      const data = await res.json();
      if (data.ok) {
        if (depsUpdateStatus) {
          depsUpdateStatus.textContent = t().ytdlpUpdateSuccess;
          depsUpdateStatus.classList.remove("hidden");
        }
        // NOTE: the server restarts itself after a successful update.
        waitForServerAndReload();
        return;
      }
      if (depsUpdateStatus) {
        depsUpdateStatus.textContent = `${t().ytdlpUpdateFailed}: ${data.output || ""}`.trim();
        depsUpdateStatus.classList.remove("hidden");
      }
    } catch (err) {
      if (depsUpdateStatus) {
        depsUpdateStatus.textContent = t().errNetwork + err.message;
        depsUpdateStatus.classList.remove("hidden");
      }
    }
    depsUpdateBtn.disabled = false;
    depsUpdateBtn.textContent = t().depsUpdateBtn;
  });
}

// --- Ayarlar: sekme gecisi ---

const settingsNav = document.getElementById("settings-nav");

function showSettingsTab(tabId) {
  const panels = document.querySelectorAll(".settings-panels [data-panel]");
  if (!panels.length) return;
  const validIds = Array.from(panels).map((p) => p.dataset.panel);
  if (!validIds.includes(tabId)) tabId = validIds[0];

  panels.forEach((panel) => {
    panel.hidden = panel.dataset.panel !== tabId;
  });
  settingsNav?.querySelectorAll(".settings-nav-item").forEach((btn) => {
    const active = btn.dataset.tab === tabId;
    btn.classList.toggle("active", active);
    btn.setAttribute("aria-current", active ? "true" : "false");
  });
  // NOTE: below the .settings-nav-toggle breakpoint this list is a
  // collapsible dropdown (see style.css) - closing it once a category is
  // picked gets it out of the way of the panel it just opened. A no-op
  // otherwise (no "nav-open" class to remove, and harmless on desktop).
  settingsNav?.classList.remove("nav-open");
}

const settingsNavToggle = document.getElementById("settings-nav-toggle");
settingsNavToggle?.addEventListener("click", () => {
  const isOpen = settingsNav.classList.toggle("nav-open");
  settingsNavToggle.setAttribute("aria-expanded", String(isOpen));
});

if (settingsNav) {
  settingsNav.querySelectorAll(".settings-nav-item").forEach((btn) => {
    btn.addEventListener("click", () => {
      location.hash = btn.dataset.tab;
    });
  });
  // NOTE: hash-driven rather than plain JS state, so a direct link (or a
  // refresh) lands on the right tab, and the browser's back/forward buttons
  // step through tabs the same way they'd step through pages.
  window.addEventListener("hashchange", () => showSettingsTab(location.hash.slice(1)));
  showSettingsTab(location.hash.slice(1));
}

// --- Ayarlar: cerezler ---

const cookieModes = document.getElementById("cookie-modes");
const cookieFilePanel = document.getElementById("cookie-file-panel");
const cookieBrowserPanel = document.getElementById("cookie-browser-panel");
const cookieFileInput = document.getElementById("cookie-file-input");
const cookieBrowserSelect = document.getElementById("cookie-browser-select");
const cookieSaveBtn = document.getElementById("cookie-save-btn");
const cookieTestBtn = document.getElementById("cookie-test-btn");
const cookieStatus = document.getElementById("cookie-status");
const cookieCurrent = document.getElementById("cookie-current");
const cookieUploadInput = document.getElementById("cookie-upload-input");
const cookieReview = document.getElementById("cookie-review");
const cookieHowto = document.getElementById("cookie-howto");
const cookiePathAdvanced = document.getElementById("cookie-path-advanced");
const cookieBrowserUnsupported = document.getElementById("cookie-browser-unsupported");
const cookieWindowsNote = document.getElementById("cookie-windows-note");
const defaultAudioLangInput = document.getElementById("default-audio-lang-input");
const defaultAudioLangSaveBtn = document.getElementById("default-audio-lang-save-btn");
const defaultAudioLangStatus = document.getElementById("default-audio-lang-status");
const homeServerModeToggle = document.getElementById("home-server-mode-toggle");
const remoteAccessToggle = document.getElementById("remote-access-toggle");
const remoteAccessNeedPasswordHint = document.getElementById("remote-access-need-password");
const remoteAccessCurrentPasswordRow = document.getElementById("remote-access-current-password-row");
const remoteAccessCurrentPasswordInput = document.getElementById("remote-access-current-password-input");
const remoteAccessPasswordInput = document.getElementById("remote-access-password-input");
const remoteAccessPasswordConfirmInput = document.getElementById("remote-access-password-confirm-input");
const remoteAccessShowPasswordsToggle = document.getElementById("remote-access-show-passwords-toggle");
const remoteAccessForgotPasswordHint = document.getElementById("remote-access-forgot-password-hint");
const remoteAccessPasswordSaveBtn = document.getElementById("remote-access-password-save-btn");
const remoteAccessLogoutBtn = document.getElementById("remote-access-logout-btn");
const remoteAccessStatus = document.getElementById("remote-access-status");
const remoteAccessAddressPanel = document.getElementById("remote-access-address-panel");
const remoteAccessAddressInput = document.getElementById("remote-access-address-input");
const remoteAccessAddressCopyBtn = document.getElementById("remote-access-address-copy-btn");
const remoteAccessQr = document.getElementById("remote-access-qr");
const remoteAccessMdnsHint = document.getElementById("remote-access-mdns-hint");
const remoteAccessMdnsAddress = document.getElementById("remote-access-mdns-address");
const remoteAccessQrMdnsItem = document.getElementById("remote-access-qr-mdns-item");
const remoteAccessQrMdns = document.getElementById("remote-access-qr-mdns");
const remoteAccessDevicesPanel = document.getElementById("remote-access-devices-panel");
const remoteAccessDevicesList = document.getElementById("remote-access-devices-list");
const remoteAccessStorageModes = document.getElementById("remote-access-storage-modes");
const remoteAccessStorageKeepHint = document.getElementById("remote-access-storage-keep-hint");
const remoteAccessStorageRelayHint = document.getElementById("remote-access-storage-relay-hint");
const speedLimitModes = document.getElementById("speed-limit-modes");
const speedLimitStatus = document.getElementById("speed-limit-status");
const speedLimitCustomBtn = document.getElementById("speed-limit-custom-btn");
const speedLimitCustomPanel = document.getElementById("speed-limit-custom-panel");
const speedLimitCustomInput = document.getElementById("speed-limit-custom-input");
const speedLimitCustomSaveBtn = document.getElementById("speed-limit-custom-save-btn");
const speedLimitInfoCustomValue = document.getElementById("speed-limit-info-custom-value");
const settingsExportBtn = document.getElementById("settings-export-btn");
const settingsImportBtn = document.getElementById("settings-import-btn");
const settingsImportFile = document.getElementById("settings-import-file");
const settingsBackupStatus = document.getElementById("settings-backup-status");

function showSettingsBackupStatus(text, kind) {
  if (!settingsBackupStatus) return;
  settingsBackupStatus.textContent = text;
  settingsBackupStatus.classList.remove("hidden", "ok", "bad");
  settingsBackupStatus.classList.add(kind);
}

async function importSettingsBackup() {
  const file = settingsImportFile?.files?.[0];
  if (!file) return;
  try {
    const text = await file.text();
    const data = JSON.parse(text);
    const res = await fetch("/api/settings/import", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const result = await res.json().catch(() => ({}));
      showSettingsBackupStatus(result.detail || t().settingsBackupInvalidFile, "bad");
      return;
    }
    showSettingsBackupStatus(t().settingsBackupImported, "ok");
    // NOTE: reloads so every panel (channels, cookies, speed limit, ...)
    // picks up the freshly-imported values instead of showing stale state.
    setTimeout(() => window.location.reload(), 1200);
  } catch (err) {
    showSettingsBackupStatus(t().settingsBackupInvalidFile, "bad");
  } finally {
    if (settingsImportFile) settingsImportFile.value = "";
  }
}

let cookieMode = "off";
let savedCookieBrowser = "firefox";
let speedLimitMbps = 0;
let homeServerMode = false;

// NOTE: the three fixed buttons above cover the common cases; anything else
// (the user typed their own number) is "custom" - there's no separate flag
// for this in the stored value, a custom speed is just a plain MB/s number
// that doesn't happen to match one of the presets.
const SPEED_LIMIT_PRESETS = [0, 5, 10];
// NOTE: separate from speedLimitMbps on purpose - mirrors cookieMode's "file"
// button: clicking "Custom" reveals the input panel immediately (a purely
// local UI choice, nothing saved yet), independent of whatever value is
// currently actually saved. Saving a preset clears this back to false.
let speedLimitCustomPanelOpen = false;

function renderSpeedLimitMode() {
  const isCustomValue = !SPEED_LIMIT_PRESETS.includes(speedLimitMbps);
  const showCustomPanel = speedLimitCustomPanelOpen || isCustomValue;
  speedLimitModes?.querySelectorAll("[data-speed-limit]").forEach((btn) => {
    const active = !showCustomPanel && Number(btn.dataset.speedLimit) === speedLimitMbps;
    btn.classList.toggle("active", active);
    btn.setAttribute("aria-checked", active ? "true" : "false");
  });
  speedLimitCustomBtn?.classList.toggle("active", showCustomPanel);
  speedLimitCustomBtn?.setAttribute("aria-checked", showCustomPanel ? "true" : "false");
  speedLimitCustomPanel?.classList.toggle("hidden", !showCustomPanel);
  // NOTE: don't stomp on the input while the user is actively typing in it -
  // only pre-fill it with the actually-saved value when it isn't focused.
  if (isCustomValue && speedLimitCustomInput && document.activeElement !== speedLimitCustomInput) {
    speedLimitCustomInput.value = speedLimitMbps;
  }
  updateSpeedLimitInfoRow();
}

// NOTE: MB/s is what yt-dlp/this settings panel work in, but home internet
// plans are near-universally advertised in Mbps (megabits) - 1 MB/s = 8 Mbps.
// Showing both next to each other is what avoids someone reading "5 MB/s" and
// assuming it matches their "50 Mbps" plan number for number.
function updateSpeedLimitInfoRow() {
  if (!speedLimitInfoCustomValue) return;
  const isCustomValue = !SPEED_LIMIT_PRESETS.includes(speedLimitMbps);
  const showCustomPanel = speedLimitCustomPanelOpen || isCustomValue;
  if (!showCustomPanel) {
    speedLimitInfoCustomValue.textContent = "—";
    return;
  }
  // NOTE: reflects whatever is currently TYPED, live, not just the last saved
  // value - the whole point is to help decide on a number before saving it.
  const typed = Number(speedLimitCustomInput?.value);
  if (!Number.isFinite(typed) || typed <= 0) {
    speedLimitInfoCustomValue.textContent = "—";
    return;
  }
  speedLimitInfoCustomValue.textContent = `= ${typed * 8} Mbps`;
}

function saveCustomSpeedLimit() {
  const value = Number(speedLimitCustomInput?.value);
  if (!Number.isInteger(value) || value < 1) {
    showSpeedLimitStatus(t().settingsSpeedLimitInvalid, "bad");
    return;
  }
  saveSpeedLimit(value);
}

// --- Settings -> Downloads -> Download folder ----------------------------------
// NOTE: the folder lives on the computer MediaGrab runs on, so only that
// computer can change it (the server says so in "editable"); a phone sees
// it read-only, and Docker hides the controls entirely - the compose file's
// volume decides there.

const downloadDirSection = document.getElementById("download-dir-section");
const downloadDirPath = document.getElementById("download-dir-path");
const downloadDirDefaultTag = document.getElementById("download-dir-default-tag");
const downloadDirCloud = document.getElementById("download-dir-cloud");
const downloadDirEdit = document.getElementById("download-dir-edit");
const downloadDirBrowseBtn = document.getElementById("download-dir-browse-btn");
const downloadDirResetBtn = document.getElementById("download-dir-reset-btn");
const downloadDirInput = document.getElementById("download-dir-input");
const downloadDirSaveBtn = document.getElementById("download-dir-save-btn");
const downloadDirReadonly = document.getElementById("download-dir-readonly");
const downloadDirDocker = document.getElementById("download-dir-docker");
const downloadDirStatus = document.getElementById("download-dir-status");

// NOTE: the server answers a rejected folder with a short code in "detail"
// (see app.py's _check_download_dir); this turns it into a sentence.
function downloadDirErrorText(code) {
  const messages = {
    relative: t().downloadDirErrRelative,
    inside_app: t().downloadDirErrInsideApp,
    not_a_folder: t().downloadDirErrNotFolder,
    not_writable: t().downloadDirErrNotWritable,
    not_allowed: t().downloadDirErrNotAllowed,
    picker_failed: t().downloadDirErrPicker,
  };
  return messages[code] || code || t().errUnknown;
}

function showDownloadDirStatus(text, kind) {
  if (!downloadDirStatus) return;
  downloadDirStatus.textContent = text;
  downloadDirStatus.classList.remove("hidden", "ok", "bad");
  downloadDirStatus.classList.add(kind);
}

function renderDownloadDir(info) {
  downloadDirPath.textContent = info.path;
  downloadDirDefaultTag.textContent = t().downloadDirDefaultTag;
  downloadDirDefaultTag.classList.toggle("hidden", !info.is_default);
  downloadDirCloud.textContent = info.cloud ? t().downloadDirCloud.replace("{service}", info.cloud) : "";
  downloadDirCloud.classList.toggle("hidden", !info.cloud);
  downloadDirEdit.classList.toggle("hidden", !info.editable);
  downloadDirBrowseBtn.classList.toggle("hidden", !info.can_browse);
  downloadDirResetBtn.classList.toggle("hidden", info.is_default);
  downloadDirDocker.classList.toggle("hidden", !info.is_docker);
  downloadDirReadonly.classList.toggle("hidden", info.editable || info.is_docker);
  if (info.editable && document.activeElement !== downloadDirInput) downloadDirInput.value = info.path;
}

async function loadDownloadDir() {
  if (!downloadDirSection) return;
  try {
    const res = await fetch("/api/download-dir");
    if (!res.ok) throw new Error(String(res.status));
    renderDownloadDir(await res.json());
  } catch (err) {
    showDownloadDirStatus(t().errNetwork + err.message, "bad");
  }
}

async function saveDownloadDir(path) {
  try {
    const res = await fetch("/api/download-dir", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ path }),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      showDownloadDirStatus(downloadDirErrorText(data.detail), "bad");
      return;
    }
    renderDownloadDir(data);
    showDownloadDirStatus(path ? t().downloadDirSaved : t().downloadDirResetDone, "ok");
  } catch (err) {
    showDownloadDirStatus(t().errNetwork + err.message, "bad");
  }
}

downloadDirSaveBtn?.addEventListener("click", () => {
  const value = downloadDirInput.value.trim();
  if (value) saveDownloadDir(value);
});
downloadDirInput?.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && downloadDirInput.value.trim()) saveDownloadDir(downloadDirInput.value.trim());
});
downloadDirResetBtn?.addEventListener("click", () => saveDownloadDir(""));
downloadDirBrowseBtn?.addEventListener("click", async () => {
  // NOTE: the picker opens on this computer's screen, possibly behind the
  // browser - say so, so a "nothing happened" doesn't look like a bug.
  downloadDirBrowseBtn.disabled = true;
  showDownloadDirStatus(t().downloadDirPickerOpen, "ok");
  try {
    const res = await fetch(`/api/download-dir/browse?lang=${lang}`, { method: "POST" });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      showDownloadDirStatus(downloadDirErrorText(data.detail), "bad");
      return;
    }
    if (data.path) {
      await saveDownloadDir(data.path);
    } else {
      downloadDirStatus?.classList.add("hidden");
    }
  } catch (err) {
    showDownloadDirStatus(t().errNetwork + err.message, "bad");
  } finally {
    downloadDirBrowseBtn.disabled = false;
  }
});

function showSpeedLimitStatus(text, kind) {
  if (!speedLimitStatus) return;
  speedLimitStatus.textContent = text;
  speedLimitStatus.classList.remove("hidden", "ok", "bad");
  speedLimitStatus.classList.add(kind);
}

function renderCookieMode() {
  cookieModes?.querySelectorAll("[data-cookie-mode]").forEach((btn) => {
    const active = btn.dataset.cookieMode === cookieMode;
    btn.classList.toggle("active", active);
    btn.setAttribute("aria-checked", active ? "true" : "false");
  });
  cookieFilePanel?.classList.toggle("hidden", cookieMode !== "file");
  cookieBrowserPanel?.classList.toggle("hidden", cookieMode !== "browser");
}

function showCookieStatus(text, kind) {
  if (!cookieStatus) return;
  cookieStatus.textContent = text;
  cookieStatus.classList.remove("hidden", "ok", "bad");
  cookieStatus.classList.add(kind);
}

async function loadSettings() {
  // NOTE: fetched on every page (not just /settings) - defaultAudioLang is
  // needed wherever a video gets probed, which is the home page, not here.
  try {
    const res = await fetch("/api/settings");
    const settings = await res.json();
    defaultAudioLang = settings.default_audio_lang || "";
    if (defaultAudioLangInput) defaultAudioLangInput.value = defaultAudioLang;
    speedLimitMbps = settings.download_speed_limit_mbps || 0;
    renderSpeedLimitMode();
    homeServerMode = !!settings.home_server_mode;
    if (homeServerModeToggle) homeServerModeToggle.checked = homeServerMode;
    cookiesConfigured = (settings.cookie_mode || "off") !== "off";

    if (!cookieModes) return;
    const browsersRes = await fetch("/api/cookie-browsers");
    const browsers = await browsersRes.json();
    if (cookieBrowserSelect) {
      cookieBrowserSelect.innerHTML = (browsers.browsers || [])
        .map((b) => `<option value="${escapeHtml(b)}">${escapeHtml(b)}</option>`)
        .join("");
      cookieBrowserSelect.value = settings.cookie_browser || "firefox";
    }
    if (cookieFileInput) cookieFileInput.value = settings.cookie_file || "";
    // NOTE: a container has no browser profile to read and no host paths to
    // type - uploading is the only cookie source that works there.
    if (browsers.is_docker) {
      cookieModes.querySelector('[data-cookie-mode="browser"]')?.classList.add("hidden");
      cookiePathAdvanced?.classList.add("hidden");
    }
    savedCookieBrowser = settings.cookie_browser || "firefox";
    cookieWindowsNote?.classList.toggle("hidden", browsers.platform !== "win32");
    const unsupported = !(browsers.browsers || []).includes(savedCookieBrowser);
    if (cookieBrowserUnsupported) {
      cookieBrowserUnsupported.textContent = unsupported
        ? t().cookieBrowserUnsupported.replace("{browser}", savedCookieBrowser)
        : "";
      cookieBrowserUnsupported.classList.toggle("hidden", !unsupported);
    }
    cookieMode = settings.cookie_mode || "off";
    renderCookieMode();
    loadCookieFileStatus();
  } catch (err) {
    // NOTE: settings are optional - a failure here shouldn't break the page.
  }
}

// NOTE: POST /api/settings replaces the whole settings object, not just the
// field being changed - so every save action (cookies here, the default
// audio language below) must resend every field's CURRENT value, or saving
// one would silently wipe out the other.
function collectSettingsPayload() {
  return {
    cookie_mode: cookieMode,
    // NOTE: a saved browser that isn't offered on this OS (e.g. "chrome" on
    // Windows) leaves the select with no value - resend the saved one rather
    // than quietly switching it to Firefox, which might not be installed (and
    // a missing Firefox would fail every download just the same).
    cookie_browser: cookieBrowserSelect?.value || savedCookieBrowser,
    cookie_file: cookieFileInput?.value || "",
    default_audio_lang: defaultAudioLangInput?.value || "",
    download_speed_limit_mbps: speedLimitMbps,
    home_server_mode: homeServerMode,
  };
}

// NOTE: mirrors toggleRemoteAccess()'s pattern - a change saves immediately
// (no separate "save" button) and, since this setting is only actually read
// once at process startup (see app.py's lifespan), restarts the server.
async function toggleHomeServerMode() {
  if (!homeServerModeToggle) return;
  const wantEnabled = homeServerModeToggle.checked;
  homeServerModeToggle.disabled = true;
  try {
    const res = await fetch("/api/settings", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ...collectSettingsPayload(), home_server_mode: wantEnabled }),
    });
    if (!res.ok) {
      homeServerModeToggle.checked = !wantEnabled;
      const data = await res.json().catch(() => ({}));
      showRemoteAccessStatus(data.detail || t().cookieTestFailed, "bad");
      homeServerModeToggle.disabled = false;
      return;
    }
    homeServerMode = wantEnabled;
    showRemoteAccessStatus(t().settingsHomeServerRestartNote, "ok");
    waitForServerAndReload();
  } catch (err) {
    homeServerModeToggle.checked = !wantEnabled;
    showRemoteAccessStatus(t().errNetwork + err.message, "bad");
    homeServerModeToggle.disabled = false;
  }
}

// NOTE: mirrors saveRemoteAccessStorageMode()'s pattern - a button click
// saves immediately (no separate "save" button), reverting on failure.
async function saveSpeedLimit(mbps) {
  if (mbps === speedLimitMbps) return;
  const previous = speedLimitMbps;
  speedLimitMbps = mbps;
  renderSpeedLimitMode();
  try {
    const res = await fetch("/api/settings", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(collectSettingsPayload()),
    });
    const data = await res.json();
    if (!res.ok) {
      speedLimitMbps = previous;
      renderSpeedLimitMode();
      showSpeedLimitStatus(data.detail || t().cookieTestFailed, "bad");
      return;
    }
    showSpeedLimitStatus(t().cookieSaved, "ok");
  } catch (err) {
    speedLimitMbps = previous;
    renderSpeedLimitMode();
    showSpeedLimitStatus(t().errNetwork + err.message, "bad");
  }
}

async function saveCookieSettings() {
  if (!cookieSaveBtn) return;
  cookieSaveBtn.disabled = true;
  try {
    const res = await fetch("/api/settings", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(collectSettingsPayload()),
    });
    const data = await res.json();
    if (!res.ok) {
      showCookieStatus(data.detail || t().cookieTestFailed, "bad");
      return;
    }
    showCookieStatus(t().cookieSaved, "ok");
  } catch (err) {
    showCookieStatus(t().errNetwork + err.message, "bad");
  } finally {
    cookieSaveBtn.disabled = false;
  }
}

function showDefaultAudioLangStatus(text, kind) {
  if (!defaultAudioLangStatus) return;
  defaultAudioLangStatus.textContent = text;
  defaultAudioLangStatus.classList.remove("hidden", "ok", "bad");
  defaultAudioLangStatus.classList.add(kind);
}

async function saveDefaultAudioLang() {
  if (!defaultAudioLangSaveBtn) return;
  defaultAudioLangSaveBtn.disabled = true;
  try {
    const payload = collectSettingsPayload();
    const res = await fetch("/api/settings", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    if (!res.ok) {
      showDefaultAudioLangStatus(data.detail || t().cookieTestFailed, "bad");
      return;
    }
    defaultAudioLang = payload.default_audio_lang;
    showDefaultAudioLangStatus(t().cookieSaved, "ok");
  } catch (err) {
    showDefaultAudioLangStatus(t().errNetwork + err.message, "bad");
  } finally {
    defaultAudioLangSaveBtn.disabled = false;
  }
}

async function testCookieSettings() {
  if (!cookieTestBtn) return;
  cookieTestBtn.disabled = true;
  try {
    const res = await fetch("/api/settings/test-cookies", { method: "POST" });
    const data = await res.json();
    if (data.ok) {
      showCookieStatus(t().cookieTestOk.replace("{n}", data.count), "ok");
    } else if (data.reason === "unsupported_browser") {
      showCookieStatus(t().cookieTestUnsupported.replace("{browser}", data.browser || ""), "bad");
    } else if (data.reason === "not_configured") {
      showCookieStatus(t().cookieTestNone, "bad");
    } else {
      // NOTE: yt-dlp's own message is shown verbatim - for the Chrome/Windows
      // case it names the real cause, which no summary of ours would beat.
      showCookieStatus(`${t().cookieTestFailed}: ${data.detail || ""}`.trim(), "bad");
    }
  } catch (err) {
    showCookieStatus(t().errNetwork + err.message, "bad");
  } finally {
    cookieTestBtn.disabled = false;
  }
}

// --- Settings: uploaded cookies.txt -------------------------------------------

// NOTE: the API only ever returns error CODES for a rejected file - the
// wording lives here, in both languages.
function cookieErrorText(code) {
  return t().cookieErrors[code] || code || t().cookieTestFailed;
}

// NOTE: pure (no DOM) so the review list's markup can be tested under Node.
// Site names come from the uploaded file - attacker-controlled text as far as
// this page is concerned - so every one is escaped.
function cookieReviewHtml(info) {
  const suggested = new Set(info.suggested || []);
  const rows = (info.sites || [])
    .map(
      (s) => `
      <label class="cookie-site">
        <input type="checkbox" value="${escapeHtml(s.site)}"${suggested.has(s.site) ? " checked" : ""}>
        <span class="cookie-site-name">${escapeHtml(s.site)}</span>
        <span class="cookie-site-count">${t().cookieCount.replace("{n}", s.count)}</span>
      </label>`,
    )
    .join("");
  return `
    <div class="cookie-review-title">${t().cookieReviewTitle.replace("{n}", (info.sites || []).length)}</div>
    <div class="cookie-site-list">${rows}</div>
    <p class="settings-hint">${t().cookieReviewHint}</p>
    <div class="cookie-actions">
      <button type="button" id="cookie-upload-save-btn">${t().cookieUploadSaveBtn}</button>
      <button type="button" id="cookie-upload-cancel-btn" class="btn-secondary">${t().cookieUploadCancelBtn}</button>
    </div>`;
}

// NOTE: "uploaded" and "last updated" are different moments on purpose -
// yt-dlp writes refreshed cookies back into the file on every download, so
// the file's own time keeps moving while the upload time stays put. A path
// the user typed in has no upload time at all. Pure (fmtDate is passed in)
// so it can be tested under Node.
function cookieCurrentText(data, fmtDate) {
  const summary = data.summary;
  const template = data.source === "uploaded" ? t().cookieCurrentUploaded : t().cookieCurrentPath;
  const parts = [
    template
      .replace("{sites}", summary.sites.length)
      .replace("{n}", summary.total)
      .replace("{path}", data.path || ""),
  ];
  if (data.uploaded_at) parts.push(t().cookieUploadedAt.replace("{date}", fmtDate(data.uploaded_at)));
  if (summary.updated_at) parts.push(t().cookieUpdatedAt.replace("{date}", fmtDate(summary.updated_at)));
  return parts.join(" · ");
}

let pendingCookieText = null;

function resetCookieUpload() {
  pendingCookieText = null;
  if (cookieUploadInput) cookieUploadInput.value = "";
  cookieReview?.classList.add("hidden");
  if (cookieReview) cookieReview.innerHTML = "";
}

async function loadCookieFileStatus() {
  if (!cookieCurrent) return;
  let data;
  try {
    const res = await fetch("/api/cookies");
    data = await res.json();
  } catch (err) {
    return;
  }
  const summary = data.summary;
  if (!data.source) {
    cookieCurrent.classList.add("hidden");
    cookieCurrent.innerHTML = "";
    // NOTE: nothing uploaded yet - the how-to is what the user needs next.
    if (cookieHowto) cookieHowto.open = true;
    return;
  }
  let line;
  if (!summary) {
    line = `<span class="cookie-warning">${escapeHtml(t().cookieCurrentUnreadable.replace("{path}", data.path || ""))}</span>`;
  } else {
    const text = cookieCurrentText(data, (iso) =>
      new Date(iso).toLocaleString(lang === "tr" ? "tr-TR" : "en-US"),
    );
    const youtube = summary.youtube_signed_in
      ? `<span class="cookie-youtube ok">${t().cookieYoutubeOk}</span>`
      : `<span class="cookie-youtube bad">${t().cookieYoutubeMissing}</span>`;
    line = `<div>${escapeHtml(text)}</div>${youtube}`;
  }
  // NOTE: only the uploaded copy gets a delete button - a path the user typed
  // in points at THEIR file, which MediaGrab never deletes.
  const deleteBtn =
    data.source === "uploaded"
      ? `<button type="button" id="cookie-delete-btn" class="btn-secondary">${t().cookieDeleteBtn}</button>`
      : "";
  cookieCurrent.innerHTML = `<div class="cookie-current-text">${line}</div>${deleteBtn}`;
  cookieCurrent.classList.remove("hidden");
  if (cookieHowto) cookieHowto.open = false;
  document.getElementById("cookie-delete-btn")?.addEventListener("click", deleteUploadedCookies);
}

async function inspectCookieUpload() {
  const file = cookieUploadInput?.files?.[0];
  if (!file) return;
  let text;
  try {
    text = await file.text();
  } catch (err) {
    showCookieStatus(t().cookieReadFailed, "bad");
    return;
  }
  try {
    const res = await fetch("/api/cookies/inspect", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ content: text }),
    });
    const data = await res.json();
    if (!res.ok) {
      resetCookieUpload();
      // NOTE: FastAPI's own 422 (e.g. the body-size cap) has a list here, not
      // one of our codes.
      showCookieStatus(cookieErrorText(typeof data.detail === "string" ? data.detail : "too_large"), "bad");
      return;
    }
    pendingCookieText = text;
    cookieStatus?.classList.add("hidden");
    cookieReview.innerHTML = cookieReviewHtml(data);
    cookieReview.classList.remove("hidden");
    document.getElementById("cookie-upload-save-btn")?.addEventListener("click", saveCookieUpload);
    document.getElementById("cookie-upload-cancel-btn")?.addEventListener("click", resetCookieUpload);
  } catch (err) {
    showCookieStatus(t().errNetwork + err.message, "bad");
  }
}

async function saveCookieUpload() {
  if (pendingCookieText === null || !cookieReview) return;
  const sites = [...cookieReview.querySelectorAll('input[type="checkbox"]:checked')].map((el) => el.value);
  if (!sites.length) {
    showCookieStatus(cookieErrorText("nothing_selected"), "bad");
    return;
  }
  const btn = document.getElementById("cookie-upload-save-btn");
  if (btn) btn.disabled = true;
  try {
    const res = await fetch("/api/cookies/upload", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ content: pendingCookieText, sites }),
    });
    const data = await res.json();
    if (!res.ok) {
      showCookieStatus(cookieErrorText(typeof data.detail === "string" ? data.detail : ""), "bad");
      return;
    }
    resetCookieUpload();
    // NOTE: the upload route already switched the server to file mode - the
    // page's own copy of the settings follows, so a later "Save" (or another
    // settings form, see collectSettingsPayload) doesn't switch it back.
    await loadSettings();
    showCookieStatus(t().cookieUploaded.replace("{n}", data.total), "ok");
  } catch (err) {
    showCookieStatus(t().errNetwork + err.message, "bad");
  } finally {
    if (btn) btn.disabled = false;
  }
}

async function deleteUploadedCookies() {
  if (!window.confirm(t().cookieDeleteConfirm)) return;
  try {
    const res = await fetch("/api/cookies", { method: "DELETE" });
    if (!res.ok) throw new Error(String(res.status));
    await loadSettings();
    showCookieStatus(t().cookieDeleted, "ok");
  } catch (err) {
    showCookieStatus(t().errNetwork + err.message, "bad");
  }
}

// NOTE: whether a password already exists server-side - the toggle checks
// this itself before even trying to enable, since the backend refuses to
// turn remote access on without one anyway (see /api/remote-access).
let remoteAccessHasPassword = false;
let remoteAccessDownloadMode = "keep";

// NOTE: mirrors renderCookieMode()'s button-group pattern - "keep" (a
// personal computer, plenty of disk) vs "relay" (storage-constrained host,
// e.g. a Raspberry Pi: delete the host's copy right after a remote device
// has fully received it - see _relay_delete_background in app.py).
function renderRemoteAccessStorageMode() {
  remoteAccessStorageModes?.querySelectorAll("[data-storage-mode]").forEach((btn) => {
    const active = btn.dataset.storageMode === remoteAccessDownloadMode;
    btn.classList.toggle("active", active);
    btn.setAttribute("aria-checked", active ? "true" : "false");
  });
  remoteAccessStorageKeepHint?.classList.toggle("hidden", remoteAccessDownloadMode !== "keep");
  remoteAccessStorageRelayHint?.classList.toggle("hidden", remoteAccessDownloadMode !== "relay");
}

function showRemoteAccessStatus(text, kind) {
  if (!remoteAccessStatus) return;
  remoteAccessStatus.textContent = text;
  remoteAccessStatus.classList.remove("hidden", "ok", "bad");
  remoteAccessStatus.classList.add(kind);
}

function renderRemoteAccessAddress(lanUrl, mdnsUrl) {
  if (!remoteAccessAddressPanel) return;
  if (lanUrl) {
    remoteAccessAddressPanel.classList.remove("hidden");
    if (remoteAccessAddressInput) remoteAccessAddressInput.value = lanUrl;
    renderRemoteAccessQr(remoteAccessQr, lanUrl);
  } else {
    remoteAccessAddressPanel.classList.add("hidden");
  }
  // NOTE: mdnsUrl is a best-effort EXTRA alongside lanUrl (which is always
  // shown/used as the primary address) - never a replacement for it. See
  // RemoteAccessStatus.mdns_url in models.py. Its own QR code is a separate,
  // clearly-labeled one next to the IP's - scanning the wrong one on a device
  // where ".local" doesn't resolve would otherwise look like a silent failure.
  if (mdnsUrl && remoteAccessMdnsHint && remoteAccessMdnsAddress) {
    remoteAccessMdnsAddress.textContent = mdnsUrl;
    remoteAccessMdnsHint.classList.remove("hidden");
    remoteAccessQrMdnsItem?.classList.remove("hidden");
    renderRemoteAccessQr(remoteAccessQrMdns, mdnsUrl);
  } else {
    remoteAccessMdnsHint?.classList.add("hidden");
    remoteAccessQrMdnsItem?.classList.add("hidden");
  }
}

// NOTE: QRCode (mediagrab/static/qrcode.js, loaded only on this page) has no
// "update" method - re-rendering means clearing the container and building a
// fresh instance, which is fine here since this only ever runs once per
// Settings page load / remote-access status refresh, not on every keystroke.
function renderRemoteAccessQr(container, text) {
  if (!container || typeof QRCode === "undefined") return;
  container.innerHTML = "";
  new QRCode(container, { text, width: 160, height: 160, correctLevel: QRCode.CorrectLevel.M });
}

// NOTE: the button reads "Update" once a password already exists, rather
// than always "Save" - a password is never shown back after saving, so
// "Update" is the only signal that submitting again REPLACES a real, working
// password rather than setting one for the first time.
function renderRemoteAccessPasswordBtnLabel() {
  if (remoteAccessPasswordSaveBtn) {
    remoteAccessPasswordSaveBtn.textContent = remoteAccessHasPassword
      ? t().settingsRemoteAccessUpdatePasswordBtn
      : t().settingsRemoteAccessSetPasswordBtn;
  }
  // NOTE: nothing to confirm against on the very first password - the
  // "current password" field (and the forgot-password pointer next to it)
  // only make sense once a real one already exists.
  remoteAccessCurrentPasswordRow?.classList.toggle("hidden", !remoteAccessHasPassword);
  remoteAccessForgotPasswordHint?.classList.toggle("hidden", !remoteAccessHasPassword);
}

async function loadRemoteAccessStatus() {
  if (!remoteAccessToggle) return;
  try {
    const res = await fetch("/api/remote-access");
    const data = await res.json();
    remoteAccessHasPassword = !!data.has_password;
    remoteAccessToggle.checked = !!data.enabled;
    remoteAccessDownloadMode = data.download_mode || "keep";
    renderRemoteAccessAddress(data.lan_url, data.mdns_url);
    renderRemoteAccessPasswordBtnLabel();
    renderRemoteAccessStorageMode();
  } catch (err) {
    // NOTE: same as the rest of settings - a failed fetch just leaves the
    // panel at its default (off), it doesn't break the page.
  }
  loadRemoteAccessDevices();
}

// NOTE: a plain locale-formatted timestamp - "which device connected when"
// only needs to be roughly legible, not a fancy "3 minutes ago" ticker.
function fmtDeviceConnectedAt(unixSeconds) {
  const date = new Date(unixSeconds * 1000);
  return date.toLocaleString(lang === "tr" ? "tr-TR" : "en-US", {
    dateStyle: "medium",
    timeStyle: "short",
  });
}

function remoteAccessDeviceRowHtml(session) {
  const action = session.is_current
    ? `<span class="remote-access-device-badge">${escapeHtml(t().settingsRemoteAccessThisDevice)}</span>`
    : `<button type="button" class="btn-secondary remote-access-revoke-btn" data-session-id="${escapeHtml(session.id)}">${escapeHtml(t().settingsRemoteAccessRevokeBtn)}</button>`;
  return `
    <div class="remote-access-device-row">
      <div>
        <span class="remote-access-device-name">${escapeHtml(session.device)}</span>
        <span class="remote-access-device-meta">${escapeHtml(fmtDeviceConnectedAt(session.created_at))}</span>
      </div>
      ${action}
    </div>`;
}

async function loadRemoteAccessDevices() {
  if (!remoteAccessDevicesPanel || !remoteAccessDevicesList) return;
  try {
    const res = await fetch("/api/remote-access/sessions");
    const data = await res.json();
    const sessions = data.sessions || [];
    if (sessions.length === 0) {
      remoteAccessDevicesPanel.classList.add("hidden");
      return;
    }
    remoteAccessDevicesPanel.classList.remove("hidden");
    remoteAccessDevicesList.innerHTML = sessions.map(remoteAccessDeviceRowHtml).join("");
  } catch (err) {
    // NOTE: best-effort, same as the rest of this panel.
  }
}

async function revokeRemoteAccessDevice(sessionId) {
  try {
    await fetch(`/api/remote-access/sessions/${sessionId}`, { method: "DELETE" });
  } catch (err) {
    // NOTE: best-effort - if this failed, the row simply won't disappear
    // and the user can just try again.
  }
  loadRemoteAccessDevices();
}

async function toggleRemoteAccess() {
  const wantEnabled = remoteAccessToggle.checked;
  if (wantEnabled && !remoteAccessHasPassword) {
    remoteAccessToggle.checked = false;
    remoteAccessNeedPasswordHint?.classList.remove("hidden");
    return;
  }
  remoteAccessNeedPasswordHint?.classList.add("hidden");
  remoteAccessToggle.disabled = true;
  try {
    const res = await fetch("/api/remote-access", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ enabled: wantEnabled, download_mode: remoteAccessDownloadMode }),
    });
    const data = await res.json();
    if (!res.ok) {
      remoteAccessToggle.checked = !wantEnabled;
      showRemoteAccessStatus(data.detail || t().cookieTestFailed, "bad");
      return;
    }
    // NOTE: changing this setting restarts the server (it changes which
    // network interface it listens on - see run.py) - same "tell the user,
    // then poll until it's back" flow as the yt-dlp/deps updaters.
    showRemoteAccessStatus(t().settingsRemoteAccessRestartNote, "ok");
    waitForServerAndReload();
  } catch (err) {
    remoteAccessToggle.checked = !wantEnabled;
    showRemoteAccessStatus(t().errNetwork + err.message, "bad");
    remoteAccessToggle.disabled = false;
  }
}

async function saveRemoteAccessPassword() {
  if (!remoteAccessPasswordSaveBtn) return;
  const currentPassword = remoteAccessCurrentPasswordInput?.value || "";
  const password = remoteAccessPasswordInput?.value || "";
  const confirmPassword = remoteAccessPasswordConfirmInput?.value || "";

  // NOTE: checked client-side first purely to save a round trip on an
  // obvious mistake - the server enforces the same rules regardless (never
  // trust the client alone for the current-password check in particular).
  if (remoteAccessHasPassword && !currentPassword) {
    showRemoteAccessStatus(t().settingsRemoteAccessCurrentPasswordRequired, "bad");
    return;
  }
  if (password.length < 8) {
    showRemoteAccessStatus(t().settingsRemoteAccessPasswordTooShort, "bad");
    return;
  }
  if (password !== confirmPassword) {
    showRemoteAccessStatus(t().settingsRemoteAccessPasswordsDontMatch, "bad");
    return;
  }

  remoteAccessPasswordSaveBtn.disabled = true;
  try {
    const res = await fetch("/api/remote-access/password", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ password, current_password: currentPassword }),
    });
    const data = await res.json();
    if (!res.ok) {
      const isWrongCurrent = res.status === 401;
      showRemoteAccessStatus(
        isWrongCurrent ? t().settingsRemoteAccessWrongCurrentPassword : data.detail || t().cookieTestFailed,
        "bad"
      );
      return;
    }
    remoteAccessHasPassword = !!data.has_password;
    if (remoteAccessCurrentPasswordInput) remoteAccessCurrentPasswordInput.value = "";
    if (remoteAccessPasswordInput) remoteAccessPasswordInput.value = "";
    if (remoteAccessPasswordConfirmInput) remoteAccessPasswordConfirmInput.value = "";
    renderRemoteAccessPasswordBtnLabel();
    showRemoteAccessStatus(t().settingsRemoteAccessPasswordSaved, "ok");
  } catch (err) {
    showRemoteAccessStatus(t().errNetwork + err.message, "bad");
  } finally {
    remoteAccessPasswordSaveBtn.disabled = false;
  }
}

async function saveRemoteAccessStorageMode(mode) {
  if (mode === remoteAccessDownloadMode) return;
  const previous = remoteAccessDownloadMode;
  remoteAccessDownloadMode = mode;
  renderRemoteAccessStorageMode();
  try {
    const res = await fetch("/api/remote-access", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      // NOTE: enabled is resent as its CURRENT value, unchanged - this call
      // only ever changes download_mode. Since remote_access_active() (what
      // decides whether the server needs to restart) depends only on
      // enabled+password, never on download_mode, this never restarts the
      // server - it's a plain settings save.
      body: JSON.stringify({ enabled: !!remoteAccessToggle?.checked, download_mode: mode }),
    });
    if (!res.ok) {
      remoteAccessDownloadMode = previous;
      renderRemoteAccessStorageMode();
      const data = await res.json().catch(() => ({}));
      showRemoteAccessStatus(data.detail || t().cookieTestFailed, "bad");
      return;
    }
    showRemoteAccessStatus(t().settingsRemoteAccessStorageSaved, "ok");
  } catch (err) {
    remoteAccessDownloadMode = previous;
    renderRemoteAccessStorageMode();
    showRemoteAccessStatus(t().errNetwork + err.message, "bad");
  }
}

async function logoutRemoteAccess() {
  if (!remoteAccessLogoutBtn) return;
  remoteAccessLogoutBtn.disabled = true;
  try {
    await fetch("/api/logout", { method: "POST" });
    showRemoteAccessStatus(t().settingsRemoteAccessLoggedOut, "ok");
  } catch (err) {
    // NOTE: best-effort - if this fails the session just expires on its own.
  } finally {
    remoteAccessLogoutBtn.disabled = false;
  }
}

cookieModes?.querySelectorAll("[data-cookie-mode]").forEach((btn) => {
  btn.addEventListener("click", () => {
    cookieMode = btn.dataset.cookieMode;
    renderCookieMode();
  });
});
cookieSaveBtn?.addEventListener("click", saveCookieSettings);
cookieUploadInput?.addEventListener("change", inspectCookieUpload);
cookieTestBtn?.addEventListener("click", testCookieSettings);
speedLimitModes?.querySelectorAll("[data-speed-limit]").forEach((btn) => {
  btn.addEventListener("click", () => {
    speedLimitCustomPanelOpen = false;
    saveSpeedLimit(Number(btn.dataset.speedLimit));
  });
});
speedLimitCustomBtn?.addEventListener("click", () => {
  speedLimitCustomPanelOpen = true;
  renderSpeedLimitMode();
  speedLimitCustomInput?.focus();
});
speedLimitCustomSaveBtn?.addEventListener("click", saveCustomSpeedLimit);
speedLimitCustomInput?.addEventListener("keydown", (e) => {
  if (e.key === "Enter") saveCustomSpeedLimit();
});
speedLimitCustomInput?.addEventListener("input", updateSpeedLimitInfoRow);
settingsExportBtn?.addEventListener("click", () => {
  // NOTE: native navigation, not fetch() - the route's Content-Disposition:
  // attachment header is what makes the browser save the file; fetch()
  // would just receive the bytes into JS and discard them (same reasoning
  // as revealFile()'s remote-download path).
  window.location.href = "/api/settings/export";
});
settingsImportBtn?.addEventListener("click", () => settingsImportFile?.click());
settingsImportFile?.addEventListener("change", importSettingsBackup);
defaultAudioLangSaveBtn?.addEventListener("click", saveDefaultAudioLang);
remoteAccessToggle?.addEventListener("change", toggleRemoteAccess);
homeServerModeToggle?.addEventListener("change", toggleHomeServerMode);
remoteAccessPasswordSaveBtn?.addEventListener("click", saveRemoteAccessPassword);
remoteAccessLogoutBtn?.addEventListener("click", logoutRemoteAccess);
remoteAccessStorageModes?.querySelectorAll("[data-storage-mode]").forEach((btn) => {
  btn.addEventListener("click", () => saveRemoteAccessStorageMode(btn.dataset.storageMode));
});
remoteAccessShowPasswordsToggle?.addEventListener("change", () => {
  const fieldType = remoteAccessShowPasswordsToggle.checked ? "text" : "password";
  [remoteAccessCurrentPasswordInput, remoteAccessPasswordInput, remoteAccessPasswordConfirmInput].forEach((input) => {
    if (input) input.type = fieldType;
  });
});
remoteAccessAddressCopyBtn?.addEventListener("click", () => {
  if (!remoteAccessAddressInput) return;
  navigator.clipboard?.writeText(remoteAccessAddressInput.value).catch(() => {});
  const original = remoteAccessAddressCopyBtn.textContent;
  remoteAccessAddressCopyBtn.textContent = t().settingsRemoteAccessCopied;
  setTimeout(() => {
    remoteAccessAddressCopyBtn.textContent = original;
  }, 1500);
});
// NOTE: one delegated listener, like the download dock - the list's rows are
// rebuilt wholesale on every refresh, so per-button listeners would just be
// lost (and re-added) each time.
remoteAccessDevicesList?.addEventListener("click", (e) => {
  const btn = e.target.closest?.(".remote-access-revoke-btn");
  if (btn) revokeRemoteAccessDevice(btn.dataset.sessionId);
});

probeBtn?.addEventListener("click", probe);
urlInput?.addEventListener("keydown", (e) => {
  if (e.key === "Enter") probe();
});
urlInput?.addEventListener("paste", () => {
  // NOTE: the paste event fires before the input's value actually contains
  // the pasted text in some browsers - a 0ms timeout lets that settle
  // before reading it, so "paste = resolve" doesn't fire on the stale
  // (pre-paste) value.
  setTimeout(() => {
    if (urlInput.value.trim()) probe();
  }, 0);
});
if (pasteBtn && (!window.isSecureContext || !navigator.clipboard?.readText)) {
  // NOTE: the Clipboard read API is entirely absent (no permission prompt to
  // even deny) on any non-HTTPS origin other than localhost/127.0.0.1 -
  // exactly MediaGrab's own Remote Access, which is plain HTTP by design
  // (see the README's security note). That's every device connecting over
  // the LAN, desktop or mobile - a dedicated paste-shortcut button can never
  // work there, so it's hidden rather than sitting there doing nothing (a
  // focus()-and-hope fallback was tried and confirmed NOT to read as "did
  // something" on a real phone). Long-pressing the field for the OS's own
  // Paste option still works and still auto-resolves via the "paste" event
  // handler below - no functionality is actually lost, only the shortcut.
  pasteBtn.hidden = true;
} else {
  pasteBtn?.addEventListener("click", async () => {
    try {
      const text = await navigator.clipboard.readText();
      if (text && text.trim()) {
        urlInput.value = text.trim();
        probe();
      }
    } catch (err) {
      // NOTE: clipboard read can be denied by the browser (permissions) - the
      // user can still paste manually into the input, so fail silently.
    }
  });
}
langSwitch?.querySelectorAll("button").forEach((btn) => {
  btn.addEventListener("click", () => setLang(btn.dataset.lang));
});
// NOTE: one delegated listener on the dock container, which is never
// replaced - individual rows are, so per-button listeners would be lost
// (and re-added) on every rebuild.
downloadDock?.addEventListener("click", (e) => {
  const revealBtn = e.target.closest?.(".dock-reveal-btn");
  if (revealBtn) {
    const job = dockJobs.find((j) => j.jobId === revealBtn.dataset.jobId);
    revealFile(`/api/file/${revealBtn.dataset.jobId}`, job?.filename).then((outcome) =>
      showSaveOutcome(revealBtn, outcome),
    );
    return;
  }
  const closeBtn = e.target.closest?.(".dock-dismiss-btn");
  if (!closeBtn) return;
  if (closeBtn.dataset.action === "cancel") {
    cancelDockJob(closeBtn.dataset.jobId);
  } else {
    dismissDockJob(closeBtn.dataset.jobId);
  }
});
themeToggle?.addEventListener("click", toggleTheme);
themeChoice?.querySelectorAll("[data-theme-choice]").forEach((btn) => {
  btn.addEventListener("click", () => setThemePreference(btn.dataset.themeChoice));
});
renderThemeControls();

// NOTE: the sticky result-preview panel needs to stop exactly where the
// sticky header ends, not a guessed pixel value - measuring the real,
// rendered height keeps this correct even if the header's content (nav
// items, font) ever changes its height.
function updateHeaderHeightVar() {
  const header = document.querySelector(".site-header");
  if (header) {
    document.documentElement.style.setProperty("--header-height", `${header.offsetHeight}px`);
  }
}
updateHeaderHeightVar();
window.addEventListener("resize", updateHeaderHeightVar);

// NOTE: below the .nav-toggle breakpoint (see style.css), the nav is a
// collapsible vertical list instead of always-visible links - closed by
// default, since the page's own heading already says where you are.
const navToggle = document.getElementById("nav-toggle");
const siteNavEl = document.getElementById("site-nav");
navToggle?.addEventListener("click", () => {
  const isOpen = siteNavEl.classList.toggle("nav-open");
  navToggle.setAttribute("aria-expanded", String(isOpen));
});

// NOTE: while following the OS (no explicit choice), track live changes to it
// so the icon doesn't go stale if the system flips theme on a schedule.
window.matchMedia("(prefers-color-scheme: light)").addEventListener("change", () => {
  if (!document.documentElement.dataset.theme) renderThemeControls();
});
historyClearBtn?.addEventListener("click", clearAllHistory);
historySearchInput?.addEventListener("input", applyHistoryFilters);
historyChannelFilter?.addEventListener("change", applyHistoryFilters);
historyTypeFilter?.addEventListener("change", applyHistoryFilters);

// --- Gecmis: izgara/liste gorunumu ---

function applyHistoryViewMode(mode) {
  if (!historyList) return;
  historyList.classList.toggle("view-list", mode === "list");
  historyViewGridBtn?.classList.toggle("active", mode !== "list");
  historyViewListBtn?.classList.toggle("active", mode === "list");
}

if (historyList) {
  let savedView = "grid";
  try {
    savedView = localStorage.getItem("mediagrab_history_view") || "grid";
  } catch (e) {
    // NOTE: private browsing / storage disabled - just default to grid.
  }
  applyHistoryViewMode(savedView);

  historyViewGridBtn?.addEventListener("click", () => {
    applyHistoryViewMode("grid");
    try {
      localStorage.setItem("mediagrab_history_view", "grid");
    } catch (e) {}
  });
  historyViewListBtn?.addEventListener("click", () => {
    applyHistoryViewMode("list");
    try {
      localStorage.setItem("mediagrab_history_view", "list");
    } catch (e) {}
  });
}
// --- History -> Statistics ---------------------------------------------------
// NOTE: no chart library (that would mean a CDN, against "local, works
// offline") - plain HTML/CSS bars. Data comes from /api/stats, which groups
// the stored UTC hours into THIS browser's days/weeks/months (tz below).

const historyTabButtons = document.querySelectorAll("[data-history-tab]");
const historyFilesPanel = document.getElementById("history-files-panel");
const historyStatsPanel = document.getElementById("history-stats-panel");
const statsPeriodButtons = document.querySelectorAll("[data-stats-period]");
const statsStatus = document.getElementById("stats-status");
const statsTiles = document.getElementById("stats-tiles");
const statsBars = document.getElementById("stats-bars");
const statsSites = document.getElementById("stats-sites");
const statsAudio = document.getElementById("stats-audio");
const statsVideo = document.getElementById("stats-video");
const statsDisk = document.getElementById("stats-disk");
const statsResetBtn = document.getElementById("stats-reset-btn");
const statsTooltip = document.getElementById("stats-tooltip");

// NOTE: colour follows the FORMAT, never its rank - 1080p is the same colour
// whether it's the most or least downloaded, and adding a 4K download
// doesn't repaint the rest. Slots map to the --series-N tokens (style.css),
// a palette validated for colour-blind separation in both themes; anything
// outside these lists (rare 4320p, unreadable files) is the neutral "other".
const STATS_FORMAT_ORDER = {
  audio: ["opus", "m4a", "mp3"],
  video: ["2160p", "1440p", "1080p", "720p", "480p", "360p", "240p", "144p"],
};

let statsPeriod = "day";
let statsPollTimer = null;

// NOTE: binary units like the rest of the app (human_size in downloader.py),
// with a decimal only where it carries information ("1,4 GB", not "1 GB";
// "512 MB", not "512,0 MB"), in the page's own number format.
function formatBytes(bytes, language) {
  const units = ["B", "KB", "MB", "GB", "TB"];
  let value = Math.max(0, Number(bytes) || 0);
  let unit = 0;
  while (value >= 1024 && unit < units.length - 1) {
    value /= 1024;
    unit++;
  }
  const digits = unit >= 3 && value < 100 ? 1 : 0;
  const text = new Intl.NumberFormat(language === "en" ? "en-US" : "tr-TR", {
    maximumFractionDigits: digits,
  }).format(value);
  return `${text} ${units[unit]}`;
}

function statsBucketLabel(startIso, period, language) {
  const [y, m, d] = startIso.split("-").map(Number);
  const date = new Date(y, m - 1, d);
  const locale = language === "en" ? "en-US" : "tr-TR";
  if (period === "month") return new Intl.DateTimeFormat(locale, { month: "short", year: "2-digit" }).format(date);
  return new Intl.DateTimeFormat(locale, { day: "numeric", month: "short" }).format(date);
}

// NOTE: rows -> stacked-bar segments with a fixed colour slot each. Formats
// outside the known order fold into one "other" segment at the end, so the
// bar never needs a colour the palette doesn't have.
function statsShares(rows, kind) {
  const order = STATS_FORMAT_ORDER[kind] || [];
  const total = rows.reduce((sum, row) => sum + row.count, 0);
  if (!total) return [];
  const known = [];
  let other = null;
  for (const row of rows) {
    const slot = order.indexOf(row.name);
    if (slot === -1) {
      other = other || { name: "", slot: 0, count: 0, bytes: 0 };
      other.count += row.count;
      other.bytes += row.bytes;
    } else {
      known.push({ name: row.name, slot: slot + 1, count: row.count, bytes: row.bytes });
    }
  }
  known.sort((a, b) => a.slot - b.slot);
  if (other) known.push(other);
  return known.map((share) => ({ ...share, percent: (share.count / total) * 100 }));
}

function statsPercentText(percent) {
  if (percent > 0 && percent < 1) return "<1%";
  return `${Math.round(percent)}%`;
}

function statsSiteName(name) {
  if (!name) return t().statsUnknownSite;
  if (name === "Generic") return t().statsGenericSite;
  return name;
}

function statsFilesText(count) {
  const template = count === 1 ? t().statsFileOne : t().statsFiles;
  return template.replace("{n}", new Intl.NumberFormat(lang === "en" ? "en-US" : "tr-TR").format(count));
}

function renderStatsTiles(data) {
  const windowLabel = { day: t().statsWindowDay, week: t().statsWindowWeek, month: t().statsWindowMonth }[data.period];
  const since = data.total.since
    ? t().statsSince.replace("{date}", new Intl.DateTimeFormat(lang === "en" ? "en-US" : "tr-TR", { dateStyle: "medium" }).format(new Date(`${data.total.since}T00:00:00`)))
    : "";
  const tiles = [
    { label: windowLabel, value: statsFilesText(data.window.count), sub: formatBytes(data.window.bytes, lang) },
    { label: t().statsTotal, value: statsFilesText(data.total.count), sub: [formatBytes(data.total.bytes, lang), since].filter(Boolean).join(" · ") },
  ];
  if (data.disk) {
    tiles.push({
      label: t().statsDiskFree,
      value: formatBytes(data.disk.free, lang),
      sub: t().statsDiskOf.replace("{total}", formatBytes(data.disk.total, lang)),
    });
  }
  statsTiles.innerHTML = tiles
    .map(
      (tile) => `
      <div class="stats-tile">
        <div class="stats-tile-label">${escapeHtml(tile.label)}</div>
        <div class="stats-tile-value">${escapeHtml(tile.value)}</div>
        <div class="stats-tile-sub">${escapeHtml(tile.sub)}</div>
      </div>`,
    )
    .join("");
}

function renderStatsBars(data) {
  const max = Math.max(1, ...data.buckets.map((b) => b.count));
  statsBars.innerHTML = `
    <div class="stats-bars-scale" aria-hidden="true"><span>${max}</span><span>0</span></div>
    <div class="stats-bars-plot">
      ${data.buckets
        .map((bucket) => {
          const label = statsBucketLabel(bucket.start, data.period, lang);
          const tip = `${label}: ${statsFilesText(bucket.count)} · ${formatBytes(bucket.bytes, lang)}`;
          const height = bucket.count ? Math.max(2, (bucket.count / max) * 100) : 0;
          return `
            <div class="stats-bar-col" tabindex="0" data-tip="${escapeHtml(tip)}" aria-label="${escapeHtml(tip)}">
              <div class="stats-bar-track"><div class="stats-bar" style="height:${height}%"></div></div>
              <div class="stats-bar-label">${escapeHtml(label)}</div>
            </div>`;
        })
        .join("")}
    </div>`;
}

function renderStatsSites(rows) {
  if (!rows.length) {
    statsSites.innerHTML = `<div class="stats-empty">${t().statsEmpty}</div>`;
    return;
  }
  // NOTE: one series, so one colour and no legend - the names ARE the labels.
  const shown = rows.slice(0, 7);
  const rest = rows.slice(7);
  if (rest.length) {
    shown.push({
      name: null,
      count: rest.reduce((s, r) => s + r.count, 0),
      bytes: rest.reduce((s, r) => s + r.bytes, 0),
    });
  }
  const max = Math.max(...shown.map((r) => r.count));
  statsSites.innerHTML = shown
    .map((row) => {
      const name = row.name === null ? t().statsOther : statsSiteName(row.name);
      const detail = `${statsFilesText(row.count)} · ${formatBytes(row.bytes, lang)}`;
      return `
        <div class="stats-site-row">
          <div class="stats-site-head"><span class="stats-site-name">${escapeHtml(name)}</span><span class="stats-site-detail">${escapeHtml(detail)}</span></div>
          <div class="stats-site-track"><div class="stats-site-bar" style="width:${(row.count / max) * 100}%"></div></div>
        </div>`;
    })
    .join("");
}

function renderStatsShares(container, rows, kind) {
  const shares = statsShares(rows, kind);
  if (!shares.length) {
    container.innerHTML = `<div class="stats-empty">${t().statsEmpty}</div>`;
    return;
  }
  const nameOf = (share) => (share.name ? share.name : share.slot === 0 && kind === "video" ? t().statsOtherFormat : t().statsOther);
  container.innerHTML = `
    <div class="stats-stack" role="img" aria-label="${escapeHtml(shares.map((s) => `${nameOf(s)} ${statsPercentText(s.percent)}`).join(", "))}">
      ${shares
        .map((share) => {
          const tip = `${nameOf(share)}: ${statsPercentText(share.percent)} · ${statsFilesText(share.count)} · ${formatBytes(share.bytes, lang)}`;
          return `<div class="stats-seg" data-slot="${share.slot}" style="flex-grow:${share.count}" data-tip="${escapeHtml(tip)}"></div>`;
        })
        .join("")}
    </div>
    <ul class="stats-legend">
      ${shares
        .map(
          (share) => `
          <li>
            <span class="stats-swatch" data-slot="${share.slot}"></span>
            <span class="stats-legend-name">${escapeHtml(nameOf(share))}</span>
            <span class="stats-legend-value">${statsPercentText(share.percent)}</span>
            <span class="stats-legend-detail">${escapeHtml(statsFilesText(share.count))}</span>
          </li>`,
        )
        .join("")}
    </ul>`;
}

function renderStatsDisk(disk) {
  if (!disk) {
    statsDisk.innerHTML = `<div class="stats-empty">${t().statsDiskUnavailable}</div>`;
    return;
  }
  const otherUsed = Math.max(0, disk.used - disk.downloads);
  const parts = [
    { key: "downloads", label: t().statsDiskDownloads, bytes: disk.downloads },
    { key: "other", label: t().statsDiskOther, bytes: otherUsed },
    { key: "free", label: t().statsDiskFree, bytes: disk.free },
  ];
  const total = Math.max(1, disk.total);
  statsDisk.innerHTML = `
    <div class="stats-stack stats-disk-stack" role="img" aria-label="${escapeHtml(parts.map((p) => `${p.label} ${formatBytes(p.bytes, lang)}`).join(", "))}">
      ${parts
        .map((part) => {
          const tip = `${part.label}: ${formatBytes(part.bytes, lang)} (${statsPercentText((part.bytes / total) * 100)})`;
          return `<div class="stats-seg stats-disk-${part.key}" style="flex-grow:${part.bytes}" data-tip="${escapeHtml(tip)}"></div>`;
        })
        .join("")}
    </div>
    <ul class="stats-legend">
      ${parts
        .map(
          (part) => `
          <li>
            <span class="stats-swatch stats-disk-${part.key}"></span>
            <span class="stats-legend-name">${escapeHtml(part.label)}</span>
            <span class="stats-legend-value">${escapeHtml(formatBytes(part.bytes, lang))}</span>
          </li>`,
        )
        .join("")}
    </ul>`;
}

function showStatsStatus(text, kind) {
  if (!statsStatus) return;
  statsStatus.textContent = text;
  statsStatus.className = `stats-status${kind ? ` ${kind}` : ""}`;
  statsStatus.classList.toggle("hidden", !text);
}

async function loadStats() {
  if (!historyStatsPanel) return;
  clearTimeout(statsPollTimer);
  statsPeriodButtons.forEach((btn) => {
    const active = btn.dataset.statsPeriod === statsPeriod;
    btn.classList.toggle("active", active);
    btn.setAttribute("aria-checked", active ? "true" : "false");
  });
  try {
    const tz = -new Date().getTimezoneOffset();
    const res = await fetch(`/api/stats?period=${statsPeriod}&tz=${tz}`);
    if (!res.ok) throw new Error(String(res.status));
    const data = await res.json();
    renderStatsTiles(data);
    renderStatsBars(data);
    renderStatsSites(data.window.sites);
    renderStatsShares(statsAudio, data.window.audio_formats, "audio");
    renderStatsShares(statsVideo, data.window.video_formats, "video");
    renderStatsDisk(data.disk);
    if (data.backfilling) {
      // NOTE: the one-time import of files already on disk is still running
      // (it reads every video's resolution) - check back until it's done.
      showStatsStatus(t().statsBackfilling, "");
      statsPollTimer = setTimeout(loadStats, 3000);
    } else {
      showStatsStatus(t().statsNote, "");
    }
  } catch (err) {
    showStatsStatus(t().statsLoadFailed + err.message, "bad");
  }
}

function showHistoryTab(tab) {
  if (!historyStatsPanel || !historyFilesPanel) return;
  const stats = tab === "stats";
  historyTabButtons.forEach((btn) => {
    const active = btn.dataset.historyTab === tab;
    btn.classList.toggle("active", active);
    btn.setAttribute("aria-selected", active ? "true" : "false");
  });
  historyFilesPanel.classList.toggle("hidden", stats);
  historyStatsPanel.classList.toggle("hidden", !stats);
  // NOTE: "Clear All" deletes FILES - out of place on the statistics tab.
  historyClearBtn?.classList.toggle("history-clear-hidden", stats);
  if (stats) loadStats();
  else clearTimeout(statsPollTimer);
}

function initHistoryTabs() {
  if (!historyStatsPanel) return;
  try {
    const saved = localStorage.getItem("mediagrab_stats_period");
    if (saved && ["day", "week", "month"].includes(saved)) statsPeriod = saved;
  } catch (e) {}
  historyTabButtons.forEach((btn) => {
    btn.addEventListener("click", () => {
      const tab = btn.dataset.historyTab;
      // NOTE: replaceState, not location.hash - no extra Back-button step,
      // but a reload (or a shared link) still opens the same tab.
      window.history.replaceState(null, "", tab === "stats" ? "#stats" : window.location.pathname + window.location.search);
      showHistoryTab(tab);
    });
  });
  statsPeriodButtons.forEach((btn) => {
    btn.addEventListener("click", () => {
      statsPeriod = btn.dataset.statsPeriod;
      try {
        localStorage.setItem("mediagrab_stats_period", statsPeriod);
      } catch (e) {}
      loadStats();
    });
  });
  statsResetBtn?.addEventListener("click", async () => {
    if (!confirm(t().statsResetConfirm)) return;
    try {
      const res = await fetch("/api/stats/reset", { method: "POST" });
      if (!res.ok) throw new Error(String(res.status));
      loadStats();
    } catch (err) {
      showStatsStatus(t().statsLoadFailed + err.message, "bad");
    }
  });
  // NOTE: one shared tooltip for every bar/segment (data-tip), on hover and
  // on keyboard focus; the same text is each bar's aria-label too.
  const showTip = (target, x, y) => {
    statsTooltip.textContent = target.dataset.tip;
    statsTooltip.classList.remove("hidden");
    const rect = statsTooltip.getBoundingClientRect();
    const left = Math.min(window.innerWidth - rect.width - 8, Math.max(8, x - rect.width / 2));
    statsTooltip.style.left = `${left}px`;
    statsTooltip.style.top = `${Math.max(8, y - rect.height - 12)}px`;
  };
  const hideTip = () => statsTooltip.classList.add("hidden");
  historyStatsPanel.addEventListener("pointermove", (e) => {
    const target = e.target.closest?.("[data-tip]");
    if (target) showTip(target, e.clientX, e.clientY);
    else hideTip();
  });
  historyStatsPanel.addEventListener("pointerleave", hideTip);
  historyStatsPanel.addEventListener("focusin", (e) => {
    const target = e.target.closest?.("[data-tip]");
    if (!target) return;
    const rect = target.getBoundingClientRect();
    showTip(target, rect.left + rect.width / 2, rect.top);
  });
  historyStatsPanel.addEventListener("focusout", hideTip);
  showHistoryTab(window.location.hash === "#stats" ? "stats" : "files");
}

// --- media player (item page) ----------------------------------------------
// NOTE: MediaGrab's own controls instead of the browser's built-in ones,
// which look different in every browser and carry a "Download" entry in
// their menu (meaningless here - the file is already on this machine/server).
// Deliberately simple, Drive/YouTube-style: no playlists, no quality menu
// (a downloaded file only ever holds one quality - see the Resolution row).

const PLAYER_SPEEDS = [0.5, 0.75, 1, 1.25, 1.5, 2];

const PLAYER_ICONS = {
  play: '<path d="M8 5.5v13l11-6.5z"/>',
  pause: '<path d="M7 5h3.5v14H7zM13.5 5H17v14h-3.5z"/>',
  volume:
    '<path d="M4 9.5h3.5L12 5.5v13l-4.5-4H4z"/><path d="M15 9a4 4 0 0 1 0 6M17.5 6.5a7.5 7.5 0 0 1 0 11" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>',
  muted:
    '<path d="M4 9.5h3.5L12 5.5v13l-4.5-4H4z"/><path d="M15.5 9.5l5 5M20.5 9.5l-5 5" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>',
  pip: '<path d="M3.5 5.5h17v13h-17z" fill="none" stroke="currentColor" stroke-width="1.8"/><path d="M12 12h7v5h-7z"/>',
  fullscreen:
    '<path d="M4 9V4h5M15 4h5v5M20 15v5h-5M9 20H4v-5" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>',
  exitFullscreen:
    '<path d="M9 4v5H4M20 9h-5V4M15 20v-5h5M4 15h5v5" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>',
};

function playerIcon(name) {
  return `<svg viewBox="0 0 24 24" width="22" height="22" fill="currentColor" aria-hidden="true">${PLAYER_ICONS[name]}</svg>`;
}

// NOTE: "1:05", or "1:02:05" past an hour; anything not yet known (NaN
// before metadata loads, Infinity for a still-growing file) shows as 0:00.
function formatPlayerTime(seconds) {
  if (!Number.isFinite(seconds) || seconds < 0) seconds = 0;
  seconds = Math.floor(seconds);
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = String(seconds % 60).padStart(2, "0");
  return h > 0 ? `${h}:${String(m).padStart(2, "0")}:${s}` : `${m}:${s}`;
}

// NOTE: the same keys YouTube uses, so nothing new to learn. Pure (key in,
// action out) so it can be tested outside a browser; null = not ours, let
// the browser handle it.
function playerKeyAction(key) {
  if (key === " " || key === "k" || key === "K") return { type: "toggle" };
  if (key === "ArrowLeft") return { type: "seekBy", value: -5 };
  if (key === "ArrowRight") return { type: "seekBy", value: 5 };
  if (key === "j" || key === "J") return { type: "seekBy", value: -10 };
  if (key === "l" || key === "L") return { type: "seekBy", value: 10 };
  if (key === "ArrowUp") return { type: "volumeBy", value: 0.1 };
  if (key === "ArrowDown") return { type: "volumeBy", value: -0.1 };
  if (key === "m" || key === "M") return { type: "mute" };
  if (key === "f" || key === "F") return { type: "fullscreen" };
  if (key === "Home") return { type: "seekTo", fraction: 0 };
  if (key === "End") return { type: "seekTo", fraction: 1 };
  if (/^[0-9]$/.test(key)) return { type: "seekTo", fraction: Number(key) / 10 };
  return null;
}

function speedLabel(rate) {
  return rate === 1 ? t().playerSpeedNormal : `${rate}×`;
}

function loadPlayerPrefs() {
  try {
    const prefs = JSON.parse(localStorage.getItem("mediagrab_player") || "{}");
    return prefs && typeof prefs === "object" ? prefs : {};
  } catch (e) {
    return {};
  }
}

function savePlayerPrefs(media) {
  try {
    localStorage.setItem(
      "mediagrab_player",
      JSON.stringify({ volume: media.volume, muted: media.muted, rate: media.playbackRate }),
    );
  } catch (e) {}
}

// NOTE: builds the player inside `container` and returns a destroy()
// function (pauses, leaves picture-in-picture, unhooks the page-wide
// keyboard listener).
function createMediaPlayer(container, src, kind) {
  const isVideo = kind === "video";
  const canPip = isVideo && document.pictureInPictureEnabled === true;
  const speedItems = PLAYER_SPEEDS.map(
    (rate) =>
      `<button type="button" role="menuitemradio" class="mgp-speed-item" data-rate="${rate}">${speedLabel(rate)}</button>`,
  ).join("");
  container.innerHTML = `
    <div class="mgp ${isVideo ? "mgp-video" : "mgp-audio"} mgp-paused">
      <${kind} class="mgp-media" preload="metadata" playsinline></${kind}>
      ${isVideo ? `<button type="button" class="mgp-big-play" aria-label="${t().playerPlay}">${playerIcon("play")}</button>` : ""}
      <div class="mgp-osd" aria-hidden="true"></div>
      <div class="mgp-bar">
        <div class="mgp-progress">
          <div class="mgp-track"><div class="mgp-buffered"></div><div class="mgp-played"></div></div>
          <input class="mgp-seek" type="range" min="0" max="1000" step="1" value="0" aria-label="${t().playerSeek}">
          <div class="mgp-hover-time"></div>
        </div>
        <div class="mgp-controls">
          <button type="button" class="mgp-btn mgp-play"></button>
          <div class="mgp-volume">
            <button type="button" class="mgp-btn mgp-mute"></button>
            <input class="mgp-volume-slider" type="range" min="0" max="1" step="0.05" aria-label="${t().playerVolume}">
          </div>
          <span class="mgp-time">0:00 / 0:00</span>
          <span class="mgp-spacer"></span>
          <div class="mgp-speed">
            <button type="button" class="mgp-btn mgp-speed-btn" aria-haspopup="menu" aria-expanded="false" title="${t().playerSpeed}" aria-label="${t().playerSpeed}"></button>
            <div class="mgp-speed-menu hidden" role="menu" aria-label="${t().playerSpeed}">${speedItems}</div>
          </div>
          ${canPip ? `<button type="button" class="mgp-btn mgp-pip" title="${t().playerPip}" aria-label="${t().playerPip}">${playerIcon("pip")}</button>` : ""}
          ${isVideo ? `<button type="button" class="mgp-btn mgp-fullscreen"></button>` : ""}
        </div>
      </div>
    </div>`;

  const root = container.querySelector(".mgp");
  const media = root.querySelector(".mgp-media");
  const q = (sel) => root.querySelector(sel);
  const playBtn = q(".mgp-play");
  const bigPlay = q(".mgp-big-play");
  const muteBtn = q(".mgp-mute");
  const volumeSlider = q(".mgp-volume-slider");
  const seek = q(".mgp-seek");
  const played = q(".mgp-played");
  const buffered = q(".mgp-buffered");
  const hoverTime = q(".mgp-hover-time");
  const timeText = q(".mgp-time");
  const speedBtn = q(".mgp-speed-btn");
  const speedMenu = q(".mgp-speed-menu");
  const pipBtn = q(".mgp-pip");
  const fsBtn = q(".mgp-fullscreen");
  const osd = q(".mgp-osd");
  const progress = q(".mgp-progress");

  const prefs = loadPlayerPrefs();
  if (typeof prefs.volume === "number") media.volume = Math.min(1, Math.max(0, prefs.volume));
  media.muted = prefs.muted === true;
  media.src = src;
  // NOTE: set after src - loading a new source resets playbackRate to
  // defaultPlaybackRate, so both are set.
  const savedRate = PLAYER_SPEEDS.includes(prefs.rate) ? prefs.rate : 1;
  media.defaultPlaybackRate = savedRate;
  media.playbackRate = savedRate;

  function setButton(btn, icon, label) {
    if (!btn) return;
    btn.innerHTML = playerIcon(icon);
    btn.title = label;
    btn.setAttribute("aria-label", label);
  }

  function isFullscreen() {
    return document.fullscreenElement === root;
  }

  // NOTE: video controls fade out while playing and the mouse is still -
  // the picture is the point. Audio has nothing to cover, so they stay.
  let hideTimer = null;
  function showControls() {
    root.classList.remove("mgp-idle");
    clearTimeout(hideTimer);
  }
  function scheduleHide() {
    if (!isVideo) return;
    clearTimeout(hideTimer);
    hideTimer = setTimeout(() => {
      if (!media.paused && speedMenu.classList.contains("hidden")) root.classList.add("mgp-idle");
    }, 2500);
  }
  function poke() {
    showControls();
    if (!media.paused) scheduleHide();
  }

  function renderPlayState() {
    const paused = media.paused;
    root.classList.toggle("mgp-paused", paused);
    setButton(playBtn, paused ? "play" : "pause", paused ? t().playerPlay : t().playerPause);
    if (paused) showControls();
    else scheduleHide();
  }

  function renderVolume() {
    const silent = media.muted || media.volume === 0;
    setButton(muteBtn, silent ? "muted" : "volume", silent ? t().playerUnmute : t().playerMute);
    const level = media.muted ? 0 : media.volume;
    volumeSlider.value = level;
    volumeSlider.style.setProperty("--fill", `${level * 100}%`);
  }

  function renderSpeed() {
    speedBtn.textContent = `${media.playbackRate}×`;
    speedMenu.querySelectorAll(".mgp-speed-item").forEach((item) => {
      item.setAttribute("aria-checked", Number(item.dataset.rate) === media.playbackRate ? "true" : "false");
    });
  }

  function renderFullscreen() {
    if (!fsBtn) return;
    const on = isFullscreen();
    root.classList.toggle("mgp-is-fullscreen", on);
    setButton(fsBtn, on ? "exitFullscreen" : "fullscreen", on ? t().playerExitFullscreen : t().playerFullscreen);
  }

  function renderTime() {
    const duration = Number.isFinite(media.duration) ? media.duration : 0;
    const fraction = duration ? media.currentTime / duration : 0;
    played.style.width = `${fraction * 100}%`;
    seek.value = Math.round(fraction * 1000);
    const label = `${formatPlayerTime(media.currentTime)} / ${formatPlayerTime(duration)}`;
    seek.setAttribute("aria-valuetext", label);
    timeText.textContent = label;
  }

  function renderBuffered() {
    const duration = media.duration;
    if (!Number.isFinite(duration) || !duration || media.buffered.length === 0) return;
    // NOTE: the buffered range around the playhead - what the user cares about.
    let end = 0;
    for (let i = 0; i < media.buffered.length; i++) {
      if (media.buffered.start(i) <= media.currentTime + 0.5) end = Math.max(end, media.buffered.end(i));
    }
    buffered.style.width = `${(end / duration) * 100}%`;
  }

  let osdTimer = null;
  function flashOsd(text) {
    osd.textContent = text;
    osd.classList.add("visible");
    clearTimeout(osdTimer);
    osdTimer = setTimeout(() => osd.classList.remove("visible"), 700);
  }

  function togglePlay() {
    if (media.paused || media.ended) media.play().catch(() => {});
    else media.pause();
  }

  function seekBy(delta) {
    if (!Number.isFinite(media.duration)) return;
    media.currentTime = Math.min(media.duration, Math.max(0, media.currentTime + delta));
    flashOsd(`${delta > 0 ? "+" : "−"}${Math.abs(delta)} ${t().playerSeconds}`);
  }

  function setVolume(value) {
    media.volume = Math.min(1, Math.max(0, Math.round(value * 100) / 100));
    media.muted = media.volume === 0;
  }

  function toggleMute() {
    if (media.muted || media.volume === 0) {
      media.muted = false;
      if (media.volume === 0) media.volume = 0.5;
    } else {
      media.muted = true;
    }
  }

  async function toggleFullscreen() {
    if (!isVideo) return;
    try {
      if (isFullscreen()) await document.exitFullscreen();
      else if (root.requestFullscreen) await root.requestFullscreen();
      // NOTE: iPhone Safari has no element fullscreen - only the video's own.
      else if (media.webkitEnterFullscreen) media.webkitEnterFullscreen();
    } catch (e) {}
  }

  async function togglePip() {
    try {
      if (document.pictureInPictureElement === media) await document.exitPictureInPicture();
      else await media.requestPictureInPicture();
    } catch (e) {}
  }

  function closeSpeedMenu() {
    speedMenu.classList.add("hidden");
    speedBtn.setAttribute("aria-expanded", "false");
  }

  media.addEventListener("play", renderPlayState);
  media.addEventListener("pause", renderPlayState);
  media.addEventListener("ended", renderPlayState);
  media.addEventListener("timeupdate", renderTime);
  media.addEventListener("durationchange", renderTime);
  media.addEventListener("loadedmetadata", renderTime);
  media.addEventListener("progress", renderBuffered);
  // NOTE: tearing down (destroy below) unloads the source, which resets the
  // speed to 1x and fires ratechange - that must not overwrite the user's
  // saved choice, so saving stops first.
  let destroyed = false;
  media.addEventListener("volumechange", () => {
    renderVolume();
    if (!destroyed) savePlayerPrefs(media);
  });
  media.addEventListener("ratechange", () => {
    renderSpeed();
    if (!destroyed) savePlayerPrefs(media);
  });
  // NOTE: no right-click menu on the picture - the browser's own one offers
  // "Save video as...", the very thing the custom controls leave out.
  media.addEventListener("contextmenu", (e) => e.preventDefault());

  // NOTE: mouse: click = play/pause, double-click = full screen. Touch: while
  // the controls are hidden, a tap only brings them back - tapping straight
  // into a pause while reaching for the controls is the classic mobile
  // player annoyance.
  let lastPointer = "mouse";
  media.addEventListener("pointerdown", (e) => {
    lastPointer = e.pointerType;
  });
  media.addEventListener("click", () => {
    if (lastPointer === "touch" && root.classList.contains("mgp-idle")) {
      poke();
      return;
    }
    togglePlay();
  });
  media.addEventListener("dblclick", toggleFullscreen);
  bigPlay?.addEventListener("click", togglePlay);
  playBtn.addEventListener("click", togglePlay);
  muteBtn.addEventListener("click", toggleMute);
  volumeSlider.addEventListener("input", () => setVolume(Number(volumeSlider.value)));
  seek.addEventListener("input", () => {
    if (Number.isFinite(media.duration)) media.currentTime = (Number(seek.value) / 1000) * media.duration;
  });
  progress.addEventListener("pointermove", (e) => {
    if (!Number.isFinite(media.duration)) return;
    const rect = progress.getBoundingClientRect();
    const fraction = Math.min(1, Math.max(0, (e.clientX - rect.left) / rect.width));
    hoverTime.textContent = formatPlayerTime(fraction * media.duration);
    hoverTime.style.left = `${fraction * 100}%`;
    hoverTime.classList.add("visible");
  });
  progress.addEventListener("pointerleave", () => hoverTime.classList.remove("visible"));
  speedBtn.addEventListener("click", () => {
    const opening = speedMenu.classList.contains("hidden");
    speedMenu.classList.toggle("hidden", !opening);
    speedBtn.setAttribute("aria-expanded", opening ? "true" : "false");
    if (opening) showControls();
  });
  speedMenu.addEventListener("click", (e) => {
    const item = e.target.closest(".mgp-speed-item");
    if (!item) return;
    media.playbackRate = Number(item.dataset.rate);
    closeSpeedMenu();
    poke();
  });
  pipBtn?.addEventListener("click", togglePip);
  fsBtn?.addEventListener("click", toggleFullscreen);
  root.addEventListener("pointermove", poke);
  root.addEventListener("pointerleave", () => {
    if (!media.paused) scheduleHide();
  });
  document.addEventListener("fullscreenchange", renderFullscreen);

  const onOutsideClick = (e) => {
    if (!e.target.closest?.(".mgp-speed")) closeSpeedMenu();
  };
  document.addEventListener("click", onOutsideClick);

  // NOTE: page-wide, not just while the player has focus - on this page the
  // player is the only thing a key could mean (YouTube does the same).
  // Typing in a field and browser shortcuts (Ctrl/Cmd/Alt + key) are left
  // alone; the player's own two sliders are not "typing".
  const onKeyDown = (e) => {
    if (e.ctrlKey || e.metaKey || e.altKey) return;
    const target = e.target;
    const inPlayerSlider = target?.classList?.contains("mgp-seek") || target?.classList?.contains("mgp-volume-slider");
    if (!inPlayerSlider && (target?.isContentEditable || ["INPUT", "TEXTAREA", "SELECT"].includes(target?.tagName))) {
      return;
    }
    if (e.key === "Escape" && !speedMenu.classList.contains("hidden")) {
      closeSpeedMenu();
      return;
    }
    const action = playerKeyAction(e.key);
    if (!action) return;
    // NOTE: a focused button would otherwise ALSO activate on Space, and a
    // focused slider would move on the arrows on top of the shortcut.
    e.preventDefault();
    poke();
    if (action.type === "toggle") togglePlay();
    else if (action.type === "seekBy") seekBy(action.value);
    else if (action.type === "seekTo") {
      if (Number.isFinite(media.duration)) media.currentTime = action.fraction * media.duration;
    } else if (action.type === "volumeBy") {
      setVolume((media.muted ? 0 : media.volume) + action.value);
      flashOsd(`${Math.round(media.volume * 100)}%`);
    } else if (action.type === "mute") toggleMute();
    else if (action.type === "fullscreen") toggleFullscreen();
  };
  // NOTE: Space activates a focused button on key UP - swallowed too, so a
  // focused control doesn't fire a second time after the shortcut.
  const onKeyUp = (e) => {
    if (e.key === " " && e.target?.closest?.(".mgp")) e.preventDefault();
  };
  document.addEventListener("keydown", onKeyDown);
  document.addEventListener("keyup", onKeyUp);

  renderPlayState();
  renderVolume();
  renderSpeed();
  renderFullscreen();
  renderTime();
  media.play().catch(() => {});

  return function destroy() {
    destroyed = true;
    clearTimeout(hideTimer);
    clearTimeout(osdTimer);
    document.removeEventListener("keydown", onKeyDown);
    document.removeEventListener("keyup", onKeyUp);
    document.removeEventListener("click", onOutsideClick);
    document.removeEventListener("fullscreenchange", renderFullscreen);
    if (document.pictureInPictureElement === media) document.exitPictureInPicture().catch(() => {});
    if (isFullscreen()) document.exitFullscreen().catch(() => {});
    media.pause();
    media.removeAttribute("src");
    media.load();
    container.innerHTML = "";
  };
}

let destroyItemPlayer = null;

function closeItemPlayer() {
  destroyItemPlayer?.();
  destroyItemPlayer = null;
  itemPreviewPlayer?.classList.add("hidden");
}

itemRevealBtn?.addEventListener("click", async () => {
  const outcome = await revealFile(itemRevealBtn.dataset.revealUrl, itemRevealBtn.dataset.filename);
  showSaveOutcome(itemRevealBtn, outcome);
  if (outcome === "removed") {
    // NOTE: the file is gone from the server now - playing it would only 404.
    closeItemPlayer();
    itemPreviewBtn?.classList.add("hidden");
  }
});
itemPreviewBtn?.addEventListener("click", () => {
  if (!itemPreviewPlayer) return;
  if (itemPreviewPlayer.classList.contains("hidden")) {
    const kind = itemPreviewBtn.dataset.ext === "mp4" ? "video" : "audio";
    itemPreviewPlayer.classList.remove("hidden");
    destroyItemPlayer = createMediaPlayer(itemPreviewPlayer, itemPreviewBtn.dataset.streamUrl, kind);
    itemPreviewBtn.textContent = t().itemPreviewClose;
  } else {
    closeItemPlayer();
    itemPreviewBtn.textContent = t().itemPreviewPlay;
  }
});
channelAddBtn?.addEventListener("click", addChannel);
channelModeRadios.forEach((r) => r.addEventListener("change", updateChannelChoiceVisibility));
pendingClearBtn?.addEventListener("click", clearPending);
updateChannelChoiceVisibility();

// NOTE: isLocalClient has to be resolved BEFORE anything renders a
// reveal/download button (history cards, the dock) - otherwise a remote
// device could briefly render "Show in folder" (or vice versa) until
// whichever fetch happened to finish first. All of these are independent,
// so awaiting just the one flag first costs nothing but a few ms.
(async () => {
  await loadClientInfo();
  initHistoryTabs();
  // NOTE: the item page's label is rendered server-side, which can't know
  // whether THIS browser supports the save picker - fixed up here.
  if (itemRevealBtn) itemRevealBtn.textContent = revealOrDownloadLabel();
  loadHistory();
  loadChannels();
  loadPending();
  loadMediagrabVersion();
  loadYtdlpVersion();
  loadFfmpegVersion();
  loadDependencies();
  wireDepsUpdateBtn();
  loadSettings();
  loadDownloadDir();
  loadRemoteAccessStatus();
  resumeTrackedDockJobs();
})();

// NOTE: lets an external trigger (e.g. a browser extension/bookmarklet)
// open MediaGrab pre-filled and already resolving, via
// "/?url=<encoded-link>", instead of requiring copy-paste into the page.
if (urlInput) {
  const sharedUrl = new URLSearchParams(window.location.search).get("url");
  if (sharedUrl) {
    urlInput.value = sharedUrl;
    probe();
  }
}

if ("serviceWorker" in navigator) {
  // NOTE: only makes the page installable as a PWA (native-app-like window,
  // taskbar icon) - see sw.js for why there's no offline caching. Registered
  // from "/sw.js" (not "/static/sw.js") so its default scope covers the
  // whole app - see the matching NOTE on the /sw.js route in app.py.
  navigator.serviceWorker.register("/sw.js").catch(() => {});
}
