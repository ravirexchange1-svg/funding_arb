#!/usr/bin/env python3
"""Run the dashboard locally with Extended enabled.

    python3 serve.py            # then open http://localhost:8000

Serves index.html and relays Extended's public markets feed at /extended, so the
browser sees one origin and no CORS proxy is needed.
"""
import http.server
import urllib.request

UPSTREAM = "https://api.starknet.extended.exchange/api/v1/info/markets"
PORT = 8000


class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path.split("?")[0] == "/extended":
            try:
                req = urllib.request.Request(UPSTREAM, headers={"user-agent": "funding-dashboard"})
                body = urllib.request.urlopen(req, timeout=20).read()
                self.send_response(200)
            except Exception as e:
                body = str(e).encode()
                self.send_response(502)
            self.send_header("content-type", "application/json")
            self.send_header("content-length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            super().do_GET()


if __name__ == "__main__":
    print(f"Dashboard: http://localhost:{PORT}")
    http.server.ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
