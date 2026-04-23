# Cost Breakdown — Quant Resource Index

All numbers below are grounded in the current build (2384 rows, April 2026). Where growth projections are involved, they're stated as "per year" so you can interpolate. **No estimate below assumes a paid data feed** (Bloomberg, Refinitiv, WRDS, S&P, FactSet) — the index is composed entirely of free/public sources.

---

## TL;DR

For the index as it stands today, **everything fits on a laptop for $0/month for the next 3-5 years** under any reasonable growth scenario. The real cost gates are:

1. **Do you want to mirror content locally?** (PDFs, git clones) — 2 GB to 65 GB depending on ambition
2. **Do you need remote DB access from an app?** — $0 on free tiers up to multi-GB scale
3. **Do you want a public-facing API?** — ~$5/mo at the cheapest Fly/Railway tier

A realistic starting bill is **$0/month indefinitely**. The first dollar you'd spend is on a 1 TB external SSD (~$80 one-time) if you decide to mirror repos + papers. Everything upstream of that fits in free tiers.

---

## 1. Index metadata storage (the DB layer)

### Size per row

| Format | Bytes/row | Current 2384 rows | Notes |
|---|---:|---:|---|
| JSON (current) | ~750 | 1.7 MB | field names repeat per row |
| SQLite denormalized single table | ~475 | ~1.1 MB | 35% smaller than JSON |
| SQLite normalized (sources/tags junctions) | ~420 | ~1.0 MB | marginal gain; worth it for queryability |
| Postgres | ~500 | ~1.2 MB | row overhead is higher than SQLite |
| DuckDB | ~300 | ~0.7 MB | columnar; best read perf |

### Growth rate (drivers)

| Source | New rows/year | Driver |
|---|---:|---|
| arxiv q-fin (7 cats) | 3,000–5,000 | q-fin submits ~50-100 papers/week across TR/PM/ST/CP/RM/MF/PR |
| Institutional (AQR/Man/Fed/BIS) | 200–500 | Fed FEDS Notes + BIS working papers dominate |
| Blogs (QS/RW/HT) | 100–300 | low; blog cadence is monthly |
| Awesome-lists drift | 50–100 | README updates; slow |
| Seed / quantscience_ig | 20–50 | only if HAR is re-captured |
| **Total** | **~3,500–6,000 rows/yr** | |

### Three storage scenarios

#### Scenario A — Minimal: resources table only, upsert-in-place
Single table. No verification log, no historical snapshots. Current rows get overwritten on each refresh.

| Year | DB size | Notes |
|---|---:|---|
| 0 (now) | 1.1 MB | |
| 1 | ~4 MB | +3,500-6,000 rows |
| 3 | ~12 MB | |
| 5 | ~20 MB | |
| 10 | ~40 MB | |

#### Scenario B — Recommended: + verification log + metric snapshots
One `verification_log` row per resource per scrape run (tracks "was URL still 200?", captures HTTP status over time). One `metric_snapshot` row per resource per week (captures citation_count / stargazers to plot trends).

- Verification log: weekly × ~2,400 rows × ~80 bytes = ~10 MB/yr
- Metric snapshots: weekly × ~1,750 rows (papers + repos) × ~40 bytes = ~4 MB/yr
- Plus resources-table growth from Scenario A

| Year | DB size | Notes |
|---|---:|---|
| 1 | ~20 MB | |
| 3 | ~60 MB | |
| 5 | ~100 MB | |
| 10 | ~200 MB | |

#### Scenario C — Aggressive: daily ingest, full history, every index
Daily arxiv polls, full verification log retained forever, indexes on (type, confidence, year, canonical_url, every topic_tag token).

| Year | DB size |
|---|---:|
| 1 | ~80 MB |
| 3 | ~240 MB |
| 5 | ~400 MB |
| 10 | ~800 MB |

### Platform fit (free tiers)

| Platform | Free storage limit | Cost after | Fits through |
|---|---:|---|---|
| Local SQLite (on SSD) | unlimited | $0 | forever |
| Turso (hosted SQLite) | 9 GB | $29/mo for 24 GB | Scenario C past year 100 |
| Neon Postgres free | 0.5 GB | $19/mo Launch tier | Scenario B until year ~20; Scenario C until year ~6 |
| Supabase free | 500 MB | $25/mo Pro | same as Neon |
| Cloudflare D1 free | 5 GB | $0.75/GB/mo over | Scenario C past year 60 |
| Railway Postgres | ~1 GB ($5 credit/mo) | ~$0.25/GB/mo | Scenario B for decades |

**Verdict for the DB layer: any free tier works.** Local SQLite is the cheapest and simplest; Turso is the best upgrade path if you ever want remote reads without migration.

---

## 2. Content bulk storage (the actual papers/repos the URLs point to)

This is where size balloons. The index is 1.7 MB of metadata; the content it references is 25-65 GB if you mirror it all.

### Per-type size

| Type | Count in index | Avg size | Bulk |
|---|---:|---:|---:|
| arxiv papers (PDF) | ~920 | ~1 MB | **~1 GB** |
| Institutional whitepapers (BIS/AQR/Fed/Man PDFs) | 246 | ~2-3 MB | **~600 MB** |
| Seed + SSRN-accessible papers | ~200 | ~1 MB | **~200 MB** |
| GitHub repos (shallow, `--depth=1 --filter=blob:none`) | 627 | ~5-10 MB | **~3-6 GB** |
| GitHub repos (full clone, full history) | 627 | ~50 MB avg | **20-60 GB** |
| Blog posts (HTML snapshot via `wget -p`) | 388 | ~200 KB | **~80 MB** |
| Textbooks | 3 | — | skip (Amazon links only) |

### Tiers of ambition

| Tier | What you get | Size |
|---|---|---:|
| **1 — Reading archive** | Papers + whitepapers + blogs. No code. | **~2 GB** |
| **2 — Reading + code** | Tier 1 + shallow repo clones. | **~5-8 GB** |
| **3 — Full archive** | Tier 2 + full git history on every repo. | **25-65 GB** |
| **4 — Tier 3 + model weights** | Follows Git LFS on all repos (stable-diffusion weights, docling models, etc.). | **100+ GB** — avoid |

### Storage hardware

| Medium | Cost | Fits |
|---|---:|---|
| Laptop internal SSD (assuming 50+ GB free) | $0 | Tiers 1-3 |
| 1 TB external SSD (Samsung T7 / SanDisk Extreme) | ~$80 one-time | Tiers 1-3 with years of growth buffer |
| 2 TB external SSD | ~$150 one-time | Tier 4 + multi-year |
| AWS S3 Standard, 100 GB | ~$2.30/mo | Tier 3 in cloud |
| Backblaze B2, 100 GB | ~$0.50/mo | Tier 3, cheap cloud |
| Cloudflare R2, 100 GB | ~$1.50/mo (no egress fees) | Tier 3 with API access |

### Bandwidth / rate constraints on the grab

| Source | Rate limit | 1-time grab time |
|---|---|---|
| arxiv (PDFs) | 1 req / 3 s courtesy | 920 papers × 3 s = **~46 min** serial |
| BIS/RePEc | none published; be polite 1/s | ~200 papers = ~3 min |
| AQR/Man/Fed/Blogs | no documented limit | negligible |
| GitHub shallow clone | TCP-bound; use 8 concurrent workers | 627 repos × ~10 s avg = **~15 min** at 8 concurrency |
| GitHub full clone | same, but transfer-bound | **60-180 min** depending on repo whales (google-research alone can be 10+ min) |

### Licensing / legal

| Source | Bulk download posture |
|---|---|
| arxiv | CC licenses; bulk download explicitly allowed via `arxiv.org/bulk-data` |
| BIS / RePEc | free for personal use; be polite |
| AQR / Man / Fed / Federal Reserve | public research; free to archive |
| SSRN | ToS prohibits bulk download; grab individually if at all |
| GitHub | each repo is its own license; cloning is always OK |
| Blogs (QS/RW/HT) | personal archival fine; redistribution not |
| Textbooks (Amazon links) | never grab |

**Do not attempt Bloomberg, Refinitiv, WRDS data through any of these pipes.** Those are separate paid subscriptions the index does not cover.

---

## 3. API + rate-limit costs (for ongoing ingestion)

All APIs used by `index_builder.py` today are **free**. Rate limits are the only operational constraint.

| API | Free limit | With auth | In-use where |
|---|---|---|---|
| arxiv Atom API | 1 req / 3 s courtesy; no hard limit | same (no auth option) | Tier 2 |
| Semantic Scholar | 100 req / 5 min unauth | 1000 req/s with API key (free) | Tier 2 citation lookups |
| GitHub REST API | 60 req/hr unauth | 5,000 req/hr with PAT | seed re-verify + could backfill Tier 1 stars |
| arxiv OAI-PMH bulk | unrestricted | — | not used; for full-archive grabs |
| RePEc | unrestricted | — | Tier 3 BIS |

### Cost of auth tokens

- **GitHub PAT**: free. Classic `read:public_repo` scope is enough. ~30 s to generate at https://github.com/settings/tokens
- **Semantic Scholar API key**: free at https://www.semanticscholar.org/product/api. Optional; raises limit from 100/5min to 1/sec. Apply-via-form, 1-2 day turnaround.
- **arxiv**: no auth model. Just observe 3 s spacing.

### What auth unlocks in this codebase

| Setup | Unlocks | Runtime impact |
|---|---|---|
| No tokens (current) | Basic unauth operation | seed re-verify ~40 calls; S2 citations 19 min |
| + `GITHUB_TOKEN` env | 5,000 req/hr → backfill Tier 1 repo stars (625 calls) | Tier 1 stars column populates (currently null) |
| + S2 API key | 1 req/s → Tier 2 citations drops from 19 min to 6 min | modest win |

**Neither auth upgrade costs money.** Both are worth setting if you plan to re-run monthly.

---

## 4. Ongoing compute — re-run costs

### Per-run wall time breakdown (fresh build, all tiers)

| Phase | Wall time | API cost |
|---|---:|---|
| Load seeds | <1 s | 0 |
| Re-verify seed URLs | ~40 s | ~40 GitHub calls |
| Tier 1 awesome-lists | ~10 s | 2 raw-readme fetches |
| Tier 2 arxiv Atom × 7 cats | ~25 s | 7 arxiv calls + 21 s pacing |
| Tier 2 Semantic Scholar citations (350) | **~19 min** | 350 S2 calls (biggest cost) |
| Tier 3 institutional | ~30 s | 4 page fetches |
| Tier 4 SSRN (blocked) | ~10 s | 5 failed calls |
| Tier 5 blogs | ~15 s | 3 page fetches |
| Output writers | ~2 s | 0 |
| **Total** | **~21 min** | ~410 API calls |

### Compute budgets by host

| Host | Free tier | Runs/mo at 21 min each |
|---|---|---:|
| Local laptop | unlimited | ∞ ($0) |
| GitHub Actions (public repo) | 2,000 min/mo | **95 runs/mo** — more than daily |
| GitHub Actions (private repo) | 2,000 min/mo | same |
| Fly.io | 3 × 256 MB CPU-shared VMs free | plenty for a weekly cron |
| Railway | $5 free credit/mo | ~20 runs/mo |
| AWS Lambda (if broken into steps) | 400k GB-sec/mo | essentially free |

### Recommended cadence vs cost

| Cadence | Purpose | $/mo |
|---|---|---:|
| Manual only | You run it when you want | $0 |
| launchd/cron weekly | Local laptop, silent-on-failure | $0 |
| GitHub Actions weekly | Cloud-hosted, commits JSON back to repo | $0 |
| GitHub Actions daily | Daily arxiv refresh | $0 (still inside 2000 min) |
| GitHub Actions hourly | Overkill; spams API budget | $0 infra, potentially blacklisted |

**$0 covers any reasonable cadence.** The only way you pay is if you push into daily S2 citation re-fetches on thousands of papers without a S2 key, which just wastes wall-clock time, not money.

---

## 5. Hosting costs (if you expose the index)

### Read-only API

| Stack | Cost | Notes |
|---|---:|---|
| Datasette on Fly.io free VM | $0 | serves SQLite directly; publicly readable |
| Datasette on Railway | ~$5/mo | same, easier to set up |
| FastAPI + SQLite on Fly | $0 | if you want custom endpoints |
| Cloudflare Workers + D1 | $0 (100k reqs/day free) | globally edge-deployed |
| Vercel Serverless + Postgres | $0 Hobby | Neon-compatible; 100k serverless invocations |

### Read-write API (authenticated writes only)

Same tier, same cost. Writes are rare (ingest jobs). No extra infra.

### Frontend

| Stack | Cost | Notes |
|---|---:|---|
| Next.js on Vercel Hobby | $0 | unlimited if under 100 GB/mo bandwidth |
| Static export on Cloudflare Pages | $0 | unlimited bandwidth |

**Full stack estimate: $0–5/mo for the index portion**, scaling only if you pick Railway instead of Fly.

---

## 6. Total $/month scenarios

| Scenario | What you get | One-time | $/mo |
|---|---|---:|---:|
| **A — Status quo** | Current repo, manual rescrapes on laptop | $0 | **$0** |
| **B — Auto-refreshed** | A + GitHub Actions weekly cron, updated JSON committed | $0 | **$0** |
| **C — Remote-queryable** | B + Turso for remote reads | $0 | **$0** |
| **D — Public API** | C + Fly/Railway FastAPI/Datasette front | $0 | **$5** |
| **E — Paper archive** | D + 1 TB external SSD for offline PDFs | **$80** | $5 |
| **F — Full repo archive** | E + full git clones of all 627 repos | $80 | $5 |
| **G — Cloud mirror** | F + S3/Backblaze backup of archive | $80 | ~$7 |
| **H — DuckDB analytics** | G + DuckDB alongside SQLite for queries | $80 | $7 |

For context: a Bloomberg terminal is ~$24,000/yr. A single WRDS academic subscription is $1,500-4,000/yr. This index — as infrastructure — is genuinely ~0.02% of that cost.

---

## 7. What breaks the $0/mo tier

In rough order of likelihood:

1. **>500 MB DB on Neon/Supabase free tier.** You hit this in Scenario C around year 6. Migration path: Turso (9 GB free) or Cloudflare D1 (5 GB free).
2. **>9 GB DB anywhere.** Very unlikely; requires daily ingest + full-history retention for decades. If hit, use local SQLite and skip hosted.
3. **Hosting a public archive with real traffic.** Bandwidth overages on Vercel ($40/TB over 100 GB), Fly ($0.02/GB egress). Static CDN (Cloudflare Pages) has unlimited bandwidth — prefer it.
4. **GitHub Actions hitting 2,000 min/mo.** Only if you run hourly for some reason. Weekly or daily is fine.
5. **Exceeding S2's 100 req/5 min unauth.** Happens in a single run if you expand ARXIV_CITATION_TOP_N from 50 to ~100 across 7 cats. Get a free S2 API key.
6. **Paying for SSRN, Bloomberg, Refinitiv, or WRDS.** Out of scope for this index. The design is explicitly to stay on free sources.

---

## 8. Recommended starting setup

If you're picking one config today:

1. **SQLite, local file** (`quant_index.db` alongside `quant_index.json`) — Scenario B schema (resources + sources + verification_log + metric_snapshot).
2. **GitHub PAT in env** — `GITHUB_TOKEN=...` so Tier 1 can backfill stars on 625 repos in a single full run.
3. **arxiv PDF mirror**, one-time — `~/quant-archive/papers/` (~1 GB, 46 min to download). Filename pattern: `{arxiv_id}.pdf`. Don't re-download on every run.
4. **Shallow repo clones on-demand only** — script that takes a repo name, clones `--depth=1` into `~/quant-archive/repos/{owner}__{repo}/` when you actually need the code.
5. **Manual re-runs for now.** Promote to weekly `launchd` once you have a feel for what noise creeps in week-to-week.
6. **Defer hosted DB** until you have a real app that queries it. SQLite → Turso migration is `turso db create --from-file quant_index.db` later; zero schema changes required.

Estimated marginal cost over current setup: **$0 plus ~90 minutes of one-time setup**.

---

## Appendix — quick cost decision rules

- **<10 MB DB, local only** → SQLite file, no ceremony.
- **<9 GB DB, remote access wanted** → Turso free.
- **Need full Postgres features (JSONB, FTS, pg_trgm)** → Neon free up to 0.5 GB; then $19/mo.
- **Public-readable API, low traffic** → Datasette on Fly free / Cloudflare Workers + D1.
- **Any downloaded papers / repos >10 GB** → external SSD > cloud storage (egress fees on AWS/GCP hurt).
- **Archive >100 GB with cloud access** → Cloudflare R2 (no egress fees) or Backblaze B2.
- **Don't mirror stable-diffusion weights or any Git LFS model assets.** They're what push you from 65 GB to 100+ GB for no analytical gain.
