import sqlite3

DB_NAME = "database.db"

def create_connection():
    try:
        conn = sqlite3.connect(DB_NAME, timeout=10)
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn
    except sqlite3.Error as e:
        print(f"Error connecting to database: {e}")
        return None

def display_all_tables(conn):
    cursor = conn.cursor()
    tables = [
        "brands", "categories", "descriptions", "units_of_measurement", 
        "products", "inventory", "inventory_batches", "sales", 
        "sale_batches", "expense_categories", "expenses"
    ]
    for table in tables:
        try:
            cursor.execute(f"SELECT * FROM {table}")
            rows = cursor.fetchall()
            if rows:
                print(f"\nTable: {table}")
                print("-" * 40)
                for row in rows:
                    print(row)
            else:
                print(f"\nTable: {table} (empty)")
        except sqlite3.Error as e:
            print(f"Error reading table {table}: {e}")

def inject_data():
    conn = create_connection()
    if not conn:
        return
    cursor = conn.cursor()

    try:
        # Data from test data.xlsx
        data = [
            {"product": "Cement", "brands": "Hima, Tororo, Simba, Kampala", "category": "Building Materials", 
             "descriptions": "Portland Cement CEM 1 42.5 N, Portland Cement CEM II 32.5 N, Low Heat Cement", "units": "50kg bag"},
            {"product": "Rebar", "brands": "Steelco, Armco", "category": "Building Materials", 
             "descriptions": "10mm diameter, ribbed; 12mm diameter, ribbed; 16mm diameter, smooth", "units": "14ft piece"},
            {"product": "Paint", "brands": "Plascon, Crown, Dulux", "category": "Paints and Coatings", 
             "descriptions": "PVC Emulsion Paint, Gloss Enamel Paint, WeatherGuard", "units": "20 litre can, 4kg tin, 1 litre"},
            {"product": "PVC Pipe", "brands": "Armco, Pipo", "category": "Plumbing", 
             "descriptions": "4-inch diameter; 2-inch diameter; 1-inch diameter", "units": "meter"},
            {"product": "Electrical Cable", "brands": "Kable, UPL", "category": "Electricals", 
             "descriptions": "1.5mm single core; 2.5mm single core; 4.0mm twin and earth", "units": "meter, roll"},
            {"product": "Roofing Sheet", "brands": "Sky, Simba", "category": "Roofing", 
             "descriptions": "Corrugated metal sheet; Aluminium corrugated sheet; Iron sheet gauge 30", "units": "piece, bundle"},
            {"product": "Shovel", "brands": "Haffner, Roko", "category": "Hand Tools", 
             "descriptions": "Wooden handle; Fiberglass handle; Square point", "units": "piece"},
            {"product": "Trowel", "brands": "Haffner, Roko", "category": "Hand Tools", 
             "descriptions": "4-inch plastic handle; 6-inch steel handle; Pointed", "units": "piece"},
            {"product": "Wood Screws", "brands": "Boss, T-Fare", "category": "Fasteners", 
             "descriptions": "Self-tapping, assorted; Flat head; Phillips head", "units": "box, kg"},
            {"product": "Padlock", "brands": "UPL, Benda", "category": "Fasteners", 
             "descriptions": "40mm diameter; 50mm diameter; 60mm shackle", "units": "piece"},
            {"product": "Water Pump", "brands": "Benda, Armco", "category": "Plumbing", 
             "descriptions": "Manual hand pump; 300W submersible; 1 HP centrifugal", "units": "piece"},
            {"product": "Angle Grinder", "brands": "Roko, T-Fare", "category": "Hand Tools", 
             "descriptions": "4.5-inch disc; 7-inch disc; 115mm cordless", "units": "piece"},
            {"product": "Drill", "brands": "Roko, Boss", "category": "Hand Tools", 
             "descriptions": "Corded hammer drill; Cordless drill driver; Impact drill", "units": "piece"},
            {"product": "Roofing Nail", "brands": "T-Fare, Simba", "category": "Roofing", 
             "descriptions": "Flat sheets; Galvanized iron, gauge 28; Plastic head", "units": "box, kg"},
            {"product": "Gumboots", "brands": "Pipo", "category": "Hand Tools", 
             "descriptions": "PVC gumboots, various sizes", "units": "pair"},
            {"product": "Hosepipe", "brands": "Roko, Benda", "category": "Plumbing", 
             "descriptions": "12mm diameter, ribbed; Garden hose, braided; 25mm diameter", "units": "meter"},
            {"product": "Hammer", "brands": "Boss, Haffner", "category": "Hand Tools", 
             "descriptions": "Claw hammer; Sledge hammer; Ball-peen hammer", "units": "piece"},
            {"product": "Nail", "brands": "T-Fare, Boss", "category": "Fasteners", 
             "descriptions": "Wire nail, assorted; Concrete nail; Common nail", "units": "box, 50kg bag"},
            {"product": "Paint Brush", "brands": "Plascon, Crown", "category": "Paints and Coatings", 
             "descriptions": "2-inch wide; 4-inch wide; Roller brush", "units": "piece"},
            {"product": "Socket", "brands": "Kable, UPL", "category": "Electricals", 
             "descriptions": "Single socket outlet; Double socket outlet; 13A switched", "units": "piece"},
            {"product": "Switch", "brands": "Kable, UPL", "category": "Electricals", 
             "descriptions": "Single gang light switch; Double gang light switch; Two-way switch", "units": "piece"},
            {"product": "Pliers", "brands": "Haffner, Boss", "category": "Hand Tools", 
             "descriptions": "Combination pliers; Long nose pliers; Water pump pliers", "units": "piece"},
            {"product": "Wrench", "brands": "Haffner, Roko", "category": "Hand Tools", 
             "descriptions": "Adjustable spanner; Pipe wrench; Hex key set", "units": "piece"},
            {"product": "Tape Measure", "brands": "Roko, T-Fare", "category": "Hand Tools", 
             "descriptions": "5m steel tape; 8m steel tape; 30m fiberglass tape", "units": "piece"},
            {"product": "Wheelbarrow", "brands": "Roko, Benda", "category": "Hand Tools", 
             "descriptions": "Heavy duty; Single wheel; Double wheel", "units": "piece"},
            {"product": "Safety Goggles", "brands": "Pipo, Simba", "category": "Hand Tools", 
             "descriptions": "Clear lenses; Tinted lenses; Face shield", "units": "piece"},
            {"product": "Drill Bit", "brands": "Roko, Boss", "category": "Hand Tools", 
             "descriptions": "Masonry bit set; Wood bit set; HSS metal drill bits", "units": "box"},
            {"product": "Caulking Gun", "brands": "Plascon, Crown", "category": "Hand Tools", 
             "descriptions": "Standard size; Heavy duty", "units": "piece"},
            {"product": "Padlock Shackle", "brands": "UPL, Benda", "category": "Fasteners", 
             "descriptions": "Long shackle; Standard shackle", "units": "piece"},
            {"product": "Pipe Cutter", "brands": "Armco, Benda", "category": "Plumbing", 
             "descriptions": "Copper pipe cutter; PVC pipe cutter", "units": "piece"}
        ]

        inserted_count = 0
        skipped_count = 0

        conn.execute("BEGIN TRANSACTION")

        for row in data:
            # Insert or get category
            category = row["category"].strip()
            cursor.execute("SELECT category_id FROM categories WHERE category_name=?", (category,))
            category_id = cursor.fetchone()
            if not category_id:
                cursor.execute("INSERT INTO categories (category_name) VALUES (?)", (category,))
                category_id = (cursor.lastrowid,)

            # Split brands, descriptions, units
            brands = [b.strip() for b in row["brands"].replace(";", ",").split(",")]
            descriptions = [d.strip() for d in row["descriptions"].replace(";", ",").split(",")]
            units = [u.strip() for u in row["units"].replace(";", ",").split(",")]

            for brand in brands:
                # Insert or get brand
                cursor.execute("SELECT brand_id FROM brands WHERE brand_name=?", (brand,))
                brand_id = cursor.fetchone()
                if not brand_id:
                    cursor.execute("INSERT INTO brands (brand_name) VALUES (?)", (brand,))
                    brand_id = (cursor.lastrowid,)

                for desc in descriptions:
                    # Insert or get description
                    cursor.execute("SELECT description_id FROM descriptions WHERE description_text=?", (desc,))
                    description_id = cursor.fetchone()
                    if not description_id:
                        cursor.execute("INSERT INTO descriptions (description_text) VALUES (?)", (desc,))
                        description_id = (cursor.lastrowid,)

                    for unit in units:
                        # Insert or get unit
                        cursor.execute("SELECT unit_id FROM units_of_measurement WHERE unit_name=?", (unit,))
                        unit_id = cursor.fetchone()
                        if not unit_id:
                            cursor.execute("INSERT INTO units_of_measurement (unit_name) VALUES (?)", (unit,))
                            unit_id = (cursor.lastrowid,)

                        # Check for existing product
                        cursor.execute("""
                            SELECT product_id FROM products
                            WHERE product_name=? AND brand_id=? AND category_id=? AND description_id=? AND unit_id=?
                        """, (row["product"], brand_id[0], category_id[0], description_id[0], unit_id[0]))
                        existing_product = cursor.fetchone()

                        if not existing_product:
                            # Insert product
                            cursor.execute("""
                                INSERT INTO products (product_name, brand_id, category_id, description_id, unit_id)
                                VALUES (?, ?, ?, ?, ?)
                            """, (row["product"], brand_id[0], category_id[0], description_id[0], unit_id[0]))
                            inserted_count += 1
                        else:
                            skipped_count += 1

        conn.commit()
        print(f"Data injected successfully: {inserted_count} products inserted, {skipped_count} duplicates skipped.")

        # Prompt to view all tables
        response = input("\nWould you like to view all tables in the database? (yes/no): ").strip().lower()
        if response == "yes":
            display_all_tables(conn)

    except sqlite3.Error as e:
        conn.rollback()
        print(f"Error injecting data: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    inject_data()