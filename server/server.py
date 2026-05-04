from concurrent import futures
import grpc
import time

import ai_inference_pb2
import ai_inference_pb2_grpc

from ai_engine import ask_ollama


class AIService(ai_inference_pb2_grpc.AIInferenceServicer):

    # Unary RPC
    def AnalyzeSentiment(self, request, context):
        prompt = f"""
Classify sentiment of this text.
Return only label and confidence.

Text: {request.text}
"""
        result = ask_ollama(prompt)

        label = "POSITIVE"
        confidence = 0.90

        if "negative" in result.lower():
            label = "NEGATIVE"
            confidence = 0.88

        return ai_inference_pb2.SentimentResponse(
            label=label,
            confidence=confidence
        )

    # Server streaming
    def GenerateStream(self, request, context):
        for token in ask_ollama(request.prompt, stream=True):
            yield ai_inference_pb2.TokenResponse(token=token)

    # Client streaming
    def SummarizeStream(self, request_iterator, context):
        text = ""
        for chunk in request_iterator:
            text += chunk.chunk + " "

        prompt = f"Summarize this:\n{text}"
        summary = ask_ollama(prompt)

        return ai_inference_pb2.SummaryResponse(summary=summary)

    # Bidirectional streaming
    def Chat(self, request_iterator, context):
        history = []

        for msg in request_iterator:
            history.append(f"{msg.role}: {msg.content}")

            prompt = "\n".join(history) + "\nassistant:"
            response = ask_ollama(prompt)

            history.append(f"assistant: {response}")

            yield ai_inference_pb2.ChatMessage(
                role="assistant",
                content=response
            )


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))

    ai_inference_pb2_grpc.add_AIInferenceServicer_to_server(
        AIService(), server
    )

    server.add_insecure_port("[::]:50051")
    server.start()

    print("gRPC server running on 50051")
    server.wait_for_termination()


if __name__ == "__main__":
    serve()