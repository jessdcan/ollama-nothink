#!/usr/bin/env python3
# ponytail: stdlib-only proxy. Forces thinking off for Ollama's Anthropic endpoint
# because ollama_launch_claude can't pass thinking:{type:disabled} itself.
# Point Claude Code at this: ANTHROPIC_BASE_URL=http://localhost:11435
import http.server, urllib.request, json

UPSTREAM = "http://localhost:11434"
PORT = 11435

class H(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        body = self.rfile.read(int(self.headers.get("content-length", 0)))
        if self.path.endswith("/v1/messages"):
            try:
                d = json.loads(body)
                d["thinking"] = {"type": "disabled"}
                body = json.dumps(d).encode()
            except Exception:
                pass  # not JSON we understand — pass through untouched
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

    def log_message(self, *a): pass

http.server.ThreadingHTTPServer(("127.0.0.1", PORT), H).serve_forever()
