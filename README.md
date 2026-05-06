# gRPC AI Inference Microservice

A fully-containerised AI inference service demonstrating all four gRPC communication patterns, load-balanced through Nginx, backed by a local Ollama LLM.

```
┌────────────────────────────────────────────────────────────┐
│  CLI Client  (localhost)                                    │
│       │                                                     │
│       ▼  HTTP/2 on port 80                                  │
│  ┌─────────────┐                                            │
│  │    Nginx    │  Layer-7 load balancer (grpc_pass)         │
│  └──────┬──────┘                                            │
│         │  Round-robin across 3 instances                   │
│  ┌──────┴───────────────────────────┐                       │
│  │  server-1  server-2  server-3    │  (port 50051 each)    │
│  └──────────────────────────────────┘                       │
│         │  HTTP to host machine                             │
│  ┌──────┴──────┐                                            │
│  │  Ollama LLM │  tinyllama (runs on your host)             │
│  └─────────────┘                                            │
└────────────────────────────────────────────────────────────┘
```

---

## Prerequisites

| Tool | Version | Install |
|------|---------|---------|
| Python | ≥ 3.10 | https://python.org |
| Docker + Docker Compose | v2 | https://docs.docker.com/get-docker/ |
| Ollama | latest | https://ollama.com |
| grpcio-tools | 1.64.x | `pip install grpcio-tools` |

---

## Quick Start (3 commands)

```bash
# 1. Pull the tiny model and start Ollama (one-time)
ollama pull tinyllama
ollama serve          # keep this running in a separate terminal

# 2. Build + launch the stack
make build && make up

# 3. Run the CLI tester
make test
```

---

## Step-by-Step Guide

### Step 1 – Install Ollama and pull the model

```bash
# macOS / Linux
curl -fsSL https://ollama.com/install.sh | sh

# Pull tinyllama (~600 MB – fits in low RAM)
ollama pull tinyllama

# Start the Ollama server (leave this terminal open)
ollama serve
```

Verify it works:
```bash
curl http://localhost:11434/api/generate \
  -d '{"model":"tinyllama","prompt":"say hi","stream":false}'
```

---

### Step 2 – Clone / set up the project

```bash
git clone <your-repo>
cd grpc-ai-project

# Install Python tools (only needed on the HOST for proto compilation)
pip install grpcio-tools==1.64.1
```

---

### Step 3 – Compile the .proto file

```bash
make proto
```

This runs:
```bash
python -m grpc_tools.protoc \
    -I protos \
    --python_out=protos \
    --grpc_python_out=protos \
    protos/ai_inference.proto
```

You will see two new files appear:
- `protos/ai_inference_pb2.py`      — message classes
- `protos/ai_inference_pb2_grpc.py` — service stubs

---

### Step 4 – Build Docker images

```bash
make build
```

This also copies the generated stubs into `server/` so Docker can package them.

Behind the scenes:
```bash
docker compose build
```

---

### Step 5 – Start the full stack

```bash
make up
```

Docker Compose brings up:
- `grpc-server-1`, `grpc-server-2`, `grpc-server-3` — three Python gRPC servers
- `grpc-nginx` — Nginx load balancer listening on `localhost:80`

Check all containers are healthy:
```bash
docker compose ps
```

Expected output:
```
NAME            STATUS    PORTS
grpc-nginx      Up        0.0.0.0:80->80/tcp
grpc-server-1   Up        50051/tcp
grpc-server-2   Up        50051/tcp
grpc-server-3   Up        50051/tcp
```

---

### Step 6 – Run the CLI Tester

```bash
make test
```

Or manually:
```bash
pip install -r client/requirements.txt
PYTHONPATH=protos python client/client.py
```

You should see output like:

```
────────────────────────────────────────────────────────────
  Task 2 – Unary: Sentiment Analysis
────────────────────────────────────────────────────────────
  Input : I absolutely love this product! It changed my life.
  Result: POSITIVE  confidence=0.95  [███████████████████ ]

  Input : This is the worst purchase I have ever made.
  Result: NEGATIVE  confidence=0.90  [██████████████████  ]
...

────────────────────────────────────────────────────────────
  Task 3 – Server-Streaming: Real-time Generation
────────────────────────────────────────────────────────────
  Streaming tokens: gRPC is better than REST because...
...

All tests completed successfully! ✓
```

---

## Watch load-balancing in action

Open a second terminal and watch the Nginx access log:

```bash
make logs-nginx
```

Each request will show a different `upstream` IP (the three backend containers), proving round-robin is working.

---

## Useful Commands

```bash
make help         # list all targets
make up           # start the stack
make down         # stop the stack
make logs         # stream logs from all containers
make logs-nginx   # stream Nginx access log only
make test         # run CLI client
make clean        # delete generated proto stubs
```

---

## Project Structure

```
grpc-ai-project/
├── protos/
│   └── ai_inference.proto          # API contract (Tasks 1–5)
├── server/
│   ├── server.py                   # gRPC server (Tasks 2–5)
│   ├── Dockerfile                  # containerises the server
│   └── requirements.txt
├── client/
│   ├── client.py                   # CLI tester (Task 7)
│   └── requirements.txt
├── nginx/
│   └── nginx.conf                  # HTTP/2 + grpc_pass config (Task 6)
├── docker-compose.yml              # 3 servers + Nginx (Task 6)
├── Makefile                        # convenience commands
└── README.md
```

---

## How Each gRPC Pattern Works

### Unary (Task 2 – Sentiment)
```
Client ──[SentimentRequest]──► Server
Client ◄──[SentimentResponse]── Server
```
One request, one response. Simplest pattern. Ollama classifies sentiment then returns a label + confidence score.

### Server-Streaming (Task 3 – Text Generation)
```
Client ──[GenerateRequest]──► Server
Client ◄──[GenerateChunk]──── Server  (× many)
Client ◄──[GenerateChunk]──── Server
Client ◄──[GenerateChunk]──── Server  ...until done
```
Client sends one prompt; server streams tokens back as Ollama generates them — the "typing" effect.

### Client-Streaming (Task 4 – Summarisation)
```
Client ──[TextChunk]──► Server  (× many)
Client ──[TextChunk]──► Server
Client closes stream
Client ◄──[SummaryResponse]── Server
```
Client streams document chunks; server buffers them all, then calls Ollama once to summarise.

### Bidirectional-Streaming (Task 5 – Live Chat)
```
Client ──[ChatMessage]──► Server
Client ◄──[ChatMessage]── Server (token 1)
Client ◄──[ChatMessage]── Server (token 2)
Client ──[ChatMessage]──► Server (next user turn)
...both sides can send at any time...
```
Full-duplex persistent connection. Server maintains conversation history across turns.

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `Connection refused` on port 80 | Run `make up` first |
| Servers can't reach Ollama | Make sure `ollama serve` is running on your host |
| `host.docker.internal` not found | On Linux, Docker Compose sets `extra_hosts` automatically; if it fails, replace with your host IP (e.g. `172.17.0.1`) |
| `tinyllama` not found | Run `ollama pull tinyllama` |
| Slow responses | tinyllama is CPU-only by default; responses may take 5–30 seconds |
| Port 80 already in use | Change `"80:80"` to `"8080:80"` in docker-compose.yml and set `LOAD_BALANCER = "localhost:8080"` in client.py |
