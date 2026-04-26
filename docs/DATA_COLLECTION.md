# Data Collection — On-Demand Retrieval over the Quant Index

How to stop thinking about the index as a static artifact and start thinking about it as a queryable, retrieval-augmented substrate — the way an AI system treats its corpus. Load nothing up-front. Fetch only what a question needs. Cache what you fetched. Learn from what was used.

**Governing principle:** the index metadata (2,783 rows, ~2 MB) is small enough to keep fully in RAM. The *content* it references (25–65 GB of PDFs + repos + HTML) is NOT — and trying to mirror it all up-front is expensive, legally messy, and wasted effort on 95% of resources you'll never read. Lazy, on-demand, cached.

---

## 1. Framing — "How AI does it"

Modern AI retrieval systems follow a consistent pattern. Map each piece to the quant index:

| AI pattern | What it means | Quant-index equivalent |
|---|---|---|
| **Embedding-based retrieval** | Encode each doc as a vector; cosine-similarity to query vector | Embed each resource's title + summary + tags; query via natural language |
| **Hybrid search** | Combine semantic (meaning) + lexical (BM25 keyword) | Semantic over title/summary + exact-match over topic_tags / author |
| **Reranking** | First pass: fast, wide. Second pass: slow, narrow. | Retrieve top 50 via embedding, rerank top 5 with cross-encoder or LLM |
| **Tool use / function calling** | Expose atomic operations; let the agent compose | `search_index`, `fetch_content`, `get_citations` as MCP tools |
| **Context compression** | Summarize long docs before injection | Cached PDF → extractive summary → feed to LLM |
| **Caching with TTL** | Don't re-fetch what you fetched recently | Fetched-content cache; metric snapshots |
| **Query rewriting** | Translate NL → structured filter + semantic query | "Avellaneda-Stoikov papers from 2020+" → `{year≥2020, embed("Avellaneda-Stoikov market making")}` |
| **Iterative / agentic retrieval** | Multi-hop navigation | Paper → its citations → the repo that implements it → examples |

You've probably used every one of these when talking to Claude. Same patterns apply here; the corpus is just your resource index instead of the entire web.

---

## 2. Layered architecture

Five layers, each independently useful, each building on the previous.

```
┌─────────────────────────────────────────────────────────────┐
│ Layer 5: LLM synthesis       "summarize top 3 for me"       │
├─────────────────────────────────────────────────────────────┤
│ Layer 4: Tool/MCP exposure   Claude (or any agent) queries  │
├─────────────────────────────────────────────────────────────┤
│ Layer 3: Content fetch       On-demand PDF/HTML/repo cache  │
├─────────────────────────────────────────────────────────────┤
│ Layer 2: Semantic retrieval  Embeddings + vector search     │
├─────────────────────────────────────────────────────────────┤
│ Layer 1: Structured query    SQL/DuckDB over metadata       │
└─────────────────────────────────────────────────────────────┘
```

### Layer 1 — Structured metadata query

Foundation. Zero AI magic; just SQL over what's already in `data/quant_index.json`.

**Tech:** DuckDB (reads JSON directly, zero-server, fast) OR SQLite (load JSON → table once, very portable).

```python
import duckdb
con = duckdb.connect(":memory:")
con.execute("""
  CREATE TABLE resources AS
  SELECT * FROM read_json_auto('data/quant_index.json',
                                format='array', records=true,
                                maximum_object_size=20000000) AS r,
         UNNEST(r.resources) AS unnest(row)
""")
# Done in ~200ms. Now query freely:
con.execute("""
  SELECT title, citation_count_or_stars, canonical_url
  FROM resources
  WHERE type='paper'
    AND sources LIKE '%arxiv/q-fin.TR%'
    AND citation_count_or_stars >= 50
  ORDER BY citation_count_or_stars DESC
  LIMIT 10
""").fetchall()
```

**Answers questions like:**
- "Highest-starred repos with source including seeds_ig"
- "Arxiv papers from 2025 in q-fin.PM with ≥100 citations"
- "Resources mentioned across ≥3 sources"
- "Institutional whitepapers from AQR published 2024+"

No embeddings, no AI. Just SQL on 2,783 rows.

### Layer 2 — Semantic retrieval

Now for the magic. Embed each resource's text into a vector; find similar by cosine distance.

**What gets embedded per row:**
```
{title}
{authors_or_owners}
{one_line_summary}
{topic_tags}
```
(~100-200 tokens per resource)

**Embedding model options:**

| Model | Cost | Quality | Where |
|---|---|---|---|
| OpenAI `text-embedding-3-small` (1536d) | $0.02/M tokens | Strong | API |
| OpenAI `text-embedding-3-large` (3072d) | $0.13/M tokens | Very strong | API |
| Voyage `voyage-3` (1024d) | $0.06/M tokens | Best for technical | API |
| `BGE-M3` (1024d) | $0 | Strong open | Self-host, ~2 GB weights |
| `nomic-embed-text-v1.5` (768d) | $0 | Good open | Self-host, ~500 MB |
| `sentence-transformers/all-MiniLM-L6-v2` | $0 | Mediocre but fast | Self-host, ~80 MB |

**Full corpus embed cost (2,783 rows × ~200 tokens avg = 557K tokens):**
- text-embedding-3-small: **~$0.011**
- voyage-3: ~$0.033
- BGE-M3 local: $0 (10 min on a laptop CPU)

Re-embedding monthly is effectively free.

**Vector store options:**

| Store | Fit | Notes |
|---|---|---|
| **sqlite-vss** | Drop into existing SQLite | Single file, zero-ops. Best for <100k rows. |
| **DuckDB VSS extension** | Same DB as Layer 1 | Unified querying; strong choice. |
| **LanceDB** | Columnar, parquet-backed | Rust core; scales to millions. Overkill here. |
| **Chroma** | Python-native | Easy setup, a bit heavy for 2,783 rows. |
| **Qdrant / Weaviate / Pinecone** | Production hosted | Overkill. Don't reach for these. |

**Recommendation:** DuckDB + VSS extension. Keeps Layer 1 and 2 in the same DB, queryable together.

```python
# Hybrid query: metadata filter + semantic similarity
con.execute("""
  SELECT title, canonical_url,
         array_cosine_similarity(embedding, ?::FLOAT[1536]) AS score
  FROM resources
  WHERE type='paper' AND year >= 2020
  ORDER BY score DESC
  LIMIT 10
""", [query_embedding])
```

### Layer 3 — On-demand content fetch

The "need-to-know" layer. Content is NEVER preloaded. Fetched only when a query or the user demands it. Cached once fetched.

```python
class CachedFetcher:
    CACHE = Path("~/quant-archive/cache").expanduser()

    def get(self, resource_id: str, force: bool = False) -> str:
        """Return extracted text for a resource. Cache on disk."""
        cache_path = self.CACHE / f"{resource_id}.txt"
        if cache_path.exists() and not force:
            return cache_path.read_text()

        resource = load_resource(resource_id)
        text = self._fetch(resource)
        cache_path.write_text(text)
        return text

    def _fetch(self, r: Resource) -> str:
        if r.type == "paper" and "arxiv.org" in r.canonical_url:
            pdf = download_arxiv(r.canonical_url)
            return extract_text_pymupdf(pdf)  # ~90% accurate, fast
        elif r.type == "repo":
            return fetch_github_readme(r.canonical_url)  # README only — not full clone
        elif r.type == "blog_post":
            return extract_article_text(r.canonical_url)  # readability.py
        elif r.type == "whitepaper":
            pdf = download_pdf(r.canonical_url)
            return extract_text_pymupdf(pdf)
```

**Cache policy:**
- Papers: keep indefinitely (immutable once published)
- Repos (READMEs): 30-day TTL (README edits are rare but happen)
- Blogs: 90-day TTL
- Store in `~/quant-archive/cache/{resource_id}.{txt,pdf}`

**Storage size:** if you fetch 200 papers over a year, you'll have ~200 MB of PDFs + extracted text. Trivial.

### Layer 4 — Tool / MCP exposure

Expose the index as **tools** an LLM (or Claude Code) can invoke. This is what turns the index from a static file into an agentic substrate.

**Minimal tool surface:**

```python
# search_index(query: str, filters: dict = None, k: int = 10) -> list[dict]
# Structured filter + semantic similarity; returns top-k resource rows

# fetch_content(resource_id: str) -> str
# Returns extracted text; cached after first call

# list_similar(resource_id: str, k: int = 5) -> list[dict]
# K nearest neighbors in embedding space

# get_citations(arxiv_id: str) -> list[dict]
# Fetch from Semantic Scholar; returns papers that cite this one

# expand_topic(topic: str, k: int = 20) -> list[dict]
# Soft topic expansion — find all resources tagged near this topic
```

**As an MCP server** (Claude Code native): wrap these in a `mcp` Python server, register in `.claude/mcp.json`, and Claude calls them directly during conversations. No copy-pasting URLs.

**Sample session:**

> **User:** "what's the state of the art on volatility surface fitting with neural nets"
>
> **Claude internally:**
> 1. `search_index(query="volatility surface neural network", filters={type:'paper', year>=2022}, k=10)`
> 2. Gets 8 papers back with snippets.
> 3. `fetch_content(top_result.resource_id)` for the 2 most promising.
> 4. Synthesizes summary with citations.

**Benefit:** the corpus lives where you already work (Claude Code). No separate web UI needed.

### Layer 5 — LLM synthesis

On top of retrieval, actually generate answers with citations.

Pattern (standard RAG):
1. User question → query rewriter (optional) → structured filter + embedding
2. Retrieve top 10–20 via Layer 2
3. Rerank with cross-encoder OR LLM (filter to top 5)
4. Fetch content via Layer 3 for top 5
5. Compose context window: question + top-5 snippets
6. Claude/GPT synthesizes answer with citations

**Cost per query (at 2026 prices):**
- Query embedding: negligible
- Retrieval: negligible (local)
- Content fetch: ~0–500ms if cached, 2-5s if not
- LLM synthesis: ~$0.01-0.05 (Claude Sonnet 4.6 at ~10k input tokens, 500 output)

A "research chat" session of 20 questions is ~$0.50. Sustainable at personal-use scale.

---

## 3. The "need to know" workflow — concrete example

Question: *"what papers discuss regime-switching in vol modeling, ideally with code"*

```
Layer 1 + 2 (search_index):
  Embed query → find top 15 papers matching "regime switching vol modeling"
  Filter: type in {paper, repo}, year >= 2018, confidence=high
  Result: 15 candidates

Layer 2 rerank:
  Cross-encoder scores → top 5 papers + 2 repos

Layer 3 (fetch_content, on-demand):
  For top 5: check cache → miss for 3, hit for 2
  Fetch 3 arxiv PDFs (~45s total), extract text, cache
  Fetch 2 repo READMEs (~2s)

Layer 5 (synthesize):
  Context: question + 7 extracted snippets
  Claude Sonnet 4.6 produces a 4-paragraph summary with footnote citations
```

Total wall time: 60s first-time query, 5s on follow-up re-queries. Total cost: ~$0.04.

At no point do you have the full 2,783-row corpus loaded into LLM context. You have exactly the 7 resources the question needs.

---

## 4. Storage + cost summary

| Layer | One-time | Ongoing |
|---|---|---|
| L1 (metadata) | $0 (already have `data/quant_index.json`) | $0 |
| L2 (embeddings) | $0.01 (OpenAI) or 10 min CPU (BGE-M3) | $0 — re-embed on index changes |
| L2 (vector store) | $0 (DuckDB VSS) | $0 |
| L3 (content cache) | $0 | disk — grows ~1 MB per paper fetched |
| L4 (MCP server) | 1 hour code | $0 |
| L5 (LLM synthesis) | $0 | ~$0.01–0.05 per query |

**Realistic monthly bill for a serious research user (~200 queries/mo):** $2–10.
**Realistic disk footprint after a year of use:** 500 MB–2 GB of cached content.

---

## 5. Implementation phases

Each phase is independently shippable. You don't need all 5 to get value.

### Phase 1 — DuckDB query layer (1-2 hrs)
Load `data/quant_index.json` into a DuckDB in-memory table on script start. Expose a few one-liner helpers: `find_by_tag`, `find_by_source`, `top_cited_in_category`. No ML needed. Already 10× more powerful than `jq` over the JSON.

### Phase 2 — Embeddings + semantic search (2-4 hrs)
Pick embedding model (BGE-M3 local for free, or OpenAI for convenience). Embed all 2,783 rows once. Store in DuckDB VSS (or `sqlite-vss` if you prefer SQLite). Add `semantic_search(query, k)` helper.

### Phase 3 — On-demand content fetcher (3-6 hrs)
Build `CachedFetcher` with handlers per resource type (arxiv PDF → PyMuPDF text extract; GitHub README via API; blog article via readability.py). Disk cache in `~/quant-archive/cache/`.

### Phase 4 — MCP server (2-4 hrs)
Wrap layers 1-3 as MCP tools. Register in `.claude/mcp.json`. Now Claude can query the corpus inline during any session.

### Phase 5 — RAG synthesis endpoint (4-8 hrs)
FastAPI endpoint: takes a question, does retrieval + rerank + LLM synthesis, returns answer with citations. Hook into your Symbols Terminal UI when you want.

---

## 6. Tech stack pick for the pragmatic version

If I were to write this tomorrow:

```python
# deps
duckdb                    # unified L1 + L2
openai                    # text-embedding-3-small
httpx                     # async fetch in L3
pymupdf                   # PDF text extraction in L3
readability-lxml          # blog article extraction in L3
mcp                       # L4
anthropic                 # L5 synthesis
```

- **No vector DB service** — DuckDB VSS is plenty for 2,783 rows.
- **No LangChain / LlamaIndex** — they add abstraction without saving lines. Write the retrieval logic directly.
- **No self-hosted embedding model** unless you want $0 cost and have the RAM headroom. OpenAI API at $0.01/embed pass is easier.
- **Cache content on disk, not in a DB.** Text files are grep-friendly.

---

## 7. What this enables downstream (Symbols Terminal integration)

Once Layer 4 (MCP) exists, a few directly-useful compositions:

1. **"What's the literature on X?" inline in notebooks.** User writes a backtest comment "testing a Parkinson vol estimator"; Claude suggests 3 papers, grabs abstracts, links them.
2. **Auto-enrich backtest reports.** When a strategy mentions "volatility targeting", attach relevant papers and repo references at report-generation time.
3. **Cross-reference across data sources.** "Find papers that cite the CBOE VIX methodology AND have a public Python implementation." That's a two-hop query — paper → its references → repos referenced.
4. **Regression into new seeds.** The index gets better the more you use it. If a fetched paper reveals 5 previously-unindexed citations, the indexer ingests them. Self-improving.

---

## 8. On-demand vs bulk — when to switch

| Scenario | Bulk makes sense | On-demand makes sense |
|---|---|---|
| You'll read >30% of the corpus | ✓ | |
| You work offline often | ✓ | |
| Corpus is <10 GB | ✓ either works | ✓ either works |
| Corpus is >100 GB | | ✓ — bulk is impractical |
| Queries are unpredictable | | ✓ |
| Latency <1s critical | ✓ (warm cache) | (need cache warmup) |

**Verdict for this index (25-65 GB content, unpredictable use):** on-demand. Bulk only for the 200 arxiv papers if you're serious about offline reading.

---

## 9. Gotchas

1. **Embedding drift** — if you upgrade embedding models, all historical vectors are invalidated. Re-embed the whole corpus. Cheap enough that this is fine.
2. **PDF text extraction quality varies.** Math-heavy papers extract badly. Budget for 5-10% of fetched papers being near-unreadable. Consider Marker (<github.com/VikParuchuri/marker>) or Unstructured for higher-fidelity extraction at higher cost.
3. **Stale content cache.** Blog posts and READMEs change. TTL-based invalidation or content-hash-based.
4. **LLM hallucination on citations.** Synthesis step can invent papers. Mitigation: force the LLM to cite only IDs you provided in context; post-validate that cited resource_ids exist in the index.
5. **Rate limits on fetch sources.** arxiv courtesy delay (3s), GitHub unauth (60/hr). On-demand fetches can stall if many queries hit the same rate-limited source.
6. **Legal posture.** Fetched content stays on your disk, fine for personal use. Don't re-host paid content. SSRN, Bloomberg, Refinitiv data — never cache-and-serve.

---

## 10. Open questions

1. **Embed locally or via API?** BGE-M3 is free but needs 2 GB RAM; OpenAI is $0.01 and trivial. For 2,783 rows, go API. For 500k+ rows, self-host.
2. **Is the MCP server for personal use only, or shared team?** If shared, needs auth + multi-user cache. Personal = much simpler.
3. **Synthesis LLM: Claude, GPT, or local?** Claude Sonnet 4.6 is the best quality/$ for this right now. Local (Llama 3.3 70B) works but slower and lower quality for synthesis with citations.
4. **Retention policy for content cache?** LRU eviction if disk cap hit, or just let it grow? At personal scale, grow.
5. **Query logging?** Useful for understanding what you actually ask the index, feeding back into the indexer (fill gaps). Privacy consideration if shared.

---

## 11. TL;DR

Build it as **five independent layers** so you can ship value after each:

1. **L1:** DuckDB over `data/quant_index.json`. SQL access in minutes. Done = queryable corpus.
2. **L2:** Embeddings (OpenAI $0.01 or BGE-M3 free), vector search in DuckDB VSS. Done = semantic search.
3. **L3:** `CachedFetcher` — fetch PDFs/HTML/READMEs only on demand, cache on disk. Done = read without leaving tools.
4. **L4:** MCP server wrapping L1-L3 as tools. Done = Claude can query the corpus inline.
5. **L5:** RAG synthesis endpoint. Done = "tell me the state of the art on X" answered with citations.

Governing principle, again: **load nothing up front, embed everything, fetch on demand, cache what you touch, learn from usage.** The same pattern an AI uses internally — the difference is the corpus is yours.
