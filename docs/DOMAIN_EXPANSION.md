# Domain Expansion — Growing the Index

How to take the index from 2,783 curated rows to 50,000+ rows across more domains, with richer metadata, deeper relationships, and better organization. Three axes: **wider** (more sources), **deeper** (richer metadata), **smarter** (better structure).

Companion to `DATA_COLLECTION.md` (which is about retrieval). This doc is about growing the corpus.

---

## 1. Where we are today

| Dimension | Current state |
|---|---|
| Rows | 2,783 |
| Source tiers | 5 (seeds, awesome-lists, arxiv q-fin, institutional, blogs) |
| Source count | 6 (quantscience_ig, awesome-quant, financial-ml, arxiv/q-fin.*, {aqr,man,fed,bis}, {quantstart,rw,ht}) |
| Types | paper, repo, textbook, whitepaper, blog_post |
| Metadata fields | 16 (title, authors, year, URL, tags, summary, citations/stars, date, mention_count, confidence, etc.) |
| Citation graph | none — each resource is an island |
| Topic taxonomy | free-text `topic_tags`, inconsistent |
| Asset class coverage | implicit in tags, not structured |
| Language | English only (de facto) |
| Temporal freshness | refreshed on manual re-run |

---

## 2. Target shape (rough)

- **50,000+ rows** across 20+ source families
- **Structured author graph** — every author normalized with h-index
- **Citation graph** — bidirectional paper↔paper and paper↔repo links
- **Hierarchical taxonomy** — 40-60 topic nodes, auto-assigned via zero-shot classifier or k-means over embeddings
- **Asset-class tagging** — equities / options / futures / FX / fixed income / crypto / macro / cross-asset
- **Difficulty tagging** — intro / intermediate / advanced / research-grade
- **Venue/institution tagging** — journal (JFE, RFS, JFQA), conference (NeurIPS, ICAIF, QuantMinds), institution (AQR, MIT)
- **Multilingual** — pipeline detects + optionally translates non-English abstracts
- **Retraction awareness** — cross-ref with Retraction Watch

---

## 3. Expansion axes

### Axis A — Wider: more source families

### Axis B — Deeper: richer metadata per row

### Axis C — Smarter: structure layered on top

Each axis is tackled independently. The index grows one new source at a time; the schema evolves one field at a time.

---

## 4. Axis A — New source families to add

Prioritized by ROI (free + high volume + legitimately permissive + useful) descending.

### Tier S — Big free APIs we haven't touched

| Source | API | Est. free rows | Coverage | Notes |
|---|---|---:|---|---|
| **OpenAlex** | `api.openalex.org/works` | 200M+ works | All academic | **Biggest win.** Free, no auth required, 100k req/day. Full abstracts, DOIs, authors, citations, concepts. Filter by concept (`Quantitative Finance`, `Market Microstructure`, etc.) for a curated slice. Expected pull for finance-adjacent: 100k-500k works. |
| **Crossref** | `api.crossref.org/works` | 130M+ works | DOI registry | Free, no auth. Slightly thinner metadata than OpenAlex but authoritative. |
| **Semantic Scholar bulk** | `api.semanticscholar.org/graph/v1/paper/search/bulk` | 200M+ | All academic | Free with key. We already use it for citations; could drive discovery directly. |
| **CORE** | `api.core.ac.uk/v3/` | 250M papers | Broad academic | Free tier 10k req/day. UK-based. Good for open-access discovery. |
| **arxiv beyond q-fin** | Same Atom API | 50k–150k/yr relevant | cs.LG, stat.ML, math.OC, cs.AI papers applying to finance | Same scraper, new categories. Heuristic filter: `abstract contains finance/market/trading/option/portfolio`. |
| **NBER working papers** | RSS + `nber.org/papers` listings | ~30k historical, 1k/yr | Macro, finance | Institutional quality. Free. |
| **CEPR discussion papers** | `cepr.org/publications` | ~18k historical | European finance + macro | Free. Less structured scraping. |
| **Fed Working Papers** beyond FEDS Notes | St. Louis / NY / Atlanta Fed research pages | ~15k historical | Monetary + regulatory | Each Fed bank has own archive. |
| **BIS beyond WPs** | Speeches, Quarterly Review, statistical pubs | ~10k | Central bank research | Already have a RePEc path; expand to other series. |
| **ECB Working Papers** | ECB research page + RePEc mirror | ~3k | EU central bank | Free. |
| **SSRN author pages** | `papers.ssrn.com/sol3/cf_dev/AbsByAuth.cfm?per_id=X` | ~1M+ via author walk | Tracked-author crawl | Top-ten pages are Cloudflare-blocked; author pages are not. Crawl high-value authors (Taleb, Lo, Gabaix, Campbell, Duffie...) to get their full output. |

### Tier A — Specialized / structured sources

| Source | Access | Volume | Notes |
|---|---|---:|---|
| **RePEc full** | `ideas.repec.org` series index | 4.5M+ papers | Free, HTML scraping. We've only scraped BIS; add NBER, ECB, Federal Reserve banks, academic series (Stanford GSB, Wharton, LSE FMG). |
| **OpenAIRE** | `api.openaire.eu` | 200M+ research products | EU-funded; research graph with linked funding, projects, datasets. |
| **DBLP** | `dblp.org/search/publ/api` | 6M+ CS papers | Free. Computational finance + ML-for-finance overlap. |
| **IEEE Xplore** | Paid API; free browsing | Millions | Signal processing, ML, control theory — relevant to HFT/execution. Licensed for personal access at IEEE member level. |
| **ACM Digital Library** | Paid API; DOIs via Crossref | Millions | Computational finance conferences. |
| **arxiv-sanity-lite** | `arxiv-sanity-lite.com` | Curated ML papers | Karpathy's tool. Scrapable; ML-focused. |
| **Papers With Code** (if revived) | Currently redirects to HuggingFace | Millions | Was the single best source for "paper + code" pairs. Huggingface Papers is the successor but not yet a great API. |
| **HuggingFace Papers** | `huggingface.co/papers` | ~100k | Growing; JSON accessible. Finance subset small. |
| **GitHub trending, by topic** | `github.com/topics/quantitative-finance` etc. | 500-2000/topic | Pull repos by topic tag: `quantitative-finance`, `algorithmic-trading`, `options-pricing`, `market-microstructure`. |
| **PyPI + pip search by keyword** | PyPI JSON API | 500k+ packages | Filter by keyword: `finance`, `trading`, `backtest`, `quant`. |
| **Kaggle notebooks + datasets** | `kaggle.com/api` | 1M+ notebooks | Many finance-tagged. Includes actual backtest code. |
| **HuggingFace Datasets** | `huggingface.co/api/datasets` | 200k+ datasets | Filter by tag: `finance`, `time-series`, `financial-news`. |
| **OpenML datasets** | `openml.org/api/v1/` | 20k+ | Structured ML datasets; finance subset. |

### Tier B — Content modalities beyond papers/repos

| Modality | Sources | Est. rows | Notes |
|---|---|---:|---|
| **Podcasts** | Listen Notes API, Apple Podcasts RSS, direct show RSS | 500-2000 episodes | Chat with Traders, Flirting with Models, Top Traders Unplugged, The Meb Faber Show, Odd Lots, Masters in Business, Superinvestors, Macro Voices. Metadata-only (no audio fetch). |
| **YouTube channels** | YouTube Data API v3 (free tier 10k units/day) | 10k+ videos | Curated list: QuantPy, QuantInsti, Hudson & Thames, Corey Hoffstein, Cam Harvey, NYU Stern lectures. Titles + descriptions only. |
| **Conference recordings** | Event sites (NeurIPS, ICAIF, Global Derivatives, QuantMinds) | 5-10k talks | Scrape program pages. Many have YouTube mirrors. |
| **Free university courses** | MIT OCW, Stanford Engineering Everywhere, Columbia MFE materials | 50-200 full courses | Includes Lo's 18.S096, Darrell Duffie's materials, Gatheral's NYU Courant notes. |
| **Newsletters (Substack / email)** | Public archives of: Matt Levine's Money Stuff, Doomberg, Accruing Edge, The Wall Street Experience, The Overshoot, Nishant Joshi, Robot James, Macro Ops | 10k+ posts | RSS per newsletter. |
| **Structured regulatory data** | SEC rule releases (EDGAR), FINRA notices, ESMA publications, CFTC rules | 50k+ | Quant-relevant: Reg SCI, MiFID II, PFOF rulings, market-structure rulemakings. |
| **Technical protocol docs** | FIX protocol, ISO 20022, OPRA feeds, ITCH/OUCH specs | ~100 | Low volume but high value for execution-layer work. |
| **Exchange notices** | CME, CBOE, ICE, NYSE, Nasdaq notices | 1k/yr | Rule changes, product launches, circuit breaker tests. |
| **Discord / Forum transcripts** | Manual curation only | Small | QuantConnect forums, Elite Trader, Reddit r/quant. Noisy; curated best-of. |

### Tier C — Quantitative data catalogs (index datasets, not content)

| Source | API | Notes |
|---|---|---|
| **Databento catalog** | databento.com | Product catalog only, not data |
| **Polygon.io product pages** | polygon.io | Same — index the datasets, not fetch them |
| **Refinitiv / LSEG data catalog** | Public product pages | For "what exists commercially" reference |
| **FRED data series** | fred.stlouisfed.org | 800k+ series; metadata-only index is useful even without pulling data |

### Tier D — Adjacent fields worth selective inclusion

- **Operations research** (math.OC) — portfolio optimization methods
- **Statistics / econometrics** (stat.ME, econ.EM) — GARCH, cointegration, state-space
- **Machine learning** (cs.LG, stat.ML) — filtered for finance relevance
- **Reinforcement learning for trading** (cs.LG + heuristic filter)
- **Behavioral economics** — context for market anomalies
- **Game theory / mechanism design** — market microstructure theory

---

## 5. Axis B — Deeper metadata per row

Current schema is flat and lossy. Most high-value operations need fields we don't have.

### Fields to add (priority order)

| Field | Type | Source | Priority | Why |
|---|---|---|---:|---|
| `doi` | str | Crossref / OpenAlex | P0 | Canonical ID for papers. Enables de-dup across sources. |
| `abstract` | str | OpenAlex / arxiv | P0 | Drives embeddings quality in L2 of retrieval. |
| `references` | list[resource_id] | OpenAlex `referenced_works` | P0 | Citation graph. |
| `cited_by_count` | int | OpenAlex / S2 | P0 | Already have partial (top 50 per arxiv cat). Extend. |
| `authors` | list[Author] | OpenAlex | P1 | Structured (name, orcid, h_index, affiliation) vs current CSV string. |
| `venue` | str | Crossref | P1 | Journal or conference name. |
| `open_access` | bool | OpenAlex `is_oa` | P1 | Can this PDF be legally downloaded? |
| `license` | str | OpenAlex | P2 | CC-BY, CC0, etc. |
| `concepts` | list[str] | OpenAlex `concepts` | P1 | Auto-tagged topics (e.g., `Market microstructure`, `Volatility modeling`). |
| `asset_class` | enum | Derived | P1 | equities / options / futures / fx / fixed-income / crypto / macro / cross-asset. |
| `difficulty` | enum | Derived (LLM) | P2 | intro / intermediate / advanced / research-grade. |
| `has_code` | bool | Cross-ref github | P1 | Does a github repo implement this paper? |
| `language` | str | Detect (langdetect) | P2 | ISO code. |
| `retracted` | bool | Retraction Watch API | P2 | 50k retractions tracked. |
| `altmetric_score` | int | altmetric.com API (free tier) | P3 | Social mentions aggregate. |
| `twitter_mentions` | int | Altmetric / Crossref Event Data | P3 | Filter social noise; high-mention papers often matter. |
| `repo_last_commit` | date | GitHub API | P1 | Stale repo flag. |
| `repo_stars_trend` | list[(date, stars)] | Weekly snapshot | P3 | Growth/decay signal over time. |
| `pdf_cached` | bool | local cache | P0 | Tracks what's been fetched via DATA_COLLECTION L3. |
| `embedding_model` | str | local | P1 | Which model produced the vector (for re-embedding awareness). |

### Author normalization

A single author (`Marcos López de Prado`) appears as:
- `Marcos López de Prado`
- `Marcos Lopez de Prado`
- `M. López de Prado`
- `Lopez de Prado, Marcos`
- `M.L. de Prado`

These should merge. Solution:
1. Pull `orcid` from OpenAlex where available (authoritative ID).
2. For missing ORCIDs: edit-distance match on name normalization + affiliation match.
3. Store authors as a separate table with `author_id` + `display_name` + `orcid` + `affiliations[]` + `h_index` + `paper_count`.

Benefit: "show me everything by Lopez de Prado" becomes one query. Currently impossible.

### Citation graph schema

New table `citations`:
```
from_resource_id  TEXT  -- citing paper
to_resource_id    TEXT  -- cited paper (resolved via DOI or arxiv id)
confidence        REAL  -- 1.0 for explicit OpenAlex reference, 0.5 for name-match
extracted_at      DATETIME
```

Enables:
- "papers that cite Avellaneda & Stoikov 2008"
- "papers that cite both Glosten-Milgrom AND Kyle 1985"
- Multi-hop: "papers that cite papers that cite X" (related work discovery)
- PageRank-style influence scoring

---

## 6. Axis C — Smarter organization

Metadata alone is a bag of fields. Organization is how they compose.

### Hierarchical topic taxonomy

Instead of free-text `topic_tags`, maintain a tree:

```
Quantitative Finance
├── Asset Pricing
│   ├── Factor Models
│   │   ├── Fama-French
│   │   ├── Q-factor
│   │   └── Risk Parity
│   ├── Behavioral Asset Pricing
│   └── Machine Learning for Asset Pricing
├── Derivatives
│   ├── Equity Options
│   │   ├── Vanilla Pricing
│   │   ├── Exotic Options
│   │   ├── Greeks & Hedging
│   │   └── Volatility Smile
│   ├── Interest Rate Derivatives
│   ├── Credit Derivatives
│   └── FX Options
├── Market Microstructure
│   ├── Order Book Dynamics
│   ├── Liquidity
│   ├── Market Making
│   └── HFT
├── Portfolio Management
│   ├── Mean-Variance Optimization
│   ├── Black-Litterman
│   ├── Risk Parity
│   └── Dynamic Portfolio Choice
├── Risk Management
│   ├── VaR / CVaR
│   ├── Copulas
│   └── Systemic Risk
├── Econometrics / Time Series
├── ML for Finance
│   ├── Deep Learning
│   ├── Reinforcement Learning
│   ├── NLP for Finance
│   └── Causal Inference
└── Execution
    ├── TCA
    ├── Smart Order Routing
    └── Algo Trading
```

**How to populate:**
- **OpenAlex `concepts`** auto-gives a hierarchy. Start there, reshape to fit the above.
- **Embedding-based clustering** for any concept not in OpenAlex. Cluster by k-means on L2 vectors; manually name clusters.
- **Zero-shot classifier** (e.g., BART or Claude) for difficult-to-cluster resources: "which of these 60 topics fits this abstract?"

Each resource gets 1-3 primary topics and up to 5 secondary.

### Author graph

Beyond per-author listings:
- **Co-authorship graph** — weighted edges; finds research cliques (e.g., the NBER/AQR crowd).
- **Institution cluster** — all AQR-affiliated papers/authors.
- **Influence graph** — authors whose papers most frequently get cited.

### Quality tiering (beyond current high/medium/low)

Replace the 3-tier confidence with a multi-signal score:

| Signal | Weight | Source |
|---|---:|---|
| Citation count (z-score within field/year) | 30% | OpenAlex |
| Venue prestige (JFE=1.0, arxiv-only=0.3) | 20% | Crossref venue map |
| First-author h-index | 15% | OpenAlex |
| Altmetric / social mentions | 10% | Altmetric API |
| Has code / is reproducible | 10% | GitHub cross-ref |
| Recency-adjusted citation velocity | 15% | (citations / years_since_publication) |

Output a `quality_score` in [0, 1]. Retain the 3-tier as a discretization for back-compat.

### Temporal signals

- `added_to_index` — when first seen by this pipeline
- `first_published` — authoritative publication date (not "retrieved_at")
- `velocity_30d` — citations/stars gained in last 30 days (trending signal)
- `freshness_rank` — percentile among same-type resources added in last 90 days

### Cross-references between types

- `paper_implements` — paper X → repo Y that implements it (via repo README mentioning arxiv ID, or reverse)
- `repo_cites_papers` — README parse for arxiv/DOI links
- `blog_references` — blog post → papers/repos it linked to
- `textbook_chapters` — textbook → papers cited in specific chapters

These turn the corpus from a flat list into a navigable graph.

### Geographic / institutional metadata

- `author_countries` (majority + list)
- `institutions` (top-3 affiliations per paper)
- `funding_sources` (NSF grants, corporate research funding, via OpenAlex)

Useful for: "what are the academic institutions driving quant research right now" or "which central bank produces the most useful papers on FX."

---

## 7. Dynamic / agent-driven expansion

Instead of one big initial ingest, grow the corpus from a seed via graph walks.

### Citation-following agent

```
for each high-quality paper in the index:
    references = openalex.get_references(paper.openalex_id)
    for each ref in references:
        if ref not in index:
            add_with_confidence(ref, confidence=derived_from_parent)
    if paper.cited_by_count >= 100:
        cited_by = openalex.get_citations(paper.openalex_id, limit=50)
        for cite in cited_by:
            if cite not in index:
                add_with_confidence(cite, ...)
```

Run weekly. Grows the index by ~500-2000/week organically. Bounded by quality thresholds to prevent unbounded growth.

### Author-following agent

Once you have `author_id`, for top-N most-cited authors in the corpus: pull their full publication list. Instant coverage of everything by Campbell, Lo, Duffie, Gabaix, etc.

### Topic-expansion agent

For each taxonomy leaf, query OpenAlex for top-100 papers in that concept. Fills in holes in the taxonomy.

### Code-following agent

For each paper with `has_code=True`, index the repo + its siblings (other repos by the same author/org).

### Conference-scraper agent

Every quarter: scrape the latest NeurIPS / ICAIF / ICML / KDD programs, filter for finance-relevant titles (keyword + embedding filter). Ingest.

### Retraction-monitoring agent

Weekly poll of Retraction Watch API. Flip `retracted=True` on any matching DOI. Optionally auto-demote confidence.

---

## 8. Quality curation as the index grows

Scale breaks curation. Today at 2,783 rows a human can audit; at 50k nobody will. Design for that.

### Automatic demotion rules

- Resources with `cited_by_count=0` + `year < current_year - 5` + `type=paper` → demote to low. Old + uncited = probably not useful.
- Repos with `last_commit > 3 years ago` + `stars < 50` → demote.
- Papers with retracted=true → force to low.
- Duplicate titles across venues → keep the most-cited; demote the rest.

### Auto-flagging for human review

- New source outputting >1000 rows in a single pass — likely over-pull.
- Any row with missing `abstract` AND missing `citation_count` — metadata gap; needs enrichment pass.
- Rows in the 10% highest-score but 0 human queries in 6 months — might be false-positive quality.

### Sampling-based audit

Random 20-row sample per source per quarter. Present to user in a one-shot review: "are these 20 actually useful?" Feed yes/no into confidence calibration.

---

## 9. Implementation phasing (where the ROI lives)

### Phase 1 — OpenAlex integration (biggest single win)
- Pull top 50k finance-tagged works from OpenAlex.
- Populate `doi`, `abstract`, `authors[]`, `concepts[]`, `referenced_works`, `cited_by_count` on existing rows.
- Expected new rows: 20k-40k. Expected metadata enrichment on existing rows: 80%+.
- Effort: 1-2 days.

### Phase 2 — Schema v2
- Extend `Resource` dataclass with P0 fields: doi, abstract, authors, concepts, references.
- Migration: process existing JSON through Crossref/OpenAlex to backfill.
- Effort: 0.5 day code + 1 day data-backfill wall time.

### Phase 3 — Citation graph + author normalization
- `authors` and `citations` tables.
- ORCID resolution for current authors.
- Effort: 1 day.

### Phase 4 — Podcast / YouTube / newsletter ingestion
- 5-10 of the highest-value shows/channels.
- Metadata-only; no audio/video download.
- Effort: 0.5 day per source.

### Phase 5 — Taxonomy build
- Start from OpenAlex `concepts`.
- Manually name 40-60 nodes.
- Auto-assign via nearest-centroid on embeddings + concept match.
- Effort: 1 day curation + 0.5 day code.

### Phase 6 — Dynamic expansion agents
- Citation follower (weekly cron).
- Author follower (one-shot for top 50 authors, then quarterly for new high-cited papers).
- Effort: 1 day.

### Phase 7 — Quality score v2
- Replace 3-tier confidence with weighted multi-signal score.
- Effort: 0.5 day.

### Phase 8 — Ancillary tiers (papers-with-code, HF Papers, conferences)
- Incremental.

---

## 10. Expected scale after each phase

| Phase | Rows | New metadata |
|---|---:|---|
| Current | 2,783 | baseline |
| +Phase 1 (OpenAlex) | ~25k | +doi, +abstract, +authors[], +concepts, +refs |
| +Phase 3 (citation graph) | 25k rows + 500k citation edges | graph queryable |
| +Phase 4 (podcasts/YT/newsletters) | ~35k | +modalities |
| +Phase 5 (taxonomy) | 35k | +hierarchical tags |
| +Phase 6 (dynamic agents, 1yr runtime) | ~80-100k | organic growth |
| +Phase 8 (long-tail sources) | ~150k | saturated |

150k rows is about the realistic ceiling before diminishing returns / junk dominates. Beyond that requires aggressive quality filtering and source-specific curation.

---

## 11. Storage implications

Reconcile with `COST_BREAKDOWN.md`:

| State | Metadata size | DB size (normalized) |
|---|---|---|
| Current (2,783 rows) | 2 MB JSON | ~1 MB |
| +Phase 1 (25k rows, +abstract, +authors, +refs) | ~80 MB | ~40 MB |
| +Phase 3 (+citation graph, 500k edges) | 80 MB + 40 MB edges | ~60 MB |
| Full (150k rows saturated + abstracts + cites) | ~500 MB JSON | ~200 MB |

Still fits comfortably in SQLite / Turso free tier / Neon Launch. Doesn't change the fundamental cost conclusion.

---

## 12. Risks + mitigations

| Risk | Mitigation |
|---|---|
| **Quality collapse as volume grows.** More rows = more noise. | Automatic demotion rules (section 8), quality-score floor for inclusion in top-level views. |
| **Source-scraping brittleness.** 20 sources = 20 things that can break. | Per-source tier flag like existing `RUN` dict; degrade gracefully when one fails. |
| **OpenAlex concept drift.** Their taxonomy evolves. | Pin concept IDs, not names. Re-snapshot quarterly. |
| **Dedup across sources gets harder.** 5x the rows = 25x the cross-pair checks. | DOI-first dedup (exact); then embedding-proximity pairs above 0.95 for manual review. |
| **License / ToS violations.** More sources = more ToS to read. | Document license posture per source at ingest time; never re-host paid content. |
| **Citation graph recursive bloat.** Follow citations 3 hops deep and you'll index every paper ever. | Hard limits: max_hops=2, min_parent_quality=0.6, max_new_rows_per_agent_run=2000. |
| **Author disambiguation errors.** Merging the wrong "J. Smith" papers. | Prefer ORCID (authoritative). For non-ORCID matches, require agreement on ≥2 of (affiliation, coauthor overlap, concept overlap). |
| **Retracted papers staying in circulation.** | Weekly Retraction Watch sync; force `retracted=True` blocks synthesis-layer usage. |

---

## 13. Integration with existing systems

### Feeding back into `index_builder.py`

This document assumes `index_builder.py` evolves to support:
- Multiple source modules with common interface (`class SourceConnector`).
- Per-source pluggable config (similar to current `INST_SOURCES` / `BIS_REPEC_PAGES` pattern).
- Schema-v2 aware I/O (backward-compat for existing v1 JSON).

### Feeding into `DATA_COLLECTION.md` layers

- Layer 2 (semantic retrieval) quality scales directly with abstract coverage. Phase 1 is a 10× boost.
- Layer 4 (MCP tools) gets new tool surface: `get_citations`, `list_papers_by_author`, `find_related_via_graph`.
- Layer 5 (RAG synthesis) can now answer "what are papers that cite paper X" — a question the current flat index cannot.

### Feeding into `EQUITY_REPORTS_PLAN.md`

- SEC filings become another source family (already scoped separately, as Plan doc notes).
- Author extraction from filings (corporate officers, auditors) could merge with the author graph — but that's a stretch; mostly they're separate domains.

---

## 14. Success metrics

How to know the expansion worked:

1. **Coverage:** ≥95% of papers in the "Top 200 most-cited quant finance papers" list (external benchmark) are in the index with full metadata.
2. **Freshness:** ≥90% of papers published in the last 30 days in the tracked concepts are in the index.
3. **Resolution:** a user query via Layer 2 retrieval returns ≥5 relevant results in >80% of test queries.
4. **Graph density:** median paper has ≥10 `references` and ≥3 `cited_by_count`.
5. **Taxonomy coverage:** every leaf node has ≥20 resources; no orphan leaves.
6. **Author normalization:** ≤3% duplicate authors (verified by random 100-author audit).

---

## 15. TL;DR

The 2,783-row hand-curated seed was the right starting shape. The next 10× growth is **metadata-driven, not source-driven**: OpenAlex alone adds 25k rows with abstracts, citations, and structured authors. After that, grow along three axes:

- **Wider:** OpenAlex + 10 more free APIs → ~35k rows
- **Deeper:** DOI, abstracts, citation graph, normalized authors, hierarchical taxonomy → each row is 5× more useful
- **Smarter:** agentic growth (follow citations, follow authors), quality score, retraction tracking → self-maintaining

Ceiling target: **~150k rows, ~200 MB DB, indefinitely free to host, ~40 hours of focused implementation work spread across 8 phases.** Biggest single win is Phase 1 (OpenAlex) — do that first.
