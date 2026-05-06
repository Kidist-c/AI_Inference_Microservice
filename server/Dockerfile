FROM python:3.11-slim

WORKDIR /app

COPY server/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy ALL needed folders (not individual files)
COPY protos/ protos/
COPY server/server.py .

EXPOSE 50051

CMD ["python", "server.py"]