# Quant Research Index

Quant finance resource index — papers, repos, whitepapers, blogs, textbooks — aggregated from arxiv, awesome-lists, institutional research, and a one-time seed-curation pass.

## What's in here

| Path | Purpose |
|---|---|
| `index_builder.py` | Pipeline: 5-tier scraper, dedupe, writers |
| `data/quant_index.json` | **2870 unique resources** — source of truth |
| `data/quant_index.xlsx` | Same data, Excel view with 7 sheets (All_Deduped + per-source) |
| `docs/INDEX_SUMMARY.md` | Per-source row counts, date ranges, known gaps |
| `docs/AUDIT_PROMPTS.md` | 9 fresh-chat verification prompts |
| `docs/COST_BREAKDOWN.md` | Two-part cost ref: (1) scaling this index, (2) R2 + Neon pricing for Symbols Terminal |
| `docs/DATA_COLLECTION.md` | On-demand RAG-style retrieval — 5 layers, need-to-know access |
| `docs/DOMAIN_EXPANSION.md` | Growing the index 10× via OpenAlex + citation graph + new modalities |
| `docs/EQUITY_REPORTS_PLAN.md` | Plan for collecting SEC filings + earnings/IR content |
| `docs/TEXTBOOKS.md` | Curated canonical quant textbooks not in the index |
| `docs/FINANCE_BOOK_REPOS.md` | GitHub repos that bundle finance/trading book PDFs + retrieval (sparse-checkout) instructions |
| `docs/EXTRACTION_NOTES.md` | Notes on the seed-curation HAR extraction pass |
| `legacy/` | Generic IG-HAR extraction toolkit (`extract_images.py`, `extraction.py`) — usable on any Instagram HAR capture |

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
| Seeds | Cached one-time IG-HAR curation pass (rows live in JSON, no live fetcher) | 60 |
| Tier 1 | `awesome-quant` + `firmai/financial-machine-learning` + `cbailes/awesome-deep-trading` | 695 |
| Tier 2 | arxiv q-fin (TR/PM/ST/CP/RM/MF/PR) + Semantic Scholar citations | 1096 |
| Tier 3 | AQR, Man Institute, Fed FEDS Notes, BIS (via RePEc) | 246 |
| Tier 4 | SSRN top-ten | 0 (Cloudflare-blocked; documented) |
| Tier 5 | QuantStart, Robot Wealth, Hudson & Thames | 388 |

Details on gaps (paperswithcode dead, SSRN blocked, Alpha Architect/Two Sigma dropped) live in `docs/INDEX_SUMMARY.md`.

## Prerequisites

```bash
pip install requests openpyxl feedparser beautifulsoup4 lxml
```

## Legacy IG-HAR toolkit (optional, generic)

If you ever want to seed a future curation pass from a different Instagram account, point these at a fresh HAR:

```bash
brew install tesseract
cd legacy/
HAR_PATH=/path/to/instagram.har OUT_DIR=/path/to/work python3 extract_images.py   # 1. HAR → image dedupe
# 2. OCR:
ls "$OUT_DIR"/igimgs/*.jpg | xargs -P 8 -I{} sh -c \
  'f="{}"; b=$(basename "$f" .jpg); \
   [ -f "ocr_txt/$b.txt" ] || tesseract "$f" "ocr_txt/$b" -l eng --psm 6 --oem 1'
python3 extraction.py              # 3. regex + known-entity extraction
```

Output is a free-form set of paper/repo candidates; manual curation into the index is up to you.

## Most-mentioned resources (from seed pass)

| Repo | Stars | Seed-pass posts |
|---|---:|---:|
| OpenBB-finance/OpenBBTerminal | 66K | 72+ |
| jpmorganchase/python-training | 13K | 22+ |
| tensortrade-org/tensortrade | 6K | 19+ |
| dcajasn/Riskfolio-Lib | 4K | 16+ |
| polakowo/vectorbt | 7K | 13+ |
