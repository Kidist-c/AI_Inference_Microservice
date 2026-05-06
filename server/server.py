"""
gRPC AI Inference Server
Connects to a local Ollama instance (default model: tinyllama).
"""

import asyncio
import json
import logging
import os
import re
import time
import sys
import grpc
import httpx
from grpc import aio
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, BASE_DIR)
import protos.ai_inference_pb2 as pb2
import protos.ai_inference_pb2_grpc as pb2_grpc

logging.basicConfig(level=logging.INFO, format="%(asctime)s [SERVER] %(message)s")
log = logging.getLogger(__name__)

OLLAMA_URL  = os.getenv("OLLAMA_URL", "http://host.docker.internal:11434")
MODEL       = os.getenv("OLLAMA_MODEL", "tinyllama")
SERVER_PORT = os.getenv("GRPC_PORT", "50051")
SERVER_ID   = os.getenv("SERVER_ID", "server-1")


# ─── Helpers ────────────────────────────────────────────────────────────────

async def ollama_generate(prompt: str, stream: bool = False) -> str | None:
    """Call Ollama /api/generate and return the full response text."""
    payload = {"model": MODEL, "prompt": prompt, "stream": False}
    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(f"{OLLAMA_URL}/api/generate", json=payload)
        resp.raise_for_status()
        return resp.json().get("response", "")


async def ollama_stream(prompt: str):
    """Yield tokens one-by-one from Ollama's streaming API."""
    payload = {"model": MODEL, "prompt": prompt, "stream": True}
    async with httpx.AsyncClient(timeout=120) as client:
        async with client.stream("POST", f"{OLLAMA_URL}/api/generate", json=payload) as resp:
            async for line in resp.aiter_lines():
                if not line:
                    continue
                try:
                    chunk = json.loads(line)
                    token = chunk.get("response", "")
                    if token:
                        yield token
                    if chunk.get("done"):
                        break
                except json.JSONDecodeError:
                    continue


# ─── Service Implementation ─────────────────────────────────────────────────

class AIInferenceServicer(pb2_grpc.AIInferenceServicer):

    # ── Task 2 – Unary ──────────────────────────────────────────────────────
    async def AnalyzeSentiment(self, request, context):
        log.info(f"[{SERVER_ID}] AnalyzeSentiment: '{request.text[:60]}...'")

        prompt = (
            f"Classify the sentiment of this text as exactly one word: "
            f"POSITIVE, NEGATIVE, or NEUTRAL. "
            f"Then on a new line write only a confidence number between 0.0 and 1.0.\n\n"
            f"Text: {request.text}\n\nSentiment:"
        )
        raw = await ollama_generate(prompt)
        lines = [l.strip() for l in raw.strip().splitlines() if l.strip()]

        label = "NEUTRAL"
        confidence = 0.5
        if lines:
            first = lines[0].upper()
            for word in ["POSITIVE", "NEGATIVE", "NEUTRAL"]:
                if word in first:
                    label = word
                    break
        if len(lines) >= 2:
            try:
                confidence = float(re.search(r"[\d.]+", lines[1]).group())
                confidence = min(1.0, max(0.0, confidence))
            except Exception:
                pass

        log.info(f"[{SERVER_ID}] → {label} ({confidence:.2f})")
        return pb2.SentimentResponse(label=label, confidence=confidence)

    # ── Task 3 – Server-Streaming ────────────────────────────────────────────
    async def GenerateText(self, request, context):
        log.info(f"[{SERVER_ID}] GenerateText: '{request.prompt[:60]}'")
        async for token in ollama_stream(request.prompt):
            yield pb2.GenerateChunk(token=token)

    # ── Task 4 – Client-Streaming ────────────────────────────────────────────
    async def SummarizeDocument(self, request_iterator, context):
        log.info(f"[{SERVER_ID}] SummarizeDocument: receiving chunks...")
        chunks = []
        async for chunk in request_iterator:
            chunks.append(chunk.content)
            log.info(f"[{SERVER_ID}]   received chunk ({len(chunk.content)} chars)")

        full_text = "\n".join(chunks)
        log.info(f"[{SERVER_ID}] Aggregated {len(full_text)} chars – calling Ollama")

        prompt = (
            f"Please provide a concise summary (3-5 sentences) of the following text:\n\n"
            f"{full_text}\n\nSummary:"
        )
        summary = await ollama_generate(prompt)
        return pb2.SummaryResponse(summary=summary.strip())

    # ── Task 5 – Bidirectional-Streaming ────────────────────────────────────
    async def LiveChat(self, request_iterator, context):
        log.info(f"[{SERVER_ID}] LiveChat: session started")
        history = []

        async for msg in request_iterator:
            log.info(f"[{SERVER_ID}] user: '{msg.content[:60]}'")
            history.append({"role": "user", "content": msg.content})

            # Build a conversational prompt from history
            convo = "\n".join(
                f"{'User' if h['role'] == 'user' else 'Assistant'}: {h['content']}"
                for h in history
            )
            prompt = f"{convo}\nAssistant:"

            response_tokens = []
            async for token in ollama_stream(prompt):
                response_tokens.append(token)
                yield pb2.ChatMessage(role="assistant", content=token)

            full_reply = "".join(response_tokens)
            history.append({"role": "assistant", "content": full_reply})
            log.info(f"[{SERVER_ID}] assistant replied ({len(full_reply)} chars)")


# ─── Entry Point ─────────────────────────────────────────────────────────────

async def serve():
    server = aio.server()
    pb2_grpc.add_AIInferenceServicer_to_server(AIInferenceServicer(), server)
    listen_addr = f"0.0.0.0:{SERVER_PORT}"
    server.add_insecure_port(listen_addr)
    log.info(f"[{SERVER_ID}] gRPC server listening on {listen_addr} (model={MODEL})")
    await server.start()
    await server.wait_for_termination()


if __name__ == "__main__":
    asyncio.run(serve())
