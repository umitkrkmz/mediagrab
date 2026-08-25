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


class DownloadStartResponse(BaseModel):
    job_id: str


class StatusResponse(BaseModel):
    state: Literal["basliyor", "indiriliyor", "isleniyor", "bitti", "hata", "iptal"]
    percent: float = 0.0
    speed: Optional[str] = None
    ready: bool = False
    error: Optional[str] = None
    # NOTE: 1-based place in the queue while waiting for a free worker slot;
    # None once the download has actually started.
    queue_position: Optional[int] = None


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
