from typing import Literal, Optional

from pydantic import BaseModel


class ProbeRequest(BaseModel):
    url: str


class VideoFormat(BaseModel):
    format_id: str
    label: str
    ext: str
    vcodec: str
    size: str
    # NOTE: the raw byte count behind `size` (real or tbr-estimated), used by
    # the disk-space check on download start - see DownloadRequest below.
    size_bytes: Optional[int] = None


class SubtitleOption(BaseModel):
    code: str
    label: str


class ProbeResponse(BaseModel):
    type: Literal["video"] = "video"
    title: str
    uploader: str
    duration: int
    thumbnail: Optional[str] = None
    video: list[VideoFormat]
    subtitles: list[SubtitleOption] = []


class PlaylistEntry(BaseModel):
    id: str
    title: str
    url: str
    duration: int = 0
    uploader: Optional[str] = None
    thumbnail: Optional[str] = None


class PlaylistProbeResponse(BaseModel):
    type: Literal["playlist"] = "playlist"
    title: str
    entries: list[PlaylistEntry]


class DownloadRequest(BaseModel):
    url: str
    kind: Literal["audio", "video", "subtitle", "transcript"]
    choice: str
    subtitle_langs: list[str] = []
    # NOTE: empty means "no preference" - yt-dlp's own default (the original
    # audio track) applies. One entry behaves as before this field existed;
    # two or more requests a single file with all of them as separate,
    # selectable audio tracks (video downloads only - see downloader.py).
    audio_langs: list[str] = []
    # NOTE: the selected video format's size_bytes, echoed back by the
    # client - only ever known for a probed video format (see VideoFormat
    # above). None for audio/subtitle/transcript downloads and for anything
    # queued without a prior probe (e.g. a playlist bulk download) - the
    # disk-space check in app.py falls back to an absolute floor then.
    estimated_size_bytes: Optional[int] = None


class DownloadStartResponse(BaseModel):
    job_id: str


class StatusResponse(BaseModel):
    state: Literal["basliyor", "indiriliyor", "isleniyor", "bitti", "hata", "iptal"]
    percent: float = 0.0
    speed: Optional[str] = None
    eta: Optional[str] = None
    ready: bool = False
    error: Optional[str] = None
    # NOTE: 1-based place in the queue while waiting for a free worker slot;
    # None once the download has actually started.
    queue_position: Optional[int] = None


class SettingsResponse(BaseModel):
    cookie_mode: Literal["off", "browser", "file"]
    cookie_browser: str
    # NOTE: only the PATH is ever exposed - the cookie contents never leave
    # the file, yt-dlp reads them directly from disk.
    cookie_file: str
    default_audio_lang: str = ""
    # NOTE: 0 means unlimited.
    download_speed_limit_mbps: int = 0
    # NOTE: see store.py's DEFAULT_SETTINGS - switches followed-channel
    # checking from "once at launch" to periodic.
    home_server_mode: bool = False


class SettingsUpdateRequest(BaseModel):
    cookie_mode: Literal["off", "browser", "file"] = "off"
    cookie_browser: str = "firefox"
    cookie_file: str = ""
    default_audio_lang: str = ""
    download_speed_limit_mbps: int = 0
    home_server_mode: bool = False


class LoginRequest(BaseModel):
    password: str


class ClientInfoResponse(BaseModel):
    # NOTE: whether THIS request came from the host machine itself
    # (127.0.0.1/::1) or from another device on the LAN - decides whether the
    # UI offers "show in folder" (only useful when you're sitting at the
    # host) or a real "download to this device" action.
    is_local: bool


class RemoteAccessStatus(BaseModel):
    enabled: bool
    # NOTE: never the hash itself - only whether one has been set, so the
    # settings UI can tell "off" apart from "on but no password yet".
    has_password: bool
    # NOTE: only set once this is genuinely reachable (enabled AND bound
    # beyond localhost, see store.remote_access_active) - showing a LAN
    # address before then would be a link that doesn't actually work yet.
    lan_url: Optional[str] = None
    download_mode: Literal["keep", "relay"] = "keep"


class SessionInfo(BaseModel):
    id: str
    created_at: float
    device: str
    is_current: bool


class SessionListResponse(BaseModel):
    sessions: list[SessionInfo]


class RemoteAccessUpdateRequest(BaseModel):
    enabled: bool
    download_mode: Literal["keep", "relay"] = "keep"


class SetPasswordRequest(BaseModel):
    password: str
    # NOTE: only checked when a password already exists (see the route) -
    # setting the very first password has nothing to confirm against.
    current_password: str = ""


class HistoryItem(BaseModel):
    filename: str
    folder: Optional[str] = None
    ext: str
    size: str
    downloaded_at: str


class LocaleResponse(BaseModel):
    lang: Literal["tr", "en"]


class YtdlpVersionResponse(BaseModel):
    installed: str
    latest: Optional[str] = None
    update_available: Optional[bool] = None


class ChannelAddRequest(BaseModel):
    url: str
    mode: Literal["notify", "auto"]
    choice_kind: Literal["audio", "video"]
    choice: str


class ChannelItem(BaseModel):
    id: str
    url: str
    name: str
    thumbnail: Optional[str] = None
    mode: Literal["notify", "auto"]
    choice_kind: Literal["audio", "video"]
    choice: str
    last_video_id: Optional[str] = None
    added_at: str
    last_checked_at: Optional[str] = None
    # NOTE: set when the most recent check failed, cleared on the next success.
    # Without it a broken channel (renamed, deleted, private) just silently
    # stops producing videos and the user has no way to tell.
    last_error: Optional[str] = None


class PendingVideo(BaseModel):
    channel_id: str
    channel_name: str
    id: str
    title: str
    url: str
    thumbnail: Optional[str] = None
    duration: int = 0


class SettingsImportRequest(BaseModel):
    mediagrab_export_version: int = 1
    # NOTE: a plain dict, not SettingsResponse - an older/newer export's
    # settings shape may not exactly match this version's model, and the
    # route filters it down to known, non-credential keys anyway (see its own
    # comment). Validating channels/pending as real models still catches a
    # corrupt or hand-edited file with the wrong shape there.
    settings: dict = {}
    channels: list[ChannelItem] = []
    pending: list[PendingVideo] = []
