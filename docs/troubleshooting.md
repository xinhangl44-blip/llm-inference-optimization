# Troubleshooting

## vLLM fails to start on RTX 5060 Ti (Blackwell / SM_120)

**Symptom**: Error message saying SM_120 is not in the supported architecture list.

**Cause**: PyTorch versions before 2.10 do not include Blackwell (SM_120) in the
default CUDA arch list.

**Fix**:
```bash
VLLM_DISABLE_COMPILE=1 TORCHINDUCTOR_CACHE_DIR="/tmp" python3 -m   vllm.entrypoints.openai.api_server --model ...
```
Or set `TORCH_CUDA_ARCH_LIST=12.0` before building from source.

---

## Prometheus metrics polluted across experiments

**Symptom**: Non-prefix experiment group shows GPU_Cache_Hit_Rate of 0.90
instead of ~0.

**Cause**: `increase()` in PromQL accumulates over a sliding window. If the
previous experiment's cache data falls within the 5-minute window, it inflates
the hit rate for the current group.

**Fix**: Always restart vLLM between experiment groups to reset counters.
Use `rate()` instead of `increase()` for hit rate calculation:
```promql
sum(rate(vllm:prefix_cache_hits_total[5m])) /
sum(rate(vllm:prefix_cache_queries_total[5m]))
```

---

## Prefix cache hit rate stays at 0 despite enable-prefix-caching

**Symptom**: `GPU_Cache_Hit_Rate` is 0.0 after running Locust with a fixed
system prompt.

**Cause**: System prompt was placed in `role: user` content. vLLM's prefix
caching is more stable with `role: system` messages because they appear at a
fixed position in the chat template token sequence.

**Fix**: Move the fixed prompt to `role: system`:
```python
"messages": [
    {"role": "system", "content": SYSTEM_PROMPT},
    {"role": "user", "content": dynamic_suffix}
]
```
Hit rate increased from 0 to 0.896 after this change.

---

## Locust req/s is half of expected

**Symptom**: 50 concurrent users produce only ~0.6 req/s instead of expected ~6.

**Cause**: Two UserClasses in the same locustfile split concurrent users evenly.
With 50 users and 2 classes, each class only gets 25 users.

**Fix**: Use a single UserClass per locustfile. Each experiment gets its own file.

---

## Queue time dominates TTFT, batching strategy shows no difference

**Symptom**: Continuous batching and chunked prefill show less than 3% TTFT
difference at 50 concurrent users.

**Cause**: This is expected behavior, not a bug. At 50 concurrent users on a
single 16GB GPU, queue time accounts for 96% of TTFT. Any inference-level
optimization is drowned out by queuing delay.

**Interpretation**: When queue time dominates, the correct solution is horizontal
scaling (more pods via KEDA), not scheduling optimization. This finding directly
motivates the queue-depth autoscaling design in the inference pipeline.

---

## Consumer pod stuck in Pending after KEDA scales up

**Symptom**: KEDA triggers scale-up but new Consumer pods stay in Pending.

**Cause**: Resource requests too high relative to available node capacity,
or minikube node has insufficient CPU/memory.

**Fix**:
```bash
kubectl describe pod <pending-pod-name>
# Look for "Insufficient cpu" or "Insufficient memory" in Events
minikube config set memory 4096
minikube config set cpus 4
minikube delete && minikube start
```
