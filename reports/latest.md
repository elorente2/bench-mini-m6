# Local LLM benchmark

| Metric | splash | mirai | ollama-q3kxl | ollama-default |
|---|---:|---:|---:|---:|
| Short decode | 56.3 tok/s | **60.8 tok/s** | 11.0 tok/s | 30.6 tok/s |
| Decode @ long context | **44.8 tok/s** | 39.6 tok/s | 9.6 tok/s | 20.1 tok/s |
| Prefill @ long context | 440.7 tok/s | **530.7 tok/s** | 212.2 tok/s | 271.6 tok/s |
| Cold TTFT @ long context | 41.0 s | **34.1 s** | 85.3 s | 66.6 s |
| Cached TTFT | 463 ms | **250 ms** | 830 ms | 510 ms |
| Peak engine RSS | **2,596 MB** | 15,474 MB | 14,832 MB | 11,526 MB |
| Peak wired memory | 21.64 GB | 19.63 GB | **16.16 GB** | 24.85 GB |
| Context window (API/config) | **217,081** | — | 32,768 | 32,768 |

The bold value is the best result for that row. Lower is better for TTFT and memory; higher is better for throughput and context.

## Contenders

| | splash | mirai | ollama-q3kxl | ollama-default |
|---|---|---|---|---|
| Model | unsloth/Qwen3.8-27B-GGUF:UD-Q3_K_XL | alibaba:qwen3.8:27b:mirai:mirai-m:4 | qwen3.8-27b-q3kxl:latest | qwen3.8:27b |
| Quantization | Q3_K_XL (~3-bit) | 4-bit (Mirai M) | Q3_K_XL (~3-bit, imported GGUF) | Ollama native (nvfp4) |
| Engine version | Splash 1.5.0 | cli 0.6.17 | ollama version is 0.40.14 | ollama version is 0.40.14 |
| Reasoning effort | none | disabled | none | none |

## Verdict

**Text and code:** `mirai` won 4 of 5 comparable speed metrics.
**Memory:** `ollama-q3kxl` used the least peak wired memory (16.16 GB vs 21.64 GB for `splash`, 19.63 GB for `mirai`, 24.85 GB for `ollama-default`). On macOS this is the meaningful figure: Metal allocations are wired, not ordinary process RSS.
**Context:** `splash` reports the largest window (217,081 tokens); reported values are not a verified long-context result.

> These numbers compare engine speed and memory, not output quality. Model weights and quantization differ between engines; see `docs/methodology.md`.
