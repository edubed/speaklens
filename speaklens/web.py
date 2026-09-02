"""The guided recorder: a local page that walks you through the five prompts.

    python -m speaklens.web

Why this exists is not that the terminal is ugly. The first real five-prompt
session came back at 90 seconds with three prompts unanswered, because nothing was
guiding the speaker — and the level estimate then abstained two content words short
of its threshold. A page that shows one prompt at a time, times it, and refuses to
finish early fixes the measurement, not the looks.

Two constraints shaped it, and both are the project's argument rather than taste:

  * **The server is the standard library.** A page that captures a microphone needs
    an origin to be served from, so DEC-025's "no server" cannot hold here — but a
    framework would still be ceremony. This is one handler with four routes.

  * **It binds to 127.0.0.1, never 0.0.0.0.** The audio is someone's voice; it
    should not be reachable from the network the laptop happens to be on. That the
    page is served from localhost is also what makes the microphone work at all:
    browsers only hand out getUserMedia in a secure context, and localhost counts
    as one while a plain http:// address on the LAN does not.

Nothing is fetched from a CDN, so this runs with the wifi off like everything else.
"""

from __future__ import annotations

import json
import shutil
import tempfile
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import yaml

from . import report as reporter
from . import session as pipeline

PAGE = Path(__file__).resolve().parent / "recorder.html"
PROMPTS = Path(__file__).resolve().parent.parent / "data" / "prompts.yaml"

HOST = "127.0.0.1"
PORT = 8000

# Audio arrives in whatever the browser records: Chrome gives webm/opus, Safari
# mp4/aac. ffmpeg reads both, so the extension only has to be honest enough for it
# to sniff the container.
EXTENSIONS = {"audio/webm": ".webm", "audio/ogg": ".ogg", "audio/mp4": ".mp4",
              "audio/mpeg": ".mp3", "audio/wav": ".wav"}

_lock = threading.Lock()
_status = {"state": "idle", "detail": ""}


def prompts() -> dict:
    spec = yaml.safe_load(PROMPTS.read_text(encoding="utf-8"))
    return {
        "warm_up": " ".join(spec["warm_up"]["text"].split()),
        "seconds": spec["target_seconds_per_prompt"],
        "prompts": [
            {"order": p["order"],
             "text": " ".join(p["text"].split()),
             "hint_es": " ".join(p["hint_es"].split())}
            for p in sorted(spec["prompts"], key=lambda p: p["order"])
        ],
    }


class Handler(BaseHTTPRequestHandler):
    server_version = "speaklens"

    def log_message(self, *args) -> None:  # noqa: D401 - quiet by default
        """Keep the console for the pipeline's own progress."""

    # -- responses ---------------------------------------------------------

    def _send(self, body: bytes, content_type: str, status: int = 200) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _json(self, payload: dict, status: int = 200) -> None:
        self._send(json.dumps(payload).encode("utf-8"), "application/json", status)

    # -- routes ------------------------------------------------------------

    def do_GET(self) -> None:
        route = urlparse(self.path).path

        if route == "/":
            page = PAGE.read_text(encoding="utf-8")
            page = page.replace("__PROMPTS__", json.dumps(prompts(), ensure_ascii=False))
            self._send(page.encode("utf-8"), "text/html; charset=utf-8")
        elif route == "/status":
            self._json(_status)
        elif route.startswith("/report"):
            # /report is the latest run; /reports/<file> is the copy that survives
            # the next person's turn.
            path = reporter.DEFAULT_PATH
            if route.startswith("/reports/"):
                path = reporter.ARCHIVE / Path(route).name
            if not path.exists():
                self._send(b"todavia no hay informe", "text/plain; charset=utf-8", 404)
                return
            self._send(path.read_bytes(), "text/html; charset=utf-8")
        else:
            self._send(b"not found", "text/plain", 404)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)

        if parsed.path == "/clip":
            order = parse_qs(parsed.query).get("order", ["0"])[0]
            content_type = self.headers.get("Content-Type", "audio/webm").split(";")[0]
            body = self.rfile.read(int(self.headers.get("Content-Length", 0)))
            if not body:
                self._json({"error": "clip vacío"}, 400)
                return
            # The first clip of a run clears the directory. Without this, a person
            # who answers three prompts inherits the fourth and fifth of whoever
            # went before them — and the report never says so.
            if int(order) == 1:
                for stale in self.server.clips.glob("*"):
                    stale.unlink()
            clip = self.server.clips / f"{int(order):02d}{EXTENSIONS.get(content_type, '.webm')}"
            clip.write_bytes(body)
            self._json({"ok": True, "bytes": len(body)})

        elif parsed.path.rstrip("/") == "/analyze":
            # One diagnostic at a time. The machine has 8 GB and Whisper wants most
            # of them; a second run started from a stray double-click would swap.
            if not _lock.acquire(blocking=False):
                self._json({"error": "ya hay un análisis corriendo"}, 409)
                return
            try:
                query = parse_qs(parsed.query)
                speaker = query.get("speaker", [""])[0].strip()[:40]
                declared = query.get("declared", [""])[0].strip()
                self._json(self._analyze(speaker, declared))
            finally:
                _lock.release()

        else:
            self._json({"error": "not found"}, 404)

    def _analyze(self, speaker: str = "", declared: str = "") -> dict:
        clips = sorted(self.server.clips.glob("*"))
        if not clips:
            return {"error": "no hay respuestas grabadas"}

        def progress(step: str, data=None) -> None:
            labels = {
                "transcribe": "Transcribiendo lo que dijiste…",
                "transcribed": "Midiendo la fluidez…",
                "detect": "Buscando errores…",
            }
            if step in labels:
                _status.update(state="working", detail=labels[step])
                print(f"  {labels[step]}", flush=True)

        _status.update(state="working", detail="Uniendo las respuestas…")
        joined = pipeline.join(clips, self.server.clips / "answers.wav")

        try:
            analysis = pipeline.analyze(joined, speaker=speaker, declared=declared,
                                        on_step=progress)
        except Exception as error:                       # noqa: BLE001 - shown to the user
            _status.update(state="error", detail=str(error))
            return {"error": str(error)}

        archived = reporter.archive_path(analysis.session_id, analysis.speaker)
        reporter.write(
            archive_as=archived,
            session_id=analysis.session_id,
            speaker=analysis.speaker,
            declared=analysis.declared,
            source=analysis.source,
            transcript=analysis.transcript,
            fluency=analysis.fluency,
            level=analysis.level,
            mistakes=analysis.mistakes,
            trend=analysis.trend,
        )
        _status.update(state="done", detail="")
        print(f"  informe: {archived}", flush=True)
        return {"ok": True, "report": f"/reports/{archived.name}"}


def serve(port: int = PORT, open_browser: bool = True) -> None:
    clips = Path(tempfile.mkdtemp(prefix="speaklens-clips-"))
    reporter.ARCHIVE.mkdir(parents=True, exist_ok=True)
    server = ThreadingHTTPServer((HOST, port), Handler)
    server.clips = clips

    url = f"http://{HOST}:{port}/"
    print(f"SpeakLens en {url}")
    print("Ctrl-C para salir.\n")
    if open_browser:
        webbrowser.open(url)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nlisto.")
    finally:
        server.server_close()
        # The clips are someone's voice and the diagnostic is already saved, so
        # there is no reason to leave them on disk (DEC-004).
        shutil.rmtree(clips, ignore_errors=True)


if __name__ == "__main__":
    serve()
