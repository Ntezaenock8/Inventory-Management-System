import sqlite3

DB_NAME = "database.db"

def create_connection():
    try:
        conn = sqlite3.connect(DB_NAME)
        # Enable foreign key support
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn
    except sqlite3.Error as e:
        print(f"Error connecting to database: {e}")
        return None

def create_tables():
    conn = create_connection()
    if not conn:
        return
    
    cursor = conn.cursor()
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS brands (
                brand_id INTEGER PRIMARY KEY AUTOINCREMENT,
                brand_name TEXT UNIQUE NOT NULL
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                category_id INTEGER PRIMARY KEY AUTOINCREMENT,
                category_name TEXT UNIQUE NOT NULL
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS descriptions (
                description_id INTEGER PRIMARY KEY AUTOINCREMENT,
                description_text TEXT UNIQUE NOT NULL
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                product_id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_name TEXT NOT NULL,
                brand_id INTEGER,
                category_id INTEGER,
                description_id INTEGER,
                FOREIGN KEY (brand_id) REFERENCES brands(brand_id),
                FOREIGN KEY (category_id) REFERENCES categories(category_id),
                FOREIGN KEY (description_id) REFERENCES descriptions(description_id)
            )
        """)

        conn.commit()
        print("All tables have been created successfully")
    except sqlite3.Error as e:
        print(f"Error creating tables: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    create_tables()