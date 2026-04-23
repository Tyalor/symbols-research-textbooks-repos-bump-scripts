#!/usr/bin/env python3
"""Extract research papers and GitHub repos from OCR'd Instagram post text."""
import os, re, json, glob
from collections import defaultdict

OCR_DIR = 'ocr_txt'

# ── Read all OCR files ──
texts = {}
for f in sorted(glob.glob(f'{OCR_DIR}/*.txt')):
    fid = os.path.basename(f).replace('.txt', '')
    with open(f) as fh:
        texts[fid] = fh.read()

print(f"Loaded {len(texts)} OCR texts")

# ── PAPER EXTRACTION ──
papers = []  # list of dicts

# SSRN patterns
ssrn_pat = re.compile(r'(?:ssrn\.com.*?(?:abstract|tract)\s*=?\s*(\d{6,8}))|(?:SSRN[:\s#-]*(\d{6,8}))', re.I)
# arxiv patterns
arxiv_pat = re.compile(r'(?:arxiv\.org/abs/(\d{4}\.\d{4,6}))|(?:arXiv[:\s]*(\d{4}\.\d{4,6}))', re.I)
# DOI patterns
doi_pat = re.compile(r'doi\.org/(10\.\d{4,}/\S+)', re.I)

# Paper title detection: look for common patterns in these posts
# "A N-page PDF" pattern followed by title
page_pdf_pat = re.compile(r'(?:A?\s*\d+[\s-]*page\s+PDF)', re.I)

# Known quant authors
quant_authors = [
    'Lopez de Prado', 'Kakushadze', 'Avellaneda', 'Gatheral', 'Cont',
    'Jim Simons', 'Ed Thorp', 'Perry Kaufman', 'Moskowitz', 'Pedersen',
    'Hilpisch', 'Jansen', 'Hull', 'Derman', 'Taleb', 'Mandelbrot',
    'Shreve', 'Bouchaud', 'Potters', 'Marcos Lopez'
]

# GitHub / repo patterns
github_url_pat = re.compile(r'github\.com/([a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+)', re.I)
# OCR often garbles github.com - look for owner/repo patterns after known prefixes
github_ocr_pat = re.compile(r'(?:github|Github|GitHub|althub|ithub)[.\s]*com[/\s]*([a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+)', re.I)
# Standalone owner/repo patterns (from OCR of github screenshots)
owner_repo_pat = re.compile(r'(?:^|\s)([a-zA-Z0-9_-]+/[a-zA-Z0-9_-]+)\s', re.M)
pip_install_pat = re.compile(r'pip\s+install\s+([a-zA-Z0-9_-]+)', re.I)

# Known repos/libraries to watch for
known_repos = {
    'qlib': 'microsoft/qlib',
    'vectorbt': 'polakowo/vectorbt',
    'freqtrade': 'freqtrade/freqtrade',
    'nautilus-trader': 'nautechsystems/nautilus_trader',
    'nautilus_trader': 'nautechsystems/nautilus_trader',
    'tensortrade': 'tensortrade-org/tensortrade',
    'TensorTrade': 'tensortrade-org/tensortrade',
    'ib_insync': 'erdewit/ib_insync',
    'ib-insync': 'erdewit/ib_insync',
    'zipline': 'quantopian/zipline',
    'backtrader': 'mementum/backtrader',
    'riskfolio-lib': 'dcajasn/Riskfolio-Lib',
    'riskfolio': 'dcajasn/Riskfolio-Lib',
    'pypfopt': 'robertmartin8/PyPortfolioOpt',
    'PyPortfolioOpt': 'robertmartin8/PyPortfolioOpt',
    'quantlib': 'lballabio/QuantLib',
    'QuantLib': 'lballabio/QuantLib',
    'finrl': 'AI4Finance-Foundation/FinRL',
    'FinRL': 'AI4Finance-Foundation/FinRL',
    'tf-quant-finance': 'google/tf-quant-finance',
    'openbb': 'OpenBB-finance/OpenBBTerminal',
    'OpenBB': 'OpenBB-finance/OpenBBTerminal',
    'openbb-agents': 'OpenBB-finance/openbb-agents',
    'gs-quant': 'goldmansachs/gs-quant',
    'GS-Quant': 'goldmansachs/gs-quant',
    'RD-Agent': 'microsoft/RD-Agent',
    'Pytimetk': 'business-science/pytimetk',
    'pytimetk': 'business-science/pytimetk',
    'lumibot': 'Lumiwealth/lumibot',
    'Lumibot': 'Lumiwealth/lumibot',
    'bt': 'pmorissette/bt',
    'yfinance': 'ranaroussi/yfinance',
    'QuantStats': 'ranaroussi/quantstats',
    'quantstats': 'ranaroussi/quantstats',
    'alphalens': 'quantopian/alphalens',
    'pyfolio': 'quantopian/pyfolio',
    'elegantrl': 'AI4Finance-Foundation/ElegantRL',
    'stockstats': 'jealous/stockstats',
    'ta-lib': 'TA-Lib/ta-lib-python',
    'pandas-ta': 'twopirllc/pandas-ta',
    'mlfinlab': 'hudson-and-thames/mlfinlab',
    'Docling': 'DS4SD/docling',
    'docling': 'DS4SD/docling',
    'DSPy': 'stanfordnlp/dspy',
    'dspy': 'stanfordnlp/dspy',
    'Auto-Analyst': 'Auto-Analyst/Auto-Analyst',
    'Julius': 'julius-ai/julius',
}

# Known paper titles / resources to look for
known_papers = {
    '151 Trading Strategies': {'authors': 'Zura Kakushadze, Juan Andrés Serur', 'id': 'SSRN-3247865', 'year': '2018'},
    'Advances in Financial Machine Learning': {'authors': 'Marcos Lopez de Prado', 'year': '2018'},
    'Machine Learning for Asset Managers': {'authors': 'Marcos Lopez de Prado', 'year': '2020'},
    'Pairs Trading': {'authors': 'Evan Gatev, William Goetzmann, K. Geert Rouwenhorst', 'year': '2006'},
    'Time series momentum': {'authors': 'Tobias J. Moskowitz, Yao Hua Ooi, Lasse Heje Pedersen', 'year': '2012'},
}

# ── Process each OCR text ──
paper_findings = []  # (title, authors, year, id_type, id_val, url, caption, source_ids, confidence)
repo_findings = []   # (name, github_url, caption, source_ids, confidence)

# Track which source IDs map to which findings
paper_by_key = defaultdict(lambda: {'source_ids': [], 'captions': []})
repo_by_key = defaultdict(lambda: {'source_ids': [], 'captions': []})

for fid, text in texts.items():
    # Skip very short texts (likely just graphics)
    if len(text.strip()) < 20:
        continue

    # Get caption snippet - first meaningful lines after @quantscience_
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    caption = ''
    capture = False
    for line in lines:
        if 'quantscience' in line.lower():
            capture = True
            continue
        if capture and line and not line.startswith('@'):
            caption = line
            # Get up to 2 lines of caption
            idx = lines.index(line)
            caption_lines = lines[idx:idx+3]
            caption = ' '.join(caption_lines)
            break
    if not caption and lines:
        caption = ' '.join(lines[:3])
    caption = caption[:200]

    # ── Look for SSRN ──
    for m in ssrn_pat.finditer(text):
        ssrn_id = m.group(1) or m.group(2)
        if ssrn_id:
            key = f'SSRN-{ssrn_id}'
            paper_by_key[key]['source_ids'].append(fid)
            paper_by_key[key]['captions'].append(caption)
            paper_by_key[key]['id_type'] = 'ssrn'
            paper_by_key[key]['id_val'] = ssrn_id
            paper_by_key[key]['url'] = f'https://papers.ssrn.com/sol3/papers.cfm?abstract_id={ssrn_id}'

    # ── Look for arxiv ──
    for m in arxiv_pat.finditer(text):
        arxiv_id = m.group(1) or m.group(2)
        if arxiv_id:
            key = f'arxiv-{arxiv_id}'
            paper_by_key[key]['source_ids'].append(fid)
            paper_by_key[key]['captions'].append(caption)
            paper_by_key[key]['id_type'] = 'arxiv'
            paper_by_key[key]['id_val'] = arxiv_id
            paper_by_key[key]['url'] = f'https://arxiv.org/abs/{arxiv_id}'

    # ── Look for DOI ──
    for m in doi_pat.finditer(text):
        doi = m.group(1)
        key = f'doi-{doi}'
        paper_by_key[key]['source_ids'].append(fid)
        paper_by_key[key]['captions'].append(caption)
        paper_by_key[key]['id_type'] = 'doi'
        paper_by_key[key]['id_val'] = doi
        paper_by_key[key]['url'] = f'https://doi.org/{doi}'

    # ── Look for paper titles in text ──
    # Detect "N-page PDF" pattern - strong paper signal
    text_lower = text.lower()

    # Try to extract paper title: usually appears as a formal title after the caption
    # Look for patterns like "Title\nAuthor1, Author2" or title after "page PDF"
    title_candidates = []

    for known_title, meta in known_papers.items():
        if known_title.lower() in text_lower:
            key = f'known-{known_title.lower()}'
            paper_by_key[key]['source_ids'].append(fid)
            paper_by_key[key]['captions'].append(caption)
            paper_by_key[key]['title'] = known_title
            paper_by_key[key]['authors'] = meta.get('authors', '')
            paper_by_key[key]['year'] = meta.get('year', '')
            if 'id' in meta:
                paper_by_key[key]['id_val'] = meta['id']
                if meta['id'].startswith('SSRN'):
                    paper_by_key[key]['id_type'] = 'ssrn'
                    ssrn_num = meta['id'].replace('SSRN-', '')
                    paper_by_key[key]['url'] = f'https://papers.ssrn.com/sol3/papers.cfm?abstract_id={ssrn_num}'

    # Look for "Abstract" keyword as paper signal, try to extract title before it
    if 'abstract' in text_lower:
        abstract_idx = text_lower.index('abstract')
        pre_abstract = text[:abstract_idx]
        # Title is usually a formal line before abstract
        pre_lines = [l.strip() for l in pre_abstract.split('\n') if l.strip() and len(l.strip()) > 15]
        # Filter out known non-title lines
        for pl in pre_lines:
            pl_clean = pl.strip()
            if any(skip in pl_clean.lower() for skip in ['quantscience', '@', 'page pdf', 'here', 'thread', 'breaking', 'overview', 'need to know']):
                continue
            if len(pl_clean) > 20 and len(pl_clean) < 200:
                # Check if it looks like a title (mostly title case or has capital letters)
                words = pl_clean.split()
                if len(words) >= 3:
                    title_candidates.append(pl_clean)

    # If we found a title candidate and it's a page-PDF post
    if title_candidates and page_pdf_pat.search(text):
        # Take the most likely title (longest reasonable one)
        best_title = max(title_candidates, key=lambda t: len(t) if len(t) < 150 else 0)
        if best_title:
            key = f'title-{best_title.lower()[:80]}'
            if key not in paper_by_key or not paper_by_key[key].get('title'):
                paper_by_key[key]['source_ids'].append(fid)
                paper_by_key[key]['captions'].append(caption)
                paper_by_key[key]['title'] = best_title
                paper_by_key[key]['confidence'] = 'medium'

                # Try to find authors
                authors_found = []
                for author in quant_authors:
                    if author.lower() in text_lower:
                        authors_found.append(author)
                if authors_found:
                    paper_by_key[key]['authors'] = ', '.join(authors_found)

    # Also detect papers by "page PDF" + title-like text even without "Abstract"
    if page_pdf_pat.search(text) and 'abstract' not in text_lower:
        # Try to find the title in lines after "PDF" mention
        for i, line in enumerate(lines):
            if page_pdf_pat.search(line):
                # Next few non-empty lines might be the title
                for j in range(i+1, min(i+5, len(lines))):
                    candidate = lines[j].strip()
                    if len(candidate) > 20 and len(candidate) < 200:
                        if not any(skip in candidate.lower() for skip in ['quantscience', '@', 'here', 'thread', 'breaking']):
                            key = f'title-{candidate.lower()[:80]}'
                            if key not in paper_by_key:
                                paper_by_key[key]['source_ids'].append(fid)
                                paper_by_key[key]['captions'].append(caption)
                                paper_by_key[key]['title'] = candidate
                                paper_by_key[key]['confidence'] = 'medium'
                            break

    # ── Look for GitHub repos ──
    # Direct github URLs
    for m in github_url_pat.finditer(text):
        repo = m.group(1).rstrip('.,;:)')
        key = f'gh-{repo.lower()}'
        repo_by_key[key]['source_ids'].append(fid)
        repo_by_key[key]['captions'].append(caption)
        repo_by_key[key]['github_url'] = f'https://github.com/{repo}'
        repo_by_key[key]['name'] = repo.split('/')[-1]
        repo_by_key[key]['confidence'] = 'high'

    # OCR-garbled github URLs
    for m in github_ocr_pat.finditer(text):
        repo = m.group(1).rstrip('.,;:)')
        if '/' in repo and len(repo.split('/')[0]) > 1 and len(repo.split('/')[1]) > 1:
            key = f'gh-{repo.lower()}'
            repo_by_key[key]['source_ids'].append(fid)
            repo_by_key[key]['captions'].append(caption)
            repo_by_key[key]['github_url'] = f'https://github.com/{repo}'
            repo_by_key[key]['name'] = repo.split('/')[-1]
            repo_by_key[key]['confidence'] = 'high'

    # Known repos/libraries mentioned by name
    for lib_name, gh_path in known_repos.items():
        # Use word boundary matching
        if re.search(r'(?:^|\W)' + re.escape(lib_name) + r'(?:\W|$)', text):
            key = f'gh-{gh_path.lower()}'
            repo_by_key[key]['source_ids'].append(fid)
            repo_by_key[key]['captions'].append(caption)
            repo_by_key[key]['github_url'] = f'https://github.com/{gh_path}'
            repo_by_key[key]['name'] = gh_path.split('/')[-1]
            if not repo_by_key[key].get('confidence'):
                repo_by_key[key]['confidence'] = 'medium'

    # pip install patterns
    for m in pip_install_pat.finditer(text):
        pkg = m.group(1)
        if pkg.lower() in [k.lower() for k in known_repos]:
            # Already handled above
            continue
        # Record as potential library
        key = f'pip-{pkg.lower()}'
        repo_by_key[key]['source_ids'].append(fid)
        repo_by_key[key]['captions'].append(caption)
        repo_by_key[key]['name'] = pkg
        repo_by_key[key]['confidence'] = 'low'

    # Look for owner/repo patterns that might be GitHub references (OCR of screenshots)
    # Pattern: standalone owner/repo like "jpmorganchase/python-training"
    for m in re.finditer(r'(?:^|\s)([a-zA-Z][a-zA-Z0-9_-]+/[a-zA-Z][a-zA-Z0-9_.-]+)', text):
        repo = m.group(1).strip().rstrip('.,;:)')
        parts = repo.split('/')
        if len(parts) == 2 and len(parts[0]) > 2 and len(parts[1]) > 2:
            # Filter out common false positives
            if any(fp in repo.lower() for fp in ['http', 'www', '.com', 'quantscience', 'instagram']):
                continue
            # Filter date-like patterns
            if re.match(r'\d+/\d+', repo):
                continue
            key = f'gh-{repo.lower()}'
            if key not in repo_by_key:
                repo_by_key[key]['source_ids'].append(fid)
                repo_by_key[key]['captions'].append(caption)
                repo_by_key[key]['github_url'] = f'https://github.com/{repo}'
                repo_by_key[key]['name'] = parts[1]
                repo_by_key[key]['confidence'] = 'medium'
            else:
                repo_by_key[key]['source_ids'].append(fid)
                repo_by_key[key]['captions'].append(caption)

# ── Also find hook posts (teasers without extracted signals) ──
hook_keywords = ['get it here', 'read it here', "here's the link", "here's the pdf",
                 'grab it here', 'bookmark this', 'save this', 'link in bio',
                 'here are the best parts', 'this is what you need to know']

hook_posts = []
for fid, text in texts.items():
    text_lower = text.lower()
    has_hook = any(kw in text_lower for kw in hook_keywords)
    has_paper_signal = any(kw in text_lower for kw in ['page pdf', 'paper', 'research', 'whitepaper'])
    has_extraction = any(fid in p.get('source_ids', []) for p in paper_by_key.values()) or \
                     any(fid in r.get('source_ids', []) for r in repo_by_key.values())

    if has_hook and has_paper_signal and not has_extraction:
        hook_posts.append(fid)

# ── Output results ──
print(f"\n{'='*60}")
print(f"EXTRACTION RESULTS")
print(f"{'='*60}")
print(f"\nPapers found: {len(paper_by_key)}")
print(f"Repos found: {len(repo_by_key)}")
print(f"Hook posts (unresolved): {len(hook_posts)}")

# Save results as JSON for next step
results = {
    'papers': {},
    'repos': {},
    'hook_posts': hook_posts,
}

for key, data in paper_by_key.items():
    data['source_ids'] = list(set(data['source_ids']))
    data['captions'] = list(set(data['captions']))[:3]  # Keep up to 3 unique captions
    results['papers'][key] = data

for key, data in repo_by_key.items():
    data['source_ids'] = list(set(data['source_ids']))
    data['captions'] = list(set(data['captions']))[:3]
    results['repos'][key] = data

with open('extraction_results.json', 'w') as f:
    json.dump(results, f, indent=2)

print("\nPAPERS:")
for key, data in sorted(paper_by_key.items()):
    title = data.get('title', key)
    n = len(set(data['source_ids']))
    print(f"  [{n} posts] {title}")
    if data.get('id_val'):
        print(f"           ID: {data['id_val']}")

print("\nREPOS:")
for key, data in sorted(repo_by_key.items()):
    name = data.get('name', key)
    url = data.get('github_url', '?')
    n = len(set(data['source_ids']))
    print(f"  [{n} posts] {name} — {url}")

print(f"\nHOOK POSTS (first 20):")
for fid in hook_posts[:20]:
    lines = texts[fid].split('\n')
    preview = ' '.join(l.strip() for l in lines if l.strip())[:120]
    print(f"  {fid}: {preview}")

print(f"\nResults saved to extraction_results.json")
