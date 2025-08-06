import tkinter as tk
from tkinter import ttk, font
import sqlite3

DB_NAME = "database.db"

# --- Static Category-to-Expense Mapping ---
CATEGORY_EXPENSE_MAP = {
    "Staff & Employee Costs": [
        "Salaries & Wages",
        "NSSF Contributions (Employer portion)",
        "Staff Welfare (e.g., lunch, tea allowance)",
        "Casual Labor Payments (e.g., for offloading trucks)",
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
        "Electricity (Umeme)",
        "Water (NWSC)",
        "Internet Subscription",
        "Airtime & Mobile Data Bundles",
        "Waste Disposal / Garbage Collection Fees"
    ],
    "Taxes & Licensing": [
        "Trading License (KCCA or Local Council)",
        "URA - VAT Payments",
        "URA - Income Tax / Presumptive Tax",
        "Property Rates",
        "Company Registration & Renewal Fees (URSB)"
    ],
    "Transport & Logistics": [
        "Fuel for Delivery Vehicle/Motorcycle",
        "Boda Boda Delivery Fees",
        "Vehicle Maintenance & Repairs",
        "Vehicle Insurance & Licensing",
        "Parking Fees"
    ],
    "Maintenance & Repairs": [
        "Store Repairs & Maintenance (e.g., painting, fixing shelves)",
        "Equipment Repairs (e.g., cutting machine)",
        "Generator Fuel & Maintenance",
        "IT Support & Software Costs"
    ],
    "Marketing & Sales": [
        "Advertising (e.g., radio, newspaper, flyers)",
        "Signage & Branding",
        "Social Media Promotion",
        "Customer Refreshments"
    ],
    "Professional Fees": [
        "Accounting & Bookkeeping Fees",
        "Legal & Consultation Fees",
        "Insurance Premiums (e.g., fire, theft)"
    ],
    "Other": [
        "Donations & Sponsorships",
        "Bank Loan Interest",
        "Losses due to Damage or Theft",
        "Miscellaneous Supplies"
    ]
}

# --- Helper Function ---
def fetch_expenses():
    """Fetch all expenses from database for Treeview display."""
    conn = sqlite3.connect(DB_NAME, timeout=10)
    conn.execute("PRAGMA foreign_keys = ON;")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT e.expense_id, ec.category_name, e.predefined_expense, e.description, e.amount, e.expense_date
        FROM expenses e
        JOIN expense_categories ec ON e.expense_category_id = ec.expense_category_id
    """)
    rows = cursor.fetchall()
    conn.close()
    return rows

# --- UI Setup ---
root = tk.Tk()
root.title("Expenses History")
root.geometry("800x600")

# Define font
custom_font = font.Font(family="TkDefaultFont", size=13)

# --- Treeview for History ---
tree_frame = tk.Frame(root)
tree_frame.pack(fill="both", expand=True, padx=10, pady=10)

columns = ("expense_id", "category", "expense", "description", "amount", "expense_date")
style = ttk.Style()
style.theme_use('clam')  # Use 'clam' theme to ensure background color support
style.configure("Treeview", font=custom_font)
style.configure("Treeview.Heading", font=(custom_font.cget("family"), custom_font.cget("size"), "bold"))

tree = ttk.Treeview(tree_frame, columns=columns, show="headings", style="Treeview")
tree.heading("expense_id", text="ID")
tree.heading("category", text="Category")
tree.heading("expense", text="Expense")
tree.heading("description", text="Description")
tree.heading("amount", text="Amount (UGX)")
tree.heading("expense_date", text="Date")

# Dynamically set column widths based on content
def set_column_widths():
    expenses = fetch_expenses()
    max_category_width = max([custom_font.measure(category) for category in CATEGORY_EXPENSE_MAP.keys()] + [custom_font.measure("Category")])
    max_expense_width = max([custom_font.measure(desc) for cat in CATEGORY_EXPENSE_MAP.values() for desc in cat] + [custom_font.measure("Expense")] + [custom_font.measure("Custom")])
    max_description_width = max([custom_font.measure(row[3] or "") for row in expenses] + [custom_font.measure("Description")] + [custom_font.measure("Paid to Sarah as Monthly Salary")]) if expenses else custom_font.measure("Paid to Sarah as Monthly Salary")
    max_amount_width = max([custom_font.measure(str(row[4])) for row in expenses] + [custom_font.measure("Amount (UGX)")]) if expenses else custom_font.measure("Amount (UGX)")
    tree.column("expense_id", width=custom_font.measure("ID") + 20)
    tree.column("category", width=max_category_width + 20)
    tree.column("expense", width=int(max_expense_width * 0.9) + 20)  # Reduced by ~10%
    tree.column("description", width=max_description_width + 20)
    tree.column("amount", width=max_amount_width + 20)
    tree.column("expense_date", width=custom_font.measure("Date") + 20)

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
    for row in fetch_expenses():
        tree.insert("", "end", values=row)
    set_column_widths()

refresh_tree()

# --- Run Application ---
if __name__ == "__main__":
    root.mainloop()