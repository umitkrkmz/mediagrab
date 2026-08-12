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
const footerLegal = document.getElementById("footer-legal");
const footerNote = document.getElementById("footer-note");
const langSwitch = document.getElementById("lang-switch");
const itemCard = document.querySelector(".item-card");

const LANG_KEY = "mediagrab_lang";

// NOTE: error messages from the server (yt-dlp/downloader) are dynamic and
// mostly already English/technical, so there's no translation layer for
// them; only the client-side strings defined here change with the language.
const I18N = {
  tr: {
    navHome: "Ana Sayfa",
    navHistory: "Geçmiş",
    footerLegal:
      "Bu araç yalnızca kişisel kullanım içindir. İndirdiğiniz içeriğin telif durumundan ve ilgili platformun kullanım şartlarına uyumdan tamamen siz sorumlusunuz.",
    footerNote: "MediaGrab, yt-dlp ile çalışır. Veritabanı ve hesap sistemi yoktur — sadece bu bilgisayarda çalışır.",
    heroTitle: "Link yapıştır, indir",
    heroSub: "YouTube ve YouTube Music linkini yapıştırın; ses veya video olarak indirin.",
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
    downloadBtn: "Dosyayı indir",
    errProbeFailed: "Çözümlenemedi",
    errDownloadFailed: "İndirme başlatılamadı",
    errNetwork: "Ağ hatası: ",
    errStatusFailed: "Durum alınamadı",
    errUnknown: "Bilinmeyen hata",
    historyPageTitle: "İndirme Geçmişi",
    historyEmpty: "Henüz indirme yok",
    historyDownload: "İndir",
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
  },
  en: {
    navHome: "Home",
    navHistory: "History",
    footerLegal:
      "This tool is for personal use only. You are solely responsible for the copyright status of downloaded content and compliance with the relevant platform's terms of service.",
    footerNote: "MediaGrab runs on yt-dlp. No database or account system — it only runs on this computer.",
    heroTitle: "Paste a link, download",
    heroSub: "Paste a YouTube or YouTube Music link; download it as audio or video.",
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
    downloadBtn: "Download file",
    errProbeFailed: "Could not resolve",
    errDownloadFailed: "Could not start download",
    errNetwork: "Network error: ",
    errStatusFailed: "Could not get status",
    errUnknown: "Unknown error",
    historyPageTitle: "Download History",
    historyEmpty: "No downloads yet",
    historyDownload: "Download",
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
  },
};

let lang = localStorage.getItem(LANG_KEY);
let lastProbe = null; // { url, info } - currently shown single-video detail
let lastPlaylist = null; // { url, data } - currently shown playlist listing
let lastHistory = [];
let pollTimer = null;
let selectedSubtitles = new Set(); // checked subtitle language codes - go along with the next video download

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
  if (itemCard) {
    // NOTE: the metadata labels on the /item page are rendered server-side
    // (Jinja2); rather than keeping a second translation layer in JS, we just
    // reload the page in the correct language when it changes.
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
          extraEl.innerHTML = `<a class="download-btn" href="/api/file/${jobId}">${t().downloadBtn}</a>`;
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

function historyCardHtml(item, withActions) {
  const date = new Date(item.downloaded_at).toLocaleString(t().locale, {
    dateStyle: "medium",
    timeStyle: "short",
  });
  const placeholder = VIDEO_EXTS.has(item.ext) ? "▶" : SUBTITLE_EXTS.has(item.ext) ? "CC" : "♪";
  const fileUrl = `/api/history/file/${encodeURIComponent(item.filename)}`;
  const thumbUrl = `/api/history/thumb/${encodeURIComponent(item.filename)}`;
  const itemUrl = withLang(`/item/${encodeURIComponent(item.filename)}`);
  const actions = withActions
    ? `
      <div class="history-actions">
        <a href="${fileUrl}">${t().historyDownload}</a>
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
          <div class="name" title="${escapeHtml(item.filename)}">${escapeHtml(item.filename)}</div>
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
    const res = await fetch(`/api/history/${encodeURIComponent(filename)}`, { method: "DELETE" });
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

probeBtn?.addEventListener("click", probe);
urlInput?.addEventListener("keydown", (e) => {
  if (e.key === "Enter") probe();
});
langSwitch?.querySelectorAll("button").forEach((btn) => {
  btn.addEventListener("click", () => setLang(btn.dataset.lang));
});
historyClearBtn?.addEventListener("click", clearAllHistory);

initLang();
loadHistory();
