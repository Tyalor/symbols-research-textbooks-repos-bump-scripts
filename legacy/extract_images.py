#!/usr/bin/env python3
"""Extract post images from Instagram HAR file."""
import json, base64, os, hashlib, sys

har_path = '/Users/ty/Downloads/www.instagram.com.har'
out_dir = '/Users/ty/Downloads/quantscience_output/igimgs'
os.makedirs(out_dir, exist_ok=True)

print("Loading HAR file...")
with open(har_path) as f:
    d = json.load(f)

entries = d['log']['entries']
print(f"Total HAR entries: {len(entries)}")

seen = set()
saved = 0
skipped_thumb = 0
skipped_profile = 0
skipped_small = 0
size_dist = {}

for e in entries:
    url = e['request']['url']

    # Skip profile pics
    if 't51.2885-19' in url:
        skipped_profile += 1
        continue

    # Skip thumbnails by URL pattern
    if 's150x150' in url or 's320x320' in url or 's240x240' in url:
        skipped_thumb += 1
        continue

    resp_content = e.get('response', {}).get('content', {})
    mime = resp_content.get('mimeType', '')
    if 'image' not in mime:
        continue

    text = resp_content.get('text')
    if not text:
        continue

    try:
        if resp_content.get('encoding') == 'base64':
            data = base64.b64decode(text)
        else:
            data = text.encode('latin-1')
    except Exception:
        continue

    # Skip very small files (icons, etc)
    size_kb = len(data) // 1024
    if size_kb < 10:
        skipped_small += 1
        continue

    h = hashlib.md5(data).hexdigest()
    if h in seen:
        continue
    seen.add(h)

    ext = 'jpg' if 'jpeg' in mime or 'jpg' in mime else 'webp' if 'webp' in mime else 'png' if 'png' in mime else 'jpg'
    with open(f'{out_dir}/{h}.{ext}', 'wb') as f:
        f.write(data)
    saved += 1

    # Track size distribution
    bucket = f"{(size_kb // 50) * 50}-{(size_kb // 50) * 50 + 50}KB"
    size_dist[bucket] = size_dist.get(bucket, 0) + 1

print(f"\nResults:")
print(f"  Saved: {saved} unique images")
print(f"  Skipped profile pics: {skipped_profile}")
print(f"  Skipped thumbnails: {skipped_thumb}")
print(f"  Skipped small (<10KB): {skipped_small}")
print(f"\nSize distribution:")
for k in sorted(size_dist.keys(), key=lambda x: int(x.split('-')[0])):
    print(f"  {k}: {size_dist[k]}")
