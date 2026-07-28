from __future__ import annotations

import argparse
import json
import subprocess
import sys
import threading
import webbrowser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from bevelkit import CONFIG_PATH, default_config, load_config, save_config

HERE = Path(__file__).resolve().parent
STUDIO_DIR = HERE / "studio"
RENDER_SCRIPT = HERE / "render_tiles.py"


class StudioHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(STUDIO_DIR), **kwargs)

    def log_message(self, *args):
        pass

    def _send(self, payload, content_type="application/json"):
        body = payload if isinstance(payload, bytes) else payload.encode()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path.startswith("/config.json"):
            self._send(json.dumps(load_config(), indent=2))
        elif self.path.startswith("/defaults.json"):
            self._send(json.dumps(default_config(), indent=2))
        else:
            super().do_GET()

    def do_POST(self):
        if self.path.startswith("/config.json"):
            length = int(self.headers.get("Content-Length", 0))
            incoming = json.loads(self.rfile.read(length) or b"{}")
            save_config(incoming)
            self._send(json.dumps({"saved": str(CONFIG_PATH)}))
        elif self.path.startswith("/render"):
            finished = subprocess.run(
                [sys.executable, str(RENDER_SCRIPT), "--quiet"],
                capture_output=True,
                text=True,
            )
            if finished.returncode == 0:
                self._send(finished.stdout.strip() or "baked tiles", "text/plain")
            else:
                self._send(
                    f"render failed: {finished.stderr.strip()[-400:]}", "text/plain"
                )
        else:
            self.send_error(404)


def main():
    parser = argparse.ArgumentParser(description="Serve the WebGL bevel studio")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--no-browser", action="store_true")
    arguments = parser.parse_args()

    server = ThreadingHTTPServer(("127.0.0.1", arguments.port), StudioHandler)
    url = f"http://127.0.0.1:{arguments.port}/"
    print(f"bevel studio on {url}   (config: {CONFIG_PATH})")
    if not arguments.no_browser:
        threading.Timer(0.4, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped")


if __name__ == "__main__":
    main()
