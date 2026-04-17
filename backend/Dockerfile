FROM golang:1.24-bookworm AS builder
RUN apt-get update && apt-get install -y --no-install-recommends gcc curl && rm -rf /var/lib/apt/lists/*
WORKDIR /app

COPY go.mod go.sum ./
RUN go mod download

COPY . .

RUN curl -fSL \
    https://github.com/microsoft/onnxruntime/releases/download/v1.24.1/onnxruntime-linux-x64-1.24.1.tgz \
    -o /tmp/ort.tgz && \
    tar -xzf /tmp/ort.tgz -C /tmp && \
    mv /tmp/onnxruntime-linux-x64-1.24.1/lib/libonnxruntime.so.1.24.1 /app/ai_models/libonnxruntime.so && \
    rm -rf /tmp/ort.tgz /tmp/onnxruntime-linux-x64-1.24.1

RUN go run github.com/swaggo/swag/cmd/swag@latest init -g cmd/api/main.go
RUN CGO_ENABLED=1 GOOS=linux go build -ldflags="-s -w" -o /out/api ./cmd/api
RUN CGO_ENABLED=1 GOOS=linux go build -ldflags="-s -w" -o /out/worker ./cmd/worker

FROM debian:bookworm-slim AS api

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    libstdc++6 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY --from=builder /out/api          ./api
COPY --from=builder /app/ai_models    ./ai_models
COPY --from=builder /app/docs         ./docs
COPY --from=builder /app/migrations   ./migrations

ENV ONNX_LIB_PATH=./ai_models/libonnxruntime.so
ENV ONNX_MODEL_PATH=./ai_models/XGBoost.onnx

EXPOSE 8080

ENTRYPOINT ["./api"]

FROM debian:bookworm-slim AS worker

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY --from=builder /out/worker       ./worker
COPY --from=builder /app/migrations   ./migrations

ENTRYPOINT ["./worker"]
