# Quant Resource Index — Summary

**Generated:** 2026-04-23T00:30:26Z
**Unique resources:** 2384
**By type:** paper=1121, repo=627, blog_post=387, whitepaper=246, textbook=3
**By confidence:** high=1146, medium=1235, low=3

## Sources

### Seeds_Quantscience_IG
**Rows:** 60  
**Date range:** 2006–2026  
Loaded from quantscience_findings.xlsx (22 papers + 39 repos). URLs re-verified via GitHub API; search fallback requires owner match to avoid swapping in unrelated repos (the bvschaik/julius bug was caught here).
### Awesome_Lists
**Rows:** 608  
**Date range:** n/a  
Parsed README.md of wilsonfreitas/awesome-quant + firmai/financial-machine-learning. Badges, image assets, and non-quant links filtered via classify_url. paperswithcode skipped: site redirects to huggingface.co/papers (dead).
### ArXiv
**Rows:** 1096  
**Date range:** 2024-09-10–2026-04-21  
Fetched 200 most-recent per category from export.arxiv.org Atom API (3s pacing). Semantic Scholar citation counts backfilled for top 50 per category (350 total, ~19min at 3.2s/req unauth).
### Institutional
**Rows:** 246  
**Date range:** 2026-04-07–2026-04-22  
Browser UA used to avoid Cloudflare 403s. BIS pulled via RePEc mirror (bis.org/publ/work.htm is 404 as of this run). Alpha Architect and Two Sigma both return 403 or JS-hydrated placeholders — dropped.
### SSRN_TopTen
**Rows:** 0 ⚠ blocked (Cloudflare 403)  
**Date range:** n/a  
All 5 top-ten pages return Cloudflare 403 to unauth scrapers. Not fixable without a browser session or login. Zero rows — noted, not retried.
### Blogs
**Rows:** 388  
**Date range:** n/a  
QuantStart, Robot Wealth, Hudson & Thames. Posts filtered to exclude topic/category/tag/author/page/feed/archive/ebook paths. Embedded arxiv/SSRN/github references extracted from index pages.

## Known gaps / decisions

- **SSRN top-ten (Tier 4):** Cloudflare 403 on all 5 groupings. No workaround without auth.
- **paperswithcode:** 302 → huggingface.co/papers (site retired). Skipped.
- **Alpha Architect, Two Sigma:** Cloudflare-blocked / JS-hydrated respectively. Dropped from Tier 3.
- **Tier 1 repo stars:** not backfilled — 625 calls exceeds 60/hr unauth GitHub budget. Set `GITHUB_TOKEN` and re-run with RUN['tier1_awesome']=True for star counts.
- **Awesome-list short titles:** 5 rows have title <4 chars (e.g. `ta`, `bt`) — markdown link text was just the bare repo name. URLs are real; titles could be backfilled from GitHub.

