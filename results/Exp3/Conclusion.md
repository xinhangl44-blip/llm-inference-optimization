
## 1. Experimental Environment & Configurations

All experiments were conducted using the vLLM inference framework on the Vast.ai platform. Due to the VRAM limitation of the test hardware, FP16 models could not be loaded. Therefore, the FP8 model was used as the high-precision baseline and compared against the AWQ 4-bit quantized model.

### 1.1 Hardware Environment
* **GPU:** NVIDIA GeForce RTX 5060 Ti (16GB VRAM)
* **CUDA Version:** 13.2
* **NVIDIA Driver Version:** 595.58.03

### 1.2 Software Stack
* **LLM Serving Framework:** vLLM
* **Serving Interface:** OpenAI-compatible API server

**Models Tested:**
* `Qwen2.5-7B-Instruct-1M-FP8-Dynamic`
* `Qwen2.5-7B-Instruct-AWQ`

---

### 1.3 FP8 Model Configuration
The FP8 model was used as the high-precision baseline for comparison.

**Configuration:**
* GPU memory utilization: 0.75
* Maximum model length: 1024
* Compilation optimization: disabled
* TorchInductor cache directory: `/tmp`

**Startup Command:**
```bash
VLLM_DISABLE_COMPILE=1 TORCHINDUCTOR_CACHE_DIR="/tmp" nohup python3 -m vllm.entrypoints.openai.api_server     --model /workspace/Qwen2.5-FP8     --host 127.0.0.1     --port 18000     --gpu-memory-utilization 0.75     --max-model-len 1024     --served-model-name "Qwen/Qwen2.5-7B"     > /workspace/vllm_continuous.log 2>&1 &
```

---

### 1.4 AWQ Model Configuration
The AWQ model used 4-bit weight quantization for reducing VRAM usage.

**Configuration:**
* GPU memory utilization: 0.75
* Maximum model length: 1024
* Quantization method: AWQ 4-bit
* Compilation optimization: disabled
* TorchInductor cache directory: `/tmp`

The hardware environment and vLLM serving parameters were kept identical to the FP8 experiment to ensure fair comparison.

---

### 1.5 Workload Configuration
All experiments used long-text prompts under different concurrency levels.

**Concurrency Levels Tested:**
* 10
* 30
* 50

**Metrics Collected:**
* Average TTFT (Time To First Token)
* Average prefill time
* Average decode time
* Average queue time
* Throughput (tokens/sec)
* Total completed requests
* KV cache usage
* MMLU accuracy benchmark scores

---

## 2. Hypothesis

AWQ model condenses the weights to half of the original version, so the decode time might be lower and TTFT may be similar to the original version. Because quantization mainly reduces weight storage size rather than changing model architecture, TTFT was expected to remain relatively close to the FP8 model. The total accuracy may be undermined due to less weight matrices. The overall throughput and GPU VRAM usage could be improved.

---

## 3. Result Analysis

1. **Decoding Time Bottleneck:** The main bottleneck in this experiment is decoding time. The FP8 model exhibits significantly better decoding time performance (200~300% improvement). The improved decode efficiency of the FP8 model increases overall throughput and reduces system pressure, which contributes to lower TTFT under concurrent workloads. The 4-bit weights of AWQ need to be dequantized back to high precision before each matrix multiplication. This operation occurs in every step of the decode process, and the cumulative overhead results in the decode time being three times that of FP8.
2. **VRAM Usage:** AWQ reduces VRAM usage by storing model weights in lower-bit quantized representations.
3. **Accuracy:** The accuracy difference remains relatively small (0.84%) because AWQ preserves most model behavior despite quantization approximation.

---

## 4. Difference With Hypothesis

The experimental results contradicted the initial hypothesis. On lower-end or mid-range GPUs, the theoretical bottleneck is often thought to be VRAM for KV cache. However, in this experiment, VRAM was sufficient even for the FP8 model. Hence, the dequantization overhead could not be ignored, making decoding time the main performance bottleneck instead of memory bandwidth/capacity.

---

## 5. Applicable Conditions

### Modern FP8-Supported GPUs & High-Throughput Scenarios (FP8 Recommended):
1. Modern GPUs supporting hardware-level FP8 calculations exist.
2. Online serving/reasoning requires low latency and is sensitive to delays.
3. VRAM capacity is sufficient, eliminating the need for extreme weight compression.

### Memory-Constrained Environments (AWQ Recommended):
1. Extremely limited VRAM scenarios (e.g., consumer-grade GPUs with low VRAM, edge devices).

---

## 6. Conclusion

On GPUs with FP8 hardware support, AWQ 4-bit does not exhibit a speed advantage over FP8. Specifically, the decode time deteriorates by 3x, overall throughput decreases by 60–63%, while the accuracy difference remains negligible (0.84%). 

The primary value of AWQ lies in extremely memory-constrained scenarios rather than production environments pursuing high inference speed. On modern GPUs with hardware FP8 acceleration support and sufficient VRAM capacity, FP8 provides superior throughput and latency compared to AWQ 4-bit.
