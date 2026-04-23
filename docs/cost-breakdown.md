# Cost Breakdown: Cloudflare R2 & Neon

Reference pricing for Symbols Terminal infrastructure. Last verified April 2026 against official vendor docs.

> Source of truth: [developers.cloudflare.com/r2/pricing](https://developers.cloudflare.com/r2/pricing/) · [neon.com/docs/introduction/plans](https://neon.com/docs/introduction/plans) · [neon.com/blog/new-usage-based-pricing](https://neon.com/blog/new-usage-based-pricing)

---

## Cloudflare R2

S3-compatible object storage. Zero egress fees is the headline — you pay for storage, ops, and (on IA) retrieval only.

### Rates

| Metric                        | Standard              | Infrequent Access     |
| ----------------------------- | --------------------- | --------------------- |
| Storage                       | $0.015 / GB-month     | $0.01 / GB-month      |
| Class A ops (writes/mutates)  | $4.50 / million       | $9.00 / million       |
| Class B ops (reads)           | $0.36 / million       | $0.90 / million       |
| Data retrieval (processing)   | None                  | $0.01 / GB            |
| Egress (to Internet)          | Free                  | Free                  |

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

| Scenario                                                     | Monthly cost |
| ------------------------------------------------------------ | ------------ |
| 1,000 × 1 GB Standard objects, 1M reads total                | $14.85       |
| 1,000 × 1 GB IA objects, deleted after 5 days, 1M reads      | $29.90       |
| 100K × 100 KB objects (10 GB), 10M reads/day                 | $104.40      |

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

| Resource                      | Free                              | Launch                     | Scale                      |
| ----------------------------- | --------------------------------- | -------------------------- | -------------------------- |
| Compute                       | 100 CU-hours / project / month    | **$0.106 / CU-hour**       | **$0.222 / CU-hour**       |
| Storage                       | 0.5 GB / project (up to 5 GB)     | $0.35 / GB-month           | $0.35 / GB-month           |
| Included simultaneous branches | 10 / project                     | 10 / project               | 25 / project               |
| Extra branches                | —                                 | $0.002 / branch-hour       | $0.002 / branch-hour       |
| Instant Restore (PITR)        | Up to 6 hours, ≤ 1 GB, free       | $0.20 / GB-month           | $0.20 / GB-month           |
| Max PITR window               | 6 hours                           | 7 days                     | 30 days                    |
| Max autoscale                 | 2 CU                              | 16 CU (64 GB RAM)          | 56 CU (224 GB RAM)         |
| Included egress               | 5 GB / month                      | 100 GB / month             | contact sales              |
| Monthly minimum               | $0                                | **$0** (removed Dec 2025)  | **$0** (removed Dec 2025)  |
| Project cap                   | 10                                | 100                        | 1,000                      |
| SLA                           | —                                 | —                          | 99.95% uptime              |
| Compliance                    | —                                 | —                          | SOC 2 Type 2, HIPAA, GDPR  |
| Private networking            | —                                 | —                          | $0.01 / GB (AWS PrivateLink) |

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

| Use case                                     | Answer   |
| -------------------------------------------- | -------- |
| Historical Databento archives (Parquet)      | R2 Standard |
| Cold backtest result bundles (rarely read)   | R2 IA    |
| Serving chart thumbnails / static assets     | R2 Standard + Workers |
| User accounts, positions, OAuth tokens       | Neon     |
| Regime configs, notebook metadata            | Neon     |
| Tick snapshots queried by timestamp range    | Neon (with proper indexing) or R2 + Parquet |
| Backtest trade logs needing SQL aggregation  | Neon     |
| Large model checkpoints / ML artifacts       | R2 Standard |

The decision reduces to: **SQL query access → Neon. Blob access by key → R2.** Use both; they compose well.

---

## Changelog of this doc

- 2026-04: Initial version. R2 rates current per official docs. Neon rates reflect Nov 2025 compute cut ($0.106/$0.222) and Dec 2025 removal of $5 minimum.
