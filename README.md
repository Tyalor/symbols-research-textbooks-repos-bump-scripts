# symbols-research-textbooks-repos-bump-scripts

Curated index of quant finance research papers, GitHub repos, textbooks, and Python libraries extracted from the **@quantscience_** Instagram account.

## What's in here

| File | Description |
|---|---|
| `quantscience_findings.xlsx` | **22 research papers + 39 GitHub repos** — deduplicated, verified, with confidence scores |
| `SUMMARY.md` | Data quality notes, top resources by post frequency, methodology |
| `extraction_results.json` | Raw extraction output (pre-curation) |

## Scripts (pipeline)

These scripts form a reproducible pipeline for extracting resources from an Instagram HAR capture:

| Script | Step | Description |
|---|---|---|
| `extract_images.py` | 1 | Extract unique post images from a HAR file (filters thumbnails, profile pics, dedupes by content hash) |
| `extraction.py` | 2 | OCR text mining — regex extraction for arXiv IDs, SSRN IDs, GitHub URLs, pip install patterns, known author/repo names |
| `build_excel.py` | 3 | Curated dataset assembly + GitHub API verification + Excel output with formatted sheets |

### Running the pipeline

```bash
# Prerequisites
brew install tesseract
pip install openpyxl

# 1. Extract images from HAR
python3 extract_images.py

# 2. OCR (requires tesseract)
mkdir -p ocr_txt
ls igimgs/*.jpg | xargs -P 8 -I{} sh -c \
  'f="{}"; b=$(basename "$f" .jpg); \
   [ -f "ocr_txt/$b.txt" ] || tesseract "$f" "ocr_txt/$b" -l eng --psm 6 --oem 1 2>/dev/null'

# 3. Extract signals from OCR
python3 extraction.py

# 4. Build verified Excel
python3 build_excel.py
```

## Top resources found

### Most-posted repos (by curator repost frequency)
| Repo | Stars | Posts |
|---|---|---|
| OpenBB-finance/OpenBBTerminal | 66K | 72+ |
| jpmorganchase/python-training | 13K | 22+ |
| tensortrade-org/tensortrade | 6K | 19+ |
| dcajasn/Riskfolio-Lib | 4K | 16+ |
| polakowo/vectorbt | 7K | 13+ |

### Most-posted papers
| Paper | Posts |
|---|---|
| Financial Statement Analysis with LLMs (Kim et al.) | 6+ |
| The Alchemy of Multibagger Stocks | 5+ |
| A First Look at Financial Data Analysis Using ChatGPT-4o | 5+ |
| Using Mathematics to Make Money (Jim Simons) | 4+ |
| Breaking the Trend: How to Avoid Cherry-Picked Signals | 3+ |

## Methodology

1. Captured @quantscience_ Instagram profile with browser DevTools (HAR with response bodies)
2. Extracted 1219 unique images from the 288MB HAR file
3. OCR'd all images with Tesseract (psm 6, oem 1, 8 parallel workers)
4. Regex + known-entity extraction from OCR text
5. Visual inspection of 20+ "hook" posts (teaser captions hiding the resource on carousel slide 2+)
6. GitHub API verification of all repo URLs
7. Manual curation and deduplication
