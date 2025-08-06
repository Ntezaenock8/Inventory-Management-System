import tkinter as tk
from tkinter import ttk, font, messagebox
import sqlite3
from datetime import datetime

DB_NAME = "database.db"

# --- Database Queries ---
def get_profit_data(period_type, selected_year, selected_period=None, show_all=False):
    """Fetch profit/loss data from database for the selected period type."""
    conn = sqlite3.connect(DB_NAME, timeout=10)
    conn.execute("PRAGMA foreign_keys = ON;")
    cursor = conn.cursor()
    result = []
    stock_valuation = 0.0
    
    try:
        # Stock Valuation: SUM(inventory.quantity * AVG(inventory_batches.buying_price))
        cursor.execute("""
            SELECT SUM(i.quantity * AVG(ib.buying_price))
            FROM inventory i
            LEFT JOIN inventory_batches ib ON i.item_id = ib.item_id
            GROUP BY i.item_id
        """)
        stock_rows = cursor.fetchall()
        stock_valuation = sum(row[0] for row in stock_rows if row[0] is not None) or 0.0

        # Define period filters
        month_map = {
            "January": "01", "February": "02", "March": "03", "April": "04",
            "May": "05", "June": "06", "July": "07", "August": "08",
            "September": "09", "October": "10", "November": "11", "December": "12"
        }
        if period_type == "Monthly":
            if show_all:
                periods = [(month, month_map[month]) for month in month_map]
            else:
                periods = [(selected_period, month_map.get(selected_period, "01"))]
        elif period_type == "Quarterly":
            if show_all:
                periods = [("Q1", ["01", "02", "03"]), ("Q2", ["04", "05", "06"]), 
                           ("Q3", ["07", "08", "09"]), ("Q4", ["10", "11", "12"])]
            else:
                periods = [(selected_period, [f"{i:02d}" for i in range((int(selected_period[1])-1)*3+1, int(selected_period[1])*3+1)])]
        else:  # Annual
            periods = [(selected_year, None)]

        for period_name, period_filter in periods:
            # Revenue: SUM(sales.total_price)
            revenue_query = "SELECT SUM(total_price) FROM sales WHERE strftime('%Y', sale_date) = ?"
            revenue_params = [selected_year]
            if period_type == "Monthly" and period_filter:
                revenue_query += " AND strftime('%m', sale_date) = ?"
                revenue_params.append(period_filter)
            elif period_type == "Quarterly" and period_filter:
                revenue_query += " AND strftime('%m', sale_date) IN (?, ?, ?)"
                revenue_params.extend(period_filter)
            cursor.execute(revenue_query, revenue_params)
            revenue = cursor.fetchone()[0] or 0.0

            # Cost: SUM(sales.quantity * inventory_batches.buying_price)
            cost_query = """
                SELECT SUM(s.quantity * ib.buying_price)
                FROM sales s
                JOIN inventory_batches ib ON s.item_id = ib.item_id
                WHERE strftime('%Y', s.sale_date) = ?
            """
            cost_params = [selected_year]
            if period_type == "Monthly" and period_filter:
                cost_query += " AND strftime('%m', s.sale_date) = ?"
                cost_params.append(period_filter)
            elif period_type == "Quarterly" and period_filter:
                cost_query += " AND strftime('%m', s.sale_date) IN (?, ?, ?)"
                cost_params.extend(period_filter)
            cursor.execute(cost_query, cost_params)
            cost = cursor.fetchone()[0] or 0.0

            # Expenses: SUM(expenses.amount)
            expense_query = "SELECT SUM(amount) FROM expenses WHERE strftime('%Y', expense_date) = ?"
            expense_params = [selected_year]
            if period_type == "Monthly" and period_filter:
                expense_query += " AND strftime('%m', expense_date) = ?"
                expense_params.append(period_filter)
            elif period_type == "Quarterly" and period_filter:
                expense_query += " AND strftime('%m', expense_date) IN (?, ?, ?)"
                expense_params.extend(period_filter)
            cursor.execute(expense_query, expense_params)
            expenses = cursor.fetchone()[0] or 0.0

            # Calculate Gross and Net Profit
            gross_profit = revenue - cost
            net_profit = gross_profit - expenses

            # Only append if there's valid data
            if revenue or cost or expenses:
                period_label = f"{period_name} {selected_year}" if period_type in ["Monthly", "Quarterly"] else period_name
                result.append((period_label, revenue, cost, gross_profit, expenses, net_profit))
            elif period_type == "Annual" and (revenue or cost or expenses):
                result.append((selected_year, revenue, cost, gross_profit, expenses, net_profit))

        if not result:
            return ("No records or Insufficient data", stock_valuation)
        return (result, stock_valuation)
    
    except sqlite3.Error as e:
        print(f"Database Error: {e}")
        return ("No records or Insufficient data", stock_valuation)
    finally:
        conn.close()

# --- UI Setup ---
root = tk.Tk()
root.title("Profit & Loss Report")
root.geometry("800x600")

# Define fonts
custom_font = font.Font(family="TkDefaultFont", size=13)
summary_font = font.Font(family="TkDefaultFont", size=16, weight="bold")  # Larger font for summarized report

# --- Period Selector Frame ---
selector_frame = tk.Frame(root)
selector_frame.pack(fill="x", padx=10, pady=10)

# Period Type
tk.Label(selector_frame, text="Report Type:", font=custom_font).pack(side="left", padx=5)
period_var = tk.StringVar(value="Monthly")
period_combo = ttk.Combobox(selector_frame, textvariable=period_var, font=custom_font, width=15, state="readonly")
period_combo['values'] = ("Monthly", "Quarterly", "Annual")
period_combo.pack(side="left", padx=5)

# Year
tk.Label(selector_frame, text="Year:", font=custom_font).pack(side="left", padx=5)
year_var = tk.StringVar(value="2025")
year_combo = ttk.Combobox(selector_frame, textvariable=year_var, font=custom_font, width=10, state="readonly")
year_combo['values'] = ("2024", "2025")
year_combo.pack(side="left", padx=5)

# Month or Quarter
period_detail_var = tk.StringVar(value="January")
period_detail_label = tk.Label(selector_frame, text="Month:", font=custom_font)
period_detail_label.pack(side="left", padx=5)
period_detail_combo = ttk.Combobox(selector_frame, textvariable=period_detail_var, font=custom_font, width=15, state="readonly")
period_detail_combo['values'] = ("January", "February", "March", "April", "May", "June", 
                                "July", "August", "September", "October", "November", "December")
period_detail_combo.pack(side="left", padx=5)

# All Periods Checkbox
all_periods_var = tk.BooleanVar(value=False)
all_periods_check = tk.Checkbutton(selector_frame, text="Show All Periods", variable=all_periods_var, 
                                   font=custom_font)
all_periods_check.pack(side="left", padx=5)

# Update period detail options
def update_period_detail(*args):
    period_type = period_var.get()
    if period_type == "Monthly":
        period_detail_label.config(text="Month:")
        period_detail_combo['values'] = ("January", "February", "March", "April", "May", "June", 
                                        "July", "August", "September", "October", "November", "December")
        period_detail_var.set("January")
        all_periods_check.config(state="normal")
    elif period_type == "Quarterly":
        period_detail_label.config(text="Quarter:")
        period_detail_combo['values'] = ("Q1", "Q2", "Q3", "Q4")
        period_detail_var.set("Q1")
        all_periods_check.config(state="normal")
    else:  # Annual
        period_detail_label.config(text="")
        period_detail_combo['values'] = ()
        period_detail_var.set("")
        all_periods_check.config(state="normal")
period_var.trace_add("write", update_period_detail)

# --- Generate Report Button ---
generate_btn_frame = tk.Frame(root)
generate_btn_frame.pack(fill="x", pady=5)
tk.Button(generate_btn_frame, text="Generate Report", font=custom_font, command=lambda: generate_report(), 
          bg="#28a745", fg="white", width=15).pack()

# --- Results Frame (Labels for Single Period) ---
results_frame = tk.Frame(root)
results_frame.pack(fill="x", padx=10, pady=10)
results_frame.pack_forget()  # Hidden by default

title_label = tk.Label(results_frame, text="Short Income Statement", font=summary_font)
title_label.pack(fill="x", padx=5, pady=5)
no_data_label = tk.Label(results_frame, text="No records or Insufficient data", font=summary_font, fg="red")
no_data_label.pack(fill="x", padx=5, pady=10)
no_data_label.pack_forget()  # Hidden by default
period_label = tk.Label(results_frame, text="Period: ", font=summary_font, anchor="w")
period_label.pack(fill="x", padx=5, pady=2)
revenue_label = tk.Label(results_frame, text="Revenue: UGX ", font=summary_font, anchor="w")
revenue_label.pack(fill="x", padx=5, pady=2)
cost_label = tk.Label(results_frame, text="Cost: UGX ", font=summary_font, anchor="w")
cost_label.pack(fill="x", padx=5, pady=2)
gross_profit_label = tk.Label(results_frame, text="Gross Profit/Loss: UGX ", font=summary_font, anchor="w")
gross_profit_label.pack(fill="x", padx=5, pady=2)
expenses_label = tk.Label(results_frame, text="Expenses: UGX ", font=summary_font, anchor="w")
expenses_label.pack(fill="x", padx=5, pady=2)
net_profit_label = tk.Label(results_frame, text="Net Profit/Loss: UGX ", font=summary_font, anchor="w")
net_profit_label.pack(fill="x", padx=5, pady=2)

# --- Treeview for Multi-Period Results ---
tree_frame = tk.Frame(root)
tree_frame.pack(fill="both", expand=True, padx=10, pady=10)
tree_frame.pack_forget()  # Hidden by default

columns = ("period", "revenue", "cost", "gross_profit", "expenses", "net_profit")
style = ttk.Style()
style.configure("Treeview", font=custom_font)
style.configure("Treeview.Heading", font=custom_font)

tree = ttk.Treeview(tree_frame, columns=columns, show="headings", style="Treeview", height=5)
tree.heading("period", text="Period")
tree.heading("revenue", text="Revenue (UGX)")
tree.heading("cost", text="Cost (UGX)")
tree.heading("gross_profit", text="Gross Profit/Loss (UGX)")
tree.heading("expenses", text="Expenses (UGX)")
tree.heading("net_profit", text="Net Profit/Loss (UGX)")
for col in columns:
    tree.column(col, width=150)

scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
tree.configure(yscrollcommand=scrollbar.set)
tree.grid(row=1, column=0, sticky="nsew")
scrollbar.grid(row=1, column=1, sticky="ns")
title_label_tree = tk.Label(tree_frame, text="Short Income Statement", font=custom_font)
title_label_tree.grid(row=0, column=0, columnspan=2, sticky="nsew", pady=5)
no_records_label = tk.Label(tree_frame, text="No records or Insufficient data", 
                           font=custom_font, fg="red")
no_records_label.grid(row=2, column=0, columnspan=2, sticky="nsew", pady=10)
no_records_label.grid_remove()
tree_frame.grid_rowconfigure(1, weight=1)
tree_frame.grid_columnconfigure(0, weight=1)

# --- Summary Frame ---
summary_frame = tk.Frame(root)
summary_frame.pack(fill="x", padx=10, pady=5)
gross_summary_var = tk.StringVar(value="")
gross_summary_label = tk.Label(summary_frame, textvariable=gross_summary_var, font=custom_font, anchor="w")
gross_summary_label.pack(fill="x", padx=5, pady=2)
net_summary_var = tk.StringVar(value="")
net_summary_label = tk.Label(summary_frame, textvariable=net_summary_var, font=custom_font, anchor="w")
net_summary_label.pack(fill="x", padx=5, pady=2)
stock_valuation_var = tk.StringVar(value="Current Stock Valuation: UGX 0.00")
stock_valuation_label = tk.Label(summary_frame, textvariable=stock_valuation_var, font=custom_font, anchor="w")
stock_valuation_label.pack(fill="x", padx=5, pady=2)

# --- Refresh Button ---
refresh_btn_frame = tk.Frame(root)
refresh_btn_frame.pack(fill="x", pady=5)
tk.Button(refresh_btn_frame, text="Refresh", font=custom_font, command=lambda: generate_report(), 
          bg="#28a745", fg="white", width=15).pack()

# --- Populate Results ---
def generate_report():
    """Populate labels or Treeview with profit/loss data from database."""
    for row in tree.get_children():
        tree.delete(row)
    period_type = period_var.get()
    year = year_var.get()
    period_detail = period_detail_var.get() if period_type != "Annual" else None
    show_all = all_periods_var.get()
    data, stock_valuation = get_profit_data(period_type, year, period_detail, show_all)
    
    # Update stock valuation
    stock_valuation_var.set(f"Current Stock Valuation: UGX {stock_valuation:.2f}")
    
    if isinstance(data, str):  # Error or no data
        tree_frame.pack_forget()
        results_frame.pack(fill="x", padx=10, pady=10)
        no_data_label.pack(fill="x", padx=5, pady=10)
        period_label.pack_forget()
        revenue_label.pack_forget()
        cost_label.pack_forget()
        gross_profit_label.pack_forget()
        expenses_label.pack_forget()
        net_profit_label.pack_forget()
        no_records_label.grid_remove()
        gross_summary_var.set("")
        net_summary_var.set("")
        return
    
    no_data_label.pack_forget()
    no_records_label.grid_remove()
    if show_all:  # Show Treeview for all periods
        results_frame.pack_forget()
        tree_frame.pack(fill="both", expand=True, padx=10, pady=10)
        for row in data:
            tag = "profit" if row[3] >= 0 else "loss"
            tree.insert("", "end", values=(row[0], f"UGX {row[1]:.2f}", f"UGX {row[2]:.2f}", 
                                          f"UGX {row[3]:.2f}", f"UGX {row[4]:.2f}", f"UGX {row[5]:.2f}"), tags=(tag,))
        total_gross = sum(row[3] for row in data)
        total_net = sum(row[5] for row in data)
        period_text = f"{year}" if period_type == "Annual" else f"{period_type} Periods in {year}"
        gross_summary_var.set(f"Gross {'Profit' if total_gross >= 0 else 'Loss'} for {period_text}: UGX {abs(total_gross):.2f}")
        net_summary_var.set(f"Net {'Profit' if total_net >= 0 else 'Loss'} for {period_text}: UGX {abs(total_net):.2f}")
    else:  # Show labels for single period
        tree_frame.pack_forget()
        results_frame.pack(fill="x", padx=10, pady=10)
        period_label.pack(fill="x", padx=5, pady=2)
        revenue_label.pack(fill="x", padx=5, pady=2)
        cost_label.pack(fill="x", padx=5, pady=2)
        gross_profit_label.pack(fill="x", padx=5, pady=2)
        expenses_label.pack(fill="x", padx=5, pady=2)
        net_profit_label.pack(fill="x", padx=5, pady=2)
        row = data[0]
        period_label.config(text=f"Period: {row[0]}")
        revenue_label.config(text=f"Revenue: UGX {row[1]:.2f}")
        cost_label.config(text=f"Cost: UGX {row[2]:.2f}")
        gross_profit_label.config(text=f"Gross {'Profit' if row[3] >= 0 else 'Loss'}: UGX {abs(row[3]):.2f}", 
                                 fg="green" if row[3] >= 0 else "red")
        expenses_label.config(text=f"Expenses: UGX {row[4]:.2f}")
        net_profit_label.config(text=f"Net {'Profit' if row[5] >= 0 else 'Loss'}: UGX {abs(row[5]):.2f}", 
                               fg="green" if row[5] >= 0 else "red")
        gross_summary_var.set("")
        net_summary_var.set("")

    # Configure Treeview tags
    tree.tag_configure("profit", foreground="green")
    tree.tag_configure("loss", foreground="red")

# Initial report
generate_report()

# --- Run Application ---
if __name__ == "__main__":
    root.mainloop()