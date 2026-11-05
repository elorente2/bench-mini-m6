# Local LLM benchmark

| Metric | splash | mirai |
|---|---:|---:|
| Short decode | 56.3 tok/s | **60.8 tok/s** |
| Decode @ long context | **44.8 tok/s** | 39.6 tok/s |
| Prefill @ long context | 440.7 tok/s | **530.7 tok/s** |
| Cold TTFT @ long context | 41.0 s | **34.1 s** |
| Cached TTFT | 463 ms | **250 ms** |
| Peak engine RSS | **2,596 MB** | 15,474 MB |
| Peak wired memory | 21.64 GB | **19.63 GB** |
| Context window (reported) | **217,081** | — |

The bold value is the best result for that row. Lower is better for TTFT and memory; higher is better for throughput and context.

## Contenders

| | splash | mirai |
|---|---|---|
| Model | unsloth/Qwen3.8-27B-GGUF:UD-Q3_K_XL | alibaba:qwen3.8:27b:mirai:mirai-m:4 |
| Quantization | Q3_K_XL (~3-bit) | 4-bit (Mirai M) |
| Engine version | Splash 1.5.0 | cli 0.6.17 |
| Reasoning effort | none | disabled |

## Verdict

**Text and code:** `mirai` won 4 of 5 comparable speed metrics.
**Memory:** `mirai` used the least peak wired memory (19.63 GB vs 21.64 GB for `splash`). On macOS this is the meaningful figure: Metal allocations are wired, not ordinary process RSS.
**Context:** `splash` reports the largest window (217,081 tokens); reported values are not a verified long-context result.

> These numbers compare engine speed and memory, not output quality. Model weights and quantization differ between engines; see `docs/methodology.md`.
