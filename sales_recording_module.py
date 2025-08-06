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
    """Fetch units for Combobox."""
    conn = sqlite3.connect(DB_NAME, timeout=10)
    cursor = conn.cursor()
    cursor.execute("SELECT unit_name FROM units_of_measurement")
    rows = cursor.fetchall()
    conn.close()
    return [row[0] for row in rows]

def get_sales():
    """Fetch sales for Treeview."""
    conn = sqlite3.connect(DB_NAME, timeout=10)
    conn.execute("PRAGMA foreign_keys = ON;")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT s.sale_id, p.product_name, b.brand_name, d.description_text,
               s.quantity_sold, s.selling_price, s.sale_date, u.unit_name
        FROM sales s
        JOIN products p ON s.product_id = p.product_id
        JOIN brands b ON p.brand_id = b.brand_id
        JOIN descriptions d ON p.description_id = d.description_id
        JOIN units_of_measurement u ON s.unit_id = u.unit_id
    """)
    rows = cursor.fetchall()
    conn.close()
    return [(row[0], f"{row[1]} - {row[2]} - {row[3]}", row[4], row[5], row[6], row[7]) for row in rows]

def save_sale(sale_id, product_id, quantity_sold, selling_price, sale_date, unit_name):
    """Save or update sale data in sales and sale_batches, update inventory."""
    conn = sqlite3.connect(DB_NAME, timeout=10)
    conn.execute("PRAGMA foreign_keys = ON;")
    cursor = conn.cursor()
    try:
        conn.execute("BEGIN TRANSACTION")
        # Get unit_id
        cursor.execute("SELECT unit_id FROM units_of_measurement WHERE unit_name = ?", (unit_name,))
        unit_id = cursor.fetchone()
        if not unit_id:
            messagebox.showerror("Invalid Unit", "Selected unit is not valid.")
            conn.rollback()
            return False
        
        # Check inventory stock
        cursor.execute("SELECT quantity FROM inventory WHERE product_id = ?", (product_id,))
        inventory = cursor.fetchone()
        inventory_quantity = inventory[0] if inventory else 0
        
        # Validate sale_id for edits
        is_edit = False
        if sale_id:
            try:
                sale_id = int(sale_id)  # Ensure sale_id is an integer
                is_edit = True
            except ValueError:
                messagebox.showerror("Invalid Sale ID", "Sale ID is invalid.")
                conn.rollback()
                return False
        
        if is_edit:  # Update existing sale
            # Get old sale data from sales
            cursor.execute("SELECT quantity_sold FROM sales WHERE sale_id = ?", (sale_id,))
            old_sale = cursor.fetchone()
            if not old_sale:
                messagebox.showerror("Invalid Sale", "Sale record not found.")
                conn.rollback()
                return False
            old_quantity_sold = old_sale[0]
            
            # Get batch_id and unit_id from sale_batches
            cursor.execute("SELECT batch_id, unit_id FROM sale_batches WHERE sale_id = ?", (sale_id,))
            sale_batch = cursor.fetchone()
            if not sale_batch:
                messagebox.showerror("Invalid Sale Batch", "Sale batch record not found.")
                conn.rollback()
                return False
            old_batch_id, old_unit_id = sale_batch
            
            if old_unit_id == unit_id[0]:
                # Same unit, use original batch
                batch_id = old_batch_id
                cursor.execute("SELECT quantity, buying_price FROM inventory_batches WHERE batch_id = ?", (batch_id,))
                batch = cursor.fetchone()
                if not batch:
                    messagebox.showerror("No Batch", "Original batch no longer exists.")
                    conn.rollback()
                    return False
                batch_quantity, batch_buying_price = batch
            else:
                # Unit changed, get oldest batch for new unit
                cursor.execute("""
                    SELECT batch_id, buying_price, quantity
                    FROM inventory_batches
                    WHERE product_id = ? AND unit_id = ?
                    ORDER BY purchase_date ASC
                    LIMIT 1
                """, (product_id, unit_id[0]))
                batch = cursor.fetchone()
                if not batch:
                    messagebox.showerror("No Batch", "No inventory batch available for this product and unit.")
                    conn.rollback()
                    return False
                batch_id, batch_buying_price, batch_quantity = batch
            
            # Check inventory for edit
            if inventory_quantity + old_quantity_sold < quantity_sold:
                messagebox.showerror("Insufficient Stock", "Not enough inventory to fulfill this sale.")
                conn.rollback()
                return False
            if batch_quantity < quantity_sold:
                messagebox.showerror("Insufficient Batch Stock", "Not enough stock in the selected batch.")
                conn.rollback()
                return False
            
            # Update sales
            cursor.execute("""
                UPDATE sales
                SET product_id = ?, selling_price = ?, quantity_sold = ?, sale_date = ?, unit_id = ?
                WHERE sale_id = ?
            """, (product_id, selling_price, quantity_sold, sale_date, unit_id[0], sale_id))
            
            # Update sale_batches
            cursor.execute("""
                UPDATE sale_batches
                SET quantity_used = ?, buying_price = ?, unit_id = ?, batch_id = ?
                WHERE sale_id = ?
            """, (quantity_sold, batch_buying_price, unit_id[0], batch_id, sale_id))
            
            # Adjust inventory
            new_quantity = inventory_quantity + old_quantity_sold - quantity_sold
            if new_quantity > 0:
                cursor.execute("UPDATE inventory SET quantity = ? WHERE product_id = ?", (new_quantity, product_id))
            else:
                cursor.execute("DELETE FROM inventory WHERE product_id = ?", (product_id,))
        else:  # Insert new sale
            if inventory_quantity < quantity_sold:
                messagebox.showerror("Insufficient Stock", "Not enough inventory to fulfill this sale.")
                conn.rollback()
                return False
            
            # Get oldest batch (FIFO)
            cursor.execute("""
                SELECT batch_id, buying_price, quantity
                FROM inventory_batches
                WHERE product_id = ? AND unit_id = ?
                ORDER BY purchase_date ASC
                LIMIT 1
            """, (product_id, unit_id[0]))
            batch = cursor.fetchone()
            if not batch:
                messagebox.showerror("No Batch", "No inventory batch available for this product.")
                conn.rollback()
                return False
            batch_id, batch_buying_price, batch_quantity = batch
            
            if batch_quantity < quantity_sold:
                messagebox.showerror("Insufficient Batch Stock", "Not enough stock in the oldest batch.")
                conn.rollback()
                return False
            
            cursor.execute("""
                INSERT INTO sales (product_id, selling_price, quantity_sold, sale_date, unit_id)
                VALUES (?, ?, ?, ?, ?)
            """, (product_id, selling_price, quantity_sold, sale_date, unit_id[0]))
            sale_id = cursor.lastrowid
            
            # Insert into sale_batches
            cursor.execute("""
                INSERT INTO sale_batches (sale_id, batch_id, quantity_used, buying_price, unit_id)
                VALUES (?, ?, ?, ?, ?)
            """, (sale_id, batch_id, quantity_sold, batch_buying_price, unit_id[0]))
            
            # Update inventory
            new_quantity = inventory_quantity - quantity_sold
            if new_quantity > 0:
                cursor.execute("UPDATE inventory SET quantity = ? WHERE product_id = ?", (new_quantity, product_id))
            else:
                cursor.execute("DELETE FROM inventory WHERE product_id = ?", (product_id,))
        
        conn.commit()
        return True
    except sqlite3.OperationalError as e:
        conn.rollback()
        messagebox.showerror("Database Error", f"Error saving sale: {e}")
        return False
    except sqlite3.Error as e:
        conn.rollback()
        messagebox.showerror("Database Error", f"Error saving sale: {e}")
        return False
    finally:
        conn.close()

def delete_sale(sale_id, product_id, quantity_sold):
    """Delete a sale and update inventory quantity."""
    conn = sqlite3.connect(DB_NAME, timeout=10)
    conn.execute("PRAGMA foreign_keys = ON;")
    cursor = conn.cursor()
    try:
        conn.execute("BEGIN TRANSACTION")
        # Explicitly delete from sale_batches first
        cursor.execute("DELETE FROM sale_batches WHERE sale_id = ?", (sale_id,))
        # Delete from sales
        cursor.execute("DELETE FROM sales WHERE sale_id = ?", (sale_id,))
        # Update inventory
        cursor.execute("SELECT quantity FROM inventory WHERE product_id = ?", (product_id,))
        existing = cursor.fetchone()
        if existing:
            new_quantity = existing[0] + quantity_sold
            cursor.execute("UPDATE inventory SET quantity = ? WHERE product_id = ?", (new_quantity, product_id))
        else:
            cursor.execute("INSERT INTO inventory (product_id, quantity) VALUES (?, ?)", (product_id, quantity_sold))
        conn.commit()
        return True
    except sqlite3.OperationalError as e:
        conn.rollback()
        messagebox.showerror("Database Error", f"Error deleting sale: {e}")
        return False
    except sqlite3.Error as e:
        conn.rollback()
        messagebox.showerror("Database Error", f"Error deleting sale: {e}")
        return False
    finally:
        conn.close()

def edit_selected():
    global has_unsaved_changes
    selected = tree.selection()
    if not selected:
        messagebox.showwarning("No Selection", "Please select a sale to edit.")
        return
    values = tree.item(selected[0])['values']
    # Fetch sale_id
    conn = sqlite3.connect(DB_NAME, timeout=10)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT s.sale_id
        FROM sales s
        JOIN products p ON s.product_id = p.product_id
        JOIN brands b ON p.brand_id = b.brand_id
        JOIN descriptions d ON p.description_id = d.description_id
        JOIN units_of_measurement u ON s.unit_id = u.unit_id
        WHERE p.product_name || ' - ' || b.brand_name || ' - ' || d.description_text = ?
        AND s.quantity_sold = ? AND s.selling_price = ? AND s.sale_date = ? AND u.unit_name = ?
    """, (values[0], values[1], float(values[2].replace(',', '')), values[3], values[4]))
    sale_id = cursor.fetchone()
    conn.close()
    if sale_id:
        sale_id_var.set(str(sale_id[0]))  # Ensure sale_id is a string for StringVar
        product_var.set(values[0])
        quantity_var.set(str(values[1]))
        selling_price_var.set(locale.format_string("%.2f", float(values[2].replace(',', '')), grouping=True))
        sale_date_var.set(values[3])
        unit_var.set(values[4])
        has_unsaved_changes = False

def delete_selected():
    global has_unsaved_changes
    global is_treeview_cleared
    selected = tree.selection()
    if not selected:
        messagebox.showwarning("No Selection", "Please select a sale to delete.")
        return
    values = tree.item(selected[0])['values']
    conn = sqlite3.connect(DB_NAME, timeout=10)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT s.sale_id, s.product_id, s.quantity_sold
        FROM sales s
        JOIN products p ON s.product_id = p.product_id
        JOIN brands b ON p.brand_id = b.brand_id
        JOIN descriptions d ON p.description_id = d.description_id
        JOIN units_of_measurement u ON s.unit_id = u.unit_id
        WHERE p.product_name || ' - ' || b.brand_name || ' - ' || d.description_text = ?
        AND s.quantity_sold = ? AND s.selling_price = ? AND s.sale_date = ? AND u.unit_name = ?
    """, (values[0], values[1], float(values[2].replace(',', '')), values[3], values[4]))
    result = cursor.fetchone()
    conn.close()
    if result:
        sale_id, product_id, quantity_sold = result
        if messagebox.askyesno("Confirm Deletion", "Are you sure you want to delete this sale?"):
            if delete_sale(sale_id, product_id, quantity_sold):
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
        messagebox.showerror("Invalid Quantity", "Quantity sold must be a positive integer.")
        return
    
    selling_price = selling_price_var.get().strip().replace(',', '')
    try:
        selling_price = float(selling_price)
        if selling_price < 0:
            raise ValueError
    except ValueError:
        messagebox.showerror("Invalid Price", "Selling price must be a non-negative number.")
        return
    
    sale_date = sale_date_var.get().strip()
    try:
        datetime.strptime(sale_date, "%Y-%m-%d")
    except ValueError:
        messagebox.showerror("Invalid Date", "Sale date must be in YYYY-MM-DD format (e.g., 2025-07-19).")
        return
    
    unit_name = unit_var.get().strip()
    if not unit_name:
        messagebox.showerror("Missing Data", "Please select a unit of measurement.")
        return
    
    # Validate sale_id
    sale_id = sale_id_var.get().strip()
    if sale_id:
        try:
            sale_id = int(sale_id)  # Convert to integer
        except ValueError:
            sale_id = None  # Treat invalid sale_id as new sale
    else:
        sale_id = None  # New sale
    
    # Save or update sale
    if save_sale(sale_id, product_id, quantity, selling_price, sale_date, unit_name):
        if is_treeview_cleared and sale_id:
            # Update existing Treeview row for edit
            selected = tree.selection()
            if selected:
                tree.item(selected[0], values=(product_display, quantity, locale.format_string("%.2f", selling_price, grouping=True), sale_date, unit_name))
        else:
            # Append new sale or refresh full Treeview
            if is_treeview_cleared:
                formatted_price = locale.format_string("%.2f", selling_price, grouping=True)
                tree.insert("", "end", values=(product_display, quantity, formatted_price, sale_date, unit_name))
            else:
                refresh_tree(fetch_data=True)
        clear_form()
        has_unsaved_changes = False

def clear_form():
    sale_id_var.set("")
    product_var.set("")
    quantity_var.set("")
    selling_price_var.set("")
    sale_date_var.set(datetime.today().strftime("%Y-%m-%d"))  # Set to current date
    unit_var.set("")
    search_var.set("")  # Clear search field
    product_combo['values'] = [p[0] for p in products]  # Reset Combobox to full product list
    global product_map
    product_map = {p[0]: p[1] for p in products}  # Reset product map
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
        for row in get_sales():
            # Format selling_price with commas for display
            formatted_price = locale.format_string("%.2f", row[3], grouping=True)
            tree.insert("", "end", values=(row[1], row[2], formatted_price, row[4], row[5]))
        is_treeview_cleared = False

# --- UI Setup ---
root = tk.Tk()
root.title("Sales Recording Module")
root.geometry("800x600")

# Define custom font (consistent with restocking_module.py)
custom_font = font.Font(family="TkDefaultFont", size=13)

# --- Form Frame ---
form = tk.Frame(root)
form.pack(pady=10)

# Variables
sale_id_var = tk.StringVar()  # Hidden, for editing existing sales
product_var = tk.StringVar()
quantity_var = tk.StringVar()
selling_price_var = tk.StringVar()
sale_date_var = tk.StringVar(value=datetime.today().strftime("%Y-%m-%d"))  # Set initial date
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
tk.Label(form, text="Quantity Sold", font=custom_font).grid(row=2, column=0, sticky="e", padx=5, pady=5)
tk.Entry(form, textvariable=quantity_var, font=custom_font, width=20).grid(row=2, column=1, sticky="w", padx=5, pady=5)

# Selling Price
tk.Label(form, text="Selling Price", font=custom_font).grid(row=3, column=0, sticky="e", padx=5, pady=5)
tk.Entry(form, textvariable=selling_price_var, font=custom_font, width=20).grid(row=3, column=1, sticky="w", padx=5, pady=5)

# Sale Date
tk.Label(form, text="Sale Date (YYYY-MM-DD)", font=custom_font).grid(row=4, column=0, sticky="e", padx=5, pady=5)
tk.Entry(form, textvariable=sale_date_var, font=custom_font, width=20).grid(row=4, column=1, sticky="w", padx=5, pady=5)

# Unit of Measurement Combobox
tk.Label(form, text="Unit of Measurement", font=custom_font).grid(row=5, column=0, sticky="e", padx=5, pady=5)
unit_combo = ttk.Combobox(form, textvariable=unit_var, font=custom_font, width=20, state="readonly")
unit_combo.grid(row=5, column=1, sticky="w", padx=5, pady=5)
unit_combo['values'] = get_units()

# --- Save Button Frame ---
save_btn_frame = tk.Frame(root)
save_btn_frame.pack(pady=5)
tk.Button(save_btn_frame, text="Save Sale", font=custom_font, command=save_data, bg="#28a745", fg="white", width=15).pack()

# --- Treeview for Preview ---
tree_frame = tk.Frame(root)
tree_frame.pack(fill="both", expand=True, padx=10, pady=10)

columns = ("product", "quantity_sold", "selling_price", "sale_date", "unit")
style = ttk.Style()
style.theme_use('clam')
style.configure("Treeview", font=custom_font)
style.configure("Treeview.Heading", font=(custom_font.cget("family"), custom_font.cget("size"), "bold"))

tree = ttk.Treeview(tree_frame, columns=columns, show="headings", style="Treeview")
tree.heading("product", text="Product")
tree.heading("quantity_sold", text="Quantity Sold")
tree.heading("selling_price", text="Selling Price")
tree.heading("sale_date", text="Sale Date")
tree.heading("unit", text="Unit of Measurement")
tree.column("product", width=350, anchor="w")
tree.column("quantity_sold", width=80, anchor="center")
tree.column("selling_price", width=120, anchor="center")
tree.column("sale_date", width=120, anchor="center")
tree.column("unit", width=80, anchor="center")

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

# --- Populate Treeview ---
refresh_tree()

# --- Track Changes ---
has_unsaved_changes = False

def mark_changes(*args):
    global has_unsaved_changes
    if product_var.get() or quantity_var.get() or selling_price_var.get() or sale_date_var.get() or unit_var.get():
        has_unsaved_changes = True

product_var.trace_add("write", mark_changes)
quantity_var.trace_add("write", mark_changes)
selling_price_var.trace_add("write", mark_changes)
sale_date_var.trace_add("write", mark_changes)
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