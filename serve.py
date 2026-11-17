#!/usr/bin/env python3
"""
FitFindr over HTTP. ← UNIT 9

    python serve.py                       run it on your machine
    gunicorn serve:app                    run it the way a host runs it

Everything else in this repo exits after one command. A host has nothing to
keep running, so a command line cannot be deployed. This file is the smallest
thing that can: it starts a web server, waits, and hands each request to the
same `run_agent()` your CLI calls. **No new agent logic lives here.** If your
loop works from `python app.py ask`, it works from here; if it doesn't, fix it
there, not in this file.

Two routes:

    POST /ask       {"query": "vintage graphic tee under $30",
                     "wardrobe": {...}}     ← wardrobe is optional
    GET  /health    is it awake?

`/ask` returns the session dict from `run_agent()` as JSON, unchanged — the
same keys you print from the command line, including `error`. Read
`session["error"]` first, exactly as you do everywhere else.

It runs **one request at a time**, and one route is deliberately slower than a
web server has to be. The reason is worth reading before you deploy: see the
note above `_one_at_a_time` below — it also decides which gunicorn worker you
can use.

Logging: every request to /ask writes one JSON line — to stderr and to
logs/serve.jsonl — with a request id, a running request count, the query, the
outcome, and timing split into time spent waiting for its turn and time spent
running the agent. See `_log` and the "Logging" notes in RUNNING.md.
"""

import json
import os
import sys
import threading
import time
import uuid
from datetime import datetime, timezone

# config first, and before anything that talks to the model: it loads your .env
# and fixes the Windows console encoding for every module that imports it.
import config  # noqa: F401

from flask import Flask, jsonify, request

import generate
from agent import run_agent
from utils.data_loader import get_example_wardrobe

app = Flask(__name__)


# ── structured log ────────────────────────────────────────────────────────────
# One JSON object per line. stderr is what a host captures; the file is what
# you read back and commit. A log write that fails must never fail the request.

LOG_FILE = config.ROOT / "logs" / "serve.jsonl"
_request_count = 0


def _log(event: dict) -> None:
    line = json.dumps(
        {"ts": datetime.now(timezone.utc).isoformat(timespec="milliseconds"), **event},
        ensure_ascii=False,
    )
    print(line, file=sys.stderr, flush=True)
    try:
        LOG_FILE.parent.mkdir(exist_ok=True)
        with LOG_FILE.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
    except OSError:
        pass


# ── one request at a time ─────────────────────────────────────────────────────
# Here's why this exists.
#
# A web server will happily run two requests at once. Two things in this repo
# assume otherwise:
#
#   • If you moved a tool onto MCP in unit 4, `mcp_client.call_tool` starts
#     `mcp_server.py` as a separate process over stdio, one per call. Two
#     overlapping requests means two extra Python interpreters, and the free
#     tier you're deploying to has 512 MB for all of it. That is the reason
#     that would still be here even if everything else were perfect.
#   • `generate.py`'s pacing window and its call counter are plain module
#     globals — deliberately, because that file is teaching pacing and quota,
#     not locking. Two threads sharing them means the per-minute limiter is
#     counting something that isn't true.
#
# What the lock covers is exactly the agent run: the part that spawns
# processes and calls the model. Reading the request, rejecting a bad one, and
# turning the answer into JSON all happen outside it — so a request with a
# malformed body comes straight back with a 400 instead of queueing behind
# somebody else's agent.
#
# Serialising the runs costs you nothing here — this is one user asking one
# question — and it keeps the deployed behaviour identical to the CLI's. When
# that stops being an acceptable trade, the fix is a real queue, not a bigger
# lock.
#
# The same constraint decides your start command, and this is the part that
# bites in deployment rather than on your machine. `mcp_client.call_tool`
# wraps `asyncio.run()`, and `asyncio.run()` refuses to start when an event
# loop is already running. An async worker always has one running. So under
# `gunicorn -k gevent` (or `-k eventlet`, or `serve:app` wrapped for an ASGI
# server like uvicorn) EVERY MCP call fails with "asyncio.run() cannot be
# called from a running event loop" — not some of them under load, all of
# them, every time, in a place your laptop never showed you.
#
#     gunicorn serve:app              ← right: the DEFAULT sync worker
#     gunicorn -k gevent serve:app    ← breaks every MCP call you make

_one_at_a_time = threading.Lock()


@app.get("/health")
def health():
    """Is the server awake? A host pings something like this to find out."""
    return jsonify({"status": "ok"})


@app.post("/ask")
def ask():
    """
    Run the agent on one query.

    In:   {"query": "...", "wardrobe": {...}}   wardrobe optional — leave it
                                                out and you get the same
                                                example wardrobe the CLI uses.
    Out:  the session dict from run_agent(), as JSON.
    """
    global _request_count
    started = time.monotonic()
    request_id = uuid.uuid4().hex[:8]

    # The body can be any JSON value, and `query` any type. Check both before
    # using them: a number or a list has no .strip(), and a list body has no
    # .get(), so without this they crashed here, before anything was logged.
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        payload = {}
    raw_query = payload.get("query")
    query = raw_query.strip() if isinstance(raw_query, str) else ""
    if not query:
        # 400 rather than a stack trace: the caller can act on this one.
        _log({"event": "ask", "request_id": request_id, "outcome": "bad_request",
              "status": 400,
              "reason": "missing 'query'" if raw_query is None else "'query' must be a non-empty string",
              "total_ms": round((time.monotonic() - started) * 1000)})
        return jsonify({"error": "Send JSON with a 'query' field, e.g. "
                                 '{"query": "vintage graphic tee under $30"}'}), 400

    custom_wardrobe = isinstance(payload.get("wardrobe"), dict)
    wardrobe = payload["wardrobe"] if custom_wardrobe else get_example_wardrobe()

    # A queued request should look like a queued request. Without this the
    # second caller just sits there, and "slow" and "waiting its turn" are
    # indistinguishable from the outside — which is how people conclude the
    # deployment is broken when it is behaving exactly as designed.
    #
    # `locked()` can be a moment out of date, so the note is occasionally
    # missed — which costs nothing, because nothing depends on it. The log
    # line's wait_ms is the exact number.
    if _one_at_a_time.locked():
        print(
            "  [serve] another request is still running. This one is waiting "
            "its turn — serve.py handles one at a time, on purpose.",
            file=sys.stderr,
            flush=True,
        )

    failure = None
    session = None
    waited_from = time.monotonic()
    with _one_at_a_time:
        run_from = time.monotonic()
        _request_count += 1
        number = _request_count
        calls_before = generate.call_count()
        tokens_before = generate.token_counts()
        try:
            session = run_agent(query, wardrobe)
        except Exception as exc:  # noqa: BLE001 — a 500 with a sentence beats a hang
            failure = f"{type(exc).__name__}: {exc}"
        run_ended = time.monotonic()
        calls = generate.call_count() - calls_before
        tokens = generate.token_counts()

    record = {
        "event": "ask",
        "request_id": request_id,
        "request_number": number,
        "query": query,
        "wardrobe": "custom" if custom_wardrobe else "example",
        "wait_ms": round((run_from - waited_from) * 1000),
        "run_ms": round((run_ended - run_from) * 1000),
        "total_ms": round((time.monotonic() - started) * 1000),
        "model_calls": calls,
        "prompt_tokens": tokens["prompt"] - tokens_before["prompt"],
        "output_tokens": tokens["output"] - tokens_before["output"],
    }

    # Outside the lock: building a response is not work the next caller should
    # be waiting on.
    if failure is not None:
        _log({**record, "outcome": "error", "status": 500, "error": failure})
        return jsonify({"error": failure}), 500

    item = session.get("selected_item") or {}
    check = session.get("price_check") or {}
    _log({
        **record,
        "outcome": "no_match" if session.get("error") else "completed",
        "status": 200,
        "error": session.get("error"),
        "results": len(session.get("search_results") or []),
        "selected_item": item.get("id"),
        "price_verdict": check.get("verdict"),
    })
    return jsonify(session)


if __name__ == "__main__":
    # PORT and 0.0.0.0 are not decoration. A host tells you which port to
    # listen on through PORT, and it reaches your process from outside the
    # container — bind 127.0.0.1 and nothing but the container itself can
    # connect, which looks exactly like a broken app from the browser.
    port = int(os.getenv("PORT", "5000"))

    # Never on by default. Flask's debugger executes code typed into a browser,
    # and a deployed app with it on is a stranger's shell. Set AI201_DEBUG=1 in
    # your own terminal when you want the reloader.
    debug = os.getenv("AI201_DEBUG", "0") == "1"

    print(f"\nFitFindr is listening on http://localhost:{port}")
    print("It runs one request at a time — a second one waits for the first.")
    print("Ask it something (single quotes, as always):\n")
    print(
        f"  curl -X POST http://localhost:{port}/ask \\\n"
        f"    -H 'Content-Type: application/json' \\\n"
        f"    -d '{{\"query\": \"vintage graphic tee under $30\"}}'\n"
    )
    print(f"Logging every request to {LOG_FILE.relative_to(config.ROOT)} (and stderr).")
    print("Ctrl-C to stop.\n")
    _log({"event": "start", "port": port, "debug": debug,
          "python": sys.version.split()[0], "model": config.MODEL})

    app.run(host="0.0.0.0", port=port, debug=debug)
