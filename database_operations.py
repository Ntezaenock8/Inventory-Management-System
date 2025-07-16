import sqlite3

DB_NAME = "database.db"

def add_restocking(date, item, description, quantity, unit_price, total):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO restocking (date, item, description, quantity, unit_price, total)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (date, item, description or "N/A", quantity, unit_price, total))
    conn.commit()
    conn.close()

def delete_restocking_by_id(row_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM restocking WHERE id = ?", (row_id,))
    conn.commit()
    conn.close()

def update_restocking(row_id, date, item, brand_description, quantity, unit_price, total):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE restocking
        SET date = ?, item = ?, brand_description = ?, quantity = ?, unit_price = ?, total = ?
        WHERE id = ?
    """, (date, item, brand_description or "N/A", quantity, unit_price, total, row_id))
    conn.commit()
    conn.close()
