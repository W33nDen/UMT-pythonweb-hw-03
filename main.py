import json
import mimetypes
import os
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from jinja2 import Environment, FileSystemLoader

BASE_DIR = Path(__file__).parent
STORAGE_DIR = BASE_DIR / "storage"
STORAGE_DIR.mkdir(exist_ok=True)
DATA_FILE = STORAGE_DIR / "data.json"

jinja_env = Environment(loader=FileSystemLoader(str(BASE_DIR / "templates")))


def read_data():
    if DATA_FILE.exists():
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}


def write_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/" or path == "/index.html":
            self.send_html(BASE_DIR / "index.html")
        elif path == "/message.html":
            self.send_html(BASE_DIR / "message.html")
        elif path == "/read":
            data = read_data()
            template = jinja_env.get_template("read.html")
            content = template.render(messages=data)
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(content.encode("utf-8"))
        elif path == "/style.css":
            self.send_static(BASE_DIR / "style.css")
        elif path == "/logo.png":
            self.send_static(BASE_DIR / "logo.png")
        else:
            self.send_html(BASE_DIR / "error.html", 404)

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path == "/message":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length)
            params = parse_qs(body.decode("utf-8"))
            username = params.get("username", [""])[0]
            message = params.get("message", [""])[0]
            timestamp = str(datetime.now())
            data = read_data()
            data[timestamp] = {"username": username, "message": message}
            write_data(data)
            self.send_response(302)
            self.send_header("Location", "/")
            self.end_headers()
        else:
            self.send_html(BASE_DIR / "error.html", 404)

    def send_html(self, filepath, status=200):
        self.send_response(status)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()
        with open(filepath, "rb") as f:
            self.wfile.write(f.read())

    def send_static(self, filepath):
        mime_type, _ = mimetypes.guess_type(str(filepath))
        self.send_response(200)
        self.send_header("Content-type", mime_type or "application/octet-stream")
        self.end_headers()
        with open(filepath, "rb") as f:
            self.wfile.write(f.read())

    def log_message(self, format, *args):
        pass


if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", 3000), Handler)
    print("Server running on http://localhost:3000")
    server.serve_forever()
