import tkinter as tk
from tkinter import ttk, font, messagebox
import sqlite3

DB_NAME = "database.db"

# --- Helper Functions ---
def get_joined_data():
    conn = sqlite3.connect(DB_NAME)
    conn.execute("PRAGMA foreign_keys = ON;")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT p.product_name, b.brand_name, c.category_name, d.description_text, p.product_id
        FROM products p
        JOIN brands b ON p.brand_id = b.brand_id
        JOIN categories c ON p.category_id = c.category_id
        JOIN descriptions d ON p.description_id = d.description_id
    """)
    rows = cursor.fetchall()
    conn.close()
    return rows

def update_product(product_id, product_name, brand_name, category_name, description_text):
    conn = sqlite3.connect(DB_NAME)
    conn.execute("PRAGMA foreign_keys = ON;")
    cursor = conn.cursor()
    try:
        # Get or create brand
        cursor.execute("SELECT brand_id FROM brands WHERE brand_name = ?", (brand_name,))
        brand_id = cursor.fetchone()
        if not brand_id:
            cursor.execute("INSERT INTO brands (brand_name) VALUES (?)", (brand_name,))
            brand_id = (cursor.lastrowid,)
        
        # Get or create category
        cursor.execute("SELECT category_id FROM categories WHERE category_name = ?", (category_name,))
        category_id = cursor.fetchone()
        if not category_id:
            cursor.execute("INSERT INTO categories (category_name) VALUES (?)", (category_name,))
            category_id = (cursor.lastrowid,)
        
        # Get or create description
        cursor.execute("SELECT description_id FROM descriptions WHERE description_text = ?", (description_text,))
        description_id = cursor.fetchone()
        if not description_id:
            cursor.execute("INSERT INTO descriptions (description_text) VALUES (?)", (description_text,))
            description_id = (cursor.lastrowid,)
        
        # Update product
        cursor.execute("""
            UPDATE products
            SET product_name = ?, brand_id = ?, category_id = ?, description_id = ?
            WHERE product_id = ?
        """, (product_name, brand_id[0], category_id[0], description_id[0], product_id))
        
        conn.commit()
    except sqlite3.Error as e:
        print(f"Error updating product: {e}")
    finally:
        conn.close()

def delete_product(product_id):
    conn = sqlite3.connect(DB_NAME)
    conn.execute("PRAGMA foreign_keys = ON;")
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM products WHERE product_id = ?", (product_id,))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Error deleting product: {e}")
    finally:
        conn.close()

# --- UI Setup ---
root = tk.Tk()
root.title("Product Manager")
root.geometry("800x600")

# Define custom font with 30% larger size (base 10pt -> 13pt)
custom_font = font.Font(family="TkDefaultFont", size=13)

# Treeview with Scrollbar
columns = ("product", "brand", "category", "description")
style = ttk.Style()
style.configure("Treeview", font=custom_font)
style.configure("Treeview.Heading", font=custom_font)

# Create a frame for the Treeview and Scrollbar
tree_frame = tk.Frame(root)
tree_frame.pack(fill="both", expand=True, padx=10, pady=10)

tree = ttk.Treeview(tree_frame, columns=columns, show="headings", style="Treeview")
tree.heading("product", text="Product")
tree.heading("brand", text="Brand")
tree.heading("category", text="Category")
tree.heading("description", text="Description")
for col in columns:
    tree.column(col, width=180)

# Add vertical scrollbar
scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
tree.configure(yscrollcommand=scrollbar.set)
tree.grid(row=0, column=0, sticky="nsew")
scrollbar.grid(row=0, column=1, sticky="ns")
tree_frame.grid_rowconfigure(0, weight=1)
tree_frame.grid_columnconfigure(0, weight=1)

# --- Populate Treeview ---
def refresh_tree():
    for row in tree.get_children():
        tree.delete(row)
    for row in get_joined_data():
        # Insert only the first 4 columns (product_name, brand_name, category_name, description_text)
        tree.insert("", "end", values=row[:4])

refresh_tree()

# --- Track Changes ---
has_unsaved_changes = False

def mark_changes(*args):
    global has_unsaved_changes
    if product_id.get():  # Only mark changes if a product is being edited
        has_unsaved_changes = True

# --- Edit/Save/Delete Functions ---
def edit_selected():
    global has_unsaved_changes
    selected = tree.selection()
    if not selected:
        return
    values = tree.item(selected[0])['values']
    # Fetch product_id from the database (not displayed in Treeview)
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT p.product_id
        FROM products p
        JOIN brands b ON p.brand_id = b.brand_id
        JOIN categories c ON p.category_id = c.category_id
        JOIN descriptions d ON p.description_id = d.description_id
        WHERE p.product_name = ? AND b.brand_name = ? AND c.category_name = ? AND d.description_text = ?
    """, values)
    product_id_val = cursor.fetchone()
    conn.close()
    if product_id_val:
        product_id.set(product_id_val[0])
        product_var.set(values[0])
        brand_var.set(values[1])
        category_var.set(values[2])
        description_var.set(values[3])
        has_unsaved_changes = False  # Reset initially, changes will be marked on field modification

def delete_selected():
    global has_unsaved_changes
    selected = tree.selection()
    if not selected:
        return
    values = tree.item(selected[0])['values']
    # Fetch product_id for deletion
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT p.product_id
        FROM products p
        JOIN brands b ON p.brand_id = b.brand_id
        JOIN categories c ON p.category_id = c.category_id
        JOIN descriptions d ON p.description_id = d.description_id
        WHERE p.product_name = ? AND b.brand_name = ? AND c.category_name = ? AND d.description_text = ?
    """, values)
    product_id_val = cursor.fetchone()
    conn.close()
    if product_id_val:
        delete_product(product_id_val[0])
        refresh_tree()
        clear_fields()
        has_unsaved_changes = False  # Reset changes after deletion (since deletion is committed)

def save_changes():
    global has_unsaved_changes
    pid = product_id.get()
    if not pid:
        return
    update_product(pid, product_var.get(), brand_var.get(), category_var.get(), description_var.get())
    refresh_tree()
    clear_fields()
    has_unsaved_changes = False  # Reset changes after saving
    messagebox.showinfo("Success", "Changes saved successfully!")

def clear_fields():
    product_id.set("")
    product_var.set("")
    brand_var.set("")
    category_var.set("")
    description_var.set("")
    global has_unsaved_changes
    has_unsaved_changes = False  # Reset changes when clearing fields

# --- Prevent Exit Without Saving ---
def on_closing():
    global has_unsaved_changes
    if has_unsaved_changes:
        if messagebox.askyesno("Unsaved Changes", "You have unsaved changes. Do you want to save before exiting?"):
            save_changes()
            root.destroy()  # Exit after saving
        else:
            root.destroy()  # Exit without saving
    else:
        root.destroy()

root.protocol("WM_DELETE_WINDOW", on_closing)

# --- Form Fields ---
form = tk.Frame(root)
form.pack(pady=10)

product_id = tk.StringVar()  # Hidden, used to track product_id
product_var = tk.StringVar()
brand_var = tk.StringVar()
category_var = tk.StringVar()
description_var = tk.StringVar()

# Bind variable changes to mark_changes
product_var.trace_add("write", mark_changes)
brand_var.trace_add("write", mark_changes)
category_var.trace_add("write", mark_changes)
description_var.trace_add("write", mark_changes)

tk.Label(form, text="Product", font=custom_font).grid(row=0, column=0, padx=5, pady=5)
tk.Entry(form, textvariable=product_var, font=custom_font).grid(row=0, column=1, padx=5, pady=5)

tk.Label(form, text="Brand", font=custom_font).grid(row=0, column=2, padx=5, pady=5)
tk.Entry(form, textvariable=brand_var, font=custom_font).grid(row=0, column=3, padx=5, pady=5)

tk.Label(form, text="Category", font=custom_font).grid(row=1, column=0, padx=5, pady=5)
tk.Entry(form, textvariable=category_var, font=custom_font).grid(row=1, column=1, padx=5, pady=5)

tk.Label(form, text="Description", font=custom_font).grid(row=1, column=2, padx=5, pady=5)
tk.Entry(form, textvariable=description_var, font=custom_font).grid(row=1, column=3, padx=5, pady=5)

# --- Buttons ---
btn_frame = tk.Frame(root)
btn_frame.pack(pady=10)

tk.Button(btn_frame, text="Edit", command=edit_selected, width=10, font=custom_font).pack(side=tk.LEFT, padx=5)
tk.Button(btn_frame, text="Delete", command=delete_selected, width=10, font=custom_font).pack(side=tk.LEFT, padx=5)
tk.Button(btn_frame, text="Save", command=save_changes, width=10, font=custom_font).pack(side=tk.LEFT, padx=5)

# --- Run Application ---
if __name__ == "__main__":
    root.mainloop()