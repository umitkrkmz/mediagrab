#!/usr/bin/env bash
# Smoke test for a built MediaGrab image: start it the way a user would and
# walk the main path once. Run by docker.yml before anything is pushed; also
# runnable by hand against a local build:
#
#   docker build -t mediagrab:dev .
#   bash .github/scripts/smoke-docker.sh mediagrab:dev 8422
#
# NOTE: deeper than "did the container answer" on purpose - an image can
# start fine and still ship without ffprobe or Deno (YouTube then fails for
# every user), or with a password that doesn't log in. No network needed:
# the test clip is generated inside the container.
set -eu
IMAGE="${1:-mediagrab:smoke-test}"
NAME=mediagrab-smoke
PORT="${2:-8420}"
fail() {
  echo "SMOKE FAIL: $1"
  docker logs "$NAME" || true
  exit 1
}
docker run -d --name "$NAME" \
  -e MEDIAGRAB_INITIAL_PASSWORD=smoke-test-password \
  -e MEDIAGRAB_PORT=8420 \
  -p "$PORT:8420" \
  "$IMAGE" > /dev/null
base="http://localhost:$PORT"
ok=""
for i in $(seq 1 15); do
  if curl -sf "$base/login" > /dev/null; then ok=1; break; fi
  sleep 1
done
[ -n "$ok" ] || fail "container never responded on :8420"
echo "ok: responds"

# The password from MEDIAGRAB_INITIAL_PASSWORD must actually log in -
# without it a fresh container is unusable.
jar=$(mktemp)
curl -sf -c "$jar" -H "Content-Type: application/json" \
  -d '{"password":"smoke-test-password"}' "$base/api/login" > /dev/null || fail "login with the initial password"
echo "ok: login"

# The tools the image promises to bundle.
docker exec "$NAME" ffmpeg -version > /dev/null || fail "ffmpeg missing"
docker exec "$NAME" ffprobe -version > /dev/null || fail "ffprobe missing"
docker exec "$NAME" python -c "from mediagrab import downloader as d; s = d.js_runtime_status(); assert s['js_runtime'] and s['js_solver'], s" \
  || fail "JS runtime (Deno) or its solver missing - YouTube downloads would fail"
echo "ok: ffmpeg, ffprobe, deno"

# A real file through the real pipeline: History lists it, ffprobe reads its
# resolution for the detail page, statistics answer.
docker exec "$NAME" sh -c 'mkdir -p "/app/indirilenler/Smoke" && ffmpeg -loglevel error -f lavfi -i testsrc=duration=1:size=640x360:rate=25 -f lavfi -i sine=duration=1 -shortest "/app/indirilenler/Smoke/Clip.mp4"' \
  || fail "could not write into the downloads folder"
curl -sf -b "$jar" "$base/api/history" | grep -q '"Smoke/Clip.mp4"' || fail "History does not list the file"
curl -sf -b "$jar" "$base/item/Smoke/Clip.mp4?lang=en" | grep -q "640×360 (360p)" || fail "detail page has no resolution row (ffprobe)"
curl -sf -b "$jar" "$base/api/stats?period=day&tz=0" | grep -q '"disk":{' || fail "statistics endpoint"
echo "ok: history, detail page, statistics"
echo "container passed the smoke test"
docker rm -f "$NAME" > /dev/null
