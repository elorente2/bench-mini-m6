# Accuracy revision 6 — Mirai vs Splash V3.1

Apple M6 (Mac18,5) · 34.4 GB · suite revision 6 · 4 runs · temperature 0

## Accuracy by category

| Model / engine | Instructions | JSON | Tools | Architecture | Calculation | Code | Long context | Abstention | Extraction | Total |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `mirai-qwen3.8-27b-r6-off` | 2/2 (100 %) | 1/3 (33 %) | 1/3 (33 %) | 3/3 (100 %) | 1/3 (33 %) | 5/5 (100 %) | 3/3 (100 %) | 2/2 (100 %) | 2/2 (100 %) | 20/26 (77 %) |
| `mirai-qwen3.8-27b-r6-thinkon` | 2/2 (100 %) | 3/3 (100 %) | 1/3 (33 %) | 3/3 (100 %) | 3/3 (100 %) | 5/5 (100 %) | 3/3 (100 %) | 2/2 (100 %) | 2/2 (100 %) | 24/26 (92 %) |
| `qwen3.8-q3kxl-v31-r6-off` | 2/2 (100 %) | 1/3 (33 %) | 1/3 (33 %) | 3/3 (100 %) | 1/3 (33 %) | 5/5 (100 %) | 3/3 (100 %) | 2/2 (100 %) | 2/2 (100 %) | 20/26 (77 %) |
| `qwen3.8-q3kxl-v31-r6-thinkon` | 2/2 (100 %) | 3/3 (100 %) | 1/3 (33 %) | 3/3 (100 %) | 3/3 (100 %) | 5/5 (100 %) | 3/3 (100 %) | 2/2 (100 %) | 2/2 (100 %) | 24/26 (92 %) |

⚠ = run that cannot support a decision (see the gates section).

## Models and engines

| Run | Model | Engine | Thinking | Quantization | Max context |
|---|---|---|---|---|---:|
| `mirai-qwen3.8-27b-r6-off` | `alibaba:qwen3.8:27b:mirai:mirai-m:4` | Mirai / uzu cli 0.6.17 | off | 4-bit (Mirai M) | — |
| `mirai-qwen3.8-27b-r6-thinkon` | `alibaba:qwen3.8:27b:mirai:mirai-m:4` | Mirai / uzu cli 0.6.17 | on | 4-bit (Mirai M) | — |
| `qwen3.8-q3kxl-v31-r6-off` | `unsloth/Qwen3.8-27B-GGUF:UD-Q3_K_XL` | Splash 1.5.0 | off | Q3_K_XL (~3-bit) | 217,081 |
| `qwen3.8-q3kxl-v31-r6-thinkon` | `unsloth/Qwen3.8-27B-GGUF:UD-Q3_K_XL` | Splash 1.5.0 | on | Q3_K_XL (~3-bit) | 217,081 |

Max context is what the engine's API declares; `*` marks the value taken from the configuration because the API reports none. It is not a retrieval measure: the long-context items say that with their real prompt.

## Cost

| Run | Items | Minutes | Truncated | Max prompt (tokens) | Context coverage | Slowest item |
|---|---:|---:|---:|---:|---:|---:|
| `mirai-qwen3.8-27b-r6-off` | 26 | 3.5 | 0 | 65124 | — | 142.5 s |
| `mirai-qwen3.8-27b-r6-thinkon` | 26 | 7.5 | 0 | 65164 | — | 147.3 s |
| `qwen3.8-q3kxl-v31-r6-off` | 26 | 4.9 | 0 | 65124 | 30 % | 195.8 s |
| `qwen3.8-q3kxl-v31-r6-thinkon` | 26 | 11.2 | 0 | 65164 | 30 % | 197.7 s |

Coverage is the share of the declared window the suite actually exercises: the longest prompt divided by the engine's max context. Low coverage does not mean the rest of the window fails; it means this suite has not tried it.

## Decision by task

| Task | Best | Accuracy | Tied for first |
|---|---|---:|---|
| Instructions | tie (4) | 100 % | `mirai-qwen3.8-27b-r6-off`, `mirai-qwen3.8-27b-r6-thinkon`, `qwen3.8-q3kxl-v31-r6-off`, `qwen3.8-q3kxl-v31-r6-thinkon` |
| JSON | tie (2) | 100 % | `mirai-qwen3.8-27b-r6-thinkon`, `qwen3.8-q3kxl-v31-r6-thinkon` |
| Tools | tie (4) | 33 % | `mirai-qwen3.8-27b-r6-off`, `mirai-qwen3.8-27b-r6-thinkon`, `qwen3.8-q3kxl-v31-r6-off`, `qwen3.8-q3kxl-v31-r6-thinkon` |
| Architecture | tie (4) | 100 % | `mirai-qwen3.8-27b-r6-off`, `mirai-qwen3.8-27b-r6-thinkon`, `qwen3.8-q3kxl-v31-r6-off`, `qwen3.8-q3kxl-v31-r6-thinkon` |
| Calculation | tie (2) | 100 % | `mirai-qwen3.8-27b-r6-thinkon`, `qwen3.8-q3kxl-v31-r6-thinkon` |
| Code | tie (4) | 100 % | `mirai-qwen3.8-27b-r6-off`, `mirai-qwen3.8-27b-r6-thinkon`, `qwen3.8-q3kxl-v31-r6-off`, `qwen3.8-q3kxl-v31-r6-thinkon` |
| Long context | tie (4) | 100 % | `mirai-qwen3.8-27b-r6-off`, `mirai-qwen3.8-27b-r6-thinkon`, `qwen3.8-q3kxl-v31-r6-off`, `qwen3.8-q3kxl-v31-r6-thinkon` |
| Abstention | tie (4) | 100 % | `mirai-qwen3.8-27b-r6-off`, `mirai-qwen3.8-27b-r6-thinkon`, `qwen3.8-q3kxl-v31-r6-off`, `qwen3.8-q3kxl-v31-r6-thinkon` |
| Extraction | tie (4) | 100 % | `mirai-qwen3.8-27b-r6-off`, `mirai-qwen3.8-27b-r6-thinkon`, `qwen3.8-q3kxl-v31-r6-off`, `qwen3.8-q3kxl-v31-r6-thinkon` |

The decision compares only runs of the newest revision without infrastructure failures. When several tie for first, the row says so and names them: a tie is never broken by speed.

## Items that do not discriminate

| Item | Result | Reading |
|---|---|---|
| `abstain-telefono` | everyone passes | candidate for pruning or a harder variant |
| `abstain-version` | everyone passes | candidate for pruning or a harder variant |
| `arch-adr` | everyone passes | candidate for pruning or a harder variant |
| `arch-contradiccion` | everyone passes | candidate for pruning or a harder variant |
| `arch-tradeoff` | everyone passes | candidate for pruning or a harder variant |
| `code-js-normaliza` | everyone passes | candidate for pruning or a harder variant |
| `code-py-lru` | everyone passes | candidate for pruning or a harder variant |
| `code-py-permisos` | everyone passes | candidate for pruning or a harder variant |
| `code-py-ranges` | everyone passes | candidate for pruning or a harder variant |
| `code-py-sqlite` | everyone passes | candidate for pruning or a harder variant |
| `es-formato-vinetas` | everyone passes | candidate for pruning or a harder variant |
| `es-restricciones-triples` | everyone passes | candidate for pruning or a harder variant |
| `extract-factura` | everyone passes | candidate for pruning or a harder variant |
| `extract-traza` | everyone passes | candidate for pruning or a harder variant |
| `json-pedido` | everyone passes | candidate for pruning or a harder variant |
| `math-fecha` | everyone passes | candidate for pruning or a harder variant |
| `needle-24k` | everyone passes | candidate for pruning or a harder variant |
| `needle-64k-tokens` | everyone passes | candidate for pruning or a harder variant |
| `needle-dos` | everyone passes | candidate for pruning or a harder variant |
| `tool-agenda` | everyone fails | either a ceiling or a badly written item |
| `tool-orden` | everyone fails | either a ceiling or a badly written item |
| `tool-tiempo` | everyone passes | candidate for pruning or a harder variant |

## Gates

- All runs pass the gates.
