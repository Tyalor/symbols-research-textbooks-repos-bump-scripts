# Plan — Equity Reports Collection

Companion to `index_builder.py`. Different domain (per-ticker, per-filing) than the resource index, so it gets its own script and schema. This doc is a planning artifact; no code is committed yet.

---

## Scope — what "equity reports" means here

The term covers three fundamentally different bodies of content:

| Kind | Examples | Free? |
|---|---|---|
| **SEC filings** | 10-K, 10-Q, 8-K, DEF 14A, 13F, S-1, Form 4 | ✅ EDGAR is fully free + bulk-downloadable |
| **Earnings materials** | Press release, earnings call transcript, investor deck, supplemental | ⚠️ Free on company IR pages; transcripts sometimes paywalled |
| **Sell-side research** | Goldman BUY target on NVDA; Morgan Stanley model; JPM analyst note | ❌ Bloomberg / Refinitiv / FactSet / S&P CIQ only |

**Recommended scope for this repo:** kinds 1 and 2. Sell-side research is explicitly out — it's expensive, licensing-restricted, and not the kind of durable public data the resource index is built on. If you ever need analyst consensus, use Visible Alpha or Koyfin (both paid, but cheaper than Bloomberg).

---

## Sources tiered by usefulness

### Tier A — SEC EDGAR (the spine)

- **Full-text search API:** `https://efts.sec.gov/LATEST/search-index?q=...&forms=10-K`
- **Submissions API:** `https://data.sec.gov/submissions/CIK{cik}.json` — returns every filing ever made by a company
- **Company facts API:** `https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json` — normalized XBRL financials
- **Bulk archives:** `https://www.sec.gov/Archives/edgar/data/{cik}/{accession}/` — actual filing documents
- **Financial Statement Data Sets:** `https://www.sec.gov/dera/data/financial-statement-data-sets.html` — quarterly ZIPs of all filed XBRL facts
- **Rate limit:** SEC asks for a User-Agent with contact email + max 10 req/sec
- **Cost:** free
- **License:** public domain

### Tier B — Company IR pages

- Earnings press releases, 8-K attachments, investor presentation decks, annual reports (glossy PDF)
- No unified API; each site is a one-off scrape
- Rate limit: be polite (1/sec)
- Cost: free
- License: public; archival OK

### Tier C — Earnings call transcripts

- **SeekingAlpha** — free for recent; paywall for >30 days old
- **Motley Fool transcripts** — free, limited universe
- **Company IR pages** — some post transcripts directly (Amazon, Google, JPM do; most do not)
- **Refinitiv StreetEvents** — the paid gold standard; not in scope
- Realistic take: expect 40-60% coverage of S&P 500 transcripts from free sources; gaps in small-cap

### Tier D — Macro + sector data (context, not reports)

- **FRED** (stlouisfed.org) — free API, bulk download for all macro series
- **BLS** — employment, CPI, PPI; free API
- **Federal Reserve H-series** — H.4.1 balance sheet, H.6 money stock, etc.
- **Yahoo Finance CSVs** — quick OHLCV for any ticker; unofficial but works
- Already-indexed: Fed FEDS Notes (research-grade, different from raw data)

### Tier E — Aggregators with free tiers

- **Stockanalysis.com** — fundamentals, financials; ~5-year free lookback
- **Macrotrends** — charts + historical ratios
- **Finchat.io** — AI-over-filings; free tier limited queries
- **OpenFIGI** — free ticker/ISIN/CUSIP mapping (Bloomberg-owned but free API)
- **FMP (Financial Modeling Prep)** — free tier: 250 req/day; lots of endpoints
- **Polygon.io** — free tier: 5 req/min; EOD data

### Explicitly out of scope

Bloomberg Terminal ($2k/mo), Refinitiv Eikon/Workspace ($1.5k/mo), FactSet ($2-3k/mo), S&P Capital IQ ($1k+/mo), Morningstar Direct, Visible Alpha, Koyfin Pro. Also Quandl/Nasdaq Data Link's paid datasets.

---

## Ticker universe — scope decision

| Option | Count | Annual growth | 10-Ks × 10 yr | Total 10-Ks |
|---|---:|---:|---:|---:|
| S&P 100 | 100 | low | 100 × 10 = 1,000 | |
| S&P 500 | 500 | 5-10% turnover | 500 × 10 = 5,000 | |
| S&P 1500 | 1,500 | — | — | 15,000 |
| Russell 3000 | 3,000 | 5-10% | — | 30,000 |
| All SEC filers (US) | ~10,000+ | — | — | 100,000+ |

Recommended starting point: **S&P 500 × 10 years of 10-K/10-Q/8-K**. Already ~45,000 filings. Expand only when that's proven working.

For options-focused work (your stated context), consider narrowing further: the ~100 highest-option-volume tickers are more useful per-filing than the 500 S&P members.

---

## Schema proposal

Equity data doesn't fit the current `Resource` schema cleanly — it's per-ticker, per-fiscal-period, time-series. Two options:

### Option A — Extend existing schema (not recommended)
Add fields: `ticker`, `filing_type`, `period_of_report`, `cik`, `fiscal_year`. Works but bloats every row with nulls for the 2384 existing resources.

### Option B — Separate schema + table (recommended)

```python
@dataclass
class EquityFiling:
    filing_id: str          # SEC accession number (e.g., "0001193125-25-123456")
    ticker: str             # AAPL
    cik: str                # 0000320193
    company_name: str
    filing_type: str        # 10-K | 10-Q | 8-K | DEF 14A | 13F | S-1 | ...
    period_of_report: str   # YYYY-MM-DD (fiscal period end)
    filed_at: str           # YYYY-MM-DD (submission timestamp)
    fiscal_year: int
    fiscal_period: str      # FY | Q1 | Q2 | Q3 | Q4
    canonical_url: str      # link to the primary filing document
    secondary_urls: str     # comma-delimited; exhibits
    size_bytes: int
    has_xbrl: bool
    topic_tags: str         # auto-extracted: "tech", "regulated-utility", etc.
    retrieved_at: str
```

Separate from `Resource`. Lives in its own JSON/table: `data/equity_filings.json`. Index doesn't merge with `quant_index.json` — just cross-references by URL where a research paper happens to cite a specific filing.

---

## Schema for earnings materials (Tier B/C)

```python
@dataclass
class EarningsEvent:
    event_id: str           # sha1(ticker + period)
    ticker: str
    period_of_report: str   # fiscal period end
    call_date: str          # YYYY-MM-DD
    press_release_url: str
    transcript_url: str     # may be empty if only paywalled sources have it
    deck_url: str           # investor presentation PDF
    supplemental_url: str
    source: str             # ir-page | seekingalpha | motley-fool
    retrieved_at: str
```

---

## Ingestion approach

New script: `equity_fetcher.py`. Same config pattern as `index_builder.py`:

```python
RUN = {
    "sec_filings": True,
    "earnings_events": True,
    "ir_decks": False,          # slow; one-off scrapes per ticker
    "backfill_xbrl": False,     # expensive; only when needed
}

UNIVERSE = "sp500"              # "sp100" | "sp500" | "sp1500" | "custom"
LOOKBACK_YEARS = 10
```

### Phase 1 — Universe resolution
1. Fetch S&P 500 constituents from Wikipedia or slickcharts.com (free, no auth)
2. Resolve each ticker → CIK via SEC's ticker lookup: `https://www.sec.gov/files/company_tickers.json`
3. Cache `data/tickers.json` with `{ticker, cik, company_name, sector, industry}`

### Phase 2 — Filings fetch
1. For each CIK, hit `https://data.sec.gov/submissions/CIK{cik:010d}.json`
2. Parse the returned filings list; filter to desired filing_types + date range
3. For each filing, record metadata (no PDF download yet)
4. Dedupe by accession number (SEC filing IDs are unique)

### Phase 3 — IR / earnings enrichment
1. For each ticker, crawl the company IR page (slow, per-ticker)
2. Regex for earnings-release links near fiscal period end dates
3. Merge into `EarningsEvent` rows

### Phase 4 — Optional PDF archival
If you want filings locally (see COST_BREAKDOWN.md for sizing):
1. `aria2c` with SEC-appropriate user agent, 4 concurrent downloads
2. Store under `~/equity-archive/{ticker}/{filing_type}/{accession}.{ext}`
3. 10-K PDFs: ~5-15 MB each. S&P 500 × 10 yr × 10-K only ≈ 50 GB. Full (10-K + 10-Q + 8-K) ≈ 150 GB.

### Rate limit budget

| API | Limit | S&P 500 pass time |
|---|---|---:|
| SEC submissions API | 10 req/sec | ~50 s for 500 companies |
| SEC filing documents | 10 req/sec | depends on document count |
| IR page scrape | 1/sec courtesy | ~500 s = ~8 min |
| EDGAR full-text search | 10 req/sec | budget-dependent |

Full S&P 500 Phase 1+2 pass: **~3 min wall time**. Phase 3 (IR pages): **~10-15 min**. Phase 4 (PDF archival): **hours**, run overnight.

---

## Storage implications

(See also `docs/COST_BREAKDOWN.md` for R2 / SSD sizing.)

| Tier | Scope | Size |
|---|---|---:|
| Metadata only (JSON index of filings) | 45k filings × 1 KB | ~45 MB |
| + XBRL structured facts | companyfacts.json × 500 | ~2 GB |
| + 10-K PDFs, 10 yr × S&P 500 | 5,000 × 10 MB | ~50 GB |
| + 10-K + 10-Q + 8-K PDFs, 10 yr × S&P 500 | 45,000 × avg 5 MB | ~200 GB |
| + full-text extracted (PDF → text) | ~0.5× PDF size | +100 GB |

Realistic target: **metadata + XBRL + 10-K PDFs only**. That's ~50 GB. Fits on the 1 TB external SSD scenario in the cost breakdown.

---

## Integration with existing index

These two worlds compose, they don't merge:

- `data/quant_index.json` = "what's the literature on factor investing?" — research references
- `data/equity_filings.json` = "what did MSFT say in their Q4 FY25 10-K?" — primary source data
- Cross-reference: when a Tier 2 arxiv paper cites a specific 10-K, the filing can be linked by URL. Store under `secondary_urls` on the paper.

The resource index is **canon** (what published knowledge exists). The equity archive is **primary sources** (raw company disclosures). Different schemas, different cadences, different queries.

---

## Decisions the user needs to make before coding

1. **Ticker universe:** S&P 100 / 500 / 1500 / Russell 3000 / custom list?
2. **Lookback period:** 5 / 10 / 20 years of history?
3. **Filing types:** 10-K + 10-Q + 8-K only, or add 13F / DEF 14A / Form 4 / S-1?
4. **Store PDFs or just URLs?** (Cost: URLs only = ~50 MB; full PDFs = 50-200 GB)
5. **Transcripts?** If yes, accept the ~50% coverage ceiling from free sources.
6. **Cadence:** quarterly (aligned to earnings), weekly, or daily?
7. **Share schema with resource index or keep separate?** Recommendation: separate.

Once these are fixed, the implementation is straightforward — 1-2 sessions of coding for Phase 1-2, another for Phase 3, Phase 4 is just running the download script.

---

## Suggested first-run config

```python
# equity_fetcher.py defaults
UNIVERSE = "sp100"              # start small
LOOKBACK_YEARS = 5
FILING_TYPES = ["10-K", "10-Q", "8-K"]
STORE_PDFS = False              # metadata only; add PDF grab as Phase 4
USER_AGENT = "Symbols Terminal research indexer (tyalorkny@gmail.com)"
```

Ship this, validate output against EDGAR manually for a few known tickers (AAPL, MSFT, JPM), then expand to S&P 500.

---

## Known issues to expect

- **CIK-ticker drift:** companies change tickers (FB → META, TWTR → X/delisted). The ticker map needs a `valid_from` / `valid_to` or historical lookup for clean backfill.
- **Restated financials:** 10-K/A amendments change historical numbers. EDGAR tracks these; the XBRL companyfacts API normalizes but a manual audit on 2-3 known cases is worth doing.
- **IPOs and delistings:** Russell reconstitutes yearly. If you fix a universe at runtime, you'll miss companies that were in the index historically but no longer are.
- **Foreign filers:** ADR-backed companies (BABA, TSM, ASML) file 20-F instead of 10-K. Annual but different schema.
- **Deregistered companies:** still have EDGAR history but no current filings. EDGAR's API handles this cleanly; just accept null current-fiscal-period for them.
