// NOTE: this script is loaded on the index/history/item pages alike (for the
// shared header/footer/language switcher), so every DOM element can be null -
// check it exists before using it.
const urlInput = document.getElementById("url-input");
const probeBtn = document.getElementById("probe-btn");
const card = document.getElementById("card");
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
const navHome = document.getElementById("nav-home");
const navHistory = document.getElementById("nav-history");
const navSites = document.getElementById("nav-sites");
const navSettings = document.getElementById("nav-settings");
const footerLegal = document.getElementById("footer-legal");
const footerNote = document.getElementById("footer-note");
const langSwitch = document.getElementById("lang-switch");
const itemCard = document.querySelector(".item-card");
const itemRevealBtn = document.getElementById("item-reveal-btn");
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
    errProbeFailed: "Çözümlenemedi",
    errDownloadFailed: "İndirme başlatılamadı",
    errNetwork: "Ağ hatası: ",
    errStatusFailed: "Durum alınamadı",
    errUnknown: "Bilinmeyen hata",
    historyPageTitle: "İndirme Geçmişi",
    historyEmpty: "Henüz indirme yok",
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
    errProbeFailed: "Could not resolve",
    errDownloadFailed: "Could not start download",
    errNetwork: "Network error: ",
    errStatusFailed: "Could not get status",
    errUnknown: "Unknown error",
    historyPageTitle: "Download History",
    historyEmpty: "No downloads yet",
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

let lang = localStorage.getItem(LANG_KEY);
let lastProbe = null; // { url, info } - currently shown single-video detail
let lastPlaylist = null; // { url, data } - currently shown playlist listing
let lastHistory = [];
let pollTimer = null;
let selectedSubtitles = new Set(); // checked subtitle language codes - go along with the next video download
let lastPending = [];
let lastChannels = [];

function t() {
  return I18N[lang];
}

async function initLang() {
  if (!lang) {
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
  if (probeBtn) probeBtn.textContent = probeBtn.disabled ? t().resolveBtnBusy : t().resolveBtn;
  if (recentTitle) recentTitle.textContent = t().recentTitle;
  if (recentSeeAll) {
    recentSeeAll.textContent = t().recentSeeAll;
    recentSeeAll.href = withLang("/history");
  }
  if (historyPageTitle) historyPageTitle.textContent = t().historyPageTitle;
  if (historyClearBtn) historyClearBtn.textContent = t().historyClear;

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
  if (historyList) renderHistory(lastHistory);
  if (recentList) renderRecent(lastHistory);
}

function fmtDuration(seconds) {
  seconds = Math.floor(seconds || 0);
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${m}:${String(s).padStart(2, "0")}`;
}

function showError(message) {
  if (!card) return;
  card.classList.remove("hidden");
  card.innerHTML = `<div class="error">${escapeHtml(message)}</div>`;
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
  if (pollTimer) {
    clearInterval(pollTimer);
    pollTimer = null;
  }
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
    showError(err.message);
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
    showError(err.message);
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

  card.innerHTML = `
    ${backLink}
    <div class="info-row">
      ${thumb}
      <div class="info-meta">
        <div class="title">${escapeHtml(info.title)}</div>
        <div class="sub">${escapeHtml(info.uploader)} · ${fmtDuration(info.duration)}</div>
      </div>
    </div>
    <div class="section-title">${t().sectionAudio}</div>
    ${audioHtml}
    <div class="section-title">${t().sectionVideo}</div>
    ${videoHtml}
    ${subtitleHtml}
  `;

  card.querySelectorAll(".option").forEach((btn) => {
    btn.addEventListener("click", () => {
      const subs = btn.dataset.kind === "video" ? Array.from(selectedSubtitles) : [];
      startDownload(url, btn.dataset.kind, btn.dataset.choice, subs);
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

async function startDownload(url, kind, choice, subtitleLangs) {
  card.innerHTML = `
    <div class="progress-wrap">
      <div class="progress-status" id="progress-status">${t().states.basliyor}</div>
      <div class="progress-bar-bg"><div class="progress-bar-fg" id="progress-bar" style="width:0%"></div></div>
      <div class="progress-extra" id="progress-extra"></div>
    </div>
  `;

  try {
    const res = await fetch("/api/download", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url, kind, choice, subtitle_langs: subtitleLangs || [] }),
    });
    const data = await res.json();
    if (!res.ok) {
      showError(data.detail || t().errDownloadFailed);
      return;
    }
    pollStatus(data.job_id);
  } catch (err) {
    showError(t().errNetwork + err.message);
  }
}

function pollStatus(jobId) {
  pollTimer = setInterval(async () => {
    try {
      const res = await fetch(`/api/status/${jobId}`);
      const data = await res.json();
      if (!res.ok) {
        clearInterval(pollTimer);
        showError(data.detail || t().errStatusFailed);
        return;
      }

      const statusEl = document.getElementById("progress-status");
      const barEl = document.getElementById("progress-bar");
      const extraEl = document.getElementById("progress-extra");

      if (data.state === "hata") {
        clearInterval(pollTimer);
        showError(data.error || t().errUnknown);
        return;
      }

      if (statusEl) statusEl.textContent = t().states[data.state] || data.state;
      if (barEl) barEl.style.width = `${data.percent || 0}%`;
      if (extraEl) extraEl.textContent = data.speed ? data.speed : "";

      if (data.state === "bitti" && data.ready) {
        clearInterval(pollTimer);
        if (extraEl) {
          extraEl.innerHTML = `<button type="button" class="download-btn" id="reveal-btn-${jobId}">${t().downloadBtn}</button>`;
          document
            .getElementById(`reveal-btn-${jobId}`)
            ?.addEventListener("click", () => revealFile(`/api/file/${jobId}`));
        }
        loadHistory();
      }
    } catch (err) {
      clearInterval(pollTimer);
      showError(t().errNetwork + err.message);
    }
  }, 800);
}

async function loadHistory() {
  if (!historyList && !recentList) return;
  try {
    const res = await fetch("/api/history");
    const data = await res.json();
    if (!res.ok) return;
    lastHistory = data;
    if (historyList) renderHistory(lastHistory);
    if (recentList) renderRecent(lastHistory);
  } catch (err) {
    // NOTE: if history fails to load, give up silently - don't break the main flow.
  }
}

const VIDEO_EXTS = new Set(["mp4"]);
const SUBTITLE_EXTS = new Set(["srt"]);

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
  const placeholder = VIDEO_EXTS.has(item.ext) ? "▶" : SUBTITLE_EXTS.has(item.ext) ? "CC" : "♪";
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
  historyClearBtn?.classList.toggle("hidden", !items || items.length === 0);

  if (!items || items.length === 0) {
    historyList.innerHTML = `<div class="history-empty">${t().historyEmpty}</div>`;
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
    </ol>`;
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
langSwitch?.querySelectorAll("button").forEach((btn) => {
  btn.addEventListener("click", () => setLang(btn.dataset.lang));
});
historyClearBtn?.addEventListener("click", clearAllHistory);
itemRevealBtn?.addEventListener("click", () => revealFile(itemRevealBtn.dataset.revealUrl));
channelAddBtn?.addEventListener("click", addChannel);
channelModeRadios.forEach((r) => r.addEventListener("change", updateChannelChoiceVisibility));
pendingClearBtn?.addEventListener("click", clearPending);
updateChannelChoiceVisibility();

initLang();
loadHistory();
loadChannels();
loadPending();
loadYtdlpVersion();
