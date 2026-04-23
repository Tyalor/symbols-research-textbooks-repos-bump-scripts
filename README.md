# symbols-research-textbooks-repos-bump-scripts

Quant finance resource index — papers, repos, whitepapers, blogs — aggregated from arxiv, awesome-lists, institutional research, and the **@quantscience_** Instagram curation pass.

## What's in here

| Path | Purpose |
|---|---|
| `quant_index.json` | **2384 unique resources** — source of truth (1.7 MB) |
| `quant_index.xlsx` | Same data, Excel workbook with 7 sheets (All_Deduped + per-source) |
| `index_builder.py` | Pipeline: loads seeds, scrapes 5 tiers of sources, dedupes, writes outputs |
| `data/quantscience_findings.xlsx` | Seed data (22 papers + 39 repos from the HAR extraction) |
| `docs/COST_BREAKDOWN.md` | Storage/compute/hosting costs for scaling this out |
| `docs/INDEX_SUMMARY.md` | Per-source row counts, date ranges, known gaps |
| `docs/AUDIT_PROMPTS.md` | 9 standalone prompts for fresh-chat verification |
| `docs/EXTRACTION_NOTES.md` | Notes on the original HAR extraction pass (data quality, methodology) |
| `legacy/` | Previous-session HAR tooling (`extraction.py`, `extract_images.py`, `build_excel.py`) |

## Running the pipeline

```bash
# Full rebuild (all tiers, ~20 min; S2 citations dominate)
python3 index_builder.py

# Cache-only regeneration of outputs (~5 s)
python3 -c "import index_builder as ib; ib.RUN={k: False for k in ib.RUN}; ib.main([])"

# Refresh just one tier (example: blogs)
python3 -c "import index_builder as ib; ib.RUN={k: False for k in ib.RUN}; ib.RUN['tier5_blogs']=True; ib.main([])"
```

Flip flags in the `RUN` dict at the top of `index_builder.py` to enable/disable tiers per run. Disabled tiers reuse cached data from the existing `quant_index.json`.

## Sources wired in

| Tier | Source | Current row count |
|---|---|---:|
| Seeds | `data/quantscience_findings.xlsx` | 60 |
| Tier 1 | `awesome-quant` + `firmai/financial-machine-learning` | 608 |
| Tier 2 | arxiv q-fin (TR/PM/ST/CP/RM/MF/PR) + Semantic Scholar citations | 1096 |
| Tier 3 | AQR, Man Institute, Fed FEDS Notes, BIS (via RePEc) | 246 |
| Tier 4 | SSRN top-ten | 0 (Cloudflare-blocked; documented) |
| Tier 5 | QuantStart, Robot Wealth, Hudson & Thames | 388 |

Details on gaps (paperswithcode dead, SSRN blocked, Alpha Architect/Two Sigma dropped) live in `docs/INDEX_SUMMARY.md`.

## Prerequisites

```bash
pip install requests openpyxl feedparser beautifulsoup4 lxml
```

## Legacy pipeline (seed xlsx regeneration only)

Only relevant if you're re-extracting from a fresh Instagram HAR capture:

```bash
brew install tesseract
cd legacy/
python3 extract_images.py          # 1. HAR → image dedupe
# 2. OCR:
ls igimgs/*.jpg | xargs -P 8 -I{} sh -c \
  'f="{}"; b=$(basename "$f" .jpg); \
   [ -f "ocr_txt/$b.txt" ] || tesseract "$f" "ocr_txt/$b" -l eng --psm 6 --oem 1'
python3 extraction.py              # 3. regex + known-entity extraction
python3 build_excel.py             # 4. curated xlsx
# Move resulting xlsx into ../data/ to feed index_builder.py
```

## Most-mentioned resources (from seed curator)

| Repo | Stars | Curator posts |
|---|---:|---:|
| OpenBB-finance/OpenBBTerminal | 66K | 72+ |
| jpmorganchase/python-training | 13K | 22+ |
| tensortrade-org/tensortrade | 6K | 19+ |
| dcajasn/Riskfolio-Lib | 4K | 16+ |
| polakowo/vectorbt | 7K | 13+ |
