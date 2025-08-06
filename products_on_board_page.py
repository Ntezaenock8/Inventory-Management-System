import tkinter as tk
from tkinter import messagebox, ttk
import sqlite3
from data_cache import add_product_to_cache

DB_NAME = "database.db"

# --- Database Functions ---
def save_to_database(product_name, brands, category_name, descriptions, units):
    conn = sqlite3.connect(DB_NAME)
    conn.execute("PRAGMA foreign_keys = ON;")
    cursor = conn.cursor()
    try:
        conn.execute("BEGIN TRANSACTION")
        # Insert or get category
        cursor.execute("SELECT category_id FROM categories WHERE category_name = ?", (category_name,))
        category_id = cursor.fetchone()
        if not category_id:
            cursor.execute("INSERT INTO categories (category_name) VALUES (?)", (category_name,))
            category_id = (cursor.lastrowid,)
        
        inserted_count = 0
        skipped_count = 0
        # Insert products for each brand-description-unit combination
        for brand in brands:
            # Insert or get brand
            cursor.execute("SELECT brand_id FROM brands WHERE brand_name = ?", (brand,))
            brand_id = cursor.fetchone()
            if not brand_id:
                cursor.execute("INSERT INTO brands (brand_name) VALUES (?)", (brand,))
                brand_id = (cursor.lastrowid,)
            
            for desc in descriptions:
                # Insert or get description
                cursor.execute("SELECT description_id FROM descriptions WHERE description_text = ?", (desc,))
                description_id = cursor.fetchone()
                if not description_id:
                    cursor.execute("INSERT INTO descriptions (description_text) VALUES (?)", (desc,))
                    description_id = (cursor.lastrowid,)
                
                for unit in units:
                    # Insert or get unit
                    cursor.execute("SELECT unit_id FROM units_of_measurement WHERE unit_name = ?", (unit,))
                    unit_id = cursor.fetchone()
                    if not unit_id:
                        cursor.execute("INSERT INTO units_of_measurement (unit_name) VALUES (?)", (unit,))
                        unit_id = (cursor.lastrowid,)
                    
                    # Check for existing product
                    cursor.execute("""
                        SELECT product_id FROM products
                        WHERE product_name = ? AND brand_id = ? AND category_id = ? AND description_id = ? AND unit_id = ?
                    """, (product_name, brand_id[0], category_id[0], description_id[0], unit_id[0]))
                    existing_product = cursor.fetchone()
                    
                    if not existing_product:
                        # Insert product if it doesn't exist
                        cursor.execute("""
                            INSERT INTO products (product_name, brand_id, category_id, description_id, unit_id)
                            VALUES (?, ?, ?, ?, ?)
                        """, (product_name, brand_id[0], category_id[0], description_id[0], unit_id[0]))
                        product_id = cursor.lastrowid
                        # Add to cache
                        product_display = f"{product_name} - {brand} - {desc}"
                        add_product_to_cache(product_display, product_id)
                        inserted_count += 1
                    else:
                        skipped_count += 1
        
        conn.commit()
        return inserted_count, skipped_count
    except sqlite3.Error as e:
        conn.rollback()
        print(f"Error saving to database: {e}")
        return 0, 0
    finally:
        conn.close()

# --- Main Window ---
root = tk.Tk()
root.title("Product Onboarding Form")
root.geometry("950x650")

FONT = ("Arial", 13)
ENTRY_WIDTH = 30

# --- Variables ---
product_var = tk.StringVar()
brand_var = tk.StringVar()
category_var = tk.StringVar()
desc_var = tk.StringVar()
unit_var = tk.StringVar()

# --- Form Frame ---
form = tk.Frame(root)
form.pack(pady=20)

# --- Product ---
tk.Label(form, text="Product", font=FONT).grid(row=0, column=0, sticky="e", padx=5, pady=5)
tk.Entry(form, textvariable=product_var, font=FONT, width=ENTRY_WIDTH).grid(row=0, column=1, padx=5, pady=5)

# --- Brand (Multi-entry with Listbox) ---
tk.Label(form, text="Brand", font=FONT).grid(row=1, column=0, sticky="ne", padx=5, pady=5)
brand_frame = tk.Frame(form)
brand_frame.grid(row=1, column=1, sticky="w")

brand_entry = tk.Entry(brand_frame, textvariable=brand_var, font=FONT, width=ENTRY_WIDTH - 5)
brand_entry.grid(row=0, column=0, padx=5, pady=2)

brand_listbox = tk.Listbox(brand_frame, height=4, width=40, font=("Arial", 11), selectmode=tk.SINGLE)
brand_listbox.grid(row=1, column=0, columnspan=2, pady=5)

def add_brand():
    val = brand_var.get().strip()
    if val and val not in brand_listbox.get(0, tk.END):
        brand_listbox.insert(tk.END, val)
        brand_var.set("")

def delete_brand():
    selected = brand_listbox.curselection()
    if selected:
        brand_listbox.delete(selected[0])
    else:
        messagebox.showwarning("No Selection", "Please select a brand to delete.")

tk.Button(brand_frame, text="Add Brand", font=("Arial", 11), command=add_brand).grid(row=0, column=1, padx=5)
tk.Button(brand_frame, text="Delete Brand", font=("Arial", 11), command=delete_brand).grid(row=0, column=2, padx=5)

# --- Category ---
tk.Label(form, text="Category", font=FONT).grid(row=2, column=0, sticky="e", padx=5, pady=5)
tk.Entry(form, textvariable=category_var, font=FONT, width=ENTRY_WIDTH).grid(row=2, column=1, padx=5, pady=5)

# --- Description (Multi-entry with Listbox) ---
tk.Label(form, text="Description(s)", font=FONT).grid(row=3, column=0, sticky="ne", padx=5, pady=5)
desc_frame = tk.Frame(form)
desc_frame.grid(row=3, column=1, sticky="w")

desc_entry = tk.Entry(desc_frame, textvariable=desc_var, font=FONT, width=ENTRY_WIDTH - 5)
desc_entry.grid(row=0, column=0, padx=5, pady=2)

desc_listbox = tk.Listbox(desc_frame, height=4, width=40, font=("Arial", 11), selectmode=tk.SINGLE)
desc_listbox.grid(row=1, column=0, columnspan=2, pady=5)

def add_description():
    val = desc_var.get().strip()
    if val and val not in desc_listbox.get(0, tk.END):
        desc_listbox.insert(tk.END, val)
        desc_var.set("")

def delete_description():
    selected = desc_listbox.curselection()
    if selected:
        desc_listbox.delete(selected[0])
    else:
        messagebox.showwarning("No Selection", "Please select a description to delete.")

tk.Button(desc_frame, text="Add Description", font=("Arial", 11), command=add_description).grid(row=0, column=1, padx=5)
tk.Button(desc_frame, text="Delete Description", font=("Arial", 11), command=delete_description).grid(row=0, column=2, padx=5)

# --- Unit of Measurement (Multi-entry with Listbox) ---
tk.Label(form, text="Unit(s) of Measurement", font=FONT).grid(row=4, column=0, sticky="ne", padx=5, pady=5)
unit_frame = tk.Frame(form)
unit_frame.grid(row=4, column=1, sticky="w")

unit_entry = tk.Entry(unit_frame, textvariable=unit_var, font=FONT, width=ENTRY_WIDTH - 5)
unit_entry.grid(row=0, column=0, padx=5, pady=2)

unit_listbox = tk.Listbox(unit_frame, height=4, width=40, font=("Arial", 11), selectmode=tk.SINGLE)
unit_listbox.grid(row=1, column=0, columnspan=2, pady=5)

def add_unit():
    val = unit_var.get().strip()
    if val and val not in unit_listbox.get(0, tk.END):
        unit_listbox.insert(tk.END, val)
        unit_var.set("")

def delete_unit():
    selected = unit_listbox.curselection()
    if selected:
        unit_listbox.delete(selected[0])
    else:
        messagebox.showwarning("No Selection", "Please select a unit to delete.")

tk.Button(unit_frame, text="Add Unit", font=("Arial", 11), command=add_unit).grid(row=0, column=1, padx=5)
tk.Button(unit_frame, text="Delete Unit", font=("Arial", 11), command=delete_unit).grid(row=0, column=2, padx=5)

# --- Save Functionality ---
def save_data():
    # Check and add any unadded entries in the entry fields to their respective Listboxes
    if brand_var.get().strip():
        add_brand()
    if desc_var.get().strip():
        add_description()
    if unit_var.get().strip():
        add_unit()

    product = product_var.get().strip()
    category = category_var.get().strip()
    brands = list(brand_listbox.get(0, tk.END))
    descriptions = list(desc_listbox.get(0, tk.END))
    units = list(unit_listbox.get(0, tk.END))

    if not product or not category or not brands or not descriptions or not units:
        messagebox.showerror("Missing Data", "All fields (Product, Category, at least one Brand, Description, and Unit) are required.")
        return

    inserted_count, skipped_count = save_to_database(product, brands, category, descriptions, units)
    if inserted_count > 0 or skipped_count > 0:
        message = f"Successfully saved {inserted_count} entries."
        if skipped_count > 0:
            message += f" Skipped {skipped_count} duplicate product(s)."
        messagebox.showinfo("Success", message)
        clear_form()
    else:
        messagebox.showerror("Error", "Failed to save data to the database.")

def clear_form():
    product_var.set("")
    brand_var.set("")
    category_var.set("")
    desc_var.set("")
    unit_var.set("")
    brand_listbox.delete(0, tk.END)
    desc_listbox.delete(0, tk.END)
    unit_listbox.delete(0, tk.END)

# --- Prevent Exit Without Saving ---
def on_closing():
    # Check and add any unadded entries in the entry fields to their respective Listboxes
    if brand_var.get().strip():
        add_brand()
    if desc_var.get().strip():
        add_description()
    if unit_var.get().strip():
        add_unit()

    if (product_var.get().strip() or category_var.get().strip() or 
        brand_listbox.get(0, tk.END) or desc_listbox.get(0, tk.END) or
        unit_listbox.get(0, tk.END)):
        if messagebox.askyesno("Unsaved Changes", "You have unsaved changes. Do you want to save before exiting?"):
            save_data()
        else:
            root.destroy()
    else:
        root.destroy()

root.protocol("WM_DELETE_WINDOW", on_closing)

# --- Save Button ---
tk.Button(root, text="Save Entries", font=("Arial", 14), command=save_data, bg="#28a745", fg="white", width=20).pack(pady=20)

# --- Run Application ---
if __name__ == "__main__":
    root.mainloop()