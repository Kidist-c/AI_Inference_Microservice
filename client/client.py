import grpc
import ai_inference_pb2
import ai_inference_pb2_grpc


channel = grpc.insecure_channel("localhost:5000")
stub = ai_inference_pb2_grpc.AIInferenceStub(channel)

# Unary
resp = stub.AnalyzeSentiment(
    ai_inference_pb2.SentimentRequest(
        text="This laptop is fantastic."
    )
)
print("Unary:", resp.label, resp.confidence)

# Server streaming
print("\nStreaming:")
for token in stub.GenerateStream(
    ai_inference_pb2.GenerationRequest(
        prompt="Explain gRPC in one paragraph"
    )
):
    print(token.token, end="", flush=True)

# Client streaming
def chunks():
    texts = [
        "gRPC is efficient.",
        "It uses HTTP/2.",
        "It supports streaming."
    ]
    for t in texts:
        yield ai_inference_pb2.TextChunk(chunk=t)

summary = stub.SummarizeStream(chunks())
print("\n\nSummary:", summary.summary)

# Bidirectional streaming
def chat():
    msgs = [
        "Hello",
        "What is gRPC?",
        "Why is it fast?"
    ]
    for m in msgs:
        yield ai_inference_pb2.ChatMessage(
            role="user",
            content=m
        )

print("\nChat:")
for msg in stub.Chat(chat()):
    print("AI:", msg.content)