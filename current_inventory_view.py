import tkinter as tk
from tkinter import ttk, font, messagebox
import sqlite3
from data_cache import get_products

DB_NAME = "database.db"
LOW_STOCK_THRESHOLD = 10  # Global limit for low stock warning

# --- Helper Functions ---
def get_inventory():
    """Fetch current inventory for Treeview."""
    conn = sqlite3.connect(DB_NAME, timeout=10)
    conn.execute("PRAGMA foreign_keys = ON;")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT i.product_id, p.product_name, b.brand_name, d.description_text,
               i.quantity, u.unit_name
        FROM inventory i
        JOIN products p ON i.product_id = p.product_id
        JOIN brands b ON p.brand_id = b.brand_id
        JOIN descriptions d ON p.description_id = d.description_id
        JOIN units_of_measurement u ON p.unit_id = u.unit_id
    """)
    rows = cursor.fetchall()
    conn.close()
    return [(f"{row[1]} - {row[2]} - {row[3]}", row[4], row[5]) for row in rows]

# --- UI Setup ---
root = tk.Tk()
root.title("Current Inventory View")
root.geometry("800x600")

# Define custom font (consistent with other modules)
custom_font = font.Font(family="TkDefaultFont", size=13)

# --- Treeview for Inventory ---
tree_frame = tk.Frame(root)
tree_frame.pack(fill="both", expand=True, padx=10, pady=10)

columns = ("product", "quantity", "unit")
style = ttk.Style()
style.theme_use('clam')  # Use 'clam' theme to ensure background color support
style.configure("Treeview", font=custom_font)
style.configure("Treeview.Heading", font=(custom_font.cget("family"), custom_font.cget("size"), "bold"))

tree = ttk.Treeview(tree_frame, columns=columns, show="headings", style="Treeview")
tree.heading("product", text="Product")
tree.heading("quantity", text="Quantity")
tree.heading("unit", text="Unit of Measurement")
tree.column("product", width=350, anchor="w")
tree.column("quantity", width=80, anchor="center")
tree.column("unit", width=80, anchor="center")
tree.tag_configure("low_stock", background="#FF9999")  # Light red for low stock tag

# Add vertical scrollbar
scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
tree.configure(yscrollcommand=scrollbar.set)
tree.grid(row=0, column=0, sticky="nsew")
scrollbar.grid(row=0, column=1, sticky="ns")
tree_frame.grid_rowconfigure(0, weight=1)
tree_frame.grid_columnconfigure(0, weight=1)

# --- Message Label for No Records ---
no_records_label = tk.Label(tree_frame, text="No inventory records found.", font=custom_font, fg="red")
no_records_label.grid(row=1, column=0, sticky="nsew", pady=10)
no_records_label.grid_remove()  # Hide by default

# --- Refresh Button ---
refresh_btn_frame = tk.Frame(root)
refresh_btn_frame.pack(pady=5)
tk.Button(refresh_btn_frame, text="Refresh", font=custom_font, command=lambda: refresh_tree(), bg="#28a745", fg="white", width=15).pack()

# --- Populate Treeview ---
def refresh_tree():
    """Refresh Treeview with current inventory data, highlighting low stock."""
    for row in tree.get_children():
        tree.delete(row)
    inventory = get_inventory()
    if not inventory:
        no_records_label.grid()  # Show "No records" message
    else:
        no_records_label.grid_remove()  # Hide message
        for row in inventory:
            # Ensure quantity is treated as an integer
            quantity = int(row[1])
            # Apply low_stock tag if quantity < LOW_STOCK_THRESHOLD
            tags = ("low_stock",) if quantity < LOW_STOCK_THRESHOLD else ()
            tree.insert("", "end", values=row, tags=tags)
            # Debug print to verify quantity and tag
            print(f"Product: {row[0]}, Quantity: {quantity}, Tags: {tags}")

refresh_tree()

# --- Run Application ---
if __name__ == "__main__":
    root.mainloop()