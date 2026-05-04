proto:
	python -m grpc_tools.protoc \
	-I./protos \
	--python_out=. \
	--grpc_python_out=. \
	./protos/ai_inference.proto

up:
	docker compose up --build

down:
	docker compose down

client:
	python client/client.py