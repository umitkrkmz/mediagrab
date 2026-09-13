"""Tests for the SSE job-progress endpoint (/api/events), which replaced the
download dock's old 800ms-per-job polling.

NOTE: these drive job_events()'s returned StreamingResponse's body_iterator
directly with asyncio.run(), rather than going through
fastapi.testclient.TestClient's streaming support. That was tried first and
reliably hung forever in this environment's starlette/httpx2 pairing - a real
uvicorn server was confirmed live (curl -N and a real browser download, both
against an actual socket) to deliver bytes immediately and incrementally, so
that hang is a limitation of the in-process ASGI test transport, not a bug in
the endpoint. Driving the async generator directly exercises the exact same
production code (job_events, _broadcast_job_event, _set_job) without relying
on that transport.
"""

import asyncio
import json

import pytest

import mediagrab.app as app_module


class _FakeRequest:
    """Answers is_disconnected() False a fixed number of times, then True -
    stands in for a real client staying connected just long enough for the
    test, then "disconnecting" so the generator's own loop exits on its own.
    """

    def __init__(self, disconnect_after: int):
        self._checks = 0
        self._disconnect_after = disconnect_after

    async def is_disconnected(self) -> bool:
        self._checks += 1
        return self._checks > self._disconnect_after


@pytest.fixture(autouse=True)
def _event_loop_for_broadcast(monkeypatch):
    # NOTE: _broadcast_job_event needs _event_loop set (normally done once by
    # `lifespan` at real startup) - each test below runs inside its own
    # asyncio.run(), so it sets this to ITS running loop before calling
    # _set_job, and this fixture guarantees it's cleared again afterwards
    # regardless of pass/fail.
    monkeypatch.setattr(app_module, "_event_loop", None)
    yield


def test_the_stream_yields_a_ready_comment_immediately():
    async def scenario():
        response = await app_module.job_events(_FakeRequest(disconnect_after=0))
        agen = response.body_iterator
        first = await agen.__anext__()
        await agen.aclose()
        return first

    first = asyncio.run(scenario())
    assert first == ": connected\n\n"


def test_a_broadcast_job_update_is_yielded_as_a_data_line():
    job_id = "probe-job"
    app_module.jobs[job_id] = {
        "state": "basliyor",
        "percent": 0.0,
        "speed": None,
        "eta": None,
        "ready": False,
        "error": None,
        "seq": 0,
    }
    try:

        async def scenario():
            app_module._event_loop = asyncio.get_running_loop()
            response = await app_module.job_events(_FakeRequest(disconnect_after=2))
            agen = response.body_iterator
            first = await agen.__anext__()  # ": connected\n\n"

            async def push_soon():
                await asyncio.sleep(0.05)
                # NOTE: called from a plain coroutine here, but this is the
                # exact function yt-dlp's progress hooks call from a WORKER
                # THREAD in the real app (see _run_job) - the thread-safety
                # of that handoff isn't what this test is checking.
                app_module._set_job(job_id, state="indiriliyor", percent=42.0, speed="1.2 MB/s")

            pusher = asyncio.create_task(push_soon())
            second = await agen.__anext__()  # the generator awaits queue.get() until push_soon() delivers
            await pusher
            await agen.aclose()
            return first, second

        first, second = asyncio.run(scenario())
        assert first == ": connected\n\n"
        assert second.startswith("data:")
        payload = json.loads(second[len("data:") :].strip())
        assert payload["job_id"] == job_id
        assert payload["state"] == "indiriliyor"
        assert payload["percent"] == 42.0
        assert payload["speed"] == "1.2 MB/s"
    finally:
        app_module.jobs.pop(job_id, None)


def test_queue_position_in_a_broadcast_event_matches_a_polled_snapshot():
    # NOTE: queue_position is computed (depends on every OTHER waiting job),
    # not stored - this proves _set_job's broadcast recomputes it the same
    # way GET /api/status/{job_id} (the `status` function) does, so a pushed
    # event looks identical to what polling would have returned right then.
    waiting_id, target_id = "waiting-job", "target-job"
    app_module.jobs[waiting_id] = {
        "state": "basliyor", "percent": 0.0, "speed": None, "eta": None,
        "ready": False, "error": None, "seq": 1,
    }
    app_module.jobs[target_id] = {
        "state": "basliyor", "percent": 0.0, "speed": None, "eta": None,
        "ready": False, "error": None, "seq": 2,
    }
    try:

        async def scenario():
            app_module._event_loop = asyncio.get_running_loop()
            response = await app_module.job_events(_FakeRequest(disconnect_after=2))
            agen = response.body_iterator
            await agen.__anext__()  # ": connected\n\n"

            async def push_soon():
                await asyncio.sleep(0.05)
                app_module._set_job(target_id, percent=1.0)  # no real change, just re-triggers a broadcast

            pusher = asyncio.create_task(push_soon())
            data_line = await agen.__anext__()
            await pusher
            await agen.aclose()
            return data_line

        data_line = asyncio.run(scenario())
        payload = json.loads(data_line[len("data:") :].strip())
        assert payload["job_id"] == target_id

        polled = app_module.status(target_id)
        assert payload["queue_position"] == polled["queue_position"] == 2
    finally:
        app_module.jobs.pop(waiting_id, None)
        app_module.jobs.pop(target_id, None)


def test_the_stream_stops_once_the_client_disconnects():
    async def scenario():
        request = _FakeRequest(disconnect_after=0)
        response = await app_module.job_events(request)
        agen = response.body_iterator
        await agen.__anext__()  # ": connected\n\n" - unconditional, before the loop even checks is_disconnected

        with pytest.raises(StopAsyncIteration):
            await agen.__anext__()  # is_disconnected() now returns True -> loop breaks -> generator ends

    asyncio.run(scenario())


def test_disconnecting_removes_the_queue_so_nothing_leaks():
    async def scenario():
        response = await app_module.job_events(_FakeRequest(disconnect_after=0))
        agen = response.body_iterator
        await agen.__anext__()
        assert len(app_module._event_queues) == 1, "the connection should have registered its own queue"
        try:
            await agen.__anext__()
        except StopAsyncIteration:
            pass
        assert len(app_module._event_queues) == 0, "a finished/disconnected stream must clean up its queue"

    assert len(app_module._event_queues) == 0, "no leftover queues from a previous test"
    asyncio.run(scenario())


def test_broadcasting_with_no_connected_clients_does_not_raise():
    # NOTE: the common case - most job updates happen with nobody's SSE
    # connection open at all. Must be a silent no-op, not an error that
    # would take the download thread down with it. No event loop is even
    # set up here (the autouse fixture clears it) - _broadcast_job_event
    # must tolerate that too, since it's the state right after a fresh
    # server start before anyone has opened /api/events.
    app_module._broadcast_job_event("nonexistent-job", {"state": "bitti"})
