# Cost Breakdown

Reference doc for two related but distinct cost questions:

- **Part 1** — What does it cost to run *this* resource index? Sizing, scaling, hosting for `quant_index.{json,xlsx}` specifically.
- **Part 2** — Cloudflare R2 + Neon Postgres pricing reference, for Symbols Terminal infrastructure at large.

All numbers verified April 2026 against official vendor docs. The R2/Neon section reflects the **November 2025 Neon compute cut and December 2025 removal of the $5/mo minimum** — treat anything older than that as stale.

> Vendor refs: [developers.cloudflare.com/r2/pricing](https://developers.cloudflare.com/r2/pricing/) · [neon.com/docs/introduction/plans](https://neon.com/docs/introduction/plans) · [neon.com/blog/new-usage-based-pricing](https://neon.com/blog/new-usage-based-pricing)

---

## TL;DR

- **This index (2783 rows, 1.7 MB metadata):** $0/mo on a laptop for the next 3-5 years across any reasonable growth scenario. Free tier of any hosted DB covers it. The only dollars you'd spend are on local archival hardware (~$80 for a 1 TB external SSD) if you decide to mirror papers/repos offline.
- **Symbols Terminal at large:** Neon Launch for Postgres (scale-to-zero plus $0.106/CU-hr is cheap for bursty workloads), R2 for blob storage (zero egress is the killer feature vs S3). Realistic starting bill for a live-but-low-traffic system: **$20-50/mo** total across DB + storage.

The decision rule: **SQL query access → Neon. Blob access by key → R2.** Use both; they compose well.

---

# Part 1 — This Resource Index

Grounded in the current build (2783 rows after BIS pagination, April 2026). Growth projections stated as "per year" so you can interpolate. **No estimate assumes a paid data feed** (Bloomberg, Refinitiv, WRDS, S&P, FactSet) — the index is composed entirely of free/public sources.

---

## 1. Index metadata storage (the DB layer)

### Size per row

| Format | Bytes/row | Current 2783 rows | Notes |
|---|---:|---:|---|
| JSON (current) | ~750 | ~2.1 MB | field names repeat per row |
| SQLite denormalized single table | ~475 | ~1.3 MB | 35% smaller than JSON |
| SQLite normalized (sources/tags junctions) | ~420 | ~1.2 MB | marginal gain; worth it for queryability |
| Postgres | ~500 | ~1.4 MB | row overhead is higher than SQLite |
| DuckDB | ~300 | ~0.8 MB | columnar; best read perf |

### Growth rate (drivers)

| Source | New rows/year | Driver |
|---|---:|---|
| arxiv q-fin (7 cats) | 3,000–5,000 | q-fin submits ~50-100 papers/week across TR/PM/ST/CP/RM/MF/PR |
| Institutional (AQR/Man/Fed/BIS) | 200–500 | Fed FEDS Notes + BIS working papers dominate |
| Blogs (QS/RW/HT) | 100–300 | low; blog cadence is monthly |
| Awesome-lists drift | 50–100 | README updates; slow |
| Seed / seeds_ig | 20–50 | only if HAR is re-captured |
| **Total** | **~3,500–6,000 rows/yr** | |

### Three storage scenarios

#### Scenario A — Minimal: resources table only, upsert-in-place
Single table. No verification log, no historical snapshots. Current rows overwritten on each refresh.

| Year | DB size |
|---|---:|
| 0 (now) | 1.3 MB |
| 1 | ~4 MB |
| 3 | ~12 MB |
| 5 | ~20 MB |
| 10 | ~40 MB |

#### Scenario B — Recommended: + verification log + metric snapshots
One `verification_log` row per resource per scrape run (tracks URL 200-status over time). One `metric_snapshot` row per resource per week (captures citation_count / stargazers for trend lines).

- Verification log: weekly × ~2,800 rows × ~80 bytes = ~12 MB/yr
- Metric snapshots: weekly × ~1,750 rows (papers + repos) × ~40 bytes = ~4 MB/yr

| Year | DB size |
|---|---:|
| 1 | ~20 MB |
| 3 | ~60 MB |
| 5 | ~100 MB |
| 10 | ~200 MB |

#### Scenario C — Aggressive: daily ingest, full history, every index
Daily arxiv polls, full verification log retained forever, indexes on every searchable column.

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
| Neon Postgres free | 0.5 GB | see Part 2 | Scenario B until year ~20 |
| Supabase free | 500 MB | $25/mo Pro | same as Neon |
| Cloudflare D1 free | 5 GB | $0.75/GB/mo over | Scenario C past year 60 |
| Railway Postgres | ~1 GB ($5 credit/mo) | ~$0.25/GB/mo | Scenario B for decades |

**For the DB layer: any free tier works.** Local SQLite is cheapest/simplest; Turso is the best upgrade path if you want remote reads without schema changes.

---

## 2. Content bulk storage (the actual papers/repos the URLs point to)

The metadata index is 2 MB; the content it references is 25-65 GB if you mirror it all.

### Per-type size

| Type | Count in index | Avg size | Bulk |
|---|---:|---:|---:|
| arxiv papers (PDF) | ~920 | ~1 MB | **~1 GB** |
| Institutional whitepapers (BIS/AQR/Fed/Man PDFs) | 642 | ~2-3 MB | **~1.6 GB** |
| Seed + SSRN-accessible papers | ~200 | ~1 MB | **~200 MB** |
| GitHub repos (shallow, `--depth=1 --filter=blob:none`) | 627 | ~5-10 MB | **~3-6 GB** |
| GitHub repos (full clone, full history) | 627 | ~50 MB avg | **20-60 GB** |
| Blog posts (HTML snapshot via `wget -p`) | 388 | ~200 KB | **~80 MB** |
| Textbooks | 3 | — | skip (Amazon links only) |

### Tiers of ambition

| Tier | What you get | Size |
|---|---|---:|
| **1 — Reading archive** | Papers + whitepapers + blogs. No code. | **~3 GB** |
| **2 — Reading + code** | Tier 1 + shallow repo clones. | **~6-9 GB** |
| **3 — Full archive** | Tier 2 + full git history on every repo. | **25-65 GB** |
| **4 — Tier 3 + model weights** | Follows Git LFS on all repos. | **100+ GB** — avoid |

### Storage hardware

| Medium | Cost | Fits |
|---|---:|---|
| Laptop internal SSD (assuming 50+ GB free) | $0 | Tiers 1-3 |
| 1 TB external SSD (Samsung T7 / SanDisk Extreme) | ~$80 one-time | Tiers 1-3 with years of growth buffer |
| 2 TB external SSD | ~$150 one-time | Tier 4 + multi-year |
| AWS S3 Standard, 100 GB | ~$2.30/mo | Tier 3 in cloud |
| Backblaze B2, 100 GB | ~$0.50/mo | Tier 3, cheap cloud |
| Cloudflare R2, 100 GB | ~$1.50/mo (no egress fees) | Tier 3 with API access — see Part 2 |

### Bandwidth / rate constraints on the grab

| Source | Rate limit | 1-time grab time |
|---|---|---|
| arxiv (PDFs) | 1 req / 3 s courtesy | 920 papers × 3 s = **~46 min** serial |
| BIS/RePEc | none published; be polite 1/s | ~600 papers = ~10 min |
| AQR/Man/Fed/Blogs | no documented limit | negligible |
| GitHub shallow clone | TCP-bound; use 8 concurrent workers | 627 repos × ~10 s avg = **~15 min** at 8 concurrency |
| GitHub full clone | same, but transfer-bound | **60-180 min** depending on repo whales |

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

**Do not attempt Bloomberg, Refinitiv, WRDS, or FactSet data through any of these pipes.** Those are separate paid subscriptions the index does not cover.

---

## 3. API + rate-limit costs (for ongoing ingestion)

All APIs used by `index_builder.py` today are **free**. Rate limits are the only operational constraint.

| API | Free limit | With auth | Where used |
|---|---|---|---|
| arxiv Atom API | 1 req / 3 s courtesy; no hard limit | same (no auth option) | Tier 2 |
| Semantic Scholar | 100 req / 5 min unauth | 1000 req/s with API key (free) | Tier 2 citation lookups |
| GitHub REST API | 60 req/hr unauth | 5,000 req/hr with PAT | seed re-verify + could backfill Tier 1 stars |
| arxiv OAI-PMH bulk | unrestricted | — | not used; for full-archive grabs |
| RePEc | unrestricted | — | Tier 3 BIS |

### Cost of auth tokens

- **GitHub PAT**: free. Classic `read:public_repo` scope. ~30 s to generate at https://github.com/settings/tokens
- **Semantic Scholar API key**: free at https://www.semanticscholar.org/product/api. Raises limit from 100/5min to 1/sec. Apply-via-form, 1-2 day turnaround.
- **arxiv**: no auth model. Just observe 3 s spacing.

### What auth unlocks here

| Setup | Unlocks | Runtime impact |
|---|---|---|
| No tokens (current) | Basic unauth operation | seed re-verify ~40 calls; S2 citations 19 min |
| + `GITHUB_TOKEN` env | 5,000 req/hr → Tier 1 repo stars backfill (625 calls) | Tier 1 stars column populates (currently null) |
| + S2 API key | 1 req/s → Tier 2 citations drops from 19 min to 6 min | modest win |

**Neither auth upgrade costs money.** Both worth setting if you re-run monthly.

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
| Tier 3 institutional (incl. BIS × 3 pages) | ~45 s | 6 page fetches |
| Tier 4 SSRN (blocked) | ~10 s | 5 failed calls |
| Tier 5 blogs | ~15 s | 3 page fetches |
| Output writers | ~2 s | 0 |
| **Total** | **~22 min** | ~410 API calls |

### Compute budgets by host

| Host | Free tier | Runs/mo at 22 min each |
|---|---|---:|
| Local laptop | unlimited | ∞ ($0) |
| GitHub Actions (public repo) | 2,000 min/mo | **90 runs/mo** — more than daily |
| GitHub Actions (private repo) | 2,000 min/mo | same |
| Fly.io | 3 × 256 MB CPU-shared VMs free | plenty for a weekly cron |
| Railway | $5 free credit/mo | ~20 runs/mo |
| AWS Lambda (if broken into steps) | 400k GB-sec/mo | essentially free |

### Recommended cadence vs cost

| Cadence | Purpose | $/mo |
|---|---|---:|
| Manual only | Run when you want | $0 |
| launchd/cron weekly | Local laptop, silent-on-failure | $0 |
| GitHub Actions weekly | Cloud-hosted, commits JSON back to repo | $0 |
| GitHub Actions daily | Daily arxiv refresh | $0 (still inside 2,000 min) |
| GitHub Actions hourly | Overkill; spams API budget | $0 infra, potentially blacklisted |

**$0 covers any reasonable cadence.** The only way you pay is if you push into daily S2 citation re-fetches on thousands of papers without a S2 key — that wastes wall-clock, not money.

---

## 5. Hosting costs (if you expose the index)

### Read-only API

| Stack | Cost | Notes |
|---|---:|---|
| Datasette on Fly.io free VM | $0 | serves SQLite directly; publicly readable |
| Datasette on Railway | ~$5/mo | same, easier to set up |
| FastAPI + SQLite on Fly | $0 | if you want custom endpoints |
| Cloudflare Workers + D1 | $0 (100k reqs/day free) | globally edge-deployed |
| Vercel Serverless + Postgres | $0 Hobby | Neon-compatible; 100k invocations |

### Frontend

| Stack | Cost | Notes |
|---|---:|---|
| Next.js on Vercel Hobby | $0 | unlimited if under 100 GB/mo bandwidth |
| Static export on Cloudflare Pages | $0 | unlimited bandwidth |

**Full stack estimate for this index portion: $0–5/mo.**

---

## 6. Total $/month scenarios (this index only)

| Scenario | What you get | One-time | $/mo |
|---|---|---:|---:|
| **A — Status quo** | Current repo, manual rescrapes on laptop | $0 | **$0** |
| **B — Auto-refreshed** | A + GitHub Actions weekly cron | $0 | **$0** |
| **C — Remote-queryable** | B + Turso for remote reads | $0 | **$0** |
| **D — Public API** | C + Fly/Railway FastAPI/Datasette front | $0 | **$5** |
| **E — Paper archive** | D + 1 TB external SSD for offline PDFs | **$80** | $5 |
| **F — Full repo archive** | E + full git clones of all 627 repos | $80 | $5 |
| **G — Cloud mirror** | F + R2/Backblaze backup of archive | $80 | ~$7 |
| **H — DuckDB analytics** | G + DuckDB alongside SQLite for queries | $80 | $7 |

For context: a Bloomberg terminal is ~$24,000/yr. A single WRDS academic subscription is $1,500-4,000/yr. This index — as infrastructure — is ~0.02% of that cost.

---

## 7. Recommended starting setup (this index)

1. **SQLite, local file** (`quant_index.db` alongside `quant_index.json`) — Scenario B schema (resources + sources + verification_log + metric_snapshot).
2. **GitHub PAT in env** — `GITHUB_TOKEN=...` so Tier 1 can backfill stars on 625 repos.
3. **arxiv PDF mirror**, one-time — `~/quant-archive/papers/` (~1 GB, 46 min).
4. **Shallow repo clones on-demand only** — script takes a repo name, clones `--depth=1` into `~/quant-archive/repos/` when you actually need code.
5. **Manual re-runs for now.** Promote to weekly `launchd` after a few weeks.
6. **Defer hosted DB** until you have a real app querying it. SQLite → Turso migration is `turso db create --from-file quant_index.db`, no schema changes.

Marginal cost over current setup: **$0 plus ~90 minutes of one-time setup**.

---

# Part 2 — Platform Reference: Cloudflare R2 & Neon Postgres

Broader reference for Symbols Terminal infrastructure. This part answers: when you eventually reach for a cloud DB or blob store, what will it cost?

---

## Cloudflare R2

S3-compatible object storage. Zero egress fees is the headline — you pay for storage, ops, and (on IA) retrieval only.

### Rates

| Metric | Standard | Infrequent Access |
|---|---|---|
| Storage | $0.015 / GB-month | $0.01 / GB-month |
| Class A ops (writes/mutates) | $4.50 / million | $9.00 / million |
| Class B ops (reads) | $0.36 / million | $0.90 / million |
| Data retrieval (processing) | None | $0.01 / GB |
| Egress (to Internet) | Free | Free |

### Free tier (Standard only, monthly)

- 10 GB-month storage
- 1,000,000 Class A ops
- 10,000,000 Class B ops
- Unlimited free egress

IA has **no free tier**.

### Operation classes

- **Class A (expensive, mutating):** `PutObject`, `CopyObject`, `CreateMultipartUpload`, `UploadPart`, `UploadPartCopy`, `CompleteMultipartUpload`, `ListMultipartUploads`, `ListParts`, `ListObjects`, `ListBuckets`, `PutBucket`, `PutBucketEncryption`, `PutBucketCors`, `PutBucketLifecycleConfiguration`, `LifecycleStorageTierTransition`
- **Class B (reads):** `GetObject`, `HeadObject`, `HeadBucket`, `UsageSummary`, `GetBucketEncryption`, `GetBucketLocation`, `GetBucketCors`, `GetBucketLifecycleConfiguration`
- **Free:** `DeleteObject`, `DeleteBucket`, `AbortMultipartUpload`

### Gotchas

- **Rounding up, always.** 1,000,001 ops → bills as 2,000,000. 1.1 GB-month → bills as 2 GB-month. 1.1 GB retrieved → 2 GB billed. Painful at small scale.
- **Storage is GB-month averaged hourly.** Peak daily storage averaged across a 30-day billing period. Storing 1 GB for 5 days + 3 GB for 25 days = 2.66 GB-month.
- **IA has a 30-day minimum storage duration.** Delete an IA object after 5 days and you still pay for the full 30.
- **Unauthorized requests are free.** Calls that return HTTP 401 are not billed.
- **Egress is only free direct from R2.** Via Workers API, S3 API, and `r2.dev` domains. If a metered service (e.g. another cloud provider) fronts R2, that service will bill you.
- **Super Slurper / Sippy migrations:** tools are free; you pay Class A ops for the copy-in. Objects < 100 MiB (Slurper) / < 200 MiB (Sippy) = 1 Class A op; larger objects use multipart and cost several Class A ops.

### Billing examples (from Cloudflare docs)

| Scenario | Monthly cost |
|---|---|
| 1,000 × 1 GB Standard objects, 1M reads total | $14.85 |
| 1,000 × 1 GB IA objects, deleted after 5 days, 1M reads | $29.90 |
| 100K × 100 KB objects (10 GB), 10M reads/day | $104.40 |

The asset-hosting example is the one to study — storage is in free tier, but 290M billable Class B reads × $0.36/M = $104.40.

### Mental model for Symbols workloads

- **Many small objects, read-heavy** (tick snapshots, chart thumbnails, notebook cell outputs): **Class B ops dominate, not storage.** A viral backtest that triggers millions of reads is where the bill shows up.
- **Big objects, write-once read-many** (Databento historical archives, backtest result bundles): **storage dominates.** Free egress is the killer feature vs S3 — serving 20 TB on S3 costs ~$1,700 in egress; R2 costs $15 for storage, $0 for egress.
- **Cold archives / rarely-accessed backtests:** IA wins on storage ($0.01 vs $0.015) but only if you read **≤ ~3 GB per GB stored per month.** Beyond that, the $0.01/GB retrieval + 2.5× Class A/B op pricing erases the savings. Rule of thumb: if it's read more than 2–3× a month, keep it on Standard.

### Calculator

Live: https://r2-calculator.cloudflare.com/

---

## Neon (Serverless Postgres)

Neon's pricing changed materially in 2025–2026. Treat anything published before November 2025 as stale.

### Timeline of recent pricing changes

- **May 2025:** Databricks acquired Neon for ~$1B.
- **Aug 2025:** Moved to fully usage-based pricing. Storage dropped from $1.75 → $0.35/GB-month (−80%). Compute dropped to $0.14 (Launch) / $0.26 (Scale). $5/month minimum introduced.
- **Oct 2025:** Free-tier compute doubled from 50 → 100 CU-hours per project.
- **Nov 2025:** Compute dropped again: Launch $0.14 → **$0.106** per CU-hour; Scale $0.26 → **$0.222** per CU-hour.
- **Dec 2025:** **$5/month minimum removed.** Paid plans now pay exact usage with no floor.
- **May 1, 2026:** Snapshot storage billing begins at $0.09/GB-month (free during beta until then).

### What you pay for

Four core resources:

1. **Compute** (CU-hours): 1 CU = 1 vCPU + 4 GB RAM. Metered by the second; billed hourly-aggregated.
2. **Storage** (GB-months): metered hourly, summed monthly. Copy-on-write branches only bill the delta.
3. **Extra branch-hours**: only when concurrent branches exceed plan quota.
4. **Instant Restore (PITR) history**: GB-months of retained WAL.

### Plan rates

| Resource | Free | Launch | Scale |
|---|---|---|---|
| Compute | 100 CU-hours / project / month | **$0.106 / CU-hour** | **$0.222 / CU-hour** |
| Storage | 0.5 GB / project (up to 5 GB) | $0.35 / GB-month | $0.35 / GB-month |
| Included simultaneous branches | 10 / project | 10 / project | 25 / project |
| Extra branches | — | $0.002 / branch-hour | $0.002 / branch-hour |
| Instant Restore (PITR) | Up to 6 hours, ≤ 1 GB, free | $0.20 / GB-month | $0.20 / GB-month |
| Max PITR window | 6 hours | 7 days | 30 days |
| Max autoscale | 2 CU | 16 CU (64 GB RAM) | 56 CU (224 GB RAM) |
| Included egress | 5 GB / month | 100 GB / month | contact sales |
| Monthly minimum | $0 | **$0** (removed Dec 2025) | **$0** (removed Dec 2025) |
| Project cap | 10 | 100 | 1,000 |
| SLA | — | — | 99.95% uptime |
| Compliance | — | — | SOC 2 Type 2, HIPAA, GDPR |
| Private networking | — | — | $0.01 / GB (AWS PrivateLink) |

### Snapshots (coming May 1, 2026)

$0.09 / GB-month once billing starts. Scheduled backups don't count against manual snapshot limits on paid plans.

### Key billing mechanics

- **Scale-to-zero:** idle databases suspend after 5 min (Free) or configurable (paid). Cold start ~300–500 ms. This is where the serverless bill savings come from.
- **Copy-on-write branches:** a new branch starts at 0 GB billable and only charges for written deltas vs its parent. Running 1,000 ephemeral preview branches against a 100 GB root does not create 100 TB of billable storage.
- **PITR is WAL volume, not data size.** A quiet 100 GB DB with a 7-day restore window might retain only a few GB of WAL. A write-heavy DB will retain more. Formula: (daily WAL churn) × (restore window days) × $0.20/GB-month.
- **Usage starts at zero on paid plans.** Free-tier allowances do not carry over once you upgrade.
- **Archived branches bill at the same rate as active branches** — Neon auto-archives inactive branches but you still pay for their storage.

### Worked examples (from Neon docs)

**Launch, small prod app**
- Compute: 250 CU-hours (2 CU × 125 hrs): 250 × $0.106 = **$26.50**
- Root branch storage: 40 GB × $0.35 = **$14.00**
- Child branch delta: 10 GB × $0.35 = **$3.50**
- PITR (20 GB WAL × 7d): 20 × $0.20 = **$4.00**
- **Total: ~$48**

**Scale, mid-size prod**
- Compute: 1,700 CU-hours (4 CU × 425 hrs): 1,700 × $0.222 = **$377.40**
- Root storage: 100 GB × $0.35 = **$35.00**
- Child delta: 25 GB × $0.35 = **$8.75**
- PITR: 50 GB × $0.20 = **$10.00**
- **Total: ~$431**

**Launch, light SaaS (0.5 CU × 8 hrs/day × 30 days, 10 GB)**
- Compute: 120 CU-hours × $0.106 = **$12.72**
- Storage: 10 × $0.35 = **$3.50**
- **Total: ~$16** (well above $0 floor, no minimum applies)

### Mental model for Symbols workloads

- **Single-process FastAPI backend (Symbols today, no Redis).** Neon Launch fits well: scale-to-zero on dev branches is essentially free, prod compute billed only when requests hit. One instance at 0.5 CU running 12 hrs/day ≈ 180 CU-hrs × $0.106 = **$19/month** compute.
- **Preview branches per PR / per feature spec.** Copy-on-write means near-free until the branch writes — ideal for validating regime_executor changes against a realistic dataset without duplicating storage.
- **Dev/staging that's idle overnight and weekends.** Scale-to-zero cuts the bill to roughly business hours only. A dev DB that would be $40/mo always-on drops to ~$10–12/mo with proper idle.
- **Heavy read workloads (backtest playback, chart scrub).** Compute scales up automatically — model as peak CU × peak hours, not as 24/7 at peak. Cap the autoscale max to avoid runaways.
- **When Neon becomes the wrong answer:** always-on, high-utilization workloads at 8+ CU consistently. At that duty cycle, RDS reserved instances or self-hosted Postgres on a colo box starts winning on price. Rule of thumb: if you'd run > ~4 CU for > ~600 hrs/month steady, run the numbers against RDS reserved.

### Cost-control levers

1. **Enable scale-to-zero on every non-prod branch.** Default on Free, configurable on paid.
2. **Cap autoscale max CU** per branch — prevents a runaway query from eating $200 of compute.
3. **Delete unused branches.** They bill even when archived.
4. **Shorten PITR window** on dev/preview. 7d → 1d meaningfully cuts WAL storage.
5. **Keep root branch lean.** Child branches only pay deltas; bloat in root compounds across every branch.

---

## R2 vs Neon: when to use which

| Use case | Answer |
|---|---|
| Historical Databento archives (Parquet) | R2 Standard |
| Cold backtest result bundles (rarely read) | R2 IA |
| Serving chart thumbnails / static assets | R2 Standard + Workers |
| User accounts, positions, OAuth tokens | Neon |
| Regime configs, notebook metadata | Neon |
| Tick snapshots queried by timestamp range | Neon (with proper indexing) or R2 + Parquet |
| Backtest trade logs needing SQL aggregation | Neon |
| Large model checkpoints / ML artifacts | R2 Standard |
| This resource index (2,783 rows) | SQLite local; migrate to Neon free if remote access needed |

**SQL query access → Neon. Blob access by key → R2.** Use both; they compose well.

---

## Quick cost-decision rules (across both parts)

- **<10 MB DB, local only** → SQLite file, no ceremony.
- **<9 GB DB, remote access wanted** → Turso free.
- **Need full Postgres features (JSONB, FTS, pg_trgm)** → Neon free up to 0.5 GB; then usage-based (no minimum since Dec 2025).
- **Public-readable API, low traffic** → Datasette on Fly free / Cloudflare Workers + D1.
- **Downloaded papers / repos >10 GB** → external SSD > cloud storage (egress fees on AWS/GCP hurt).
- **Archive >100 GB with cloud access** → R2 (no egress fees) or Backblaze B2.
- **Don't mirror stable-diffusion weights or any Git LFS model assets.** They push you from 65 GB to 100+ GB for no analytical gain.

---

## What breaks the $0/mo tier

In rough order of likelihood:

1. **>500 MB DB on Neon/Supabase free tier.** Scenario C hits this around year 6. Migration path: Turso (9 GB free) or Cloudflare D1 (5 GB free).
2. **>9 GB DB anywhere.** Very unlikely; requires daily ingest + full-history retention for decades.
3. **Hosting a public archive with real traffic.** Bandwidth overages on Vercel ($40/TB over 100 GB), Fly ($0.02/GB egress). Static CDN (Cloudflare Pages) has unlimited bandwidth — prefer it.
4. **GitHub Actions hitting 2,000 min/mo.** Only if you run hourly for some reason.
5. **Exceeding S2's 100 req/5 min unauth.** Happens in a single run if you expand `ARXIV_CITATION_TOP_N` from 50 to ~100 across 7 cats. Get a free S2 API key.
6. **R2 read-heavy asset hosting.** Hit the 10M Class B free tier with a viral URL and Class B ops are $0.36/M from row 10M+1. Cache aggressively.
7. **Paying for SSRN, Bloomberg, Refinitiv, FactSet, or WRDS.** Out of scope for this index by design.

---

## Changelog

- **2026-04-23:** Merged into a single doc. Part 1 numbers reflect 2783-row state (BIS expanded from 199 to 595 rows). Part 2 (R2 + Neon) verified against official vendor docs as of this date. Neon rates reflect Nov 2025 compute cut ($0.106/$0.222) and Dec 2025 removal of $5 minimum.
- **2026-04-22:** Initial split across two files.
