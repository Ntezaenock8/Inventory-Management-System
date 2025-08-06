import tkinter as tk
from tkinter import ttk, font, messagebox
import sqlite3
from datetime import datetime
from data_cache import get_products
import locale

# Set locale for currency formatting
locale.setlocale(locale.LC_ALL, '')

DB_NAME = "database.db"

# --- Helper Functions ---
def get_units():
    """Fetch all units for Combobox."""
    conn = sqlite3.connect(DB_NAME, timeout=10)
    cursor = conn.cursor()
    cursor.execute("SELECT unit_name FROM units_of_measurement")
    rows = cursor.fetchall()
    conn.close()
    return [row[0] for row in rows]

def get_batches():
    """Fetch inventory_batches for Treeview."""
    conn = sqlite3.connect(DB_NAME, timeout=10)
    conn.execute("PRAGMA foreign_keys = ON;")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT ib.batch_id, p.product_name, b.brand_name, d.description_text,
               ib.quantity, ib.buying_price, ib.purchase_date, u.unit_name
        FROM inventory_batches ib
        JOIN products p ON ib.product_id = p.product_id
        JOIN brands b ON p.brand_id = b.brand_id
        JOIN descriptions d ON p.description_id = d.description_id
        JOIN units_of_measurement u ON ib.unit_id = u.unit_id
    """)
    rows = cursor.fetchall()
    conn.close()
    return [(row[0], f"{row[1]} - {row[2]} - {row[3]}", row[4], row[5], row[6], row[7]) for row in rows]

def save_restock(batch_id, product_id, quantity, buying_price, purchase_date, unit_name):
    """Save or update restocking data in inventory_batches and update inventory."""
    conn = sqlite3.connect(DB_NAME, timeout=10)
    conn.execute("PRAGMA foreign_keys = ON;")
    cursor = conn.cursor()
    try:
        conn.execute("BEGIN TRANSACTION")
        # Get unit_id
        cursor.execute("SELECT unit_id FROM units_of_measurement WHERE unit_name = ?", (unit_name,))
        unit_id = cursor.fetchone()
        if not unit_id:
            cursor.execute("INSERT INTO units_of_measurement (unit_name) VALUES (?)", (unit_name,))
            unit_id = (cursor.lastrowid,)
        
        if batch_id:  # Update existing batch
            # Get old quantity for inventory adjustment
            cursor.execute("SELECT quantity FROM inventory_batches WHERE batch_id = ?", (batch_id,))
            old_quantity = cursor.fetchone()[0]
            cursor.execute("""
                UPDATE inventory_batches
                SET product_id = ?, buying_price = ?, quantity = ?, purchase_date = ?, unit_id = ?
                WHERE batch_id = ?
            """, (product_id, buying_price, quantity, purchase_date, unit_id[0], batch_id))
            # Adjust inventory
            cursor.execute("SELECT quantity FROM inventory WHERE product_id = ?", (product_id,))
            existing = cursor.fetchone()
            if existing:
                new_quantity = existing[0] - old_quantity + quantity
                cursor.execute("UPDATE inventory SET quantity = ? WHERE product_id = ?", (new_quantity, product_id))
        else:  # Insert new batch
            cursor.execute("""
                INSERT INTO inventory_batches (product_id, buying_price, quantity, purchase_date, unit_id)
                VALUES (?, ?, ?, ?, ?)
            """, (product_id, buying_price, quantity, purchase_date, unit_id[0]))
            # Update or insert into inventory
            cursor.execute("SELECT quantity FROM inventory WHERE product_id = ?", (product_id,))
            existing = cursor.fetchone()
            if existing:
                new_quantity = existing[0] + quantity
                cursor.execute("UPDATE inventory SET quantity = ? WHERE product_id = ?", (new_quantity, product_id))
            else:
                cursor.execute("INSERT INTO inventory (product_id, quantity) VALUES (?, ?)", (product_id, quantity))
        
        conn.commit()
        return True
    except sqlite3.OperationalError as e:
        conn.rollback()
        messagebox.showerror("Database Error", f"Error saving restock: {e}")
        return False
    except sqlite3.Error as e:
        conn.rollback()
        messagebox.showerror("Database Error", f"Error saving restock: {e}")
        return False
    finally:
        conn.close()

def delete_batch(batch_id, product_id, quantity):
    """Delete a batch and update inventory quantity."""
    conn = sqlite3.connect(DB_NAME, timeout=10)
    conn.execute("PRAGMA foreign_keys = ON;")
    cursor = conn.cursor()
    try:
        conn.execute("BEGIN TRANSACTION")
        # Delete from inventory_batches
        cursor.execute("DELETE FROM inventory_batches WHERE batch_id = ?", (batch_id,))
        # Update inventory
        cursor.execute("SELECT quantity FROM inventory WHERE product_id = ?", (product_id,))
        existing = cursor.fetchone()
        if existing:
            new_quantity = existing[0] - quantity
            if new_quantity > 0:
                cursor.execute("UPDATE inventory SET quantity = ? WHERE product_id = ?", (new_quantity, product_id))
            else:
                cursor.execute("DELETE FROM inventory WHERE product_id = ?", (product_id,))
        conn.commit()
        return True
    except sqlite3.OperationalError as e:
        conn.rollback()
        messagebox.showerror("Database Error", f"Error deleting batch: {e}")
        return False
    except sqlite3.Error as e:
        conn.rollback()
        messagebox.showerror("Database Error", f"Error deleting batch: {e}")
        return False
    finally:
        conn.close()

def edit_selected():
    global has_unsaved_changes
    selected = tree.selection()
    if not selected:
        messagebox.showwarning("No Selection", "Please select a batch to edit.")
        return
    values = tree.item(selected[0])['values']
    # Fetch batch_id
    conn = sqlite3.connect(DB_NAME, timeout=10)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT ib.batch_id
        FROM inventory_batches ib
        JOIN products p ON ib.product_id = p.product_id
        JOIN brands b ON p.brand_id = b.brand_id
        JOIN descriptions d ON p.description_id = d.description_id
        JOIN units_of_measurement u ON ib.unit_id = u.unit_id
        WHERE p.product_name || ' - ' || b.brand_name || ' - ' || d.description_text = ?
        AND ib.quantity = ? AND ib.buying_price = ? AND ib.purchase_date = ? AND u.unit_name = ?
    """, (values[0], values[1], float(values[2].replace(',', '')), values[3], values[4]))
    batch_id = cursor.fetchone()
    conn.close()
    if batch_id:
        batch_id_var.set(batch_id[0])
        product_var.set(values[0])
        quantity_var.set(str(values[1]))
        buying_price_var.set(locale.format_string("%.2f", values[2].replace(',', ''), grouping=True))
        purchase_date_var.set(values[3])
        unit_var.set(values[4])
        has_unsaved_changes = False

def delete_selected():
    global has_unsaved_changes
    global is_treeview_cleared
    selected = tree.selection()
    if not selected:
        messagebox.showwarning("No Selection", "Please select a batch to delete.")
        return
    values = tree.item(selected[0])['values']
    conn = sqlite3.connect(DB_NAME, timeout=10)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT ib.batch_id, ib.product_id, ib.quantity
        FROM inventory_batches ib
        JOIN products p ON ib.product_id = p.product_id
        JOIN brands b ON p.brand_id = b.brand_id
        JOIN descriptions d ON p.description_id = d.description_id
        JOIN units_of_measurement u ON ib.unit_id = u.unit_id
        WHERE p.product_name || ' - ' || b.brand_name || ' - ' || d.description_text = ?
        AND ib.quantity = ? AND ib.buying_price = ? AND ib.purchase_date = ? AND u.unit_name = ?
    """, (values[0], values[1], float(values[2].replace(',', '')), values[3], values[4]))
    result = cursor.fetchone()
    conn.close()
    if result:
        batch_id, product_id, quantity = result
        if messagebox.askyesno("Confirm Deletion", "Are you sure you want to delete this batch?"):
            if delete_batch(batch_id, product_id, quantity):
                refresh_tree(fetch_data=not is_treeview_cleared)
                clear_form()
                has_unsaved_changes = False

def save_data():
    global has_unsaved_changes
    global is_treeview_cleared
    # Validate inputs
    product_display = product_var.get().strip()
    if not product_display:
        messagebox.showerror("Missing Data", "Please select a product.")
        return
    product_id = product_map.get(product_display)
    if not product_id:
        messagebox.showerror("Invalid Product", "Selected product is invalid.")
        return
    
    quantity = quantity_var.get().strip()
    try:
        quantity = int(quantity)
        if quantity <= 0:
            raise ValueError
    except ValueError:
        messagebox.showerror("Invalid Quantity", "Quantity must be a positive integer.")
        return
    
    buying_price = buying_price_var.get().strip().replace(',', '')
    try:
        buying_price = float(buying_price)
        if buying_price < 0:
            raise ValueError
    except ValueError:
        messagebox.showerror("Invalid Price", "Buying price must be a non-negative number.")
        return
    
    purchase_date = purchase_date_var.get().strip()
    try:
        datetime.strptime(purchase_date, "%Y-%m-%d")
    except ValueError:
        messagebox.showerror("Invalid Date", "Purchase date must be in YYYY-MM-DD format (e.g., 2025-07-19).")
        return
    
    unit_name = unit_var.get().strip()
    if not unit_name:
        messagebox.showerror("Missing Data", "Please select or enter a unit of measurement.")
        return
    
    # Save or update batch
    batch_id = batch_id_var.get()
    if save_restock(batch_id, product_id, quantity, buying_price, purchase_date, unit_name):
        if is_treeview_cleared:
            # Append only the new batch to Treeview
            formatted_price = locale.format_string("%.2f", buying_price, grouping=True)
            tree.insert("", "end", values=(product_display, quantity, formatted_price, purchase_date, unit_name))
        else:
            refresh_tree(fetch_data=True)
        clear_form()
        has_unsaved_changes = False

def clear_form():
    batch_id_var.set("")
    product_var.set("")
    quantity_var.set("")
    buying_price_var.set("")
    purchase_date_var.set(datetime.today().strftime("%Y-%m-%d"))  # Set to current date
    unit_var.set("")
    search_var.set("")  # Clear search field
    product_combo['values'] = [p[0] for p in products]  # Reset Combobox to full product list
    global product_map
    product_map = {p[0]: p[1] for p in products}  # Reset product map
    unit_combo['values'] = get_units()  # Reset to all units
    global has_unsaved_changes
    has_unsaved_changes = False

def clear_treeview():
    """Clear Treeview without affecting database."""
    global is_treeview_cleared
    for row in tree.get_children():
        tree.delete(row)
    is_treeview_cleared = True

def refresh_tree(fetch_data=True):
    """Refresh Treeview, optionally fetching data from database."""
    global is_treeview_cleared
    for row in tree.get_children():
        tree.delete(row)
    if fetch_data and not is_treeview_cleared:
        for row in get_batches():
            # Format buying_price with commas for display
            formatted_price = locale.format_string("%.2f", row[3], grouping=True)
            tree.insert("", "end", values=(row[1], row[2], formatted_price, row[4], row[5]))
        is_treeview_cleared = False

# --- UI Setup ---
root = tk.Tk()
root.title("Restocking Module")
root.geometry("800x600")

# Define custom font (consistent with products_manager_view.py)
custom_font = font.Font(family="TkDefaultFont", size=13)

# --- Form Frame ---
form = tk.Frame(root)
form.pack(pady=10)

# Variables
batch_id_var = tk.StringVar()  # Hidden, for editing existing batches
product_var = tk.StringVar()
quantity_var = tk.StringVar()
buying_price_var = tk.StringVar()
purchase_date_var = tk.StringVar(value=datetime.today().strftime("%Y-%m-%d"))  # Set initial date
unit_var = tk.StringVar()
search_var = tk.StringVar()

# Initialize Treeview state
is_treeview_cleared = True

# Search Product and Product Combobox
tk.Label(form, text="Search Product", font=custom_font).grid(row=0, column=0, sticky="e", padx=5, pady=5)
product_frame = tk.Frame(form)
product_frame.grid(row=0, column=1, rowspan=2, sticky="w", padx=5, pady=5)

search_entry = tk.Entry(product_frame, textvariable=search_var, font=custom_font, width=50)
search_entry.grid(row=0, column=0, padx=5, pady=2)

tk.Label(form, text="Product", font=custom_font).grid(row=1, column=0, sticky="e", padx=5, pady=5)
product_combo = ttk.Combobox(product_frame, textvariable=product_var, font=custom_font, width=50, state="readonly")
product_combo.grid(row=1, column=0, padx=5, pady=2)

# Initialize products and product map
products = get_products()
product_map = {p[0]: p[1] for p in products}
product_combo['values'] = [p[0] for p in products]

def update_combobox(event=None):
    """Filter Combobox based on search input."""
    search_text = search_var.get().strip().lower()
    filtered_products = [(p[0], p[1]) for p in products if search_text in p[0].lower()]
    product_combo['values'] = [p[0] for p in filtered_products]
    # Update product_map with filtered products
    global product_map
    product_map = {p[0]: p[1] for p in filtered_products}
    if filtered_products and not product_var.get() in [p[0] for p in filtered_products]:
        product_combo.set("")

def open_combobox_dropdown(event=None):
    """Open Combobox dropdown after filtering."""
    update_combobox()  # Ensure filter is applied
    if product_combo['values']:  # Only open if there are filtered products
        product_combo.focus()  # Set focus to Combobox
        product_combo.event_generate("<Button-1>", x=0, y=0)  # Simulate click to open dropdown

search_entry.bind("<KeyRelease>", update_combobox)
search_entry.bind("<Return>", open_combobox_dropdown)

# Quantity
tk.Label(form, text="Quantity", font=custom_font).grid(row=2, column=0, sticky="e", padx=5, pady=5)
tk.Entry(form, textvariable=quantity_var, font=custom_font, width=20).grid(row=2, column=1, sticky="w", padx=5, pady=5)

# Buying Price
tk.Label(form, text="Buying Price", font=custom_font).grid(row=3, column=0, sticky="e", padx=5, pady=5)
tk.Entry(form, textvariable=buying_price_var, font=custom_font, width=20).grid(row=3, column=1, sticky="w", padx=5, pady=5)

# Purchase Date
tk.Label(form, text="Purchase Date (YYYY-MM-DD)", font=custom_font).grid(row=4, column=0, sticky="e", padx=5, pady=5)
tk.Entry(form, textvariable=purchase_date_var, font=custom_font, width=20).grid(row=4, column=1, sticky="w", padx=5, pady=5)

# Unit of Measurement Combobox
tk.Label(form, text="Unit of Measurement", font=custom_font).grid(row=5, column=0, sticky="e", padx=5, pady=5)
unit_combo = ttk.Combobox(form, textvariable=unit_var, font=custom_font, width=20)
unit_combo.grid(row=5, column=1, sticky="w", padx=5, pady=5)
unit_combo['values'] = get_units()

# --- Save Button Frame ---
save_btn_frame = tk.Frame(root)
save_btn_frame.pack(pady=5)
tk.Button(save_btn_frame, text="Save Stock", font=custom_font, command=save_data, bg="#28a745", fg="white", width=15).pack()

# --- Treeview for Preview ---
tree_frame = tk.Frame(root)
tree_frame.pack(fill="both", expand=True, padx=10, pady=10)

columns = ("product", "quantity", "buying_price", "purchase_date", "unit")
style = ttk.Style()
style.theme_use('clam')
style.configure("Treeview", font=custom_font)
style.configure("Treeview.Heading", font=(custom_font.cget("family"), custom_font.cget("size"), "bold"))

tree = ttk.Treeview(tree_frame, columns=columns, show="headings", style="Treeview")
tree.heading("product", text="Product")
tree.heading("quantity", text="Quantity")
tree.heading("buying_price", text="Buying Price")
tree.heading("purchase_date", text="Purchase Date")
tree.heading("unit", text="Unit of Measurement")
tree.column("product", width=300, anchor="w")
tree.column("quantity", width=100, anchor="center")
tree.column("buying_price", width=150, anchor="center")
tree.column("purchase_date", width=150, anchor="center")
tree.column("unit", width=100, anchor="center")

# Add vertical scrollbar
scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
tree.configure(yscrollcommand=scrollbar.set)
tree.grid(row=0, column=0, sticky="nsew")
scrollbar.grid(row=0, column=1, sticky="ns")
tree_frame.grid_rowconfigure(0, weight=1)
tree_frame.grid_columnconfigure(0, weight=1)

# --- Edit/Delete/Refresh Button Frame ---
edit_delete_btn_frame = tk.Frame(root)
edit_delete_btn_frame.pack(pady=5)
tk.Button(edit_delete_btn_frame, text="Edit", font=custom_font, command=edit_selected, width=15).pack(side=tk.LEFT, padx=5)
tk.Button(edit_delete_btn_frame, text="Delete", font=custom_font, command=delete_selected, width=15).pack(side=tk.LEFT, padx=5)
tk.Button(edit_delete_btn_frame, text="Refresh", font=custom_font, command=clear_treeview, width=15).pack(side=tk.LEFT, padx=5)

# --- Track Changes ---
has_unsaved_changes = False

def mark_changes(*args):
    global has_unsaved_changes
    if product_var.get() or quantity_var.get() or buying_price_var.get() or purchase_date_var.get() or unit_var.get():
        has_unsaved_changes = True

product_var.trace_add("write", mark_changes)
quantity_var.trace_add("write", mark_changes)
buying_price_var.trace_add("write", mark_changes)
purchase_date_var.trace_add("write", mark_changes)
unit_var.trace_add("write", mark_changes)

# --- Prevent Exit Without Saving ---
def on_closing():
    global has_unsaved_changes
    if has_unsaved_changes:
        if messagebox.askyesno("Unsaved Changes", "You have unsaved changes. Do you want to save before exiting?"):
            save_data()
        else:
            clear_treeview()  # Clear Treeview on close
            root.destroy()
    else:
        clear_treeview()  # Clear Treeview on close
        root.destroy()

root.protocol("WM_DELETE_WINDOW", on_closing)

# --- Run Application ---
if __name__ == "__main__":
    root.mainloop()