# Vision suite

The text suite asks whether a model knows. This one asks whether it **sees**, and
it lives in its own table because the answer says nothing about text quality.

## Why fixtures are generated, not photographed

Every image is drawn in `bench/vision/png.py` with the standard library: an
8-bit truecolour PNG is a signature plus length-tagged chunks with a CRC, and
`zlib` does the compression. That buys three things:

- **No binary files in the repository.** The image is a function of the code.
- **The expected answer cannot drift.** The same builder that paints three red
  circles writes `expect=("3",)`.
- **Traceability.** Each result records the image `sha256`, so a wrong grade
  points at the builder, not at a file someone replaced.

## Items (revision 3)

| Item | Question | Answer |
|---|---|---|
| `vision-conteo` | Red circles among blue squares | `3` |
| `vision-color` | Which band has more area, green or yellow | `verde` |
| `vision-posicion` | Is the blue circle left or right of the red square | `derecha` |
| `vision-total` | Total shapes, any colour | `4` |
| `vision-digito` | Seven-segment digit | `6` |
| `vision-solape` | Colour visible at the centre of two overlapping circles | `rojo` |
| `vision-cuentanueve` | Count nine scattered small circles | `9` |
| `vision-digitos` | Three seven-segment digits | `417` |

Grading is the same code-only rule as the text suite: the answer is compared
after NFKC, case folding and trailing punctuation removal. No judge, no model.

## Results — revision 3

| Run | Model | Engine | Score |
|---|---|---|---:|
| `qwen3.8-q3kxl-splash-vision` | Qwen3.8-27B UD-Q3_K_XL | Splash 1.5.0 | 8/8 |
| `ollama-qwen35-9b-vision` | Qwen3.5-9B UD-Q4_K_XL + mmproj | Ollama 0.40.14 | 8/8 |

Both models read the seven-segment number, count nine scattered circles and get
the occluded centre right. **Vision is not a differentiator on these items**, and
the honest reading is that synthetic shapes are too easy for models of this
generation, not that the two are equal on real images.

The 9B reaches vision without a download: Ollama imports the GGUF that sits on
disk for Splash with a Modelfile that has two `FROM` lines, the model and the
`mmproj` projector.

## Limits

- **Synthetic only.** No photographs, handwriting, charts, tables, screenshots or
  PDFs. Those are where vision actually fails, and they need real fixtures with a
  known answer, which means either a small curated set committed on purpose or a
  generator that can draw them.
- **No generation.** Image and video models are a different runtime and a
  different question. Their table can only report speed and memory: quality
  cannot be graded by code, and this repository does not use a model as a judge.
- **One image per item**, 320 px square, no rotation or noise.
- **Splash runs vision only for its supported architectures** (Qwen3.8-27B among
  them); the Qwen3.5-9B projector is used through Ollama instead.

## Commands

```bash
make vision ENGINE=splash
make vision-report

# One item while debugging a fixture.
.venv/bin/python -m bench.cli vision splash --item vision-digito
```

Results live in `results/vision/` and the table in `reports/vision-latest.md`.
Only the newest `[vision].revision` is compared; older runs stay on disk as
history.
