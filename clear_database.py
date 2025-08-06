import sqlite3
import os

DB_NAME = "database.db"

def clear_all_table_data():
    """
    Connects to the SQLite database and deletes all data from every user-created table
    in an order that respects foreign key constraints.
    """
    if not os.path.exists(DB_NAME):
        print(f"Error: Database file '{DB_NAME}' not found.")
        return

    try:
        # Establish a connection to the database
        conn = sqlite3.connect(DB_NAME, timeout=10)
        conn.execute("PRAGMA foreign_keys = ON;")
        cursor = conn.cursor()

        # Define table deletion order to respect foreign key constraints
        table_order = [
            "sale_batches",  # Depends on sales, inventory_batches
            "sales",        # Depends on products, units_of_measurement
            "inventory_batches",  # Depends on products, units_of_measurement
            "inventory",    # Depends on products
            "expenses",     # Depends on expense_categories
            "products",     # Depends on brands, categories, descriptions, units_of_measurement
            "brands",
            "categories",
            "descriptions",
            "units_of_measurement",
            "expense_categories"
        ]

        print("Clearing data from the following tables:")
        cleared_tables = []
        # Loop through tables in order
        for table_name in table_order:
            # Verify table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name = ?", (table_name,))
            if cursor.fetchone():
                print(f"- {table_name}")
                try:
                    cursor.execute(f"DELETE FROM {table_name};")
                    cleared_tables.append(table_name)
                except sqlite3.Error as e:
                    print(f"  Error clearing {table_name}: {e}")

        # Clear sqlite_sequence to reset AUTOINCREMENT counters
        cursor.execute("DELETE FROM sqlite_sequence;")
        print("- sqlite_sequence (AUTOINCREMENT counters reset)")

        # Commit changes
        conn.commit()
        if cleared_tables:
            print("\nSuccessfully cleared data from all specified tables.")
        else:
            print("\nNo tables were cleared.")

    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    # Ask for confirmation before proceeding
    confirm = input(f"Are you sure you want to permanently delete all data from '{DB_NAME}'? (yes/no): ")
    if confirm.lower() == 'yes':
        clear_all_table_data()
    else:
        print("Operation cancelled.")