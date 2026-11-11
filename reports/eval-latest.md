# Precisión por modelo

Apple M6 (Mac18,5) · 34.4 GB · revisión de la suite 1 · 1 ejecuciones · temperatura 0

## Acierto por categoría

| Modelo / motor | Instrucciones | JSON | Herramientas | Cálculo | Código | Contexto largo | Abstención | Extracción | Total |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `qwen3.8-q3kxl-splash` | 3/3 (100 %) | 3/3 (100 %) | 2/2 (100 %) | 2/3 (67 %) | 3/3 (100 %) | 2/2 (100 %) | 2/2 (100 %) | 3/3 (100 %) | 20/21 (95 %) |

⚠ = ejecución no válida para decidir (ver la sección de puertas).

## Modelos y motores

| Ejecución | Modelo | Motor | Pensamiento | Cuantización |
|---|---|---|---|---|
| `qwen3.8-q3kxl-splash` | `unsloth/Qwen3.8-27B-GGUF:UD-Q3_K_XL` | Splash 1.5.0 | no | Q3_K_XL (~3-bit) |

## Coste

| Ejecución | Ítems | Minutos | Prompt máx (tokens) | Ítem más lento |
|---|---:|---:|---:|---:|
| `qwen3.8-q3kxl-splash` | 21 | 1.9 | 24574 | 64.4 s |

## Decisión por tarea

| Tarea | Mejor | Acierto | Empate técnico |
|---|---|---:|---|
| Instrucciones | `qwen3.8-q3kxl-splash` | 100 % | — |
| JSON | `qwen3.8-q3kxl-splash` | 100 % | — |
| Herramientas | `qwen3.8-q3kxl-splash` | 100 % | — |
| Cálculo | `qwen3.8-q3kxl-splash` | 67 % | — |
| Código | `qwen3.8-q3kxl-splash` | 100 % | — |
| Contexto largo | `qwen3.8-q3kxl-splash` | 100 % | — |
| Abstención | `qwen3.8-q3kxl-splash` | 100 % | — |
| Extracción | `qwen3.8-q3kxl-splash` | 100 % | — |

La decisión solo compara ejecuciones con la misma revisión y sin fallos de infraestructura. Un empate incluye todas las que empatan en la primera posición.

## Puertas

- Todas las ejecuciones pasan las puertas.
