# Reports

Generated Markdown comparisons. Rebuild them from the committed results:

```bash
make report
# or
.venv/bin/python -m bench.cli report results/*.json --out reports/latest.md
```

- `latest.md` is overwritten by `make report` and `run-all --report`.
- Dated files such as `2026-11-m6.md` are snapshots kept with the result set.

Do not edit generated reports by hand; fix the JSON or the renderer and
regenerate.
