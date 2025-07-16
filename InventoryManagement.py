import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

root = tk.Tk()
root.title("Inventory Management")
root.geometry("900x600")

# Style
style = ttk.Style()
style.theme_use("default")
style.configure("Treeview.Heading", font=("Arial", 11, "bold"), background="#f0f0f0", relief="groove")
style.configure("Treeview", font=("Arial", 10), rowheight=28)

# ---------------- Form Frame ----------------
form_frame = tk.Frame(root)
form_frame.pack(pady=10)

# Date (auto-generated)
tk.Label(form_frame, text="Date:", font=("Arial", 10)).grid(row=0, column=0, padx=5, pady=5)
date_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
tk.Entry(form_frame, textvariable=date_var, font=("Arial", 10), state='readonly', width=15).grid(row=0, column=1, padx=5, pady=5)

# Item (Product Name)
tk.Label(form_frame, text="Item:", font=("Arial", 10)).grid(row=0, column=2, padx=5, pady=5)
item_var = tk.StringVar()
item_combo = ttk.Combobox(form_frame, textvariable=item_var, width=20)
item_combo['values'] = ["Cement", "Paint", "Iron Sheets", "Bricks", "Sand"]
item_combo.grid(row=0, column=3, padx=5, pady=5)

# Description / Brand
tk.Label(form_frame, text="Description/Brand:", font=("Arial", 10)).grid(row=1, column=0, padx=5, pady=5)
brand_var = tk.StringVar()
brand_combo = ttk.Combobox(form_frame, textvariable=brand_var, width=20)
brand_combo['values'] = ["Sadolin", "Tororo", "Roofings", "Hima", "Nyumba"]
brand_combo.grid(row=1, column=1, padx=5, pady=5)

# Quantity
tk.Label(form_frame, text="Quantity:", font=("Arial", 10)).grid(row=1, column=2, padx=5, pady=5)
quantity_var = tk.StringVar()
tk.Entry(form_frame, textvariable=quantity_var, font=("Arial", 10), width=10).grid(row=1, column=3, padx=5, pady=5)

# Price
tk.Label(form_frame, text="Price per Unit:", font=("Arial", 10)).grid(row=2, column=0, padx=5, pady=5)
price_var = tk.StringVar()
tk.Entry(form_frame, textvariable=price_var, font=("Arial", 10), width=15).grid(row=2, column=1, padx=5, pady=5)

# ---------------- Treeview ----------------
columns = ("date", "item", "description", "quantity", "price", "total")
tree = ttk.Treeview(root, columns=columns, show="headings", selectmode="browse")
tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

for col in columns:
    tree.heading(col, text=col.title())
    tree.column(col, anchor="w", width=140)

scrollbar = ttk.Scrollbar(root, orient="vertical", command=tree.yview)
tree.configure(yscrollcommand=scrollbar.set)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

# ---------------- Functions ----------------
def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

def clear_form():
    date_var.set(datetime.now().strftime("%Y-%m-%d"))
    item_var.set("")
    brand_var.set("")
    quantity_var.set("")
    price_var.set("")

def add_row():
    date = date_var.get()
    item = item_var.get()
    brand = brand_var.get()
    quantity = quantity_var.get()
    price = price_var.get()

    if not item or not brand or not quantity or not price:
        messagebox.showerror("Input Error", "Please fill in all fields.")
        return
    if not is_number(quantity) or not is_number(price):
        messagebox.showerror("Input Error", "Quantity and Price must be numbers.")
        return

    total = round(float(quantity) * float(price), 2)
    tree.insert("", "end", values=(date, item, brand, quantity, price, total))
    clear_form()

def edit_row():
    selected = tree.selection()
    if not selected:
        return
    item = tree.item(selected[0])["values"]
    if item:
        date_var.set(item[0])
        item_var.set(item[1])
        brand_var.set(item[2])
        quantity_var.set(item[3])
        price_var.set(item[4])
        tree.delete(selected[0])

def delete_row():
    selected = tree.selection()
    if not selected:
        return
    tree.delete(selected[0])
    clear_form()

# ---------------- Buttons ----------------
btn_frame = tk.Frame(root)
btn_frame.pack(pady=10)

tk.Button(btn_frame, text="Add", command=add_row, width=15).pack(side=tk.LEFT, padx=5)
tk.Button(btn_frame, text="Edit", command=edit_row, width=15).pack(side=tk.LEFT, padx=5)
tk.Button(btn_frame, text="Delete", command=delete_row, width=15).pack(side=tk.LEFT, padx=5)

root.mainloop()
