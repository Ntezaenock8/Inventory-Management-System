import sqlite3
import os

DB_NAME = "database.db"

def create_connection():
    try:
        conn = sqlite3.connect(DB_NAME, timeout=10)  # Add timeout
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn
    except sqlite3.Error as e:
        print(f"Error connecting to database: {e}")
        return None

def table_exists(conn, table_name):
    """Check if a table exists in the database."""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name=?;
    """, (table_name,))
    return cursor.fetchone() is not None

def create_tables():
    db_exists = os.path.exists(DB_NAME)
    
    conn = create_connection()
    if not conn:
        return
    
    cursor = conn.cursor()
    try:
        # Create brands table
        if not table_exists(conn, "brands"):
            cursor.execute("""
                CREATE TABLE brands (
                    brand_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    brand_name TEXT UNIQUE NOT NULL
                )
            """)
            print("Created table: brands")

        # Create categories table
        if not table_exists(conn, "categories"):
            cursor.execute("""
                CREATE TABLE categories (
                    category_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category_name TEXT UNIQUE NOT NULL
                )
            """)
            print("Created table: categories")

        # Create descriptions table
        if not table_exists(conn, "descriptions"):
            cursor.execute("""
                CREATE TABLE descriptions (
                    description_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    description_text TEXT UNIQUE NOT NULL
                )
            """)
            print("Created table: descriptions")

        # Create units_of_measurement table
        if not table_exists(conn, "units_of_measurement"):
            cursor.execute("""
                CREATE TABLE units_of_measurement (
                    unit_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    unit_name TEXT UNIQUE NOT NULL
                )
            """)
            print("Created table: units_of_measurement")

        # Check if products table exists and if it needs unit_id column
        cursor.execute("PRAGMA table_info(products)")
        columns = [col[1] for col in cursor.fetchall()]
        if not table_exists(conn, "products"):
            cursor.execute("""
                CREATE TABLE products (
                    product_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_name TEXT NOT NULL,
                    brand_id INTEGER,
                    category_id INTEGER,
                    description_id INTEGER,
                    unit_id INTEGER,
                    FOREIGN KEY (brand_id) REFERENCES brands(brand_id),
                    FOREIGN KEY (category_id) REFERENCES categories(category_id),
                    FOREIGN KEY (description_id) REFERENCES descriptions(description_id),
                    FOREIGN KEY (unit_id) REFERENCES units_of_measurement(unit_id)
                )
            """)
            print("Created table: products")
        elif "unit_id" not in columns:
            cursor.execute("""
                ALTER TABLE products
                ADD COLUMN unit_id INTEGER REFERENCES units_of_measurement(unit_id)
            """)
            print("Added unit_id column to products table")

        # Create inventory table
        if not table_exists(conn, "inventory"):
            cursor.execute("""
                CREATE TABLE inventory (
                    inventory_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_id INTEGER,
                    quantity INTEGER NOT NULL,
                    FOREIGN KEY (product_id) REFERENCES products(product_id)
                )
            """)
            print("Created table: inventory")

        # Create inventory_batches table
        if not table_exists(conn, "inventory_batches"):
            cursor.execute("""
                CREATE TABLE inventory_batches (
                    batch_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_id INTEGER,
                    buying_price REAL NOT NULL,
                    quantity INTEGER NOT NULL,
                    purchase_date DATE,
                    unit_id INTEGER,
                    FOREIGN KEY (product_id) REFERENCES products(product_id),
                    FOREIGN KEY (unit_id) REFERENCES units_of_measurement(unit_id)
                )
            """)
            print("Created table: inventory_batches")

        # Create sales table
        if not table_exists(conn, "sales"):
            cursor.execute("""
                CREATE TABLE sales (
                    sale_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_id INTEGER,
                    selling_price REAL NOT NULL,
                    quantity_sold INTEGER NOT NULL,
                    sale_date DATE,
                    unit_id INTEGER,
                    FOREIGN KEY (product_id) REFERENCES products(product_id),
                    FOREIGN KEY (unit_id) REFERENCES units_of_measurement(unit_id)
                )
            """)
            print("Created table: sales")

        # Create sale_batches table
        if not table_exists(conn, "sale_batches"):
            cursor.execute("""
                CREATE TABLE sale_batches (
                    sale_batch_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sale_id INTEGER,
                    batch_id INTEGER,
                    quantity_used INTEGER NOT NULL,
                    buying_price REAL NOT NULL,
                    unit_id INTEGER,
                    FOREIGN KEY (sale_id) REFERENCES sales(sale_id) ON DELETE CASCADE,
                    FOREIGN KEY (batch_id) REFERENCES inventory_batches(batch_id) ON DELETE CASCADE,
                    FOREIGN KEY (unit_id) REFERENCES units_of_measurement(unit_id)
                )
            """)
            print("Created table: sale_batches")

        # Create expense_categories table
        if not table_exists(conn, "expense_categories"):
            cursor.execute("""
                CREATE TABLE expense_categories (
                    expense_category_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category_name TEXT UNIQUE NOT NULL
                )
            """)
            print("Created table: expense_categories")

        # Check if expenses table exists and if it needs predefined_expense column
        cursor.execute("PRAGMA table_info(expenses)")
        columns = [col[1] for col in cursor.fetchall()]
        if not table_exists(conn, "expenses"):
            cursor.execute("""
                CREATE TABLE expenses (
                    expense_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    expense_category_id INTEGER,
                    predefined_expense TEXT,
                    description TEXT,
                    amount REAL NOT NULL,
                    expense_date DATE NOT NULL,
                    FOREIGN KEY (expense_category_id) REFERENCES expense_categories(expense_category_id)
                )
            """)
            print("Created table: expenses")
        elif "predefined_expense" not in columns:
            cursor.execute("""
                ALTER TABLE expenses
                ADD COLUMN predefined_expense TEXT
            """)
            print("Added predefined_expense column to expenses table")

        conn.commit()
        if not db_exists:
            print("New database created with all tables.")
        else:
            print("Database already exists. Checked and updated tables as needed.")
    except sqlite3.Error as e:
        print(f"Error creating tables: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    create_tables()