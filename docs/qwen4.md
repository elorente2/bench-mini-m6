# Qwen4 status (2026-11-16)

Short answer: **there are no open Qwen4 weights to run on this Mac**. The only
usable Qwen4 model is a cloud preview, and the open-weight 27B tier has not
been released.

## What exists

| Item | Status |
|---|---|
| `qwen4-max-preview` | Cloud preview since 2026-11-11, retired 2026-11-25. Token Plan / Qwen apps only. 1M context, text/image/video, up to 393,216 output tokens, thinking on by default, tools and structured outputs. No weights, model card, license or public per-token price. |
| Qwen4-Max (full) | No date. |
| Qwen4-Plus | Name announced; no weights, specs or date. |
| Qwen4-Flash | Name announced; no weights, specs or date. |
| Qwen4-27B | Open-weight tier announced; **no Hugging Face repository, no weights, no date**. |
| Qwen3.8-Flash-Next | Released 2026-08-28 as the architectural preview of Qwen4: a 125B MoE with 6B active parameters, a large n-gram/PLE memory layer, native image/video and 262K context extensible to 1M. It needs at least 32 GB with 1-bit weights and SSD offload; not a daily 32 GB model. |

The official Qwen Hugging Face organization has no Qwen4 repository. Several
community repositories use “Qwen4-27B” in their names, but they are not
official releases; some are unverified quantizations or have no weights. Do not
treat them as Qwen4.

## What this means for the 32 GB Mac mini

- **No local Qwen4 today.** The cloud preview cannot be served by Splash,
  Mirai/uzu, Ollama or llama.cpp.
- **Qwen3.8-27B remains the local generation to benchmark.** Splash V3.1 and
  Mirai/uzu are the current text leaders; the vision suite is covered by Splash.
- **Qwen3.8-Flash-Next** is the closest local Qwen4-architecture experiment,
  but its smallest quant is ~72.5 GB and needs SSD/PLE offload. It is not a
  daily driver on 32 GB.
- When Qwen4-27B weights appear, the same repository can add them as a new
  model label and a new eval revision; do not compare them against Qwen3.8
  results as if they were the same model.

## Sources

- Qwen Cloud release notes, 2026-11-11 and 2026-11-16.
- Public Qwen4-Max-Preview documentation (1M context, multimodal, Token Plan).
- Hugging Face API: `author=Qwen&search=Qwen4` returns no official model.
- Unsloth Qwen3.8-Flash-Next documentation (architecture preview).
