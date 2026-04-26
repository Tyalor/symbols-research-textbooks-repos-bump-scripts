# Quant Research Index

Quant finance resource index — papers, repos, whitepapers, blogs — aggregated from arxiv, awesome-lists, institutional research, and the **@quantscience_** Instagram curation pass.

## What's in here

| Path | Purpose |
|---|---|
| `index_builder.py` | Pipeline: 5-tier scraper, dedupe, writers |
| `data/quant_index.json` | **2783 unique resources** — source of truth |
| `data/quant_index.xlsx` | Same data, Excel view with 7 sheets (All_Deduped + per-source) |
| `docs/INDEX_SUMMARY.md` | Per-source row counts, date ranges, known gaps |
| `docs/AUDIT_PROMPTS.md` | 9 fresh-chat verification prompts |
| `docs/COST_BREAKDOWN.md` | Two-part cost ref: (1) scaling this index, (2) R2 + Neon pricing for Symbols Terminal |
| `docs/DATA_COLLECTION.md` | On-demand RAG-style retrieval — 5 layers, need-to-know access |
| `docs/DOMAIN_EXPANSION.md` | Growing the index 10× via OpenAlex + citation graph + new modalities |
| `docs/EQUITY_REPORTS_PLAN.md` | Plan for collecting SEC filings + earnings/IR content |
| `docs/TEXTBOOKS.md` | Curated canonical quant textbooks not in the index |
| `docs/EXTRACTION_NOTES.md` | Notes on the original HAR extraction pass |
| `legacy/` | Previous-session HAR tooling + `quantscience_findings.xlsx` (seed data now fully absorbed into `data/quant_index.json` with source=`quantscience_ig`) |

## Running the pipeline

```bash
# Full rebuild (all tiers, ~20 min; S2 citations dominate)
python3 index_builder.py

# Cache-only regeneration of outputs (~5 s)
python3 -c "import index_builder as ib; ib.RUN={k: False for k in ib.RUN}; ib.main([])"

# Refresh just one tier (example: blogs)
python3 -c "import index_builder as ib; ib.RUN={k: False for k in ib.RUN}; ib.RUN['tier5_blogs']=True; ib.main([])"
```

Flip flags in the `RUN` dict at the top of `index_builder.py` to enable/disable tiers per run. Disabled tiers reuse cached data from the existing `data/quant_index.json`. Output rows in both json and xlsx are grouped alphabetically by type, then title.

## Sources wired in

| Tier | Source | Current row count |
|---|---|---:|
| Seeds | `legacy/quantscience_findings.xlsx` (absorbed into main index) | 60 |
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
# Resulting xlsx stays in legacy/; index_builder.py reads it from there.
```

## Most-mentioned resources (from seed curator)

| Repo | Stars | Curator posts |
|---|---:|---:|
| OpenBB-finance/OpenBBTerminal | 66K | 72+ |
| jpmorganchase/python-training | 13K | 22+ |
| tensortrade-org/tensortrade | 6K | 19+ |
| dcajasn/Riskfolio-Lib | 4K | 16+ |
| polakowo/vectorbt | 7K | 13+ |
