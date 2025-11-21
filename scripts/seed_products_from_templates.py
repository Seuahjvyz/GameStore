#!/usr/bin/env python3
"""
Seed products into the app database by parsing product blocks in HTML templates.

Usage:
  PYTHONPATH=. DATABASE_URL="postgresql://..." .venv/bin/python3 scripts/seed_products_from_templates.py

The script finds product blocks that follow the project's markup and inserts
products into the `products` table if a product with the same title doesn't
already exist.
"""
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATES_DIR = ROOT / 'app' / 'templates'

files_to_scan = []
# Walk templates directory and collect files
for p in TEMPLATES_DIR.rglob('*.html'):
    files_to_scan.append(p)

print(f"Scanning {len(files_to_scan)} template files for product blocks...")

blocks = []
product_block_re = re.compile(r'<div\s+class=["\']producto["\']>(.*?)</div>\s*</div>', re.S)
# The above tries to roughly capture product blocks; if it misses some, we'll also
# fall back to a simpler search for <h3 class="product-title"> occurrences.

for f in files_to_scan:
    content = f.read_text(encoding='utf-8')
    # First strategy: capture product blocks
    found = product_block_re.findall(content)
    if found:
        for b in found:
            blocks.append((f, b))
    else:
        # Fallback: if file contains product-title tags, try to extract surrounding chunk
        if 'product-title' in content:
            # crude split by product div start
            parts = content.split('<div class="producto">')
            for part in parts[1:]:
                # take up to the next closing div that ends the block - crude but ok
                snippet = part.split('</div>')
                if snippet:
                    blocks.append((f, snippet[0]))

print(f"Found approximately {len(blocks)} product blocks to parse.")

extracted = []
for f, b in blocks:
    # img src
    img = None
    m = re.search(r"<img[^>]+src=[\"']([^\"']+)[\"']", b)
    if m:
        img = m.group(1).strip()
        # if it's a Jinja url_for, extract the filename
        j = re.search(r"url_for\(\s*'static'\s*,\s*filename\s*=\s*['\"]([^'\"]+)['\"]\s*\)", img)
        if j:
            img = '/static/' + j.group(1)
    # title
    title = None
    m = re.search(r"<h3[^>]*class=[\"']product-title[\"'][^>]*>(.*?)</h3>", b, re.S)
    if m:
        title = re.sub(r"\s+", " ", m.group(1)).strip()
    # category
    category = None
    m = re.search(r"<p[^>]*class=[\"']product-category[\"'][^>]*>(.*?)</p>", b, re.S)
    if m:
        category = re.sub(r"\s+", " ", m.group(1)).strip()
    # price
    price = None
    m = re.search(r"<span[^>]*class=[\"']product-price[\"'][^>]*>\$?([^<]+)</span>", b, re.S)
    if m:
        raw = m.group(1).strip()
        # remove currency thousands separators and non-numeric
        num = re.sub(r"[^0-9.,]", "", raw)
        num = num.replace(',', '')
        try:
            price = float(num)
        except Exception:
            price = 0.0
    if title:
        extracted.append({'title': title, 'price': price or 0.0, 'img': img or '/static/img/Imagenes/placeholder.svg', 'category': category or 'General', 'source': str(f)})

print(f"Parsed {len(extracted)} product records (raw).")

# Deduplicate by title keeping first occurrence
seen = set()
products = []
for e in extracted:
    if e['title'] in seen:
        continue
    seen.add(e['title'])
    products.append(e)

print(f"{len(products)} unique products to insert/update.")

# Insert into DB using app context
try:
    # ensure app import picks up DATABASE_URL env var
    sys.path.insert(0, str(ROOT))
    from app import app, db, Product
except Exception as exc:
    print('Failed to import app/models:', exc)
    raise

with app.app_context():
    inserted = 0
    updated = 0
    for p in products:
        existing = Product.query.filter_by(title=p['title']).first()
        if existing:
            # update fields if different
            changed = False
            if (existing.price or 0) != (p['price'] or 0):
                existing.price = p['price']
                changed = True
            if (existing.img or '') != p['img']:
                existing.img = p['img']
                changed = True
            if changed:
                updated += 1
        else:
            prod = Product(title=p['title'], price=p['price'], img=p['img'])
            db.session.add(prod)
            inserted += 1
    db.session.commit()

    print(f"Inserted: {inserted}, Updated: {updated}")

    total = Product.query.count()
    print(f"Total products in DB now: {total}")

print('Seeding finished.')
