#!/usr/bin/env python3
"""Run the dashboard locally with Extended enabled.

    python3 serve.py            # then open http://localhost:8000

Serves index.html and relays two public feeds that block browsers (Extended markets at
/extended, Aster funding history at /aster-funding), so the browser sees one origin.
"""
import http.server
import urllib.parse
import urllib.request

UPSTREAM = "https://api.starknet.extended.exchange/api/v1/info/markets"
ASTER_FUNDING = "https://fapi.asterdex.com/fapi/v1/fundingRate"
PORT = 8000


class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        route, _, query = self.path.partition("?")
        if route in ("/extended", "/aster-funding"):
            try:
                url = UPSTREAM
                if route == "/aster-funding":
                    keep = {k: v for k, v in urllib.parse.parse_qsl(query) if k in ("symbol", "startTime", "endTime", "limit")}
                    url = ASTER_FUNDING + "?" + urllib.parse.urlencode(keep)
                req = urllib.request.Request(url, headers={"user-agent": "funding-dashboard"})
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
