# @quantscience_ Instagram Extraction — Summary

**Date:** 2026-04-22
**Source:** HAR capture of @quantscience_ Instagram profile (288MB, 1298 entries)

## Totals

- **22 research papers** (14 high-confidence, 6 medium, 2 low)
- **39 GitHub repos** (33 verified via GitHub API, 1 could not verify, 5 unverified URLs)
- **1219 unique images** extracted, OCR'd with Tesseract

## Top resources by post frequency

| Resource | Type | Approx. post count |
|---|---|---|
| OpenBBTerminal | Repo | 72+ |
| jpmorganchase/python-training | Repo | 22+ |
| TensorTrade | Repo | 19+ |
| Riskfolio-Lib | Repo | 16+ |
| vectorbt | Repo | 13+ |
| Financial Statement Analysis with LLMs (Kim et al.) | Paper | 6+ |
| A First Look at Financial Data Analysis Using ChatGPT-4o | Paper | 5+ (with SSRN link) |
| The Alchemy of Multibagger Stocks | Paper | 5+ |
| Microsoft qlib | Repo | 5+ |
| Using Mathematics to Make Money (Jim Simons) | Paper | 4+ |

Account reposts the same content regularly (same post text, different timestamps months apart). This inflates counts but confirms these are their "greatest hits."

## Notable findings

**Papers:**
- Heavy lean toward LLM-for-finance papers (6/22), followed by classic quant papers (pairs trading, momentum, factor investing).
- Jim Simons' "Using Mathematics to Make Money" (8-page lecture transcript) is reposted frequently — short, legendary author, high engagement bait.
- The "Breaking the Trend" paper (arXiv:2504.10914) by Sebastien Valeyre was the most recently published quant paper found.
- The "A Practical Guide to Quantitative Volatility Trading" (SSRN-2715517, 327 pages) by Daniel Bloch is the longest resource referenced.
- Account has started sharing non-finance AI papers (Context Engineering 2.0, Teaching LLMs to Plan, DeepSeek-R1) — audience pivot toward AI/LLM content.

**Repos:**
- ai-hedge-fund (virattt) and TradingAgents are the most viral repos featured (52-57K stars each).
- Heavy representation of Microsoft repos (qlib, RD-Agent, AI-For-Beginners, Data-Science-For-Beginners).
- Goldman Sachs gs-quant (10K stars) and JP Morgan python-training (13K stars) are the institutional standouts.
- Nanobot (MCP agent builder) and DSPy represent the LLM tooling wave entering quant content.

## Data quality notes

- **OCR garbled most URLs.** Instagram renders text as images, and Tesseract struggles with long URLs. Most GitHub repos were identified by name/context rather than clean URL extraction.
- **Heavy reposting.** The account reposts the same content every few months. Dedupe removed many duplicates but some may survive as slightly different OCR renderings.
- **Ziplime** — mentioned as "not Zipline" but GitHub URL could not be verified. Likely limex-ai/ziplime but repo may be private or renamed.
- **Julius** — julius-ai/julius returned 404. Repo may have been renamed or taken private.
- **Stock Research Agent** — no GitHub URL identified; described as built on LangGraph+LangSmith. Could not trace to a specific public repo.
- **Hook posts** that tease "Get it here" often show the paper/repo on slide 2+ of a carousel. Visual inspection recovered all 11 hook posts — they were either duplicates of already-extracted content or contained paper frontpages that could be identified visually.
- **Matt Dancho (@mdancho84)** content appears mixed in — the account reposts his threads. Papers from his posts are included since they appeared on the @quantscience_ feed.

## Method

1. Extracted 1219 unique images from HAR (filtered profile pics, thumbnails, <10KB icons)
2. OCR with Tesseract (psm 6, oem 1, 8 parallel workers)
3. Regex extraction for SSRN IDs, arXiv IDs, GitHub URLs, pip install patterns, known repo/author names
4. Visual inspection of 20+ hook posts and key images
5. GitHub API verification of all repo URLs (rate-limited, no auth)
6. Manual curation and deduplication of final dataset
