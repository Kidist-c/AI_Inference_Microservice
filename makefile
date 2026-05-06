# Makefile for gRPC AI Inference Microservice
# Usage: make <target>

.PHONY: help proto build up down logs test clean


# Makefile for gRPC AI Inference Microservice
# Usage: make <target>

.PHONY: help proto build up down logs test clean

PROTO_DIR  := protos
PROTO_FILE := $(PROTO_DIR)/ai_inference.proto

help:  ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN{FS=":.*?## "}; {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'

# ─── Step 1: compile .proto ──────────────────────────────────────────────────
proto:  ## Compile .proto → Python stubs (run once)
	python -m grpc_tools.protoc \
		-I $(PROTO_DIR) \
		--python_out=$(PROTO_DIR) \
		--grpc_python_out=$(PROTO_DIR) \
		$(PROTO_FILE)
	@echo "✓ Stubs generated in $(PROTO_DIR)/"

# ─── Step 2: copy stubs into server/ so Docker COPY can reach them ───────────
copy-stubs:  ## Copy generated stubs into server/ for Docker build
	cp $(PROTO_DIR)/ai_inference_pb2.py      server/
	cp $(PROTO_DIR)/ai_inference_pb2_grpc.py server/
	@echo "✓ Stubs copied to server/"

# ─── Step 3: build Docker images ─────────────────────────────────────────────
build: proto copy-stubs  ## Generate stubs + build Docker images
	docker compose build
	@echo "✓ Images built"

# ─── Step 4: start everything ────────────────────────────────────────────────
up:  ## Start Nginx + 3 gRPC servers in the background
	docker compose up -d
	@echo "✓ Stack is up – Nginx → localhost:80"

# ─── Run client tester ───────────────────────────────────────────────────────
test:  ## Run the CLI client against the load balancer
	@echo "Installing client deps..."
	pip install -q -r client/requirements.txt
	@echo "Running client..."
	PYTHONPATH=protos python client/client.py

# ─── Convenience targets ──────────────────────────────────────────────────────
down:  ## Stop and remove all containers
	docker compose down

logs:  ## Follow logs of all containers
	docker compose logs -f

logs-nginx:  ## Follow Nginx access log only
	docker compose logs -f nginx

clean:  ## Remove generated proto stubs
	rm -f $(PROTO_DIR)/ai_inference_pb2.py \
	      $(PROTO_DIR)/ai_inference_pb2_grpc.py \
	      server/ai_inference_pb2.py \
	      server/ai_inference_pb2_grpc.py
	@echo "✓ Cleaned generated files"


help:  ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN{FS=":.*?## "}; {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'

# ─── Step 1: compile .proto ──────────────────────────────────────────────────
proto:  ## Compile .proto → Python stubs (run once)
	python -m grpc_tools.protoc \
		-I $(PROTO_DIR) \
		--python_out=$(PROTO_DIR) \
		--grpc_python_out=$(PROTO_DIR) \
		$(PROTO_FILE)
	@echo "✓ Stubs generated in $(PROTO_DIR)/"

# ─── Step 2: copy stubs into server/ so Docker COPY can reach them ───────────
copy-stubs:  ## Copy generated stubs into server/ for Docker build
	cp $ai_inference_pb2.py      server/
	cp $(PROTO_DIR)/ai_inference_pb2_grpc.py server/
	@echo "✓ Stubs copied to server/"

# ─── Step 3: build Docker images ─────────────────────────────────────────────
build: proto copy-stubs  ## Generate stubs + build Docker images
	docker compose build
	@echo "✓ Images built"

# ─── Step 4: start everything ────────────────────────────────────────────────
up:  ## Start Nginx + 3 gRPC servers in the background
	docker compose up -d
	@echo "✓ Stack is up – Nginx → localhost:80"

# ─── Run client tester ───────────────────────────────────────────────────────
test:  ## Run the CLI client against the load balancer
	@echo "Installing client deps..."
	pip install -q -r client/requirements.txt
	@echo "Running client..."
	PYTHONPATH=protos python client/client.py

# ─── Convenience targets ──────────────────────────────────────────────────────
down:  ## Stop and remove all containers
	docker compose down

logs:  ## Follow logs of all containers
	docker compose logs -f

logs-nginx:  ## Follow Nginx access log only
	docker compose logs -f nginx

clean:  ## Remove generated proto stubs
	rm -f $(PROTO_DIR)/ai_inference_pb2.py \
	      $(PROTO_DIR)/ai_inference_pb2_grpc.py \
	      server/ai_inference_pb2.py \
	      server/ai_inference_pb2_grpc.py
	@echo "✓ Cleaned generated files"
