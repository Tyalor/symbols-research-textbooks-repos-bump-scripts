# Audit Prompts — Fresh-Chat Verification

Standalone prompts to paste into a new Claude Code session. Each is self-contained; none reference prior-conversation context. Run from the project root.

**Layout a fresh auditor should expect:**
- `index_builder.py` at repo **root**
- `data/quant_index.json` and `data/quant_index.xlsx` — primary outputs
- `docs/INDEX_SUMMARY.md`, `docs/AUDIT_PROMPTS.md` (this file), `docs/COST_BREAKDOWN.md`, `docs/EXTRACTION_NOTES.md`, `docs/cost-breakdown.md`, `docs/EQUITY_REPORTS_PLAN.md`, `docs/TEXTBOOKS.md`
- `legacy/` holds the generic IG-HAR extraction toolkit; the original seed curation has been fully merged into `data/quant_index.json` under source=`seeds_ig`

**Known state as of last build (2026-04-23):**
- 2783 unique resources across 6 sheets
- Seeds_IG 60 · Awesome_Lists 617 · ArXiv 1096 · Institutional 642 · SSRN_TopTen 0 · Blogs 388
- BIS expanded from ~200 → ~595 (paginated 3 RePEc pages)
- SSRN_TopTen is **intentionally zero** — Cloudflare 403s; documented in `docs/INDEX_SUMMARY.md`
- Alpha Architect and Two Sigma were dropped from Tier 3 (Cloudflare / JS-rendered); not a bug
- Slug-based secondary dedup merges type=repo rows with matching (title-slug, owner); when both have URLs, a prefix guard prevents over-merging same-owner different-project repos

**Order of use:** 1, 3, 8 (offline, fast). Then 2, 4 (modest API costs). Then 5, 7, 9 (noise-hunting, most likely to find real issues).

If any audit turns up something, paste its output back into the build session (not a fresh one) — the build session has the context to fix. Fresh sessions exist for independent verification only.

---

## Prompt 1 — Schema + integrity (no network)

```
Run from the project root. Build session already wrote data/quant_index.json and data/quant_index.xlsx. Do not modify files. Do not scrape. Verify:

1. data/quant_index.json parses cleanly. Every resource has: resource_id, type ∈ {paper,repo,textbook,whitepaper,blog_post}, title, sources (non-empty list of strings), canonical_url (may be empty only for URL-less seeds), confidence ∈ {high,medium,low}, mention_count (int ≥ 1), retrieved_at (ISO8601 with Z suffix or +offset).

2. All resource_ids are unique. Show any collisions with their titles.

3. For every row with a non-empty canonical_url, re-derive resource_id = sha1(normalized_url).hexdigest()[:16] where normalization matches index_builder.py:normalize_url (lowercase github owner/repo, strip .git suffix, strip trailing slash, drop utm_/fbclid/gclid/mc_cid/mc_eid params, arxiv → https://arxiv.org/abs/<id> no version, SSRN → https://papers.ssrn.com/sol3/papers.cfm?abstract_id=<n>). Count mismatches.

4. URL-less rows (canonical_url="") should have resource_id starting with "n_". Count exceptions.

5. Row count parity: data/quant_index.json["count"] should equal the All_Deduped data-row count in data/quant_index.xlsx. Flag drift.

6. Spot-check 20 random resource_ids — for each, verify the row's `sources` column in per-source sheets (e.g. Awesome_Lists) matches the `sources` list on the matching All_Deduped row.

Report: pass/fail per check, counts, any violations. Under 300 words.
```

---

## Prompt 2 — Seed re-verification sanity (~40 GitHub API calls)

```
Run from the project root. The seed curation pass produced 22 papers + 39 repos (61 total). These should all be present in data/quant_index.json tagged with "seeds_ig" in the sources array. After dedup against awesome-lists a few seeds share rows with awesome-list sources; expect ~60 unique rows for the seeds_ig tag.

1. Every seed repo (rows tagged seeds_ig with type=repo) should have a matching title in data/quant_index.json. List any anomalies.

2. For each seed repo with a non-empty canonical_url, GET https://api.github.com/repos/{owner}/{repo} (Accept: application/vnd.github+json). Status 200 required. If 404 appears, flag — seed rows with broken URLs need scrubbing.

3. Three seeds were previously flagged as unverifiable in docs/EXTRACTION_NOTES.md: julius, Ziplime, Stock Research Agent. For each, confirm data/quant_index.json has the row retained (synthetic "n_" resource_id if URL is empty). Specifically for julius: its canonical_url must either be empty or have owner containing "julius" (NOT "bvschaik" — that was a search-fallback bug fixed in an earlier pass).

4. Seed repos with citation_count_or_stars set: sanity-check by order-of-magnitude. OpenBBTerminal ~50k+, Python-100-Days ~150k+, stable-diffusion ~70k+. Flag rows off by >10x.

Report under 200 words.
```

---

## Prompt 3 — Awesome-list noise audit (no network)

```
Run from the project root. Tier 1 scraped README.md of wilsonfreitas/awesome-quant (emitted under source tag "awesome-quant", ~438 rows) and firmai/financial-machine-learning (emitted under source tag "financial-ml", ~191 rows). NOTE: the tag is "financial-ml", not "financial-machine-learning" — expect zero rows for the longer name. Walk data/quant_index.json:

1. Any row where type="repo" but canonical_url does not match https://github.com/[a-z0-9_.-]+/[a-z0-9_.-]+ (lowercased; leading `-` is legal for GitHub repos). Count violations. The known-legit exceptions `rastaman4e/-1` and `jettbrains/-l-` have leading-dash repo names; don't flag those.

2. Rows with type="repo" AND title length < 4 characters. Expected count ~22 (bare repo names like "ta", "bt", "xts", "TTR", "XAD", "-1", "-L-" where markdown link text was just the repo's short name). List them all — sanity check by confirming each canonical_url has a plausible owner+repo path. These aren't bugs, just ugly; confirm not data corruption.

3. topic_tags should contain the heading context ("Awesome Quant > ...", etc.). Flag any row where topic_tags is "Table of Contents", "License", "Contributing", "See Also", "Contents", or empty-for-Tier-1.

4. Top 10 canonical_urls that appear with different titles across per-source sheets (means the merge took the longer title, which is correct behavior — just confirm the winner is sensible).

5. Any canonical_url containing "shields.io", "badge.fury", ".png", ".jpg", ".svg", ".gif" should be ZERO. If any exist, the badge filter is broken.

6. Count repos where canonical_url begins with https://github.com/firmai/ — confirm <5 (the awesome-list README itself shouldn't self-reference heavily).

Report. Under 300 words.
```

---

## Prompt 4 — ArXiv Tier 2 completeness + citations

```
Run from the project root. Tier 2 scraped 7 q-fin categories (TR, PM, ST, CP, RM, MF, PR), 200 most-recent each, then backfilled Semantic Scholar citation counts for the top 50 per category (~350 S2 calls).

1. For each of arxiv/q-fin.TR, arxiv/q-fin.PM, arxiv/q-fin.ST, arxiv/q-fin.CP, arxiv/q-fin.RM, arxiv/q-fin.MF, arxiv/q-fin.PR — count rows. Each should be 200 (±5 for intra-run dedup). Flag anything under 180.

2. Every arxiv row's canonical_url must match ^https://arxiv\.org/abs/\d{4}\.\d{4,5}$ exactly (no version suffix, no /pdf/, no trailing slash). Count violations.

3. Every arxiv row should have year (int), authors_or_owners (non-empty), date_published (YYYY-MM-DD). Count rows missing any.

4. Rows with citation_count_or_stars set should be ~350. For those with citations ≥ 100, why_notable should be non-empty. Count mismatches.

5. Any arxiv row with year < 2020 or year > 2027 is a parse bug (Tier 2 fetches only the 200 most recent). Flag.

6. Pick 5 rows with the highest citation_count_or_stars, hit https://api.semanticscholar.org/graph/v1/paper/arXiv:{id}?fields=citationCount, confirm within ±10%. If S2 returns 404 for the id, flag (arxiv ID format mismatch).

Report per-category counts and any anomalies. Under 300 words.
```

---

## Prompt 5 — Institutional (Tier 3) signal audit

```
Run from the project root. Tier 3 sources after patching:
- aqr (~11 rows)
- man-institute (~6 rows)
- fed-feds-notes (~30 rows)
- bis-wp-repec (~550-600 rows after paginating 3 RePEc pages; was ~199 when single-page)

alpha-architect and two-sigma were REMOVED (Cloudflare 403 / JS-rendered respectively). Zero rows for those source tags is correct.

1. Count rows per source tag. Expect AQR 8-15, Man 4-10, Fed 25-40, BIS 500-620. Flag out-of-range. Also flag any count within 2 of a round number (100, 200, 500, 600) — suggests an undetected pagination cap.

2. For BIS: every canonical_url must start with https://ideas.repec.org/p/bis/biswps/. Count violations. Titles should be real paper titles, not "By citations", "By downloads", "By date", "Share", "Tweet", "PDF" — if any of those slipped through, the junk-filter failed.

3. For AQR/Man/Fed: list 5 titles from each. Flag if they look like nav text ("Research", "Insights", "Contact", "Subscribe", "Privacy Policy"), short <10 chars, or URL fragments.

4. Spot-check: hit HEAD on 2 URLs per source with curl -sI (browser UA). Confirm 200, not 301-to-homepage. If any redirect to the site root, the URL pattern was too loose.

5. Confirm no rows exist with source tag "alpha-architect" or "two-sigma" — if present, the build session forgot to drop them.

Report under 300 words. If BIS has >10% junk titles, suggest adding filters to the BIS-specific branch in run_tier3_institutional.
```

---

## Prompt 6 — SSRN (Tier 4) confirmed-zero check (no network)

```
Run from the project root. Tier 4 (SSRN top-ten) is expected to have ZERO rows because SSRN's topTenResults.cfm pages return Cloudflare 403 to all unauth scrapers. This is documented in INDEX_SUMMARY.md.

1. Count rows with source tag starting "ssrn-" in data/quant_index.json. Expected: 0. If >0, the build session accidentally kept stale data — investigate.

2. Count data rows in the SSRN_TopTen sheet of data/quant_index.xlsx. Expected: 0.

3. INDEX_SUMMARY.md should include a note about SSRN being blocked with a ⚠ flag. If missing, the summary generator is stale.

4. Optional: run this curl and confirm the block is still real (one call, no retry):
   curl -sI -A "Mozilla/5.0" "https://papers.ssrn.com/sol3/topten/topTenResults.cfm?groupingId=203597&netorjrnl=ntwk"
   Expected status: 403. If 200, SSRN changed policy and a re-run of tier4 would now succeed — flag as "worth retrying."

Report under 150 words.
```

---

## Prompt 7 — Blogs (Tier 5) noise audit

```
Run from the project root. Tier 5 scraped index pages of QuantStart (~286 rows), Robot Wealth (~17 rows), Hudson & Thames (~85 rows). The classifier filters out path fragments: /topic/, /category/, /tag/, /author/, /page/, /feed, /archive, /ebook.

1. Count rows per source. Flag quantstart <200 or >400 (means selector broke); robot-wealth <10 or >50; hudson-thames <30 or >150.

2. Sample 10 blog_post rows per source. For each, confirm the URL path is an article slug, not a category/archive/search page. Any remaining /topic/, /category/, /tag/, /author/, /page/, /feed, /archive/ slips through = filter bug.

3. QuantStart rows typically look like /articles/{slug} or /{title}-ebook. Flag rows that are root-level (just /something) without an /articles/ prefix EXCEPT ebooks — those are intentional.

4. For type="paper" or type="repo" rows with source tag in {quantstart, robot-wealth, hudson-thames} — the regex-extracted arxiv/SSRN/github refs. For 3 random such rows per blog, hit HEAD on the canonical_url. If any 404, the regex captured a truncated URL.

5. All blog-sourced rows should have topic_tags containing "recommended-by-<blog-tag>". Count rows missing this.

Report under 300 words. If any source has >15% noise, suggest adding to BLOG_NOISE_PATHS in index_builder.py.
```

---

## Prompt 8 — Deliverables cross-check (offline)

```
Run from the project root. Verify deliverables match the spec.

1. data/quant_index.xlsx sheets (exact names, exact order): All_Deduped, Seeds_IG, Awesome_Lists, ArXiv, Institutional, SSRN_TopTen, Blogs. Flag missing or renamed.

2. Row 1 of every sheet: all cells bold (openpyxl Font.bold=True). freeze_panes="A2" on every sheet.

3. Column widths: title column wide (>40), resource_id narrow (<25), year <10. Flag sheets with default 8.43 width on wide columns.

4. data/quant_index.json: valid UTF-8, indent=2 pretty-printed, ends with newline. Top-level keys: generated_at, count, resources.

5. INDEX_SUMMARY.md: has one subsection per source (6 total: Seeds_IG, Awesome_Lists, ArXiv, Institutional, SSRN_TopTen, Blogs). Each subsection names the row count. Blocked sources (SSRN) flagged with ⚠. Known gaps section enumerates SSRN block, paperswithcode dead, AA/TS Cloudflare, unbackfilled Tier 1 stars.

6. index_builder.py: CONFIG block near top contains RUN dict with keys seeds, tier1_awesome, tier2_arxiv, tier3_institutional, tier4_ssrn, tier5_blogs — all settable without code edits.

7. Idempotency (content-stable under cache reload): the `generated_at` field of data/quant_index.json changes every run, so a naive file-hash diff always fails. Instead do this:
   ```python
   import json, hashlib
   def digest():
       d = json.load(open("data/quant_index.json"))
       # hash the resources array only, sorted by resource_id for determinism
       body = json.dumps(sorted(d["resources"], key=lambda x: x["resource_id"]), sort_keys=True)
       return hashlib.sha256(body.encode()).hexdigest()
   before = digest()
   # reload cache without re-scraping
   import index_builder as ib
   ib.RUN = {k: False for k in ib.RUN}
   ib.main([])
   after = digest()
   assert before == after, "idempotency broken: cache reload changed resource content"
   ```
   Should complete in <5s and `before == after`. If they differ, dump the first 3 differing rows — that's where the non-determinism lives.

Report under 300 words.
```

---

## Prompt 9 — Cross-source merge correctness (no network)

```
Run from the project root. When a resource appears in multiple sources the build session's merge logic (index_builder.py:merge_resources) is supposed to union sources, keep the highest confidence, sum mention_count, and take the longer title/summary.

1. Find every row where sources has length ≥ 2. Report the count. Flag only if 0 (dedup broken entirely) or >500 (dedup too aggressive, merging unrelated rows). Expect multi-hundreds — arxiv papers cross-listed across q-fin categories produce most of these, plus seed × awesome-list overlap on popular repos.

2. For each multi-source row, verify the canonical_url appears in only ONE row of data/quant_index.json (no dup). If there are two rows with the same canonical_url, dedup is broken.

3. For the row with title "OpenBBTerminal" (or similar slug): sources should include BOTH "seeds_ig" AND "awesome-quant". mention_count ≥ 72 (the seed pass had 72+ post references). confidence should be "high". If two separate rows exist (one per source), the slug-dedup pass failed — the builder merges repos with matching (slug, owner) as of this commit.

4. Spot check: for 5 multi-source rows, confirm the title is non-empty, canonical_url is the lowercased github.com/owner/repo form, and confidence is "high" or "medium" (never "low" for a cross-validated resource).

5. Count confidence distribution in multi-source rows. Expected: mostly high (because at least one source validates it strongly). Flag if >20% are "low".

Report under 250 words.
```

---

## How to triage findings

- **Schema errors** (Prompt 1): block — fix before shipping.
- **Seed-repo bugs** (Prompt 2 #2, #3): block — seeds are the trust anchor.
- **Noise in one source** (Prompts 3, 5, 7): downgrade confidence for that source tag rather than delete rows; list the fix and re-run just that tier (`RUN[tierN_*]=True`, others False).
- **Silent zero-row sources**: always investigate. Silence without an INDEX_SUMMARY ⚠ note is a scraper failure, not an empty upstream.
- **Dedup collisions** (Prompts 1 #3, 9 #2): suggests normalize_url missed a case. Add the case, re-hash, re-run from cache.

Re-running from cache after a fix takes <5s — don't regenerate from scratch unless Tier 2 (arxiv) data is what changed.
