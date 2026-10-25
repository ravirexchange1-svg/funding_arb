#!/usr/bin/env python3
"""Run the dashboard locally with Extended enabled.

    python3 serve.py            # then open http://localhost:8000

Serves index.html and relays two public feeds that block browsers (Extended markets at
/extended and /extended-funding, Aster funding history at /aster-funding), so the browser sees one origin.
It also records live funding for venues that publish no history (Variational, QFEX) into data/funding_log.jsonl
while the dashboard is open, so a backtest for them becomes possible once enough days have been collected.
"""
import http.server
import json
import os
import urllib.parse
import urllib.request

UPSTREAM = "https://api.starknet.extended.exchange/api/v1/info/markets"
ASTER_FUNDING = "https://fapi.asterdex.com/fapi/v1/fundingRate"
EXTENDED_FUNDING = "https://api.starknet.extended.exchange/api/v1/info/{market}/funding"
LOG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "funding_log.jsonl")
PORT = 8000


class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        route, _, query = self.path.partition("?")
        if route == "/recorded":
            q = dict(urllib.parse.parse_qsl(query))
            since = int(q.get("since", 0))
            out = []
            if os.path.exists(LOG):
                with open(LOG) as f:
                    for line in f:
                        try:
                            v, i, t, h = json.loads(line)
                        except ValueError:
                            continue
                        if v == q.get("venue") and i == q.get("id") and t >= since:
                            out.append([t, h])
            body = json.dumps(out).encode()
            self.send_response(200)
            self.send_header("content-type", "application/json")
            self.send_header("content-length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if route in ("/extended", "/aster-funding", "/extended-funding"):
            try:
                url = UPSTREAM
                if route == "/extended-funding":
                    keep = {k: v for k, v in urllib.parse.parse_qsl(query) if k in ("startTime", "endTime", "limit")}
                    market = urllib.parse.quote(dict(urllib.parse.parse_qsl(query)).get("market", ""), safe="")
                    url = EXTENDED_FUNDING.format(market=market) + "?" + urllib.parse.urlencode(keep)
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

    def do_POST(self):
        """Append funding snapshots ([venue, id, time_ms, hourly_rate] lists) to data/funding_log.jsonl."""
        if self.path != "/record":
            self.send_response(404)
            self.end_headers()
            return
        try:
            rows = json.loads(self.rfile.read(int(self.headers.get("content-length", 0))))
            os.makedirs(os.path.dirname(LOG), exist_ok=True)
            with open(LOG, "a") as f:
                for r in rows:
                    if isinstance(r, list) and len(r) == 4:
                        f.write(json.dumps(r) + "\n")
            self.send_response(204)
        except Exception:
            self.send_response(400)
        self.end_headers()


if __name__ == "__main__":
    print(f"Dashboard: http://localhost:{PORT}")
    http.server.ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
