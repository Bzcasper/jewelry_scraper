import sqlite3
import logging

DB_NAME = "products.db"

def initialize_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            price TEXT,
            description TEXT,
            image_urls TEXT,
            product_url TEXT,
            category TEXT,
            platform TEXT,
            date_scraped TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()
    logging.info("Database initialized.")

def add_product(product):
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO products (title, price, description, image_urls, product_url, category, platform)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            product.get("title"),
            product.get("price"),
            product.get("description"),
            ",".join(product.get("image_urls", [])),
            product.get("product_url"),
            product.get("category"),
            product.get("platform", "unknown")
        ))
        conn.commit()
        conn.close()
        logging.debug(f"Added product to database: {product.get('title')}")
    except Exception as e:
        logging.error(f"Error adding product to database: {e}")

def fetch_all_products():
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM products")
        rows = cursor.fetchall()
        conn.close()
        return [{
            "id": row[0],
            "title": row[1],
            "price": row[2],
            "description": row[3],
            "image_urls": row[4].split(','),
            "product_url": row[5],
            "category": row[6],
            "platform": row[7],
            "date_scraped": row[8]
        } for row in rows]
    except Exception as e:
        logging.error(f"Error fetching products: {e}")
        return []
