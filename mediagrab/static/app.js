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
const ytdlpInstructions = document.getElementById("ytdlp-instructions");
const ytdlpCredit = document.getElementById("ytdlp-credit");
const ffmpegStatus = document.getElementById("ffmpeg-status");
const ffmpegInstructions = document.getElementById("ffmpeg-instructions");
const depsStatus = document.getElementById("deps-status");
const depsList = document.getElementById("deps-list");
const depsActions = document.getElementById("deps-actions");
const depsUpdateBtn = document.getElementById("deps-update-btn");
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
    downloadStartedNote: "İndirme başladı — altta ilerlemesini takip edebilirsiniz.",
    dockDismiss: "Kapat",
    dockCancel: "İndirmeyi iptal et",
    etaLabel: "kalan",
    cookieSaved: "Kaydedildi.",
    cookieTestOk: "Çalışıyor — {n} çerez okundu.",
    cookieTestNone: "Çerez kaynağı ayarlanmamış.",
    cookieTestFailed: "Çerezler okunamadı",
    queuePosition: "Sırada {n}. — diğer indirmeler bekleniyor",
    itemPreviewPlay: "▶ Oynat",
    itemPreviewClose: "✕ Kapat",
    errProbeFailed: "Çözümlenemedi",
    errDownloadFailed: "İndirme başlatılamadı",
    errNetwork: "Ağ hatası: ",
    errStatusFailed: "Durum alınamadı",
    errUnknown: "Bilinmeyen hata",
    errTechnicalDetail: "Teknik detay",
    errAgeRestricted: "Bu video yaş kısıtlı, giriş yapılmış bir hesap gerektiriyor.",
    errBotCheck: "Site bot doğrulaması istiyor, bu video şu an indirilemiyor.",
    errPrivate: "Bu video gizli/özel — herkese açık değil.",
    errMembersOnly: "Bu içerik yalnızca kanal üyelerine özel.",
    errGeoRestricted: "Bu içerik bulunduğunuz ülkede kullanılamıyor (bölgesel kısıtlama).",
    errBlocked: "Site isteği reddetti (muhtemelen bot koruması).",
    errRemoved: "Bu video artık mevcut değil veya kaldırılmış.",
    errUnsupportedSite: "Bu link tanınan bir siteden değil ya da desteklenmiyor.",
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
    depsUpdatesAvailable: "paket güncellenebilir",
    depsUpdateBtn: "Tümünü Güncelle",
    ytdlpCreditText: "yt-dlp, açık kaynak katkıda bulunanlar tarafından geliştirilip sürdürülüyor.",
    ytdlpCreditLink: "GitHub'da teşekkür edin →",
    settingsRemoteAccessRestartNote: "Ayar uygulanıyor, sunucu yeniden başlatılıyor...",
    settingsRemoteAccessPasswordTooShort: "Şifre en az 8 karakter olmalı.",
    settingsRemoteAccessPasswordsDontMatch: "Yeni şifreler eşleşmiyor.",
    settingsRemoteAccessCurrentPasswordRequired: "Mevcut şifrenizi girin.",
    settingsRemoteAccessWrongCurrentPassword: "Mevcut şifre yanlış.",
    settingsRemoteAccessPasswordSaved: "Şifre kaydedildi.",
    settingsRemoteAccessStorageSaved: "Depolama ayarı kaydedildi.",
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
    downloadStartedNote: "Download started — track its progress below.",
    dockDismiss: "Dismiss",
    dockCancel: "Cancel download",
    etaLabel: "ETA",
    cookieSaved: "Saved.",
    cookieTestOk: "Working — {n} cookie(s) loaded.",
    cookieTestNone: "No cookie source configured.",
    cookieTestFailed: "Could not read cookies",
    queuePosition: "{n}. in queue — waiting for other downloads",
    itemPreviewPlay: "▶ Play",
    itemPreviewClose: "✕ Close",
    errProbeFailed: "Could not resolve",
    errDownloadFailed: "Could not start download",
    errNetwork: "Network error: ",
    errStatusFailed: "Could not get status",
    errUnknown: "Unknown error",
    errTechnicalDetail: "Technical detail",
    errAgeRestricted: "This video is age-restricted and requires a signed-in account.",
    errBotCheck: "The site is asking for bot verification - this video can't be downloaded right now.",
    errPrivate: "This video is private and not publicly accessible.",
    errMembersOnly: "This content is members-only.",
    errGeoRestricted: "This content isn't available in your country (geo-restricted).",
    errBlocked: "The site refused the request (likely bot protection).",
    errRemoved: "This video is no longer available or has been removed.",
    errUnsupportedSite: "This link isn't from a recognized or supported site.",
    errNetworkIssue: "Network connection issue — check your internet connection and try again.",
    historyEmpty: "No downloads yet",
    historyNoMatches: "No downloads match your search",
    historyAllChannels: "All channels",
    historyAllTypes: "All types",
    historyViewGrid: "Grid view",
    historyViewList: "List view",
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
    depsUpdatesAvailable: "packages can be updated",
    depsUpdateBtn: "Update All",
    ytdlpCreditText: "yt-dlp is built and maintained by its open-source contributors.",
    ytdlpCreditLink: "Say thanks on GitHub →",
    settingsRemoteAccessRestartNote: "Applying the setting, restarting the server...",
    settingsRemoteAccessPasswordTooShort: "Password must be at least 8 characters.",
    settingsRemoteAccessPasswordsDontMatch: "The new passwords don't match.",
    settingsRemoteAccessCurrentPasswordRequired: "Enter your current password.",
    settingsRemoteAccessWrongCurrentPassword: "Current password is incorrect.",
    settingsRemoteAccessPasswordSaved: "Password saved.",
    settingsRemoteAccessStorageSaved: "Storage setting saved.",
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
const ERROR_PATTERNS = [
  { patterns: ["sign in to confirm your age", "inappropriate for some users"], key: "errAgeRestricted" },
  { patterns: ["confirm you're not a bot", "confirm you are not a bot"], key: "errBotCheck" },
  { patterns: ["private video", "this video is private"], key: "errPrivate" },
  { patterns: ["members-only", "join this channel"], key: "errMembersOnly" },
  { patterns: ["not available in your country", "not made this video available in your country", "geo restrict"], key: "errGeoRestricted" },
  { patterns: ["cloudflare", "http error 403"], key: "errBlocked" },
  { patterns: ["video unavailable", "has been removed"], key: "errRemoved" },
  { patterns: ["unsupported url", "no extractor"], key: "errUnsupportedSite" },
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

function friendlyError(raw) {
  if (!raw) return null;
  const lowered = raw.toLowerCase();
  const match = ERROR_PATTERNS.find((entry) => entry.patterns.some((p) => lowered.includes(p)));
  return match ? t()[match.key] : null;
}

function showError(message, raw) {
  // NOTE: back to the simple, page-local inline error in the resolve card
  // (the cross-page toast was removed - it fought a CSS specificity bug
  // that made "hidden" not actually hide it, and was more complexity than
  // this needed). Resolve/download-start errors always happen on the home
  // page where `card` exists; background job failures still show in the
  // dock row itself (see dockRowHtml), just without a separate popup.
  if (!card) return;
  const friendly = friendlyError(raw || message);
  const displayMessage = friendly || message;
  if (!displayMessage) return;
  const showDetail = raw && raw !== displayMessage;
  card.classList.remove("hidden");
  card.innerHTML = `
    <div class="error">${escapeHtml(displayMessage)}</div>
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

async function loadClientInfo() {
  try {
    const res = await fetch("/api/client-info");
    const data = await res.json();
    isLocalClient = data.is_local !== false;
  } catch (err) {
    // NOTE: same tolerance as the rest of this file's best-effort fetches -
    // isLocalClient just stays at its safe default.
  }
}

async function revealFile(url) {
  if (isLocalClient) {
    // NOTE: fetch() rather than a plain <a href> navigation - the endpoint
    // just opens the OS file explorer server-side and returns {"ok": true};
    // navigating to it directly would have shown raw JSON in the tab.
    try {
      await fetch(url);
    } catch (err) {
      // best-effort - revealing the file in explorer is a nice-to-have here.
    }
    return;
  }
  // NOTE: a real download needs a native browser navigation - fetch() would
  // receive the bytes into JS and just discard them, triggering nothing on
  // screen. The matching /download route (see app.py) sets
  // Content-Disposition: attachment, which is what makes the browser save
  // the file instead of trying to navigate to it inline.
  window.location.href = `${url}/download`;
}

function revealOrDownloadLabel() {
  return isLocalClient ? t().downloadBtn : t().downloadToDeviceBtn;
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
      return `
    <button class="option" data-kind="audio" data-choice="${choice}">
      <span>
        <span class="opt-label">${opt.label}</span><br>
        <span class="opt-desc">${opt.desc}</span>
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
      <button type="button" class="quick-btn" data-kind="audio" data-choice="opus">${t().quickBestAudio}</button>
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
  try {
    const res = await fetch("/api/download", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url, kind, choice, subtitle_langs: subtitleLangs || [], audio_langs: audioLangs || [] }),
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
    row.querySelector(".reveal-btn")?.addEventListener("click", (e) => {
      e.preventDefault();
      revealFile(row.querySelector(".reveal-btn").dataset.revealUrl);
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

// --- Ayarlar sayfasi: yt-dlp surum kontrolu ---

const YTDLP_PIP_CMD = "pip install --upgrade yt-dlp";
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

function ytdlpInstructionsHtml() {
  return `
    <button type="button" id="ytdlp-update-now-btn" class="ytdlp-update-btn">${t().ytdlpUpdateNowBtn}</button>
    <div id="ytdlp-update-status" class="ytdlp-update-status hidden"></div>
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

function renderYtdlpVersion() {
  if (!ytdlpStatus || !lastYtdlpInfo) return;
  const info = lastYtdlpInfo;

  if (info.update_available === null) {
    ytdlpStatus.innerHTML = `<span class="ytdlp-badge unknown">${t().ytdlpCheckFailed}</span>`;
    ytdlpInstructions?.classList.add("hidden");
  } else if (info.update_available) {
    ytdlpStatus.innerHTML = `
      <span class="ytdlp-badge outdated">${t().ytdlpUpdateAvailable}</span>
      <span class="ytdlp-version-row">${t().ytdlpInstalledLabel}: ${escapeHtml(info.installed)} &rarr; ${t().ytdlpLatestLabel}: ${escapeHtml(info.latest)}</span>`;
    if (ytdlpInstructions) {
      ytdlpInstructions.classList.remove("hidden");
      ytdlpInstructions.innerHTML = ytdlpInstructionsHtml();
      wireYtdlpCopyBtn();
      wireYtdlpUpdateBtn();
    }
  } else {
    ytdlpStatus.innerHTML = `
      <span class="ytdlp-badge uptodate">${t().ytdlpUpToDate}</span>
      <span class="ytdlp-version-row">${t().ytdlpInstalledLabel}: ${escapeHtml(info.installed)}</span>`;
    ytdlpInstructions?.classList.add("hidden");
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
}

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
const defaultAudioLangInput = document.getElementById("default-audio-lang-input");
const defaultAudioLangSaveBtn = document.getElementById("default-audio-lang-save-btn");
const defaultAudioLangStatus = document.getElementById("default-audio-lang-status");
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
const remoteAccessDevicesPanel = document.getElementById("remote-access-devices-panel");
const remoteAccessDevicesList = document.getElementById("remote-access-devices-list");
const remoteAccessStorageModes = document.getElementById("remote-access-storage-modes");
const remoteAccessStorageKeepHint = document.getElementById("remote-access-storage-keep-hint");
const remoteAccessStorageRelayHint = document.getElementById("remote-access-storage-relay-hint");

let cookieMode = "off";

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
    cookieMode = settings.cookie_mode || "off";
    renderCookieMode();
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
    cookie_browser: cookieBrowserSelect?.value || "firefox",
    cookie_file: cookieFileInput?.value || "",
    default_audio_lang: defaultAudioLangInput?.value || "",
  };
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

function renderRemoteAccessAddress(lanUrl) {
  if (!remoteAccessAddressPanel) return;
  if (lanUrl) {
    remoteAccessAddressPanel.classList.remove("hidden");
    if (remoteAccessAddressInput) remoteAccessAddressInput.value = lanUrl;
  } else {
    remoteAccessAddressPanel.classList.add("hidden");
  }
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
    renderRemoteAccessAddress(data.lan_url);
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
cookieTestBtn?.addEventListener("click", testCookieSettings);
defaultAudioLangSaveBtn?.addEventListener("click", saveDefaultAudioLang);
remoteAccessToggle?.addEventListener("change", toggleRemoteAccess);
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
langSwitch?.querySelectorAll("button").forEach((btn) => {
  btn.addEventListener("click", () => setLang(btn.dataset.lang));
});
// NOTE: one delegated listener on the dock container, which is never
// replaced - individual rows are, so per-button listeners would be lost
// (and re-added) on every rebuild.
downloadDock?.addEventListener("click", (e) => {
  const revealBtn = e.target.closest?.(".dock-reveal-btn");
  if (revealBtn) {
    revealFile(`/api/file/${revealBtn.dataset.jobId}`);
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
itemRevealBtn?.addEventListener("click", () => revealFile(itemRevealBtn.dataset.revealUrl));
itemPreviewBtn?.addEventListener("click", () => {
  if (!itemPreviewPlayer) return;
  if (itemPreviewPlayer.classList.contains("hidden")) {
    const tag = itemPreviewBtn.dataset.ext === "mp4" ? "video" : "audio";
    itemPreviewPlayer.innerHTML = `<${tag} controls autoplay src="${itemPreviewBtn.dataset.streamUrl}"></${tag}>`;
    itemPreviewPlayer.classList.remove("hidden");
    itemPreviewBtn.textContent = t().itemPreviewClose;
  } else {
    itemPreviewPlayer.innerHTML = "";
    itemPreviewPlayer.classList.add("hidden");
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
  loadHistory();
  loadChannels();
  loadPending();
  loadYtdlpVersion();
  loadFfmpegVersion();
  loadDependencies();
  wireDepsUpdateBtn();
  loadSettings();
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
