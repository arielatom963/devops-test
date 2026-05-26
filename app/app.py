import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer


class HeaderHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        xff = self.headers.get("X-Forwarded-For")
        body = {
            "path": self.path,
            "x_forwarded_for": xff,
            "remote_addr": self.client_address[0],
        }
        payload = json.dumps(body, ensure_ascii=False, indent=2).encode()

        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, format, *args):
        print("%s - %s" % (self.client_address[0], format % args), flush=True)


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    HTTPServer(("0.0.0.0", port), HeaderHandler).serve_forever()
