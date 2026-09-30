#!/usr/bin/env python3
"""Serve the rough-cut selection workbench and its media API."""

import argparse
import json
import re
import subprocess
import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse


SCRIPT_DIR = Path(__file__).parent
WORK = Path()
MEDIA = Path()


def normalise_id(identifier):
    clip, _, start = identifier.rpartition("|")
    return f"{clip}|{float(start):.4f}"


def json_response(handler, status, payload):
    body = payload if isinstance(payload, bytes) else json.dumps(payload).encode()
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Content-Length", str(len(body)))
    handler.send_header("Connection", "close")
    handler.end_headers()
    handler.wfile.write(body)


def read_request_json(handler):
    length = int(handler.headers.get("Content-Length", "0"))
    return json.loads(handler.rfile.read(length) or b"{}")


def serve_media(handler, requested_name):
    name = unquote(requested_name)
    if Path(name).name != name:
        json_response(handler, 404, {})
        return
    path = MEDIA / name
    if not path.is_file():
        json_response(handler, 404, {})
        return
    size = path.stat().st_size
    start, end, status = 0, size - 1, 200
    range_header = handler.headers.get("Range", "")
    match = re.fullmatch(r"bytes=(\d*)-(\d*)", range_header)
    if match and (match.group(1) or match.group(2)):
        status = 206
        if match.group(1):
            start = int(match.group(1))
            if match.group(2):
                end = min(int(match.group(2)), size - 1)
        else:
            start = max(0, size - int(match.group(2)))
        if start >= size or start > end:
            json_response(handler, 416, {"error": "Requested range is not satisfiable."})
            return
    handler.send_response(status)
    handler.send_header("Content-Type", "video/mp4")
    handler.send_header("Accept-Ranges", "bytes")
    handler.send_header("Content-Length", str(end - start + 1))
    handler.send_header("Connection", "close")
    if status == 206:
        handler.send_header("Content-Range", f"bytes {start}-{end}/{size}")
    handler.end_headers()
    with path.open("rb") as stream:
        stream.seek(start)
        remaining = end - start + 1
        while remaining:
            chunk = stream.read(min(1024 * 1024, remaining))
            if not chunk:
                break
            handler.wfile.write(chunk)
            remaining -= len(chunk)


def render_timeline():
    command = [sys.executable, str(SCRIPT_DIR / "export_timeline.py"), "--work", str(WORK), "--media", str(MEDIA)]
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode:
        return {"error": result.stderr.strip() or result.stdout.strip(), "exit_code": result.returncode}
    summary = re.search(r"events: (\d+); duration: ([\d.]+) minutes", result.stdout)
    files = [str(WORK / filename) for filename in ("rough-cut.xml", "rough-cut.fcpxml", "rough-cut.edl") if (WORK / filename).exists()]
    return {"events": int(summary.group(1)) if summary else 0, "minutes": float(summary.group(2)) if summary else 0, "files": files}


class WorkbenchHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def do_GET(self):
        path = urlparse(self.path).path
        if path in ("/", "/index.html"):
            body = (SCRIPT_DIR / "workbench.html").read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Connection", "close")
            self.end_headers()
            self.wfile.write(body)
        elif path == "/api/candidates":
            candidates = WORK / "candidates.json"
            if candidates.exists():
                json_response(self, 200, candidates.read_bytes())
            else:
                json_response(self, 404, {"error": "Create candidates.json in the work directory first."})
        elif path == "/api/selections":
            selections = WORK / "selections.json"
            if selections.exists():
                stored = json.loads(selections.read_text())
                stored["marks"] = {normalise_id(k): v for k, v in stored.get("marks", {}).items()}
                json_response(self, 200, stored)
            else:
                json_response(self, 200, {"marks": {}})
        elif path.startswith("/media/"):
            serve_media(self, path[len("/media/"):])
        else:
            json_response(self, 404, {})

    def do_POST(self):
        path = urlparse(self.path).path
        if path == "/api/selections":
            payload = read_request_json(self)
            marks = {normalise_id(key): value for key, value in payload.get("marks", {}).items()}
            (WORK / "selections.json").write_text(json.dumps({"marks": marks}, indent=2) + "\n")
            json_response(self, 200, {"saved": time.strftime("%H:%M:%S")})
        elif path == "/api/render":
            result = render_timeline()
            json_response(self, 200 if "error" not in result else 500, result)
        else:
            json_response(self, 404, {})

    def log_message(self, format_string, *args):
        return


def main():
    global WORK, MEDIA
    parser = argparse.ArgumentParser(description="Run the rough-cut selection workbench.")
    parser.add_argument("--work", required=True, help="Directory containing candidates.json and selections.json.")
    parser.add_argument("--media", required=True, help="Directory containing candidate MP4 files.")
    parser.add_argument("--port", type=int, default=8765, help="Local HTTP port (default: 8765).")
    args = parser.parse_args()
    WORK, MEDIA = Path(args.work), Path(args.media)
    server = ThreadingHTTPServer(("127.0.0.1", args.port), WorkbenchHandler)
    print(f"Rough cut workbench: http://127.0.0.1:{args.port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
