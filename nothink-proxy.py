#!/usr/bin/env python3
# ponytail: stdlib-only proxy. Forces thinking off for Ollama's Anthropic endpoint
# because ollama_launch_claude can't pass thinking:{type:disabled} itself.
# Point Claude Code at this: ANTHROPIC_BASE_URL=http://localhost:11435
import http.server, urllib.request, json, sys

UPSTREAM = "http://localhost:11434"
PORT = 11435

def log(*a): print(*a, file=sys.stderr, flush=True)

class H(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        body = self.rfile.read(int(self.headers.get("content-length", 0)))
        patched = False
        if self.path.split("?")[0].endswith("/v1/messages"):
            try:
                d = json.loads(body)
                d["thinking"] = {"type": "disabled"}
                body = json.dumps(d).encode()
                patched = True
            except Exception:
                pass  # not JSON we understand — pass through untouched
        log(f"{self.command} {self.path}  thinking-disabled={patched}")
        req = urllib.request.Request(UPSTREAM + self.path, data=body, method="POST",
            headers={k: v for k, v in self.headers.items() if k.lower() != "content-length"})
        try:
            up = urllib.request.urlopen(req)
        except urllib.error.HTTPError as e:
            up = e
        self.send_response(up.status)
        for k, v in up.headers.items():
            if k.lower() not in ("transfer-encoding", "content-length", "connection"):
                self.send_header(k, v)
        self.end_headers()
        while chunk := up.read(1024):   # stream SSE straight through
            self.wfile.write(chunk); self.wfile.flush()

    def do_GET(self):  # passthrough for /v1/models discovery, etc — no patching needed
        log(f"{self.command} {self.path}")
        req = urllib.request.Request(UPSTREAM + self.path, method="GET",
            headers={k: v for k, v in self.headers.items() if k.lower() != "content-length"})
        try:
            up = urllib.request.urlopen(req)
        except urllib.error.HTTPError as e:
            up = e
        self.send_response(up.status)
        for k, v in up.headers.items():
            if k.lower() not in ("transfer-encoding", "content-length", "connection"):
                self.send_header(k, v)
        self.end_headers()
        while chunk := up.read(1024):
            self.wfile.write(chunk); self.wfile.flush()

    def log_message(self, *a): pass

http.server.ThreadingHTTPServer(("127.0.0.1", PORT), H).serve_forever()
