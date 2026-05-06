#!/usr/bin/env python3
"""
gRPC AI Inference – CLI Tester
Connects to Nginx load-balancer and exercises all four RPC types.
"""

import asyncio
import sys

import grpc
from grpc import aio

# Adjust this path if running from repo root

import ai_inference_pb2 as pb2
import ai_inference_pb2_grpc as pb2_grpc

LOAD_BALANCER = "localhost:80"   # Nginx front-end

YELLOW = "\033[33m"
CYAN   = "\033[36m"
GREEN  = "\033[32m"
BLUE   = "\033[34m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

def banner(title: str):
    width = 60
    print(f"\n{BOLD}{CYAN}{'─'*width}{RESET}")
    print(f"{BOLD}{CYAN}  {title}{RESET}")
    print(f"{BOLD}{CYAN}{'─'*width}{RESET}")


async def test_sentiment(stub):
    banner(" Unary: Sentiment Analysis")
    reviews = [
        "I absolutely love this product! It changed my life.",
        "This is the worst purchase I have ever made. Terrible.",
        "The item arrived on time and works as described.",
    ]
    for text in reviews:
        print(f"{YELLOW}  Input : {RESET}{text}")
        resp = await stub.AnalyzeSentiment(pb2.SentimentRequest(text=text))
        bar  = "█" * int(resp.confidence * 20)
        print(f"{GREEN}  Result: {resp.label}  confidence={resp.confidence:.2f}  [{bar:<20}]{RESET}\n")


async def test_streaming(stub):
    banner(" Server-Streaming: Real-time Generation")
    prompt = "Explain why gRPC is better than REST for microservices in 3 bullet points."
    print(f"{YELLOW}  Prompt: {RESET}{prompt}\n  {BLUE}Streaming tokens:{RESET} ", end="", flush=True)
    async for chunk in stub.GenerateText(pb2.GenerateRequest(prompt=prompt)):
        print(chunk.token, end="", flush=True)
    print(f"\n{GREEN}  ✓ Stream complete{RESET}")


async def test_client_streaming(stub):
    banner("Client-Streaming: Batch Summarization")

    doc_chunks = [
        "Chapter 1: gRPC is a modern open-source high-performance Remote Procedure Call framework. "
        "It uses HTTP/2 as the transport layer and Protocol Buffers as the interface definition language.",

        "Chapter 2: One key advantage of gRPC is its support for four communication patterns: "
        "unary, server-streaming, client-streaming, and bidirectional streaming.",

        "Chapter 3: gRPC also supports code generation in many languages, which means both the client "
        "and server can share the same strongly-typed contracts defined in .proto files.",

        "Chapter 4: In production environments, gRPC is often fronted by an Nginx or Envoy proxy that "
        "handles load-balancing, TLS termination, and HTTP/2 connection management.",
    ]

    async def chunk_generator():
        for i, chunk in enumerate(doc_chunks, 1):
            print(f"{YELLOW}  Sending chunk {i}/{len(doc_chunks)}: {RESET}{chunk[:60]}...")
            yield pb2.TextChunk(content=chunk)
            await asyncio.sleep(0.2)

    resp = await stub.SummarizeDocument(chunk_generator())
    print(f"\n{GREEN}  Summary:{RESET}\n  {resp.summary}")


async def test_bidirectional(stub):
    banner("Task 5 – Bidirectional-Streaming: Live Chat")

    messages = [
        "Hello! What is gRPC in one sentence?",
        "What is Protocol Buffers?",
        "Thanks, goodbye!",
    ]

    async def user_messages():
        for msg in messages:
            print(f"{YELLOW}  You      : {RESET}{msg}")
            yield pb2.ChatMessage(role="user", content=msg)
            await asyncio.sleep(1)   # pause between messages

    print(f"{BLUE}  Chatting...{RESET}\n")
    async for reply in stub.LiveChat(user_messages()):
        print(reply.content, end="", flush=True)
    print(f"\n{GREEN}  ✓ Chat session complete{RESET}")


async def main():
    print(f"\n{BOLD}Connecting to Nginx load-balancer → {LOAD_BALANCER}{RESET}")
    async with aio.insecure_channel(LOAD_BALANCER) as channel:
        stub = pb2_grpc.AIInferenceStub(channel)
        await test_sentiment(stub)
        await test_streaming(stub)
        await test_client_streaming(stub)
        await test_bidirectional(stub)

    print(f"\n{BOLD}{GREEN}All tests completed successfully! ✓{RESET}\n")


if __name__ == "__main__":
    asyncio.run(main())
