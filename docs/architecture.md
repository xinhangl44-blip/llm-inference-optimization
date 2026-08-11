# System Architecture

## Overview

The project has two independent modules sharing the same vLLM backend:

**Inference Pipeline**: A production-style K8s deployment with queue-based
autoscaling, designed to handle bursty traffic without dropping requests.

**Benchmarking Module**: A measurement harness for controlled experiments
across three optimization dimensions.

## Inference Pipeline

Client
↓
FastAPI Gateway (rate limiting, request validation)
↓
Redis Streams (message queue, decouples ingress from compute)
↓
Consumer Pods (pull from queue, forward to vLLM)
↓
vLLM (inference, exposes /metrics for Prometheus)
↓
Response returned to client via request_id


### Why queue-based autoscaling

GPU utilization is a poor autoscaling signal for LLM inference because:
- Under continuous batching, GPU utilization is near 100% even at moderate load
- It is a lagging indicator — by the time it rises, requests are already queuing

Queue depth (Redis Stream pending entries) is a leading indicator that directly
reflects unserved request backlog. KEDA polls this metric every 5 seconds and
scales Consumer pods accordingly, with a minimum of 1 replica to avoid cold start
latency on the first request.

### Component responsibilities

| Component | Role |
|-----------|------|
| Gateway | Rate limiting, request ingestion, writes to Redis Stream |
| Redis Streams | Decouples ingress from compute, provides KEDA scaling signal |
| Consumer | Pulls from queue, calls vLLM, handles graceful shutdown |
| vLLM | Model inference, exposes Prometheus metrics |
| KEDA | Watches queue depth, triggers HPA to scale Consumer pods |
| Prometheus | Scrapes vLLM and K8s metrics |
| Grafana | Visualizes three-layer metrics (system / request / model) |

## Benchmarking Module

Locust (load generator)
↓
vLLM (direct, no queue)
↓
Prometheus (scrapes /metrics every 15s)
↓
Grafana (real-time dashboard)
↑
export_data.py (pulls metrics via Prometheus HTTP API after each experiment)


### Three-layer observability

**System layer**: Pod status, GPU utilization, node resources.
Used to detect scheduling bottlenecks.

**Request layer**: Queue depth, QPS, error rate.
Used to detect capacity bottlenecks.

**Model layer**: TTFT, ITL, tokens/sec, KV cache hit rate.
Used to detect inference bottlenecks.

The three layers together enable fast bottleneck localization:
if queue depth is high but GPU utilization is low, the bottleneck is
in scheduling (not enough pods). If queue depth is low but TTFT is high,
the bottleneck is in inference itself (KV cache pressure or batch strategy).

## Environment Split

| Environment | Purpose |
|-------------|---------|
| Local WSL2 | vLLM inference, Prometheus + Grafana, Locust load testing |
| Local minikube | K8s config validation (probes, KEDA, PDB, Helm) |
| vast.ai GPU | GPU-intensive experiments, full inference pipeline validation |
