
## 1. Experimental Environment

All experiments were conducted on the Vast.ai platform using the vLLM inference framework. The experiment focused on evaluating the performance impact of prefix caching under long shared-prefix workloads.

### 1.1 Hardware Environment

* **GPU:** NVIDIA GeForce RTX 5060 Ti (16GB VRAM)
* **CUDA Version:** 13.1
* **NVIDIA Driver Version:** 590.48.01

**GPU memory usage during serving:**
* vLLM EngineCore GPU memory usage: approximately 11.6GB

---

### 1.2 Software Stack

* **LLM Serving Framework:** vLLM
* **Serving Interface:** OpenAI-compatible API server

**Models tested:**
* Qwen3-8B-FP8 (Prefix Caching Enabled)
* Qwen3-8B-FP8 (Prefix Caching Disabled)

---

### 1.3 Prefix Caching Configuration

The prefix caching experiment enabled reusable KV cache storage for shared prompt prefixes.

**Configuration:**
* GPU memory utilization: 0.72
* Maximum model length: 1024
* Prefix caching: enabled

**Startup command:**

```bash
VLLM_DISABLE_COMPILE=1 TORCHINDUCTOR_CACHE_DIR="/tmp" nohup python3 -m vllm.entrypoints.openai.api_server \
    --model /workspace/Qwen3-Raw \
    --host 127.0.0.1 \
    --port 18000 \
    --gpu-memory-utilization 0.72 \
    --max-model-len 1024 \
    --enable-prefix-caching \
    --served-model-name "Qwen/Qwen3-8B-FP8" \
    > /workspace/vllm_prefix.log 2>&1 &
```

---

### 1.4 Non-Prefix Configuration

The non-prefix experiment used the same hardware and vLLM parameters while disabling prefix caching to provide a controlled baseline comparison.

**Configuration:**
* GPU memory utilization: 0.72
* Maximum model length: 1024
* Prefix caching: disabled

All other experimental parameters remained identical to the prefix caching experiment.

---

### 1.5 Workload Configuration

All experiments used long-text prompts under shared-prefix and non-shared-prefix workloads.

**Concurrency levels tested:**
* 10
* 30
* 50

**Metrics collected:**
* TTFT P50 latency
* TTFT P99 latency
* Prefix cache hit rate
* KV cache usage
* Throughput (tokens/sec)
* Total completed requests

---

## 2. Hypothesis

The prefix model should achieve lower Time To First Token (TTFT) and higher GPU cache hit rate because prompts share the same system prefix. Higher cache hit rates reduce repeated prefill computation and GPU pressure, leading to improved latency and throughput performance.

---

## 3. Result Analysis

1. **TTFT Performance Improvement:**
   * Prefix model markedly improves TTFT performance (both P50 and P99). When there is high concurrency, the improvement is especially significant (1.96× ~ 18.74×).
   * Under high concurrency, GPU resources become the primary bottleneck, causing queuing time to increase significantly. Prefix cache reduces the prefill workload and drastically cuts down queuing time.

2. **GPU Cache Hit Rate:**
   * The most significant difference is in the GPU cache hit rate. The prefix model achieved nearly a 90% hit rate, while the non-prefix model had a 0% hit rate.
   * This gap stems from shared prompt prefixes in the prefix model workload, whereas the non-prefix workload contains no reusable prompt prefixes.

3. **Throughput & Completed Requests:**
   * The prefix model achieved higher throughput and total completed requests (34% ~ 116% improvement).
   * This demonstrates that the prefix model can handle significantly more requests in the same timeframe by eliminating redundant prefill computation within identical GPU resource constraints.

---

## 4. Difference With Hypothesis

Overall, the experimental results align well with the hypothesis. However, the magnitude of performance improvement significantly exceeded expectations. Additionally, the non-prefix model required higher overall KV cache usage because the prefix model was able to reuse shared prefix KV states across multiple requests.

---

## 5. Applicable Conditions

Prefix caching is most effective and applicable under the following conditions:
1. **Long Shared Prefixes:** Prompt contents contain long, highly repetitive system prompts or context prefixes.
2. **High Concurrency & GPU Pressure:** The system operates under high concurrency where GPU prefill compute is the primary bottleneck.
3. **Sufficient Prefix Length:** The shared prefix is long enough to fill at least one full KV cache block.

---

## 6. Conclusion

The prefix caching model achieves substantial performance gains with relatively low resource overhead, particularly when operating under high GPU resource pressure. However, it requires a high degree of prefix repetition across requests and dedicated GPU memory to maintain the prefix cache blocks.
