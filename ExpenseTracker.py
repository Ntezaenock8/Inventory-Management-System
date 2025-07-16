import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

root = tk.Tk()
root.title("Expense Tracker")
root.geometry("800x600")

# Styling
style = ttk.Style()
style.theme_use("default")
style.configure("Treeview.Heading", font=("Arial", 11, "bold"), background="#f0f0f0", relief="groove")
style.configure("Treeview", font=("Arial", 10), rowheight=28)

# ---------------- Form Frame ----------------
form_frame = tk.Frame(root)
form_frame.pack(pady=10)

# Date (auto-filled)
tk.Label(form_frame, text="Date:", font=("Arial", 10)).grid(row=0, column=0, padx=5, pady=5)
date_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
date_entry = tk.Entry(form_frame, textvariable=date_var, font=("Arial", 10), state='readonly', width=15)
date_entry.grid(row=0, column=1, padx=5, pady=5)

# Category (ComboBox + manual entry)
tk.Label(form_frame, text="Category:", font=("Arial", 10)).grid(row=0, column=2, padx=5, pady=5)
category_var = tk.StringVar()
category_combo = ttk.Combobox(form_frame, textvariable=category_var, width=20)
category_combo['values'] = ["Transport", "Utilities", "Wages", "Maintenance","Rent", "Other"]
category_combo.grid(row=0, column=3, padx=5, pady=5)

# Description
tk.Label(form_frame, text="Description:", font=("Arial", 10)).grid(row=1, column=0, padx=5, pady=5)
description_var = tk.StringVar()
description_entry = tk.Entry(form_frame, textvariable=description_var, font=("Arial", 10), width=30)
description_entry.grid(row=1, column=1, columnspan=3, padx=5, pady=5)

# Amount (only numbers)
tk.Label(form_frame, text="Amount:", font=("Arial", 10)).grid(row=2, column=0, padx=5, pady=5)
amount_var = tk.StringVar()
amount_entry = tk.Entry(form_frame, textvariable=amount_var, font=("Arial", 10), width=15)
amount_entry.grid(row=2, column=1, padx=5, pady=5)

# ---------------- Treeview ----------------
columns = ("date", "category", "description", "amount")
tree = ttk.Treeview(root, columns=columns, show="headings", selectmode="browse")
tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

for col in columns:
    tree.heading(col, text=col.title())
    tree.column(col, anchor="w", width=180)

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
    category_var.set("")
    description_var.set("")
    amount_var.set("")

def add_row():
    date = date_var.get()
    category = category_var.get()
    description = description_var.get()
    amount = amount_var.get()

    if not category or not description or not amount:
        messagebox.showerror("Input Error", "Please fill in all fields.")
        return
    if not is_number(amount):
        messagebox.showerror("Input Error", "Amount must be a number.")
        return

    tree.insert("", "end", values=(date, category, description, amount))
    clear_form()

def edit_row():
    selected = tree.selection()
    if not selected:
        return
    item = tree.item(selected[0])
    values = item["values"]
    if values:
        date_var.set(values[0])
        category_var.set(values[1])
        description_var.set(values[2])
        amount_var.set(values[3])
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
