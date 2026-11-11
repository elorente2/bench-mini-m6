# Visión por modelo

Apple M6 · 34.4 GB · revisión de la suite de visión 3 · 2 ejecuciones · temperatura 0

> 3 ejecuciones de revisiones anteriores quedan fuera de la tabla: la suite de visión cambia de ítems y no se comparan entre revisiones.

## Acierto por imagen

| Modelo / motor | vision-conteo | vision-color | vision-posicion | vision-total | vision-digito | vision-solape | vision-cuentanueve | vision-digitos | Total |
|---|---|---|---|---|---|---|---|---:|
| `ollama-qwen35-9b-vision` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | 8/8 (100 %) |
| `qwen3.8-q3kxl-splash-vision` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | 8/8 (100 %) |

## Ejecuciones

| Ejecución | Modelo | Motor | Tamaño |
|---|---|---|---:|
| `ollama-qwen35-9b-vision` | `qwen3.5-9b-vision:latest` | Ollama (native tag) ollama version is 0.40.14 | 320 px |
| `qwen3.8-q3kxl-splash-vision` | `unsloth/Qwen3.8-27B-GGUF:UD-Q3_K_XL` | Splash 1.5.0 | 320 px |

## Respuestas

| Ejecución | Imagen | Acierto | Respuesta |
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

Las imágenes se generan con código y su hash queda en el resultado, así que una nota solo puede ser un fallo del modelo o del generador, nunca de un fichero que alguien cambió.
