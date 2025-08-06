import tkinter as tk
from tkinter import ttk, font, messagebox
import sqlite3
from datetime import datetime
import locale

# Set locale for currency formatting
locale.setlocale(locale.LC_ALL, '')

DB_NAME = "database.db"

# --- Static Category-to-Expense Mapping ---
CATEGORY_EXPENSE_MAP = {
    "Staff & Employee Costs": [
        "Salaries & Wages",
        "NSSF Contributions (Employer portion)",
        "Staff Welfare (e.g., lunch allowance)",
        "Casual Labor Payments (e.g., offloading trucks)",
        "Staff Training & Development",
        "Medical Allowances / Insurance"
    ],
    "Store & Operational Costs": [
        "Shop/Store Rent",
        "Security Services (Askari)",
        "Bank Transaction Fees",
        "Stationery & Office Supplies",
        "Packaging Materials (e.g., boxes, bags)",
        "Cleaning Supplies & Services"
    ],
    "Utilities": [
        "Electricity",
        "Water (NWSC)",
        "Internet Subscription",
        "Airtime & Mobile Data Bundles",
        "Waste Disposal/Garbage Collection Fees"
    ],
    "Taxes & Licensing": [
        "Trading License (KCCA or Local Council)",
        "URA - VAT Payments",
        "URA - Income Tax/Presumptive Tax",
        "Property Rates",
        "Company Registration & Renewal Fees"
    ],
    "Transport & Logistics": [
        "Fuel for Delivery Vehicle/Motorcycle",
        "Boda Boda Delivery Fees",
        "Vehicle Maintenance & Repairs",
        "Vehicle Insurance & Licensing",
        "Parking Fees"
    ],
    "Maintenance & Repairs": [
        "Store Repairs & Maintenance",
        "Equipment Repairs",
        "Generator Fuel & Maintenance",
        "IT Support & Software Costs"
    ],
    "Marketing & Sales": [
        "Advertising",
        "Signage & Branding",
        "Social Media Promotion",
        "Customer Refreshments"
    ],
    "Professional Fees": [
        "Accounting & Bookkeeping Fees",
        "Legal & Consultation Fees",
        "Insurance Premiums"
    ],
    "Other": [
        "Donations & Sponsorships",
        "Bank Loan Interest",
        "Losses due to Damage or Theft",
        "Miscellaneous Supplies"
    ]
}

# --- Session Data ---
session_expenses = []  # List to store (expense_id, category_name, predefined_expense, description, amount, expense_date) for current session

# --- Helper Functions ---
def save_expense(expense_id, category_name, predefined_expense, description, amount, expense_date):
    """Save or update expense data in expenses table."""
    conn = sqlite3.connect(DB_NAME, timeout=10)
    conn.execute("PRAGMA foreign_keys = ON;")
    cursor = conn.cursor()
    try:
        conn.execute("BEGIN TRANSACTION")
        # Get or insert category_id
        cursor.execute("SELECT expense_category_id FROM expense_categories WHERE category_name = ?", (category_name,))
        category_id = cursor.fetchone()
        if not category_id:
            cursor.execute("INSERT INTO expense_categories (category_name) VALUES (?)", (category_name,))
            category_id = cursor.lastrowid
        else:
            category_id = category_id[0]
        
        if expense_id:  # Update existing expense
            cursor.execute("""
                UPDATE expenses
                SET expense_category_id = ?, predefined_expense = ?, description = ?, amount = ?, expense_date = ?
                WHERE expense_id = ?
            """, (category_id, predefined_expense or None, description or None, amount, expense_date, expense_id))
        else:  # Insert new expense
            cursor.execute("""
                INSERT INTO expenses (expense_category_id, predefined_expense, description, amount, expense_date)
                VALUES (?, ?, ?, ?, ?)
            """, (category_id, predefined_expense or None, description or None, amount, expense_date))
            expense_id = cursor.lastrowid
        
        conn.commit()
        return expense_id
    except sqlite3.OperationalError as e:
        conn.rollback()
        print(f"Database Error (save_expense): {e}")  # Debug log
        messagebox.showerror("Database Error", f"Error saving expense: {e}")
        return None
    except sqlite3.Error as e:
        conn.rollback()
        print(f"Database Error (save_expense): {e}")  # Debug log
        messagebox.showerror("Database Error", f"Error saving expense: {e}")
        return None
    finally:
        conn.close()

def delete_expense(expense_id):
    """Delete an expense from the database."""
    conn = sqlite3.connect(DB_NAME, timeout=10)
    conn.execute("PRAGMA foreign_keys = ON;")
    cursor = conn.cursor()
    try:
        conn.execute("BEGIN TRANSACTION")
        cursor.execute("DELETE FROM expenses WHERE expense_id = ?", (expense_id,))
        conn.commit()
        return True
    except sqlite3.OperationalError as e:
        conn.rollback()
        print(f"Database Error (delete_expense): {e}")  # Debug log
        messagebox.showerror("Database Error", f"Error deleting expense: {e}")
        return False
    except sqlite3.Error as e:
        conn.rollback()
        print(f"Database Error (delete_expense): {e}")  # Debug log
        messagebox.showerror("Database Error", f"Error deleting expense: {e}")
        return False
    finally:
        conn.close()

def edit_selected():
    global has_unsaved_changes
    selected = tree.selection()
    if not selected:
        return
    values = tree.item(selected[0])['values']
    expense_id_var.set(values[0])    # expense_id
    category_var.set(values[1])      # category_name
    update_expense_options()         # Update expense Combobox
    expense_var.set(values[2])       # predefined_expense
    description_var.set(values[3])   # description
    amount_var.set(str(values[4]).replace(',', ''))  # amount, remove commas for editing
    expense_date_var.set(values[5])  # expense_date
    has_unsaved_changes = False

def delete_selected():
    global has_unsaved_changes
    selected = tree.selection()
    if not selected:
        return
    values = tree.item(selected[0])['values']
    expense_id = values[0]  # expense_id
    if delete_expense(expense_id):
        global session_expenses
        session_expenses = [exp for exp in session_expenses if exp[0] != expense_id]
        refresh_tree()
        clear_form()
        has_unsaved_changes = False

def save_data():
    global has_unsaved_changes
    global session_expenses
    # Validate inputs
    category_name = category_var.get().strip()
    if not category_name:
        messagebox.showerror("Missing Data", "Please select or enter a category.")
        return
    
    predefined_expense = expense_var.get().strip()
    if not predefined_expense:
        messagebox.showerror("Missing Data", "Please select or enter an expense.")
        return
    
    description = description_var.get().strip()
    # Allow empty description (nullable in database)
    
    amount = amount_var.get().strip().replace(',', '')
    try:
        amount = float(amount)
        if amount <= 0:
            raise ValueError
    except ValueError:
        messagebox.showerror("Invalid Amount", "Amount must be a positive number.")
        return
    
    expense_date = expense_date_var.get().strip()
    try:
        datetime.strptime(expense_date, "%Y-%m-%d")
    except ValueError:
        messagebox.showerror("Invalid Date", "Expense date must be in YYYY-MM-DD format (e.g., 2025-08-05).")
        return
    
    # Save or update expense in database
    expense_id = expense_id_var.get()
    new_expense_id = save_expense(expense_id, category_name, predefined_expense, description, amount, expense_date)
    if new_expense_id:
        if expense_id:  # Update existing in session_expenses
            session_expenses = [exp for exp in session_expenses if exp[0] != int(expense_id)]
        # Append to session_expenses
        session_expenses.append((new_expense_id, category_name, predefined_expense, description, amount, expense_date))
        refresh_tree()
        clear_form()
        has_unsaved_changes = False

def clear_form():
    expense_id_var.set("")
    category_var.set("")
    expense_var.set("")
    description_var.set("")
    amount_var.set("")
    expense_date_var.set(datetime.now().strftime("%Y-%m-%d"))  # Default to current date
    category_combo['values'] = list(CATEGORY_EXPENSE_MAP.keys())  # Reset Combobox
    expense_combo['values'] = []  # Clear expense options
    global has_unsaved_changes
    has_unsaved_changes = False

# --- UI Setup ---
root = tk.Tk()
root.title("Expenses Recording Module")
root.geometry("800x600")

# Define fonts
custom_font = font.Font(family="TkDefaultFont", size=13)
combo_font = font.Font(family="TkDefaultFont", size=12)

# --- Form Frame ---
form = tk.Frame(root)
form.pack(pady=10)

# Variables
expense_id_var = tk.StringVar()  # For expense_id
category_var = tk.StringVar()    # For category_name
expense_var = tk.StringVar()     # For predefined_expense
description_var = tk.StringVar() # For user-entered notes
amount_var = tk.StringVar()
expense_date_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))  # Default to current date

# Category Combobox
tk.Label(form, text="Category", font=custom_font).grid(row=0, column=0, sticky="e", padx=5, pady=5)
category_combo = ttk.Combobox(form, textvariable=category_var, font=combo_font, width=50)
category_combo.grid(row=0, column=1, sticky="w", padx=5, pady=5)
category_combo['values'] = list(CATEGORY_EXPENSE_MAP.keys())

# Update expense options based on category
def update_expense_options(*args):
    """Update Expense Combobox based on selected category."""
    category = category_var.get().strip()
    expense_combo['values'] = CATEGORY_EXPENSE_MAP.get(category, [])
    expense_var.set("")

category_var.trace_add("write", update_expense_options)

# Expense Combobox
tk.Label(form, text="Expense", font=custom_font).grid(row=1, column=0, sticky="e", padx=5, pady=5)
expense_combo = ttk.Combobox(form, textvariable=expense_var, font=combo_font, width=50)
expense_combo.grid(row=1, column=1, sticky="w", padx=5, pady=5)
expense_combo['values'] = []

# Description Entry
tk.Label(form, text="Description", font=custom_font).grid(row=2, column=0, sticky="e", padx=5, pady=5)
tk.Entry(form, textvariable=description_var, font=custom_font, width=50).grid(row=2, column=1, sticky="w", padx=5, pady=5)

# Amount
tk.Label(form, text="Amount (UGX)", font=custom_font).grid(row=3, column=0, sticky="e", padx=5, pady=5)
tk.Entry(form, textvariable=amount_var, font=custom_font, width=20).grid(row=3, column=1, sticky="w", padx=5, pady=5)

# Expense Date
tk.Label(form, text="Expense Date (YYYY-MM-DD)", font=custom_font).grid(row=4, column=0, sticky="e", padx=5, pady=5)
tk.Entry(form, textvariable=expense_date_var, font=custom_font, width=20).grid(row=4, column=1, sticky="w", padx=5, pady=5)
tk.Label(form, text="e.g., 2025-08-05", font=custom_font, fg="gray50").grid(row=4, column=2, sticky="w", padx=5, pady=5)

# --- Save Button Frame ---
save_btn_frame = tk.Frame(root)
save_btn_frame.pack(pady=5)
tk.Button(save_btn_frame, text="Save Expense", font=custom_font, command=save_data, bg="#28a745", fg="white", width=15).pack()

# --- Treeview for Preview ---
tree_frame = tk.Frame(root)
tree_frame.pack(fill="both", expand=True, padx=10, pady=10)

columns = ("expense_id", "category", "expense", "description", "amount", "expense_date")
style = ttk.Style()
style.theme_use('clam')  # Use 'clam' theme for consistency and styling support
style.configure("Treeview", font=custom_font)
style.configure("Treeview.Heading", font=(custom_font.cget("family"), custom_font.cget("size"), "bold"))

tree = ttk.Treeview(tree_frame, columns=columns, show="headings", style="Treeview")
tree.heading("expense_id", text="ID")
tree.heading("category", text="Category")
tree.heading("expense", text="Expense")
tree.heading("description", text="Description")
tree.heading("amount", text="Amount (UGX)")
tree.heading("expense_date", text="Expense Date")
tree.column("expense_id", width=80, anchor="center")
tree.column("category", width=150, anchor="w")
tree.column("expense", width=200, anchor="w")
tree.column("description", width=200, anchor="w")
tree.column("amount", width=120, anchor="center")
tree.column("expense_date", width=120, anchor="center")

# Add vertical scrollbar
scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
tree.configure(yscrollcommand=scrollbar.set)
tree.grid(row=0, column=0, sticky="nsew")
scrollbar.grid(row=0, column=1, sticky="ns")
tree_frame.grid_rowconfigure(0, weight=1)
tree_frame.grid_columnconfigure(0, weight=1)

# --- Edit/Delete Button Frame ---
edit_delete_btn_frame = tk.Frame(root)
edit_delete_btn_frame.pack(pady=5)
tk.Button(edit_delete_btn_frame, text="Edit", font=custom_font, command=edit_selected, width=15).pack(side=tk.LEFT, padx=5)
tk.Button(edit_delete_btn_frame, text="Delete", font=custom_font, command=delete_selected, width=15).pack(side=tk.LEFT, padx=5)

# --- Populate Treeview ---
def refresh_tree():
    for row in tree.get_children():
        tree.delete(row)
    for row in session_expenses:
        # Format amount with commas for display
        formatted_amount = locale.format_string("%.2f", row[4], grouping=True)
        tree.insert("", "end", values=(row[0], row[1], row[2], row[3], formatted_amount, row[5]))

refresh_tree()

# --- Track Changes ---
has_unsaved_changes = False

def mark_changes(*args):
    global has_unsaved_changes
    if category_var.get() or expense_var.get() or description_var.get() or amount_var.get() or expense_date_var.get():
        has_unsaved_changes = True

category_var.trace_add("write", mark_changes)
expense_var.trace_add("write", mark_changes)
description_var.trace_add("write", mark_changes)
amount_var.trace_add("write", mark_changes)
expense_date_var.trace_add("write", mark_changes)

# --- Prevent Exit Without Saving and Clear Session ---
def on_closing():
    global has_unsaved_changes
    global session_expenses
    if has_unsaved_changes:
        if messagebox.askyesno("Unsaved Changes", "You have unsaved changes. Do you want to save before exiting?"):
            save_data()
    session_expenses = []  # Clear session data
    root.destroy()

root.protocol("WM_DELETE_WINDOW", on_closing)

# --- Run Application ---
if __name__ == "__main__":
    root.mainloop()