-- Schema script for GameStore (Postgres)
-- Creates tables used by the Flask app (products, users, categories, product_images, orders, order_items, payments)

BEGIN;

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(120) NOT NULL UNIQUE,
    password_hash VARCHAR(200) NOT NULL,
    is_admin BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    price DOUBLE PRECISION NOT NULL DEFAULT 0,
    img VARCHAR(400),
    image_data BYTEA,
    image_mime VARCHAR(120),
    category VARCHAR(120)
);
CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);

CREATE TABLE IF NOT EXISTS categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(120) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS product_images (
    id SERIAL PRIMARY KEY,
    product_id INTEGER REFERENCES products(id) ON DELETE CASCADE,
    url VARCHAR(400) NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_product_images_product_id ON product_images(product_id);

CREATE TABLE IF NOT EXISTS orders (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    total DOUBLE PRECISION NOT NULL DEFAULT 0,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_orders_user_id ON orders(user_id);

CREATE TABLE IF NOT EXISTS order_items (
    id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES orders(id) ON DELETE CASCADE,
    product_id INTEGER REFERENCES products(id) ON DELETE SET NULL,
    quantity INTEGER NOT NULL DEFAULT 1,
    price DOUBLE PRECISION NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_order_items_order_id ON order_items(order_id);
CREATE INDEX IF NOT EXISTS idx_order_items_product_id ON order_items(product_id);

CREATE TABLE IF NOT EXISTS payments (
    id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES orders(id) ON DELETE SET NULL,
    amount DOUBLE PRECISION NOT NULL,
    method VARCHAR(80),
    status VARCHAR(50) NOT NULL DEFAULT 'pending'
);
CREATE INDEX IF NOT EXISTS idx_payments_order_id ON payments(order_id);

COMMIT;

-- Optional: seed a few categories (idempotent)
INSERT INTO categories (name) VALUES ('Consolas') ON CONFLICT (name) DO NOTHING;
INSERT INTO categories (name) VALUES ('Juegos') ON CONFLICT (name) DO NOTHING;
INSERT INTO categories (name) VALUES ('Accesorios') ON CONFLICT (name) DO NOTHING;
INSERT INTO categories (name) VALUES ('Controles') ON CONFLICT (name) DO NOTHING;
