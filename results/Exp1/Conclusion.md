
## 1. Introduction & Hypothesis

### 1.1 Hypothesis
* **Chunked Prefill Method:** Chunked prefill may reduce prefill blocking and improve request interleaving fairness by splitting long prompts into smaller scheduling units. This may reduce Time To First Token (TTFT) under long-prompt workloads and improve system responsiveness under moderate concurrency.
* **Continuous Batching Method:** Expected to show different TTFT characteristics and higher prefill times relative to chunked execution.

---

## 2. Experimental Environment

All experiments were conducted on the Vast.ai platform using the vLLM inference framework and the Qwen3-8B-FP8 model.

### 2.1 Hardware Environment

* **GPU:** NVIDIA GeForce RTX 5060 Ti (16GB VRAM)
* **CUDA Version:** 13.2
* **NVIDIA Driver Version:** 595.58.03

### 2.2 Software Stack

* **LLM Serving Framework:** vLLM
* **Model:** Qwen3-8B-FP8
* **Serving Interface:** OpenAI-compatible API server

### 2.3 Continuous Batching Configuration

The continuous batching configuration used the default vLLM scheduling strategy without chunked prefill.

**Configuration:**
* GPU memory utilization: 0.70
* Maximum model length: 1024
* Chunked prefill: disabled

**Startup command:**
```bash
nohup python3 -m vllm.entrypoints.openai.api_server \
    --model /workspace/Qwen3-Raw \
    --host 127.0.0.1 \
    --port 18000 \
    --gpu-memory-utilization 0.70 \
    --max-model-len 1024 \
    --served-model-name "Qwen/Qwen3-8B-FP8" \
    > /workspace/vllm_continuous.log 2>&1 &
```

### 2.4 Chunked Prefill Configuration

The chunked prefill configuration enabled prompt chunking to divide long prompts into smaller scheduling units during the prefill phase.

**Configuration:**
* GPU memory utilization: 0.70
* Maximum model length: 1024
* Chunked prefill: enabled
* Maximum batched tokens: 512

**Startup command:**
```bash
nohup python3 -m vllm.entrypoints.openai.api_server \
    --model Qwen/Qwen3-8B-FP8 \
    --host 127.0.0.1 \
    --port 18000 \
    --gpu-memory-utilization 0.70 \
    --max-model-len 1024 \
    --enable-chunked-prefill \
    --max-num-batched-tokens 512 \
    --served-model-name Qwen/Qwen3-8B-FP8 \
    > /workspace/vllm_chunked.log 2>&1 &
```

### 2.5 Workload Configuration

All experiments used long-text prompts under different concurrency levels.

**Concurrency levels tested:**
* 10
* 20
* 30
* 40
* 50

**Metrics collected:**
* Average TTFT (Time To First Token)
* Average prefill time
* Average decode time
* Average queue time
* Throughput (tokens/sec)
* Total completed requests

---

## 3. Result Analysis

1. **Queue Time vs. Prefill Time Dominance:**
   * When concurrency is greater than 10, the main determining factor of model performance is the average queue time (>90% of latency).
   * When concurrency is less than or equal to 10, queue time becomes negligible, making prefill time the dominant component of TTFT.
2. **Completed Requests Performance:**
   * When concurrency is greater than or equal to 30, the chunked prefill model achieves slightly better total completed requests performance (~1% improvement) under high concurrency workloads.
   * When concurrency is less than 30, the continuous batching model achieves better total completed requests performance.
3. **Prefill Time Improvement:**
   * The chunked prefill model demonstrates significantly better performance in average prefill time compared to the continuous batching model (50%–60% improvement).

---

## 4. Differences with Initial Hypothesis

In the initial hypothesis, it was expected that continuous batching might offer lower TTFT. However, experimental results demonstrate that chunked prefill lowers the total TTFT. 

Key observations include:
* At high concurrency, queuing time overshadows individual prefill optimization benefits.
* At low concurrency (e.g., concurrency = 10), the continuous batching model achieved better request completion efficiency. This indicates that under low concurrency, the additional scheduling overhead introduced by chunked prefill can slightly degrade request completion efficiency.

---

## 5. Applicable Conditions

Chunked prefill is most applicable under the following conditions:
1. When prompt lengths are large and reducing prefill latency is prioritized over maximizing raw request completion efficiency.
2. When concurrency is high and total completed request throughput needs improvement.
3. When prompt text length exceeds `max-num-batched-tokens`.

---

## 6. Conclusion

Chunked prefill effectively reduces prefill time and improves TTFT under specific workloads. However, at high concurrency levels, the primary performance bottleneck shifts to queuing time. 

Under high queuing conditions, optimizations strictly within the model inference layer yield limited gains. The primary solution is to address queue buildup directly, such as by implementing horizontal autoscaling based on queue depth (e.g., via KEDA).
