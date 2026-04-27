# Finance & Trading Book Repositories

Pointer index for GitHub repos that bundle finance/trading textbook PDFs, companion code, or curated reading lists. The `quant_index.json` is for *URL-addressable* resources (papers, blogs, repos, publisher pages). Bulk PDF dumps don't fit that schema directly — this doc captures them so you know what exists, how much it weighs, and how to pull it without dragging a 1+ GB working tree onto every clone.

Five user-added repos plus six sibling candidates I verified while compiling this. Counts and sizes are from the GitHub API at the time of writing — re-check before pulling, since several repos sit on the edge of GitHub's 2 GB file-host comfort zone.

## Categories

1. **PDF book dumps** — repos whose value is the binary content. Use sparse-checkout/partial-clone; never let CI clone these by accident.
2. **Curated awesome-lists** — repos whose README is the value. These are URL lists; if dense enough, wire them as a Tier 1 source in `index_builder.py` rather than pulling manually.
3. **Companion code + book** — repos paired with a published book. The code is small; the book may or may not be in-tree.

---

## 1. PDF book dumps

| Repo | Stars | Size | Files | Notes |
|---|---:|---:|---:|---|
| [bharaniabhishek123/some-investment-books](https://github.com/bharaniabhishek123/some-investment-books) | 770 | ~1.6 GB | 160 | Trading + investing classics. Mix of `.pdf`, `.epub`, `.mobi`, `.azw`. Default branch: `master`. Fork of `pistolla/gnidart`. |
| [alexisetechas/financial-market-trading-books-pdf](https://github.com/alexisetechas/financial-market-trading-books-pdf) | 6 | ~1.5 GB | 100+ | Author's stated description: "100+ PDF books on financial markets, trading, and quantitative analysis." Default branch: `main`. |
| [zslucky/algorithmic_trading_book](https://github.com/zslucky/algorithmic_trading_book) | 619 | ~15 MB | 2 books + code | Two algorithmic trading books with companion source code. Default branch: `master`. |
| [wx2123/Top-Investment-Books](https://github.com/wx2123/Top-Investment-Books) | 0 | ~37 MB | — | "Wall Street classical investment books." Default branch: `main`. |
| [IamBibekChhetri/technical_analysis_books](https://github.com/IamBibekChhetri/technical_analysis_books) | 0 | ~42 MB | — | Technical analysis dump. Default branch: `bibek-dev` (not `main`). |
| [Moulik3925/Quantitative-Finance-Books](https://github.com/Moulik3925/Quantitative-Finance-Books) | 0 | ~33 MB | — | Quant finance dump. Default branch: `main`. |
| [wen-jie-yuan/Finance-books](https://github.com/wen-jie-yuan/Finance-books) | 69 | ~2.9 MB | — | Chinese-language value investing collection. Default branch: `master`. |

### How to pull a single book without cloning the whole repo

```bash
# Set per-repo
REPO=https://github.com/bharaniabhishek123/some-investment-books.git
BRANCH=master   # check the table above — some are 'main' or 'bibek-dev'

git clone --filter=blob:none --no-checkout --depth=1 "$REPO" repo
cd repo
git sparse-checkout init --cone
git sparse-checkout set "Encyclopedia of Chart Patterns 2nd edition 2005.pdf"
git checkout "$BRANCH"
```

Filenames have spaces — keep them quoted. `--filter=blob:none` defers blob downloads until checkout, so the initial clone is metadata-only (~10 MB instead of 1.6 GB).

### How to list everything before pulling

```bash
gh api "repos/<owner>/<repo>/contents" \
  --jq '.[] | select(.type=="file") | "\(.size)\t\(.name)"' \
  | sort -nr | head -30
```

### License caveats

None of the bulk-PDF repos in this section carry a license file in the GitHub metadata. They are almost certainly redistributing copyrighted material without permission. Treat them as a discovery aid (titles + ISBNs) rather than a source you can cite or re-host. The clean path is: pick titles from these repos, then buy / borrow / find the publisher version, and only the *publisher URL* goes into `quant_index.json`.

`docs/TEXTBOOKS.md` already lists 60+ canonical titles with verified ISBN-13s and publisher links — start there before reaching for these dumps.

---

## 2. Curated awesome-lists

These belong in the index, not in this doc as binaries — but listing them here for symmetry with the dumps.

| Repo | Stars | Status | Notes |
|---|---:|---|---|
| [cbailes/awesome-deep-trading](https://github.com/cbailes/awesome-deep-trading) | 1874 | **Indexed** (Tier 1) | Wired into `index_builder.py:run_tier1_awesome` as `awesome-deep-trading`. Contributed 90 rows (65 papers, 21 repos, 4 blogs) at last refresh. |
| [cybergeekgyan/Quant-Developers-Resources](https://github.com/cybergeekgyan/Quant-Developers-Resources) | 3039 | Not indexed | Markdown-link curation across 24 topical subdirectories (Econometrics, Risk Management, Optimization Theory, etc.). Most subdirs are stub READMEs pointing to external resources. The `TextBooks/` subdir is a single 4 KB readme — value is in topic-specific READMEs, not file content. |

To wire `Quant-Developers-Resources` into the index later, walk every `*.md` file under the repo and feed each into `parse_awesome_markdown()` — same call shape as the existing Tier 1 sources, just multi-file:

```python
# Sketch — drop into run_tier1_awesome
import requests
api = "https://api.github.com/repos/cybergeekgyan/Quant-Developers-Resources/git/trees/main?recursive=1"
tree = requests.get(api).json()["tree"]
md_files = [n["path"] for n in tree if n["path"].endswith(".md")]
for path in md_files:
    raw = f"https://raw.githubusercontent.com/cybergeekgyan/Quant-Developers-Resources/main/{path}"
    r = http_get(raw)
    if r and r.status_code == 200:
        rows.extend(parse_awesome_markdown(r.text, "quant-dev-resources", f"https://github.com/cybergeekgyan/Quant-Developers-Resources/blob/main/{path}"))
```

I haven't merged that in this turn — `cybergeekgyan/Quant-Developers-Resources` skews heavily toward generic CS interview prep (operating systems, computer networks, brain teasers), not quant content. A direct ingest would dilute the index. Worth a manual pre-filter to `Econometrics/`, `Financial Theory/`, `Risk Management/`, `Optimization Theory/`, `Statsmodels/`, `Reinforcement Learning/`, `Technical_Indicators/`, `Credit Risk Modeling/`, `Game Theory/` before scraping.

---

## 3. Companion code + single-book repos

| Repo | Stars | Size | Notes |
|---|---:|---:|---|
| [QuantInsti/ml-trading-book](https://github.com/QuantInsti/ml-trading-book) | 6 | ~3.8 MB | "Book on Machine Learning in Trading with real-world applications." Repo is the companion code (Python notebooks + `data_modules/`). The book itself is not in-tree. Dual-licensed (MIT + CC). Default branch: `main`. |
| [ali-azary/Algorithmic-Trading-From-Beginner-to-Advanced](https://github.com/ali-azary/Algorithmic-Trading-From-Beginner-to-Advanced) | 9 | ~5.8 MB | Single-PDF mini-book (`book/Algorithmic Trading From Beginner to Advanced.pdf`, 6 MB) + curated Backtrader strategies under `codes/`. Default branch: `main`. |

These are small enough that a normal `git clone` is fine — no sparse-checkout needed.

---

## Sibling-repo discovery method (for adding more later)

The candidates in section 1 came from these `gh search repos` queries:

```bash
gh search repos "investment books"   --limit 30 --json fullName,stargazersCount,description,size
gh search repos "trading-books"      --limit 20 --json fullName,stargazersCount,description,size
gh search repos "quantitative-finance books" --limit 20 --json ...
```

Sort by stars descending, drop anything that is clearly a book-trading marketplace (people swapping physical novels), and verify each candidate's `default_branch`, license absence, and total size before adding to this doc.

A repo passes the bar for inclusion here if any of:
- size > 5 MB **and** filenames look like book titles (not source code)
- README explicitly advertises a PDF/epub bundle
- repo is paired with a published book

GitHub-search via `gh` caps each query at 30 results and ignores boolean operators in the user-friendly form — multiple narrow searches give better recall than one broad one.

---

## Adding more entries

When you find another candidate, append to the right section's table with: name, stars, size, file count (or "—" if not pulled), and a one-line "what's in it" note. Re-run the size check before committing — these repos churn (force-pushes, takedowns).
