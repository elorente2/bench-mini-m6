# Precisión por modelo

Apple M6 (Mac18,5) · 34.4 GB · revisión de la suite 1, 2, 3, 4, 5 · 13 ejecuciones · temperatura 0

> Aviso: hay resultados de revisiones distintas. No se comparan entre sí ni entran en la decisión final.

## Acierto por categoría

| Modelo / motor | Instrucciones | JSON | Herramientas | Arquitectura | Cálculo | Código | Contexto largo | Abstención | Extracción | Total |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
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

⚠ = ejecución no válida para decidir (ver la sección de puertas).

## Modelos y motores

| Ejecución | Modelo | Motor | Pensamiento | Cuantización | Contexto máx |
|---|---|---|---|---|---:|
| `qwen3.8-4bit-omlx-r3-thinkoff` | `Qwen3.8-27B-4bit` | oMLX 0.7.3 | no | 4-bit MLX | 262,144 |
| `qwen3.8-4bit-omlx-r3-thinkon` | `Qwen3.8-27B-4bit` | oMLX 0.7.3 | sí | 4-bit MLX | 262,144 |
| `qwen3.8-4bit-omlx-r5-thinkoff` | `Qwen3.8-27B-4bit` | oMLX 0.7.3 | no | 4-bit MLX | 262,144 |
| `qwen3.8-4bit-omlx-r5-thinkon` | `Qwen3.8-27B-4bit` | oMLX 0.7.3 | sí | 4-bit MLX | 262,144 |
| `qwen3.8-q3kxl-splash` | `unsloth/Qwen3.8-27B-GGUF:UD-Q3_K_XL` | Splash 1.5.0 | no | Q3_K_XL (~3-bit) | 217,081 |
| `qwen3.8-q3kxl-splash-r2-thinkoff` | `unsloth/Qwen3.8-27B-GGUF:UD-Q3_K_XL` | Splash 1.5.0 | no | Q3_K_XL (~3-bit) | 217,081 |
| `qwen3.8-q3kxl-splash-r2-thinkon` | `unsloth/Qwen3.8-27B-GGUF:UD-Q3_K_XL` | Splash 1.5.0 | sí | Q3_K_XL (~3-bit) | 217,081 |
| `qwen3.8-q3kxl-splash-r3-thinkoff` | `unsloth/Qwen3.8-27B-GGUF:UD-Q3_K_XL` | Splash 1.5.0 | no | Q3_K_XL (~3-bit) | 217,081 |
| `qwen3.8-q3kxl-splash-r3-thinkon` | `unsloth/Qwen3.8-27B-GGUF:UD-Q3_K_XL` | Splash 1.5.0 | sí | Q3_K_XL (~3-bit) | 217,081 |
| `qwen3.8-q3kxl-splash-r4-thinkoff` | `unsloth/Qwen3.8-27B-GGUF:UD-Q3_K_XL` | Splash 1.5.0 | no | Q3_K_XL (~3-bit) | 217,081 |
| `qwen3.8-q3kxl-splash-r4-thinkon` | `unsloth/Qwen3.8-27B-GGUF:UD-Q3_K_XL` | Splash 1.5.0 | sí | Q3_K_XL (~3-bit) | 217,081 |
| `qwen3.8-q3kxl-splash-r5-thinkoff` | `unsloth/Qwen3.8-27B-GGUF:UD-Q3_K_XL` | Splash 1.5.0 | no | Q3_K_XL (~3-bit) | 217,081 |
| `qwen3.8-q3kxl-splash-r5-thinkon` | `unsloth/Qwen3.8-27B-GGUF:UD-Q3_K_XL` | Splash 1.5.0 | sí | Q3_K_XL (~3-bit) | 217,081 |

El contexto máximo es el que declara la API del motor; `*` marca el que sale de la configuración porque la API no lo informa. No es una medida de recuperación: eso lo dicen los ítems de contexto largo con su prompt real.

## Coste

| Ejecución | Ítems | Minutos | Truncados | Prompt máx (tokens) | Cobertura del contexto | Ítem más lento |
|---|---:|---:|---:|---:|---:|---:|
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

La cobertura es la parte del contexto máximo que se ejercita de verdad: el prompt más largo de la suite dividido por el contexto que declara el motor. Una cobertura baja no dice que el resto del contexto falle; dice que este piloto no lo ha probado.

## Decisión por tarea

| Tarea | Mejor | Acierto | Empatan en el primer puesto |
|---|---|---:|---|
| Instrucciones | empate (4) | 100 % | `qwen3.8-4bit-omlx-r5-thinkoff`, `qwen3.8-4bit-omlx-r5-thinkon`, `qwen3.8-q3kxl-splash-r5-thinkoff`, `qwen3.8-q3kxl-splash-r5-thinkon` |
| JSON | empate (2) | 100 % | `qwen3.8-4bit-omlx-r5-thinkon`, `qwen3.8-q3kxl-splash-r5-thinkon` |
| Herramientas | empate (4) | 100 % | `qwen3.8-4bit-omlx-r5-thinkoff`, `qwen3.8-4bit-omlx-r5-thinkon`, `qwen3.8-q3kxl-splash-r5-thinkoff`, `qwen3.8-q3kxl-splash-r5-thinkon` |
| Arquitectura | empate (2) | 100 % | `qwen3.8-4bit-omlx-r5-thinkon`, `qwen3.8-q3kxl-splash-r5-thinkon` |
| Cálculo | empate (2) | 100 % | `qwen3.8-4bit-omlx-r5-thinkon`, `qwen3.8-q3kxl-splash-r5-thinkon` |
| Código | empate (2) | 100 % | `qwen3.8-4bit-omlx-r5-thinkoff`, `qwen3.8-q3kxl-splash-r5-thinkoff` |
| Contexto largo | empate (4) | 100 % | `qwen3.8-4bit-omlx-r5-thinkoff`, `qwen3.8-4bit-omlx-r5-thinkon`, `qwen3.8-q3kxl-splash-r5-thinkoff`, `qwen3.8-q3kxl-splash-r5-thinkon` |
| Abstención | empate (4) | 100 % | `qwen3.8-4bit-omlx-r5-thinkoff`, `qwen3.8-4bit-omlx-r5-thinkon`, `qwen3.8-q3kxl-splash-r5-thinkoff`, `qwen3.8-q3kxl-splash-r5-thinkon` |
| Extracción | empate (4) | 100 % | `qwen3.8-4bit-omlx-r5-thinkoff`, `qwen3.8-4bit-omlx-r5-thinkon`, `qwen3.8-q3kxl-splash-r5-thinkoff`, `qwen3.8-q3kxl-splash-r5-thinkon` |

La decisión solo compara ejecuciones de la revisión más reciente y sin fallos de infraestructura. Si varias empatan en el primer puesto, la fila lo dice y las nombra: el empate no se rompe por velocidad.

## Ítems que no discriminan

| Ítem | Resultado | Lectura |
|---|---|---|
| `abstain-telefono` | todos aciertan | candidato a poda o a subir dificultad |
| `es-formato-vinetas` | todos aciertan | candidato a poda o a subir dificultad |
| `extract-factura` | todos aciertan | candidato a poda o a subir dificultad |
| `json-pedido` | todos aciertan | candidato a poda o a subir dificultad |
| `needle-24k` | todos aciertan | candidato a poda o a subir dificultad |
| `tool-orden` | todos aciertan | candidato a poda o a subir dificultad |
| `tool-tiempo` | todos aciertan | candidato a poda o a subir dificultad |

## Puertas

- Todas las ejecuciones pasan las puertas.
