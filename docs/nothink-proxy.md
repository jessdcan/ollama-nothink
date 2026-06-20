# nothink-proxy: what made it work

The proxy forces Gemma 4's thinking off for Anthropic-API clients (Claude Code,
opencode, cline, ...) that never send the disable field themselves. Getting it
actually wired up took two non-obvious fixes. Both are recorded here so they
don't have to be rediscovered.

## 1. `ollama launch` overrides `ANTHROPIC_BASE_URL`

Prepending the env var to the launcher does **not** work:

```bash
ANTHROPIC_BASE_URL=http://localhost:11435 ollama launch claude --model ...   # bypassed
```

`ollama launch` sets its own `ANTHROPIC_BASE_URL=http://localhost:11434` on the
spawned process *after* your env var, so traffic goes straight to Ollama and
skips the proxy entirely. The proxy log stays empty — that's the tell.

**Fix:** skip `ollama launch` and run the client directly with the env it would
have set, pointed at the proxy:

```bash
ANTHROPIC_BASE_URL=http://localhost:11435 \
ANTHROPIC_AUTH_TOKEN=ollama \
ANTHROPIC_MODEL=gemma4-12b-256k \
ANTHROPIC_SMALL_FAST_MODEL=gemma4-12b-256k \
claude
```

(`ANTHROPIC_AUTH_TOKEN` can be any value — Ollama ignores it locally.)

## 2. Claude Code appends `?beta=true` to the path

Once traffic reached the proxy it *still* thought, because the request path is
`/v1/messages?beta=true`, not `/v1/messages`. The original match was:

```python
if self.path.endswith("/v1/messages"):        # misses the query string
```

so the `thinking:{type:disabled}` injection was skipped. The log showed the
request arriving with `thinking-disabled=False`.

**Fix:** strip the query string before matching:

```python
if self.path.split("?")[0].endswith("/v1/messages"):
```

## How to confirm it's working

Run the proxy with logging and watch the log:

```bash
python3 nothink-proxy.py 2>&1 | tee /tmp/nothink-proxy.log
```

A correctly routed, patched request logs:

```
POST /v1/messages?beta=true  thinking-disabled=True
```

End to end the difference is stark: the first `hi` (before the fix) took
~2m45s; after, replies return in ~1s with no "Thought for ..." preamble.
