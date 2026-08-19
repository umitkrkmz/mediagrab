// NOTE: this script is loaded on the index/history/item pages alike (for the
// shared header/footer/language switcher), so every DOM element can be null -
// check it exists before using it.
const urlInput = document.getElementById("url-input");
const pasteBtn = document.getElementById("paste-btn");
const probeBtn = document.getElementById("probe-btn");
const card = document.getElementById("card");
const downloadDock = document.getElementById("download-dock");
const heroTitle = document.getElementById("hero-title");
const heroSub = document.getElementById("hero-sub");
const recentSection = document.getElementById("recent-section");
const recentTitle = document.getElementById("recent-title");
const recentSeeAll = document.getElementById("recent-see-all");
const recentList = document.getElementById("recent-list");
const historyPageTitle = document.getElementById("history-page-title");
const historyList = document.getElementById("history-list");
const historyError = document.getElementById("history-error");
const historyClearBtn = document.getElementById("history-clear-btn");
const historySearchInput = document.getElementById("history-search");
const historyChannelFilter = document.getElementById("history-channel-filter");
const navHome = document.getElementById("nav-home");
const navHistory = document.getElementById("nav-history");
const navSites = document.getElementById("nav-sites");
const navSettings = document.getElementById("nav-settings");
const footerLegal = document.getElementById("footer-legal");
const footerNote = document.getElementById("footer-note");
const langSwitch = document.getElementById("lang-switch");
const itemCard = document.querySelector(".item-card");
const itemRevealBtn = document.getElementById("item-reveal-btn");
const itemPreviewBtn = document.getElementById("item-preview-btn");
const itemPreviewPlayer = document.getElementById("item-preview-player");
const sitesPage = document.querySelector(".sites-category");

const pendingBanner = document.getElementById("pending-banner");
const pendingTitleEl = document.getElementById("pending-title");
const pendingClearBtn = document.getElementById("pending-clear-btn");
const pendingList = document.getElementById("pending-list");

const settingsPageTitleEl = document.getElementById("settings-page-title");
const settingsAddTitleEl = document.getElementById("settings-add-title");
const settingsAddHintEl = document.getElementById("settings-add-hint");
const settingsListTitleEl = document.getElementById("settings-list-title");
const channelUrlInput = document.getElementById("channel-url-input");
const channelChoiceSelect = document.getElementById("channel-choice-select");
const channelAddBtn = document.getElementById("channel-add-btn");
const channelError = document.getElementById("channel-error");
const channelList = document.getElementById("channel-list");
const channelEmpty = document.getElementById("channel-empty");
const modeNotifyLabel = document.getElementById("mode-notify-label");
const modeAutoLabel = document.getElementById("mode-auto-label");
const channelModeRadios = document.querySelectorAll('input[name="channel-mode"]');
const settingsYtdlpTitleEl = document.getElementById("settings-ytdlp-title");
const ytdlpStatus = document.getElementById("ytdlp-status");
const ytdlpInstructions = document.getElementById("ytdlp-instructions");
const ytdlpCredit = document.getElementById("ytdlp-credit");

const LANG_KEY = "mediagrab_lang";

// NOTE: error messages from the server (yt-dlp/downloader) are dynamic and
// mostly already English/technical, so there's no translation layer for
// them; only the client-side strings defined here change with the language.
const I18N = {
  tr: {
    navHome: "Ana Sayfa",
    navHistory: "Geçmiş",
    navSites: "Desteklenen Siteler",
    navSettings: "Ayarlar",
    footerLegal:
      "Bu araç yalnızca kişisel kullanım içindir. İndirdiğiniz içeriğin telif durumundan ve ilgili platformun kullanım şartlarına uyumdan tamamen siz sorumlusunuz.",
    footerNote: "MediaGrab, yt-dlp ile çalışır. Veritabanı ve hesap sistemi yoktur — sadece bu bilgisayarda çalışır.",
    heroTitle: "Link yapıştır, indir",
    heroSub: "YouTube, YouTube Music ve yt-dlp'nin desteklediği diğer birçok siteden linki yapıştırın; ses veya video olarak indirin.",
    placeholder: "Video linkini yapıştır...",
    resolveBtn: "Çözümle",
    resolveBtnBusy: "...",
    sectionAudio: "Ses",
    sectionVideo: "Video",
    sectionSubtitle: "Altyazı",
    subtitleHint: "Seçtiğiniz video ile birlikte, aynı dosya adıyla iner",
    noVideoFormats: "Video seçeneği bulunamadı",
    sectionTranscript: "Transkript",
    transcriptDownload: "Transkript indir (.txt)",
    transcriptManual: "elle eklenmiş altyazıdan",
    transcriptAuto: "otomatik altyazıdan",
    quickBestAudio: "♪ En İyi Ses",
    quickBestVideo: "▶ En İyi Video",
    advancedOptions: "Diğer seçenekler",
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
    },
    downloadBtn: "Klasörde göster",
    downloadStartedNote: "İndirme başladı — altta ilerlemesini takip edebilirsiniz.",
    dockDismiss: "Kapat",
    pasteBtnTitle: "Panodan yapıştır",
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
    historyPageTitle: "İndirme Geçmişi",
    historyEmpty: "Henüz indirme yok",
    historyNoMatches: "Aramayla eşleşen indirme yok",
    historySearchPlaceholder: "Ara...",
    historyAllChannels: "Tüm kanallar",
    historyDownload: "Klasörde göster",
    historyDelete: "Sil",
    historyDeleteFailed: "Silinemedi",
    historyClear: "Tümünü Sil",
    historyClearConfirm: "Tüm indirme geçmişi diskten kalıcı olarak silinsin mi?",
    historyClearFailed: "Geçmiş temizlenemedi",
    recentTitle: "Son İndirilenler",
    recentSeeAll: "Tümünü gör →",
    videoWord: "video",
    backToPlaylist: "← Playlist'e dön",
    locale: "tr-TR",
    settingsPageTitle: "Ayarlar",
    settingsAddTitle: "Kanal Takip Et",
    settingsAddHint: "Uygulamayı her açtığınızda takip ettiğiniz kanallar yeni video için kontrol edilir.",
    channelUrlPlaceholder: "Kanal linki yapıştır (ör. youtube.com/@kanaladi)",
    modeNotify: "Bildir",
    modeAuto: "Otomatik indir",
    channelAddBtnLabel: "Ekle",
    settingsListTitle: "Takip Edilen Kanallar",
    channelEmpty: "Henüz takip edilen kanal yok.",
    channelCheckNow: "Şimdi kontrol et",
    channelRemove: "Kaldır",
    channelAddFailed: "Kanal eklenemedi",
    channelModeAutoBadge: "OTOMATİK",
    channelModeNotifyBadge: "BİLDİR",
    channelLastChecked: "Son kontrol",
    channelNeverChecked: "Henüz kontrol edilmedi",
    pendingTitle: "Takip Edilen Kanallarda Yeni Video",
    pendingClear: "Temizle",
    settingsYtdlpTitle: "yt-dlp Sürümü",
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
    ytdlpCreditText: "yt-dlp, açık kaynak katkıda bulunanlar tarafından geliştirilip sürdürülüyor.",
    ytdlpCreditLink: "GitHub'da teşekkür edin →",
  },
  en: {
    navHome: "Home",
    navHistory: "History",
    navSites: "Supported Sites",
    navSettings: "Settings",
    footerLegal:
      "This tool is for personal use only. You are solely responsible for the copyright status of downloaded content and compliance with the relevant platform's terms of service.",
    footerNote: "MediaGrab runs on yt-dlp. No database or account system — it only runs on this computer.",
    heroTitle: "Paste a link, download",
    heroSub: "Paste a link from YouTube, YouTube Music, or many other sites supported by yt-dlp; download it as audio or video.",
    placeholder: "Paste a video link...",
    resolveBtn: "Resolve",
    resolveBtnBusy: "...",
    sectionAudio: "Audio",
    sectionVideo: "Video",
    sectionSubtitle: "Subtitles",
    subtitleHint: "Downloads together with the video you pick, using the same filename",
    noVideoFormats: "No video options found",
    sectionTranscript: "Transcript",
    transcriptDownload: "Download transcript (.txt)",
    transcriptManual: "from manual subtitles",
    transcriptAuto: "from auto-generated captions",
    quickBestAudio: "♪ Best Audio",
    quickBestVideo: "▶ Best Video",
    advancedOptions: "More options",
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
    },
    downloadBtn: "Show in folder",
    downloadStartedNote: "Download started — track its progress below.",
    dockDismiss: "Dismiss",
    pasteBtnTitle: "Paste from clipboard",
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
    historyPageTitle: "Download History",
    historyEmpty: "No downloads yet",
    historyNoMatches: "No downloads match your search",
    historySearchPlaceholder: "Search...",
    historyAllChannels: "All channels",
    historyDownload: "Show in folder",
    historyDelete: "Delete",
    historyDeleteFailed: "Could not delete",
    historyClear: "Clear All",
    historyClearConfirm: "Permanently delete all download history from disk?",
    historyClearFailed: "Could not clear history",
    recentTitle: "Recent Downloads",
    recentSeeAll: "View all →",
    videoWord: "videos",
    backToPlaylist: "← Back to playlist",
    locale: "en-US",
    settingsPageTitle: "Settings",
    settingsAddTitle: "Follow a Channel",
    settingsAddHint: "Every time you open the app, followed channels are checked for new videos.",
    channelUrlPlaceholder: "Paste a channel link (e.g. youtube.com/@channelname)",
    modeNotify: "Notify",
    modeAuto: "Auto-download",
    channelAddBtnLabel: "Add",
    settingsListTitle: "Followed Channels",
    channelEmpty: "No followed channels yet.",
    channelCheckNow: "Check now",
    channelRemove: "Remove",
    channelAddFailed: "Could not add channel",
    channelModeAutoBadge: "AUTO",
    channelModeNotifyBadge: "NOTIFY",
    channelLastChecked: "Last checked",
    channelNeverChecked: "Not checked yet",
    pendingTitle: "New Videos From Followed Channels",
    pendingClear: "Clear",
    settingsYtdlpTitle: "yt-dlp Version",
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
    ytdlpCreditText: "yt-dlp is built and maintained by its open-source contributors.",
    ytdlpCreditLink: "Say thanks on GitHub →",
  },
};

// NOTE: defaults to "tr" synchronously (not null) so t() always has a valid
// dictionary to read from. Any load*() call that reaches t() before
// initLang()'s own async /api/locale detection resolves (a real race - nothing
// here awaits initLang() before firing) would otherwise crash on
// "Cannot read properties of undefined". The system-detected language still
// applies moments later via applyLang() once initLang() resolves.
let lang = localStorage.getItem(LANG_KEY) || "tr";
let lastProbe = null; // { url, info } - currently shown single-video detail
let lastPlaylist = null; // { url, data } - currently shown playlist listing
let lastHistory = [];
let selectedSubtitles = new Set(); // checked subtitle language codes - go along with the next video download
let lastPending = [];
let lastChannels = [];

function t() {
  return I18N[lang];
}

async function initLang() {
  if (!localStorage.getItem(LANG_KEY)) {
    // NOTE: no stored preference yet - detect from the system locale. Until
    // this resolves, `lang` stays at its safe "tr" default from above.
    try {
      const res = await fetch("/api/locale");
      const data = await res.json();
      lang = data.lang === "en" ? "en" : "tr";
    } catch (err) {
      lang = "tr";
    }
  }
  applyLang();
}

function setLang(newLang) {
  lang = newLang;
  localStorage.setItem(LANG_KEY, lang);
  if (itemCard || sitesPage) {
    // NOTE: the metadata labels on /item and the site list on
    // /supported-sites are rendered server-side (Jinja2); rather than
    // keeping a second translation layer in JS, we just reload the page in
    // the correct language when it changes.
    const url = new URL(window.location.href);
    url.searchParams.set("lang", lang);
    window.location.href = url.toString();
    return;
  }
  applyLang();
}

function withLang(path) {
  return `${path}${path.includes("?") ? "&" : "?"}lang=${lang}`;
}

function applyLang() {
  // NOTE: if html[lang] stays Turkish, CSS text-transform:uppercase applies
  // Turkish uppercasing rules (I -> İ) even to English text.
  document.documentElement.lang = lang;
  langSwitch?.querySelectorAll("button").forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.lang === lang);
  });

  if (navHome) {
    navHome.textContent = t().navHome;
    navHome.href = withLang("/");
  }
  if (navHistory) {
    navHistory.textContent = t().navHistory;
    navHistory.href = withLang("/history");
  }
  if (navSites) {
    navSites.textContent = t().navSites;
    navSites.href = withLang("/supported-sites");
  }
  if (navSettings) {
    navSettings.textContent = t().navSettings;
    navSettings.href = withLang("/settings");
  }
  if (footerLegal) footerLegal.textContent = t().footerLegal;
  if (footerNote) footerNote.textContent = t().footerNote;

  if (heroTitle) heroTitle.textContent = t().heroTitle;
  if (heroSub) heroSub.textContent = t().heroSub;
  if (urlInput) urlInput.placeholder = t().placeholder;
  if (pasteBtn) pasteBtn.title = t().pasteBtnTitle;
  if (probeBtn) probeBtn.textContent = probeBtn.disabled ? t().resolveBtnBusy : t().resolveBtn;
  if (recentTitle) recentTitle.textContent = t().recentTitle;
  if (recentSeeAll) {
    recentSeeAll.textContent = t().recentSeeAll;
    recentSeeAll.href = withLang("/history");
  }
  if (historyPageTitle) historyPageTitle.textContent = t().historyPageTitle;
  if (historyClearBtn) historyClearBtn.textContent = t().historyClear;
  if (historySearchInput) historySearchInput.placeholder = t().historySearchPlaceholder;
  if (historyChannelFilter) populateChannelFilter();
  if (historyList) applyHistoryFilters();

  if (settingsPageTitleEl) settingsPageTitleEl.textContent = t().settingsPageTitle;
  if (settingsAddTitleEl) settingsAddTitleEl.textContent = t().settingsAddTitle;
  if (settingsAddHintEl) settingsAddHintEl.textContent = t().settingsAddHint;
  if (settingsListTitleEl) settingsListTitleEl.textContent = t().settingsListTitle;
  if (channelUrlInput) channelUrlInput.placeholder = t().channelUrlPlaceholder;
  if (modeNotifyLabel) modeNotifyLabel.textContent = t().modeNotify;
  if (modeAutoLabel) modeAutoLabel.textContent = t().modeAuto;
  if (channelAddBtn) channelAddBtn.textContent = t().channelAddBtnLabel;
  if (channelEmpty) channelEmpty.textContent = t().channelEmpty;
  if (pendingTitleEl) pendingTitleEl.textContent = t().pendingTitle;
  if (pendingClearBtn) pendingClearBtn.textContent = t().pendingClear;
  if (settingsYtdlpTitleEl) settingsYtdlpTitleEl.textContent = t().settingsYtdlpTitle;

  if (channelList) renderChannelList(lastChannels);
  if (pendingBanner) renderPending();
  if (ytdlpStatus) renderYtdlpVersion();

  if (card) {
    if (lastProbe) {
      renderCard(lastProbe.url, lastProbe.info);
    } else if (lastPlaylist) {
      renderPlaylist();
    }
  }
  if (recentList) renderRecent(lastHistory);
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

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

async function revealFile(url) {
  // NOTE: fetch() rather than a plain <a href> navigation - the endpoint
  // just opens the OS file explorer server-side and returns {"ok": true};
  // navigating to it directly would have shown raw JSON in the tab.
  try {
    await fetch(url);
  } catch (err) {
    // best-effort - revealing the file in explorer is a nice-to-have here.
  }
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

async function probe() {
  const url = urlInput.value.trim();
  if (!url) return;

  probeBtn.disabled = true;
  probeBtn.textContent = t().resolveBtnBusy;
  lastProbe = null;
  lastPlaylist = null;
  selectedSubtitles = new Set();

  try {
    const data = await fetchProbe(url);
    if (data.type === "playlist") {
      lastPlaylist = { url, data };
      renderPlaylist();
    } else {
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
  try {
    const data = await fetchProbe(entry.url);
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
        const selected = selectedSubtitles.has(s.code) ? " selected" : "";
        return `<button type="button" class="subtitle-chip${selected}" data-choice="${escapeHtml(s.code)}">${escapeHtml(s.label)}</button>`;
      })
      .join("");
    subtitleHtml = `
    <div class="section-title">${t().sectionSubtitle}</div>
    <div class="subtitle-hint">${t().subtitleHint}</div>
    <div class="subtitle-grid">${chipsHtml}</div>`;
  }

  let transcriptHtml = "";
  if (info.transcript) {
    const sourceLabel = info.transcript.source === "auto" ? t().transcriptAuto : t().transcriptManual;
    transcriptHtml = `
    <div class="section-title">${t().sectionTranscript}</div>
    <button type="button" class="option" data-kind="transcript" data-choice="${escapeHtml(info.transcript.code)}:${info.transcript.source}">
      <span>
        <span class="opt-label">${t().transcriptDownload}</span><br>
        <span class="opt-desc">${escapeHtml(info.transcript.code.toUpperCase())} · ${sourceLabel}</span>
      </span>
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

  card.innerHTML = `
    ${backLink}
    <div class="info-row">
      ${thumb}
      <div class="info-meta">
        <div class="title">${escapeHtml(info.title)}</div>
        <div class="sub">${escapeHtml(info.uploader)} · ${fmtDuration(info.duration)}</div>
      </div>
    </div>
    ${quickHtml}
    <details class="advanced-options">
      <summary>${t().advancedOptions}</summary>
      <div class="section-title">${t().sectionAudio}</div>
      ${audioHtml}
      <div class="section-title">${t().sectionVideo}</div>
      ${videoHtml}
      ${subtitleHtml}
      ${transcriptHtml}
    </details>
  `;

  card.querySelectorAll(".option, .quick-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      const subs = btn.dataset.kind === "video" ? Array.from(selectedSubtitles) : [];
      startDownload(url, btn.dataset.kind, btn.dataset.choice, subs, info.title);
    });
  });

  card.querySelectorAll(".subtitle-chip").forEach((chip) => {
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

  card.innerHTML = `
    <div class="playlist-title">${escapeHtml(data.title)}</div>
    <div class="playlist-count">${data.entries.length} ${t().videoWord}</div>
    <div class="playlist-list">${itemsHtml}</div>
  `;

  card.querySelectorAll(".playlist-item").forEach((btn) => {
    btn.addEventListener("click", () => {
      selectPlaylistEntry(data.entries[Number(btn.dataset.index)]);
    });
  });
}

async function startDownload(url, kind, choice, subtitleLangs, title) {
  try {
    const res = await fetch("/api/download", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url, kind, choice, subtitle_langs: subtitleLangs || [] }),
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
const dockPollTimers = {};

function loadTrackedJobIds() {
  try {
    return JSON.parse(localStorage.getItem(DOCK_JOBS_KEY) || "[]");
  } catch (err) {
    return [];
  }
}

function saveTrackedJobIds() {
  const stillActive = dockJobs.filter((j) => j.state !== "hata" && !(j.state === "bitti" && j.ready));
  localStorage.setItem(DOCK_JOBS_KEY, JSON.stringify(stillActive.map((j) => ({ jobId: j.jobId, title: j.title }))));
}

function trackDockJob(jobId, title) {
  dockJobs.push({ jobId, title, state: "basliyor", percent: 0, speed: null, ready: false, error: null });
  saveTrackedJobIds();
  renderDock();
  pollDockJob(jobId);
}

function dismissDockJob(jobId) {
  dockJobs = dockJobs.filter((j) => j.jobId !== jobId);
  if (dockPollTimers[jobId]) {
    clearInterval(dockPollTimers[jobId]);
    delete dockPollTimers[jobId];
  }
  saveTrackedJobIds();
  renderDock();
}

function pollDockJob(jobId) {
  if (dockPollTimers[jobId]) return;
  dockPollTimers[jobId] = setInterval(async () => {
    const job = dockJobs.find((j) => j.jobId === jobId);
    if (!job) {
      clearInterval(dockPollTimers[jobId]);
      delete dockPollTimers[jobId];
      return;
    }
    try {
      const res = await fetch(`/api/status/${jobId}`);
      if (res.status === 404) {
        // NOTE: the server has no record of this job at all - almost always
        // because it restarted since this job was tracked (its jobs dict is
        // in-memory only) and a stale entry survived in this browser's
        // localStorage. That's infrastructure noise, not a real download
        // failure the user did anything to cause, so this cleans it up
        // silently instead of popping an alarming, unexplained error toast.
        clearInterval(dockPollTimers[jobId]);
        delete dockPollTimers[jobId];
        dismissDockJob(jobId);
        return;
      }
      const data = await res.json();
      if (!res.ok) {
        clearInterval(dockPollTimers[jobId]);
        delete dockPollTimers[jobId];
        job.state = "hata";
        job.error = data.detail || t().errStatusFailed;
        saveTrackedJobIds();
        renderDock();
        return;
      }
      Object.assign(job, data);
      if (data.state === "hata" || (data.state === "bitti" && data.ready)) {
        clearInterval(dockPollTimers[jobId]);
        delete dockPollTimers[jobId];
        saveTrackedJobIds();
        if (data.state === "bitti" && data.ready) loadHistory();
      }
      renderDock();
    } catch (err) {
      // NOTE: transient network hiccup while polling - keep retrying rather
      // than killing the row, since the download itself keeps running
      // server-side regardless of whether this poll succeeds.
    }
  }, 800);
}

function dockRowHtml(job) {
  const percent = job.percent || 0;
  let statusHtml;
  if (job.state === "hata") {
    const friendly = friendlyError(job.error) || job.error || t().errUnknown;
    statusHtml = `<div class="dock-row-error">${escapeHtml(friendly)}</div>`;
  } else if (job.state === "bitti" && job.ready) {
    statusHtml = `<button type="button" class="dock-reveal-btn" data-job-id="${job.jobId}">${t().downloadBtn}</button>`;
  } else {
    statusHtml = `
      <div class="dock-row-bar-bg"><div class="dock-row-bar-fg" style="width:${percent}%"></div></div>
      <div class="dock-row-meta">${t().states[job.state] || job.state}${job.speed ? " · " + escapeHtml(job.speed) : ""}</div>`;
  }
  return `
    <div class="dock-row" data-job-id="${job.jobId}">
      <div class="dock-row-title" title="${escapeHtml(job.title)}">${escapeHtml(job.title)}</div>
      <div class="dock-row-status">${statusHtml}</div>
      <button type="button" class="dock-dismiss-btn" data-job-id="${job.jobId}" title="${t().dockDismiss}">✕</button>
    </div>`;
}

function renderDock() {
  if (!downloadDock) return;
  if (dockJobs.length === 0) {
    downloadDock.classList.add("hidden");
    downloadDock.innerHTML = "";
    return;
  }
  downloadDock.classList.remove("hidden");
  downloadDock.innerHTML = dockJobs.map(dockRowHtml).join("");

  downloadDock.querySelectorAll(".dock-reveal-btn").forEach((btn) => {
    btn.addEventListener("click", () => revealFile(`/api/file/${btn.dataset.jobId}`));
  });
  downloadDock.querySelectorAll(".dock-dismiss-btn").forEach((btn) => {
    btn.addEventListener("click", () => dismissDockJob(btn.dataset.jobId));
  });
}

function resumeTrackedDockJobs() {
  const stored = loadTrackedJobIds();
  if (stored.length === 0) return;
  dockJobs = stored.map((j) => ({ ...j, state: "indiriliyor", percent: 0, speed: null, ready: false, error: null }));
  renderDock();
  dockJobs.forEach((j) => pollDockJob(j.jobId));
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

function applyHistoryFilters() {
  if (!historyList) return;
  const q = (historySearchInput?.value || "").trim().toLowerCase();
  const channel = historyChannelFilter?.value || "";
  const filtered = lastHistory.filter((item) => {
    const matchesQuery = !q || item.filename.toLowerCase().includes(q);
    const matchesChannel = !channel || item.folder === channel;
    return matchesQuery && matchesChannel;
  });
  renderHistory(filtered);
}

const VIDEO_EXTS = new Set(["mp4"]);
const SUBTITLE_EXTS = new Set(["srt"]);
const TRANSCRIPT_EXTS = new Set(["txt"]);

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
  const thumbUrl = `/api/history/thumb/${encodedPath}`;
  const itemUrl = withLang(`/item/${encodedPath}`);
  const baseName = item.filename.includes("/") ? item.filename.split("/").pop() : item.filename;
  const folderBadge = item.folder ? `<div class="folder-badge">${escapeHtml(item.folder)}</div>` : "";
  const actions = withActions
    ? `
      <div class="history-actions">
        <button type="button" class="reveal-btn" data-reveal-url="${fileUrl}">${t().historyDownload}</button>
        <button type="button" class="delete-btn">${t().historyDelete}</button>
      </div>`
    : "";
  return `
    <div class="history-card" data-filename="${escapeHtml(item.filename)}">
      <a class="history-card-link" href="${itemUrl}">
        <div class="history-thumb">
          <span class="placeholder">${placeholder}</span>
          <img src="${thumbUrl}" alt="" loading="lazy" onerror="this.remove()">
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
historyClearBtn?.addEventListener("click", clearAllHistory);
historySearchInput?.addEventListener("input", applyHistoryFilters);
historyChannelFilter?.addEventListener("change", applyHistoryFilters);
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

initLang();
loadHistory();
loadChannels();
loadPending();
loadYtdlpVersion();
resumeTrackedDockJobs();

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
