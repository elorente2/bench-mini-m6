# Vision by model

Apple M6 · 34.4 GB · vision suite revision 3 · 2 runs · temperature 0

> 3 runs from older revisions are left out of the table: the vision suite changes its items, and revisions are never compared.

## Accuracy per image

| Model / engine | vision-conteo | vision-color | vision-posicion | vision-total | vision-digito | vision-solape | vision-cuentanueve | vision-digitos | Total |
|---|---|---|---|---|---|---|---|---:|
| `ollama-qwen35-9b-vision` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | 8/8 (100 %) |
| `qwen3.8-q3kxl-splash-vision` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | 8/8 (100 %) |

## Runs

| Run | Model | Engine | Size |
|---|---|---|---:|
| `ollama-qwen35-9b-vision` | `qwen3.5-9b-vision:latest` | Ollama (native tag) ollama version is 0.40.14 | 320 px |
| `qwen3.8-q3kxl-splash-vision` | `unsloth/Qwen3.8-27B-GGUF:UD-Q3_K_XL` | Splash 1.5.0 | 320 px |

## Answers

| Run | Image | Correct | Answer |
|---|---|---|---|
| `ollama-qwen35-9b-vision` | `vision-conteo` | ✓ | 3 |
| `ollama-qwen35-9b-vision` | `vision-color` | ✓ | Verde |
| `ollama-qwen35-9b-vision` | `vision-posicion` | ✓ | derecha |
| `ollama-qwen35-9b-vision` | `vision-total` | ✓ | 4 |
| `ollama-qwen35-9b-vision` | `vision-digito` | ✓ | 6 |
| `ollama-qwen35-9b-vision` | `vision-solape` | ✓ | rojo |
| `ollama-qwen35-9b-vision` | `vision-cuentanueve` | ✓ | 9 |
| `ollama-qwen35-9b-vision` | `vision-digitos` | ✓ | 417 |
| `qwen3.8-q3kxl-splash-vision` | `vision-conteo` | ✓ | 3 |
| `qwen3.8-q3kxl-splash-vision` | `vision-color` | ✓ | verde |
| `qwen3.8-q3kxl-splash-vision` | `vision-posicion` | ✓ | derecha |
| `qwen3.8-q3kxl-splash-vision` | `vision-total` | ✓ | 4 |
| `qwen3.8-q3kxl-splash-vision` | `vision-digito` | ✓ | 6 |
| `qwen3.8-q3kxl-splash-vision` | `vision-solape` | ✓ | rojo |
| `qwen3.8-q3kxl-splash-vision` | `vision-cuentanueve` | ✓ | 9 |
| `qwen3.8-q3kxl-splash-vision` | `vision-digitos` | ✓ | 417 |

Images are generated in code and their hash is stored in the result, so a wrong grade is a model or generator bug, never a file somebody replaced.
