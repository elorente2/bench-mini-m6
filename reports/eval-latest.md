# Accuracy by model

Apple M6 (Mac18,5) · 34.4 GB · suite revision 1, 2, 3, 4, 5 · 16 runs · temperature 0

> Warning: these results span more than one revision. They are not compared with each other, and only the newest revision decides.

## Accuracy by category

| Model / engine | Instructions | JSON | Tools | Architecture | Calculation | Code | Long context | Abstention | Extraction | Total |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `ollama-coder-7b-r5-off` | 1/2 (50 %) | 1/2 (50 %) | 0/2 (0 %) | 0/3 (0 %) | 1/2 (50 %) | 1/3 (33 %) | — | 2/2 (100 %) | 1/2 (50 %) | 7/18 (39 %) |
| `ollama-qwen35-9b-r5-off` | 2/2 (100 %) | 2/2 (100 %) | 2/2 (100 %) | 2/3 (67 %) | 1/2 (50 %) | 1/3 (33 %) | — | 2/2 (100 %) | 2/2 (100 %) | 14/18 (78 %) |
| `ollama-qwen35-9b-r5-thinkon` | 2/2 (100 %) | 1/2 (50 %) | 2/2 (100 %) | 3/3 (100 %) | 1/2 (50 %) | 2/3 (67 %) | — | 2/2 (100 %) | 2/2 (100 %) | 15/18 (83 %) |
| `qwen3.8-4bit-omlx-r3-thinkoff` | 3/3 (100 %) | 3/3 (100 %) | 2/2 (100 %) | — | 2/3 (67 %) | 3/3 (100 %) | 2/2 (100 %) | 2/2 (100 %) | 3/3 (100 %) | 20/21 (95 %) |
| `qwen3.8-4bit-omlx-r3-thinkon` | 3/3 (100 %) | 3/3 (100 %) | 2/2 (100 %) | — | 3/3 (100 %) | 3/3 (100 %) | 2/2 (100 %) | 2/2 (100 %) | 3/3 (100 %) | 21/21 (100 %) |
| `qwen3.8-4bit-omlx-r5-thinkoff` | 2/2 (100 %) | 1/2 (50 %) | 2/2 (100 %) | 2/3 (67 %) | 1/2 (50 %) | 3/3 (100 %) | 2/2 (100 %) | 2/2 (100 %) | 2/2 (100 %) | 17/20 (85 %) |
| `qwen3.8-4bit-omlx-r5-thinkon` | 2/2 (100 %) | 2/2 (100 %) | 2/2 (100 %) | 3/3 (100 %) | 2/2 (100 %) | 2/3 (67 %) | 2/2 (100 %) | 2/2 (100 %) | 2/2 (100 %) | 19/20 (95 %) |
| `qwen3.8-q3kxl-splash` | 3/3 (100 %) | 3/3 (100 %) | 2/2 (100 %) | — | 2/3 (67 %) | 3/3 (100 %) | 2/2 (100 %) | 2/2 (100 %) | 3/3 (100 %) | 20/21 (95 %) |
| `qwen3.8-q3kxl-splash-r2-thinkoff` | 3/3 (100 %) | 3/3 (100 %) | 2/2 (100 %) | — | 2/3 (67 %) | 3/3 (100 %) | 2/2 (100 %) | 2/2 (100 %) | 3/3 (100 %) | 20/21 (95 %) |
| `qwen3.8-q3kxl-splash-r2-thinkon` | 3/3 (100 %) | 3/3 (100 %) | 2/2 (100 %) | — | 2/3 (67 %) | 3/3 (100 %) | 2/2 (100 %) | 2/2 (100 %) | 3/3 (100 %) | 20/21 (95 %) |
| `qwen3.8-q3kxl-splash-r3-thinkoff` | 3/3 (100 %) | 3/3 (100 %) | 2/2 (100 %) | — | 2/3 (67 %) | 3/3 (100 %) | 2/2 (100 %) | 2/2 (100 %) | 3/3 (100 %) | 20/21 (95 %) |
| `qwen3.8-q3kxl-splash-r3-thinkon` | 3/3 (100 %) | 3/3 (100 %) | 2/2 (100 %) | — | 3/3 (100 %) | 3/3 (100 %) | 2/2 (100 %) | 2/2 (100 %) | 3/3 (100 %) | 21/21 (100 %) |
| `qwen3.8-q3kxl-splash-r4-thinkoff` | 2/2 (100 %) | 1/2 (50 %) | 2/2 (100 %) | 2/3 (67 %) | 1/2 (50 %) | 3/3 (100 %) | 2/2 (100 %) | 2/2 (100 %) | 2/2 (100 %) | 17/20 (85 %) |
| `qwen3.8-q3kxl-splash-r4-thinkon` | 2/2 (100 %) | 2/2 (100 %) | 2/2 (100 %) | 3/3 (100 %) | 2/2 (100 %) | 2/3 (67 %) | 2/2 (100 %) | 2/2 (100 %) | 2/2 (100 %) | 19/20 (95 %) |
| `qwen3.8-q3kxl-splash-r5-thinkoff` | 2/2 (100 %) | 1/2 (50 %) | 2/2 (100 %) | 2/3 (67 %) | 1/2 (50 %) | 3/3 (100 %) | 2/2 (100 %) | 2/2 (100 %) | 2/2 (100 %) | 17/20 (85 %) |
| `qwen3.8-q3kxl-splash-r5-thinkon` | 2/2 (100 %) | 2/2 (100 %) | 2/2 (100 %) | 3/3 (100 %) | 2/2 (100 %) | 2/3 (67 %) | 2/2 (100 %) | 2/2 (100 %) | 2/2 (100 %) | 19/20 (95 %) |

⚠ = run that cannot support a decision (see the gates section).

## Models and engines

| Run | Model | Engine | Thinking | Quantization | Max context |
|---|---|---|---|---|---:|
| `ollama-coder-7b-r5-off` | `qwen2.5-coder:7b` | Ollama (native tag) ollama version is 0.40.14 | off | Ollama native (nvfp4) | 32,768* |
| `ollama-qwen35-9b-r5-off` | `qwen3.5-9b-q4:latest` | Ollama (native tag) ollama version is 0.40.14 | off | Ollama native (nvfp4) | 32,768* |
| `ollama-qwen35-9b-r5-thinkon` | `qwen3.5-9b-q4:latest` | Ollama (native tag) ollama version is 0.40.14 | on | Ollama native (nvfp4) | 32,768* |
| `qwen3.8-4bit-omlx-r3-thinkoff` | `Qwen3.8-27B-4bit` | oMLX 0.7.3 | off | 4-bit MLX | 262,144 |
| `qwen3.8-4bit-omlx-r3-thinkon` | `Qwen3.8-27B-4bit` | oMLX 0.7.3 | on | 4-bit MLX | 262,144 |
| `qwen3.8-4bit-omlx-r5-thinkoff` | `Qwen3.8-27B-4bit` | oMLX 0.7.3 | off | 4-bit MLX | 262,144 |
| `qwen3.8-4bit-omlx-r5-thinkon` | `Qwen3.8-27B-4bit` | oMLX 0.7.3 | on | 4-bit MLX | 262,144 |
| `qwen3.8-q3kxl-splash` | `unsloth/Qwen3.8-27B-GGUF:UD-Q3_K_XL` | Splash 1.5.0 | off | Q3_K_XL (~3-bit) | 217,081 |
| `qwen3.8-q3kxl-splash-r2-thinkoff` | `unsloth/Qwen3.8-27B-GGUF:UD-Q3_K_XL` | Splash 1.5.0 | off | Q3_K_XL (~3-bit) | 217,081 |
| `qwen3.8-q3kxl-splash-r2-thinkon` | `unsloth/Qwen3.8-27B-GGUF:UD-Q3_K_XL` | Splash 1.5.0 | on | Q3_K_XL (~3-bit) | 217,081 |
| `qwen3.8-q3kxl-splash-r3-thinkoff` | `unsloth/Qwen3.8-27B-GGUF:UD-Q3_K_XL` | Splash 1.5.0 | off | Q3_K_XL (~3-bit) | 217,081 |
| `qwen3.8-q3kxl-splash-r3-thinkon` | `unsloth/Qwen3.8-27B-GGUF:UD-Q3_K_XL` | Splash 1.5.0 | on | Q3_K_XL (~3-bit) | 217,081 |
| `qwen3.8-q3kxl-splash-r4-thinkoff` | `unsloth/Qwen3.8-27B-GGUF:UD-Q3_K_XL` | Splash 1.5.0 | off | Q3_K_XL (~3-bit) | 217,081 |
| `qwen3.8-q3kxl-splash-r4-thinkon` | `unsloth/Qwen3.8-27B-GGUF:UD-Q3_K_XL` | Splash 1.5.0 | on | Q3_K_XL (~3-bit) | 217,081 |
| `qwen3.8-q3kxl-splash-r5-thinkoff` | `unsloth/Qwen3.8-27B-GGUF:UD-Q3_K_XL` | Splash 1.5.0 | off | Q3_K_XL (~3-bit) | 217,081 |
| `qwen3.8-q3kxl-splash-r5-thinkon` | `unsloth/Qwen3.8-27B-GGUF:UD-Q3_K_XL` | Splash 1.5.0 | on | Q3_K_XL (~3-bit) | 217,081 |

Max context is what the engine's API declares; `*` marks the value taken from the configuration because the API reports none. It is not a retrieval measure: the long-context items say that with their real prompt.

## Cost

| Run | Items | Minutes | Truncated | Max prompt (tokens) | Context coverage | Slowest item |
|---|---:|---:|---:|---:|---:|---:|
| `ollama-coder-7b-r5-off` | 18 | 0.7 | 0 | — | — | 7.0 s |
| `ollama-qwen35-9b-r5-off` | 18 | 0.9 | 0 | — | — | 14.9 s |
| `ollama-qwen35-9b-r5-thinkon` | 18 | 38.7 | 3 | — | — | 379.8 s |
| `qwen3.8-4bit-omlx-r3-thinkoff` | 21 | 4.1 | 0 | 24574 | 9 % | 119.1 s |
| `qwen3.8-4bit-omlx-r3-thinkon` | 21 | 15.2 | 0 | 24614 | 9 % | 216.3 s |
| `qwen3.8-4bit-omlx-r5-thinkoff` | 20 | 9.2 | 0 | 65124 | 25 % | 348.4 s |
| `qwen3.8-4bit-omlx-r5-thinkon` | 20 | 46.7 | 1 | 65164 | 25 % | 934.1 s |
| `qwen3.8-q3kxl-splash` | 21 | 1.9 | — | 24574 | 11 % | 64.4 s |
| `qwen3.8-q3kxl-splash-r2-thinkoff` | 21 | 0.4 | 0 | 24574 | 11 % | 4.6 s |
| `qwen3.8-q3kxl-splash-r2-thinkon` | 21 | 4.3 | 1 | 24614 | 11 % | 62.8 s |
| `qwen3.8-q3kxl-splash-r3-thinkoff` | 21 | 0.4 | 0 | 24574 | 11 % | 4.7 s |
| `qwen3.8-q3kxl-splash-r3-thinkon` | 21 | 4.2 | 0 | 24614 | 11 % | 116.6 s |
| `qwen3.8-q3kxl-splash-r4-thinkoff` | 20 | 4.2 | 0 | 65124 | 30 % | 189.2 s |
| `qwen3.8-q3kxl-splash-r4-thinkon` | 20 | 9.9 | 1 | 65164 | 30 % | 190.2 s |
| `qwen3.8-q3kxl-splash-r5-thinkoff` | 20 | 0.6 | 0 | 65124 | 30 % | 9.4 s |
| `qwen3.8-q3kxl-splash-r5-thinkon` | 20 | 8.4 | 1 | 65164 | 30 % | 292.3 s |

Coverage is the share of the declared window the suite actually exercises: the longest prompt divided by the engine's max context. Low coverage does not mean the rest of the window fails; it means this suite has not tried it.

## Decision by task

| Task | Best | Accuracy | Tied for first |
|---|---|---:|---|
| Instructions | tie (6) | 100 % | `ollama-qwen35-9b-r5-off`, `ollama-qwen35-9b-r5-thinkon`, `qwen3.8-4bit-omlx-r5-thinkoff`, `qwen3.8-4bit-omlx-r5-thinkon`, `qwen3.8-q3kxl-splash-r5-thinkoff`, `qwen3.8-q3kxl-splash-r5-thinkon` |
| JSON | tie (3) | 100 % | `ollama-qwen35-9b-r5-off`, `qwen3.8-4bit-omlx-r5-thinkon`, `qwen3.8-q3kxl-splash-r5-thinkon` |
| Tools | tie (6) | 100 % | `ollama-qwen35-9b-r5-off`, `ollama-qwen35-9b-r5-thinkon`, `qwen3.8-4bit-omlx-r5-thinkoff`, `qwen3.8-4bit-omlx-r5-thinkon`, `qwen3.8-q3kxl-splash-r5-thinkoff`, `qwen3.8-q3kxl-splash-r5-thinkon` |
| Architecture | tie (3) | 100 % | `ollama-qwen35-9b-r5-thinkon`, `qwen3.8-4bit-omlx-r5-thinkon`, `qwen3.8-q3kxl-splash-r5-thinkon` |
| Calculation | tie (2) | 100 % | `qwen3.8-4bit-omlx-r5-thinkon`, `qwen3.8-q3kxl-splash-r5-thinkon` |
| Code | tie (2) | 100 % | `qwen3.8-4bit-omlx-r5-thinkoff`, `qwen3.8-q3kxl-splash-r5-thinkoff` |
| Long context | tie (4) | 100 % | `qwen3.8-4bit-omlx-r5-thinkoff`, `qwen3.8-4bit-omlx-r5-thinkon`, `qwen3.8-q3kxl-splash-r5-thinkoff`, `qwen3.8-q3kxl-splash-r5-thinkon` |
| Abstention | tie (7) | 100 % | `ollama-coder-7b-r5-off`, `ollama-qwen35-9b-r5-off`, `ollama-qwen35-9b-r5-thinkon`, `qwen3.8-4bit-omlx-r5-thinkoff`, `qwen3.8-4bit-omlx-r5-thinkon`, `qwen3.8-q3kxl-splash-r5-thinkoff`, `qwen3.8-q3kxl-splash-r5-thinkon` |
| Extraction | tie (6) | 100 % | `ollama-qwen35-9b-r5-off`, `ollama-qwen35-9b-r5-thinkon`, `qwen3.8-4bit-omlx-r5-thinkoff`, `qwen3.8-4bit-omlx-r5-thinkon`, `qwen3.8-q3kxl-splash-r5-thinkoff`, `qwen3.8-q3kxl-splash-r5-thinkon` |

The decision compares only runs of the newest revision without infrastructure failures. When several tie for first, the row says so and names them: a tie is never broken by speed.

## Items that do not discriminate

| Item | Result | Reading |
|---|---|---|
| `abstain-telefono` | everyone passes | candidate for pruning or a harder variant |
| `es-formato-vinetas` | everyone passes | candidate for pruning or a harder variant |

## Gates

- All runs pass the gates.
