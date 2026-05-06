FROM python:3.11-slim

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the generated proto stubs (copied here by `make build`)
COPY ai_inference_pb2.py      .
COPY ai_inference_pb2_grpc.py .

# Copy the server logic
COPY server.py .

EXPOSE 50051

CMD ["python", "server.py"]