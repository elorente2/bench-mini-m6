# Splash V3.1 vs Mirai/uzu — speed

| Metric | mirai | splash-v31 |
|---|---:|---:|
| Short decode | **60.8 tok/s** | 55.8 tok/s |
| Decode @ long context | 39.6 tok/s | **41.1 tok/s** |
| Prefill @ long context | **530.7 tok/s** | 447.8 tok/s |
| Cold TTFT @ long context | **34.1 s** | 40.4 s |
| Cached TTFT | **250 ms** | 443 ms |
| Peak engine RSS | 15,474 MB | **2,658 MB** |
| Peak wired memory | **19.63 GB** | 21.69 GB |
| Context window (API/config) | — | **217,081** |

The bold value is the best result for that row. Lower is better for TTFT and memory; higher is better for throughput and context.

## Contenders

| | mirai | splash-v31 |
|---|---|---|
| Model | alibaba:qwen3.8:27b:mirai:mirai-m:4 | unsloth/Qwen3.8-27B-GGUF:UD-Q3_K_XL |
| Quantization | 4-bit (Mirai M) | Q3_K_XL (~3-bit) |
| Engine version | cli 0.6.17 | Splash 1.5.0 |
| Reasoning effort | disabled | none |

## Verdict

**Text and code:** `mirai` won 4 of 5 comparable speed metrics.
**Memory:** `mirai` used the least peak wired memory (19.63 GB vs 21.69 GB for `splash-v31`). On macOS this is the meaningful figure: Metal allocations are wired, not ordinary process RSS.
**Context:** `splash-v31` reports the largest window (217,081 tokens); reported values are not a verified long-context result.

> These numbers compare engine speed and memory, not output quality. Model weights and quantization differ between engines; see `docs/methodology.md`.
