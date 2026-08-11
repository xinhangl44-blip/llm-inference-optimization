# LLM Inference Optimization System

A Kubernetes-native LLM inference system with Redis Streams queue and KEDA 
autoscaling, paired with a benchmarking module that measures latency, throughput, 
and optimization trade-offs across batching strategies, prefix caching, and 
quantization schemes.

## Architecture

### Inference Pipeline (K8s)

Client → Gateway → Redis Stream → Consumer → vLLM → Response
↑
KEDA (queue depth triggers autoscaling)


### Benchmarking Module

Locust → vLLM → Prometheus → Grafana


## Key Findings

- **Batching**: Chunked prefill reduces prefill time by 57% in overload scenarios,
  but queue time dominates total latency (96% of TTFT). Horizontal scaling via KEDA
  is more effective than scheduling optimization alone.

- **Prefix caching**: 27x TTFT improvement at 50 concurrent users with high prefix
  reuse (hit rate 0.896). Negligible benefit when hit rate approaches zero.

- **Quantization**: FP8 outperforms AWQ 4-bit with 3x lower decode latency and 60%
  higher throughput on modern GPUs. Accuracy difference negligible
  (73.5% vs 72.7% on MMLU).

## Experiment Results

### Exp1: Batching Strategy

| Strategy | Concurrency | TTFT | Queue Time | Throughput |
|----------|-------------|------|------------|------------|
| Continuous | 50 | 28.18s | 26.80s (95%) | 373 tok/s |
| Chunked Prefill | 50 | 36.82s | 35.59s (97%) | 303 tok/s |

### Exp2: Prefix Caching

| Workload | Concurrency | TTFT P50 | TTFT P99 | Hit Rate | Throughput |
|----------|-------------|----------|----------|----------|------------|
| High-repeat prefix | 50 | 0.233s | 0.494s | 0.896 | 1051 tok/s |
| Random prefix | 50 | 6.376s | 9.874s | 0.0 | 482 tok/s |

### Exp3: Quantization

| Format | Concurrency | TTFT | Decode Time | Throughput | MMLU Acc |
|--------|-------------|------|-------------|------------|----------|
| FP8 | 30 | 0.254s | 7.877s | 498 tok/s | 73.5% |
| AWQ 4-bit | 30 | 1.382s | 23.237s | 150 tok/s | 72.7% |

## Requirements

- Python 3.11+
- CUDA 12.8+ (RTX 5060 Ti / Blackwell)
- Docker + Docker Compose
- kubectl + minikube
- vLLM 0.9+

## Quick Start

### 1. Clone
```bash
git clone https://github.com/yourname/llm-inference-optimization
cd llm-inference-optimization
```

### 2. Install dependencies
```bash
pip install vllm locust requests prometheus-client
```

### 3. Create Redis secret (required before applying K8s manifests)
```bash
kubectl create secret generic redis-password-secret   --from-literal=redis-password=your-password   --from-literal=redis-url=redis://:your-password@redis-service:6379
```

### 4. Deploy K8s stack
```bash
kubectl apply -f k8s/
```

### 5. Start monitoring
```bash
cd monitoring && docker-compose up -d
```

### 6. Start vLLM (benchmarking)
```bash
VLLM_DISABLE_COMPILE=1 python3 -m vllm.entrypoints.openai.api_server     --model Qwen/Qwen3-8B-FP8     --port 18000     --gpu-memory-utilization 0.72     --max-model-len 1024
```

### 7. Run benchmark
```bash
locust -f load-testing/locustfile_batching.py     --host http://localhost:18000     --users 10 --spawn-rate 2 --run-time 5m --headless
```

## Environment

| Component | Version |
|-----------|---------|
| GPU | NVIDIA RTX 5060 Ti 16GB |
| CUDA | 12.8+ |
| vLLM | 0.9+ |
| Model (inference pipeline) | Qwen2.5-7B-Instruct-AWQ |
| Model (benchmarking) | Qwen3-8B-FP8 |
| Kubernetes | minikube |
| Python | 3.11 |
