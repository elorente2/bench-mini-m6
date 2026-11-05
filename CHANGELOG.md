# Changelog

## 0.1.0 — 2026-11-05

- Initial benchmark harness for OpenAI-compatible local engines.
- Suite revision 5: short decode, cold 18K prefill, validated prefix-cache
  extension with 128-token long-context decode.
- Splash 1.5.0 and Mirai/uzu 0.6.17 clean results on Mac mini M6 32 GB.
- Ollama 0.40.14 native (`qwen3.8:27b`, nvfp4) and imported Q3_K_XL results,
  both at 32K context with thinking disabled.
- Schema-1 results, validation, Markdown report and legacy import.
- MIT license.
