import sqlite3

DB_NAME = "database.db"

# Global cache
product_cache = []

def load_products_to_cache():
    """Load products from database into cache, including product_id, product_name, brand_name, and description_text."""
    global product_cache
    conn = sqlite3.connect(DB_NAME, timeout=10)
    conn.execute("PRAGMA foreign_keys = ON;")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT p.product_id, p.product_name, b.brand_name, d.description_text
        FROM products p
        JOIN brands b ON p.brand_id = b.brand_id
        JOIN descriptions d ON p.description_id = d.description_id
    """)
    rows = cursor.fetchall()
    conn.close()
    product_cache = [(f"{row[1]} - {row[2]} - {row[3]}", row[0]) for row in rows]
    return product_cache

def get_products():
    """Return cached products, load from database if cache is empty."""
    global product_cache
    if not product_cache:
        return load_products_to_cache()
    return product_cache

def add_product_to_cache(product_display, product_id):
    """Add a new product to the cache."""
    global product_cache
    product_cache.append((product_display, product_id))

def update_product_in_cache(old_display, new_display, product_id):
    """Update a product in the cache."""
    global product_cache
    product_cache = [(new_display if p[0] == old_display else p[0], p[1]) for p in product_cache]

def remove_product_from_cache(product_display):
    """Remove a product from the cache."""
    global product_cache
    product_cache = [p for p in product_cache if p[0] != product_display]

if __name__ == "__main__":
    load_products_to_cache()