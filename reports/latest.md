# Local LLM benchmark

| Metric | splash | mirai | ollama-q3kxl | ollama-default | omlx-4bit | omlx-4bit-hot4g | ollama-coder-7b |
|---|---:|---:|---:|---:|---:|---:|---:|
| Short decode | 56.3 tok/s | **60.8 tok/s** | 11.0 tok/s | 30.6 tok/s | 9.2 tok/s | 9.5 tok/s | 31.7 tok/s |
| Decode @ long context | **44.8 tok/s** | 39.6 tok/s | 9.6 tok/s | 20.1 tok/s | 8.1 tok/s | — | 23.1 tok/s |
| Prefill @ long context | 440.7 tok/s | **530.7 tok/s** | 212.2 tok/s | 271.6 tok/s | 200.4 tok/s | — | 524.5 tok/s |
| Cold TTFT @ long context | 41.0 s | **34.1 s** | 85.3 s | 66.6 s | 90.3 s | — | 34.5 s |
| Cached TTFT | 463 ms | **250 ms** | 830 ms | 510 ms | 1.5 s | — | 282 ms |
| Peak engine RSS | **2,596 MB** | 15,474 MB | 14,832 MB | 11,526 MB | 9,500 MB | 9,084 MB | 5,809 MB |
| Peak wired memory | 21.64 GB | 19.63 GB | 16.16 GB | 24.85 GB | 23.62 GB | 21.88 GB | **8.49 GB** |
| Context window (API/config) | 217,081 | — | 32,768 | 32,768 | **262,144** | **262,144** | 32,768 |

The bold value is the best result for that row. Lower is better for TTFT and memory; higher is better for throughput and context.

## Contenders

| | splash | mirai | ollama-q3kxl | ollama-default | omlx-4bit | omlx-4bit-hot4g | ollama-coder-7b |
|---|---|---|---|---|---|---|---|
| Model | unsloth/Qwen3.8-27B-GGUF:UD-Q3_K_XL | alibaba:qwen3.8:27b:mirai:mirai-m:4 | qwen3.8-27b-q3kxl:latest | qwen3.8:27b | Qwen3.8-27B-4bit | Qwen3.8-27B-4bit | qwen2.5-coder:7b |
| Quantization | Q3_K_XL (~3-bit) | 4-bit (Mirai M) | Q3_K_XL (~3-bit, imported GGUF) | Ollama native (nvfp4) | 4-bit MLX | 4-bit MLX | Ollama native (nvfp4) |
| Engine version | Splash 1.5.0 | cli 0.6.17 | ollama version is 0.40.14 | ollama version is 0.40.14 | 0.7.3 | 0.7.3 | ollama version is 0.40.14 |
| Reasoning effort | none | disabled | none | none | none | none | none |

## Validity

- `omlx-4bit-hot4g` / `cached_ttft_long`: cached TTFT (1008 ms) is not meaningfully lower than cold TTFT (1306 ms)

## Verdict

Excluded from the verdict for an invalid case: `omlx-4bit-hot4g`.

**Text and code:** `mirai` won 4 of 5 comparable speed metrics.
**Memory:** `ollama-coder-7b` used the least peak wired memory (8.49 GB vs 21.64 GB for `splash`, 19.63 GB for `mirai`, 16.16 GB for `ollama-q3kxl`, 24.85 GB for `ollama-default`, 23.62 GB for `omlx-4bit`, 21.88 GB for `omlx-4bit-hot4g`). On macOS this is the meaningful figure: Metal allocations are wired, not ordinary process RSS.
**Context:** `omlx-4bit` reports the largest window (262,144 tokens); reported values are not a verified long-context result.

> These numbers compare engine speed and memory, not output quality. Model weights and quantization differ between engines; see `docs/methodology.md`.
