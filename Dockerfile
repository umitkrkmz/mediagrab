# NOTE: no venv - the container itself is the isolation layer, and
# PYTHONUSERBASE (below) relies on user-site packages taking import priority,
# which is disabled by default inside a venv. See V2_PLANNING.md's Docker
# section for the reasoning behind every decision in this file.
FROM python:3.12-slim

# ffmpeg is the only system dependency MediaGrab needs (merging/converting) -
# yt-dlp and every Python package come from requirements.txt below.
RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# NOTE: requirements.txt copied (and installed) before the rest of the
# source, so an ordinary code change doesn't invalidate this layer and force
# a full dependency reinstall on every rebuild.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY mediagrab/ ./mediagrab/
COPY run.py .

# NOTE: lets the "Update yt-dlp" button (Settings) install into a
# volume-mounted path that survives the container being recreated from a
# fresh image - see downloader.update_ytdlp's own comment. Every OTHER
# package updates only by pulling a new image (see app.py's
# /api/dependencies-update, which refuses in Docker).
ENV PYTHONUSERBASE=/data/pip-packages

EXPOSE 8420

CMD ["python", "run.py"]
