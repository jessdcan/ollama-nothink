# ollama-nothink

Local Ollama model configurations and tooling for running **Gemma 4 (12B)** across
several workflows on a single machine — agentic coding, a Hermes tool-use agent, and
a low-latency voice pipeline — plus a small proxy that forces thinking off for clients
that can't request it themselves.

![Ollama](https://img.shields.io/badge/Ollama-0.30%2B-000000)
![Runtime](https://img.shields.io/badge/runtime-local-4285F4)
![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB)
![Deps](https://img.shields.io/badge/dependencies-none-success)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

## Contents

| File | Purpose | Context |
|------|---------|---------|
| `gemma4-12b-256k.Modelfile` | Max-context general / coding profile | 262144 (256K) |
| `gemma4-12b-hermes.Modelfile` | Hermes agent (tool use), headroom-balanced | 131072 (128K) |
| `gemma4-12b-voice.Modelfile` | Voice pipeline, latency-optimised | 8192 (8K) |
| `nothink-proxy.py` | Strips Gemma 4 thinking for Anthropic-API clients | — |

Each Modelfile only sets `num_ctx`; the context size is the entire point of each
profile. Larger context costs KV-cache memory and slows time-to-first-token, so the
value is matched to the workload — big for long agent sessions, small for voice.

## Build

```bash
ollama pull gemma4:12b
ollama create gemma4-12b-256k   -f gemma4-12b-256k.Modelfile
ollama create gemma4-12b-hermes -f gemma4-12b-hermes.Modelfile
ollama create gemma4-12b-voice  -f gemma4-12b-voice.Modelfile
```

## The thinking problem (`nothink-proxy.py`)

Gemma 4 has **thinking on by default** and exposes no Modelfile or template lever to
disable it — the behaviour is compiled into Ollama's `gemma4` parser. Thinking tokens
are pure latency overhead for coding/agent use.

Per-request you can disable it, but the field differs by endpoint:

| Endpoint | Disable thinking via |
|----------|----------------------|
| `/api/chat` (native) | `"think": false` |
| `/v1/messages` (Anthropic-compatible) | `"thinking": {"type": "disabled"}` |

Tools like Claude Code, opencode, and cline talk to the Anthropic endpoint but never
send the disable field, so they inherit the model default (thinking **on**). The proxy
sits in front of Ollama and injects `"thinking": {"type": "disabled"}` into every
`/v1/messages` request, streaming responses straight through. Standard library only.

```bash
python3 nothink-proxy.py            # listens on :11435, forwards to :11434

# point any Anthropic-API client at the proxy instead of Ollama:
ANTHROPIC_BASE_URL=http://localhost:11435 ollama launch claude --model gemma4-12b-256k
```

Keep it alive across reboots with `nohup python3 nothink-proxy.py &` or a LaunchAgent.

## Notes

- All endpoints are localhost; the proxy adds no auth (Ollama ignores it locally).
- Memory figures in the Hermes/voice Modelfiles assume 24GB unified memory.
