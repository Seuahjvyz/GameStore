#!/usr/bin/env python3
"""
Migrate data from local SQLite `gamestore.db` into a Postgres database.

Usage:
  DATABASE_URL="postgresql://user:pass@host:5432/dbname" python3 scripts/migrate_to_postgres.py

The script expects the Postgres destination URL to be available in the
DATABASE_URL environment variable. It will create tables on the target and
then copy the rows from the SQLite `products` and `users` tables.

Notes:
- Password hashes are copied as-is.
- Existing rows in target are upserted by username (users) and by title (products).
"""
import os
import sys
import sqlite3
from pathlib import Path

# Ensure target DB URL is provided
TARGET = os.environ.get('DATABASE_URL')
if not TARGET:
    print("ERROR: set the DATABASE_URL environment variable to your Postgres database URL.")
    print("Example: export DATABASE_URL='postgresql://user:pass@localhost:5432/gamestore'")
    sys.exit(1)

# Make sure the app picks up the target DB URL when importing
os.environ['DATABASE_URL'] = TARGET

# Import application and models (app.py reads DATABASE_URL at import time now)
try:
    from app import app, db, Product, User
except Exception as e:
    print("Failed to import app/models:", e)
    raise

# Path to source sqlite DB (project root/gamestore.db)
ROOT = Path(__file__).resolve().parents[1]
SQLITE_PATH = ROOT / 'gamestore.db'
if not SQLITE_PATH.exists():
    print(f"ERROR: source SQLite DB not found at {SQLITE_PATH}")
    sys.exit(1)

# Connect to source SQLite and copy data into target via app's SQLAlchemy session
src = sqlite3.connect(str(SQLITE_PATH))
src.row_factory = sqlite3.Row

with app.app_context():
    print("Creating tables on target database (if not exist)...")
    db.create_all()

    cur = src.cursor()

    # Migrate products
    try:
        cur.execute("SELECT id, title, price, img FROM products")
        rows = cur.fetchall()
    except sqlite3.Error as e:
        print("No products table found in source SQLite or error reading it:", e)
        rows = []

    migrated_products = 0
    for r in rows:
        title = r['title']
        price = r['price']
        img = r['img']
        existing = Product.query.filter_by(title=title).first()
        if existing:
            # update fields if necessary
            updated = False
            if existing.price != price:
                existing.price = price
                updated = True
            if existing.img != img:
                existing.img = img
                updated = True
            if updated:
                migrated_products += 1
        else:
            p = Product(title=title, price=price, img=img)
            db.session.add(p)
            migrated_products += 1
    db.session.commit()
    print(f"Products migrated/updated: {migrated_products}")

    # Migrate users
    try:
        cur.execute("SELECT id, username, password_hash, is_admin FROM users")
        rows = cur.fetchall()
    except sqlite3.Error as e:
        print("No users table found in source SQLite or error reading it:", e)
        rows = []

    migrated_users = 0
    for r in rows:
        username = r['username']
        password_hash = r['password_hash']
        is_admin = bool(r['is_admin'])
        u = User.query.filter_by(username=username).first()
        if u:
            u.password_hash = password_hash
            u.is_admin = is_admin
            migrated_users += 1
        else:
            # create user; set password_hash directly
            u = User(username=username, is_admin=is_admin)
            # assign password_hash attribute directly (bypass set_password)
            u.password_hash = password_hash
            db.session.add(u)
            migrated_users += 1
    db.session.commit()
    print(f"Users migrated/updated: {migrated_users}")

print("Migration finished.")
