import tkinter as tk
from tkinter import ttk, font, messagebox

# --- Dummy Data ---
def get_dummy_profit_data(period_type, selected_year, selected_period=None, show_all=False):
    """Return dummy profit/loss data for the selected period type, including expenses."""
    print(f"get_dummy_profit_data: period_type={period_type}, year={selected_year}, period={selected_period}, show_all={show_all}")
    # Sample data: (Period, Revenue, Cost, Gross Profit/Loss, Expenses, Net Profit/Loss)
    monthly_data = [
        ("January 2025", 5000.00, 4000.00, 1000.00, 200.00, 800.00),   # Profit
        ("February 2025", 3000.00, 3500.00, -500.00, 200.00, -700.00),  # Loss
        ("March 2025", 6000.00, 4500.00, 1500.00, 200.00, 1300.00),    # Profit
    ]
    quarterly_data = [
        ("Q1 2025", 14000.00, 12000.00, 2000.00, 600.00, 1400.00),     # Profit
        ("Q2 2025", 8000.00, 9000.00, -1000.00, 600.00, -1600.00),     # Loss
    ]
    annual_data = [
        ("2024", 50000.00, 45000.00, 5000.00, 2400.00, 2600.00),       # Profit
        ("2025", 60000.00, 65000.00, -5000.00, 2400.00, -7400.00),     # Loss
    ]
    # Dummy stock valuation
    stock_valuation = 10000.00  # Simulates SUM(inventory.quantity * AVG(inventory_batches.buying_price))
    
    if period_type == "Monthly" and selected_year == "2025":
        if show_all:
            return (monthly_data, stock_valuation)
        return ([row for row in monthly_data if row[0].startswith(selected_period)], stock_valuation)
    elif period_type == "Quarterly" and selected_year == "2025":
        if show_all:
            return (quarterly_data, stock_valuation)
        return ([row for row in quarterly_data if row[0].startswith(selected_period + " ")], stock_valuation)
    elif period_type == "Annual":
        if show_all:
            return ([row for row in annual_data if row[0] < "2025"], stock_valuation)  # Exclude 2025
        return ([row for row in annual_data if row[0] == selected_year], stock_valuation)
    return ([], stock_valuation)

# --- UI Setup ---
root = tk.Tk()
root.title("Profit Report View (Dummy)")
root.geometry("800x600")

# Define custom font (consistent with other modules)
custom_font = font.Font(family="TkDefaultFont", size=13)

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
    print(f"update_period_detail: period_type={period_type}")
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
        all_periods_check.config(state="normal")  # Keep enabled for Annual
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

period_label = tk.Label(results_frame, text="Period: ", font=custom_font, anchor="w")
period_label.pack(fill="x", padx=5, pady=2)
revenue_label = tk.Label(results_frame, text="Revenue: ", font=custom_font, anchor="w")
revenue_label.pack(fill="x", padx=5, pady=2)
cost_label = tk.Label(results_frame, text="Cost: ", font=custom_font, anchor="w")
cost_label.pack(fill="x", padx=5, pady=2)
gross_profit_label = tk.Label(results_frame, text="Gross Profit/Loss: ", font=custom_font, anchor="w")
gross_profit_label.pack(fill="x", padx=5, pady=2)
net_profit_label = tk.Label(results_frame, text="Net Profit/Loss: ", font=custom_font, anchor="w")
net_profit_label.pack(fill="x", padx=5, pady=2)

# --- Treeview for Multi-Period Results ---
tree_frame = tk.Frame(root)
tree_frame.pack(fill="both", expand=True, padx=10, pady=10)
tree_frame.pack_forget()  # Hidden by default

columns = ("period", "revenue", "cost", "gross_profit", "net_profit")
style = ttk.Style()
style.configure("Treeview", font=custom_font)
style.configure("Treeview.Heading", font=custom_font)

tree = ttk.Treeview(tree_frame, columns=columns, show="headings", style="Treeview", height=5)
tree.heading("period", text="Period")
tree.heading("revenue", text="Revenue ($)")
tree.heading("cost", text="Cost ($)")
tree.heading("gross_profit", text="Gross Profit/Loss ($)")
tree.heading("net_profit", text="Net Profit/Loss ($)")
for col in columns:
    tree.column(col, width=150)

scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
tree.configure(yscrollcommand=scrollbar.set)
tree.grid(row=0, column=0, sticky="nsew")
scrollbar.grid(row=0, column=1, sticky="ns")
tree_frame.grid_rowconfigure(0, weight=1)
tree_frame.grid_columnconfigure(0, weight=1)

# --- No Records Message ---
no_records_label = tk.Label(tree_frame, text="No profit/loss records found for this period.", 
                           font=custom_font, fg="red")
no_records_label.grid(row=1, column=0, columnspan=2, sticky="nsew", pady=10)
no_records_label.grid_remove()

# --- Summary Frame ---
summary_frame = tk.Frame(root)
summary_frame.pack(fill="x", padx=10, pady=5)
gross_summary_var = tk.StringVar(value="")
gross_summary_label = tk.Label(summary_frame, textvariable=gross_summary_var, font=custom_font, anchor="w")
gross_summary_label.pack(fill="x", padx=5, pady=2)
net_summary_var = tk.StringVar(value="")
net_summary_label = tk.Label(summary_frame, textvariable=net_summary_var, font=custom_font, anchor="w")
net_summary_label.pack(fill="x", padx=5, pady=2)
stock_valuation_var = tk.StringVar(value="Current Stock Valuation: $0.00")
stock_valuation_label = tk.Label(summary_frame, textvariable=stock_valuation_var, font=custom_font, anchor="w")
stock_valuation_label.pack(fill="x", padx=5, pady=2)

# --- Refresh Button ---
refresh_btn_frame = tk.Frame(root)
refresh_btn_frame.pack(fill="x", pady=5)
tk.Button(refresh_btn_frame, text="Refresh", font=custom_font, command=lambda: generate_report(), 
          bg="#28a745", fg="white", width=15).pack()

# --- Populate Results ---
def generate_report():
    """Populate labels or Treeview with dummy profit/loss data."""
    print("generate_report called")
    for row in tree.get_children():
        tree.delete(row)
    period_type = period_var.get()
    year = year_var.get()
    period_detail = period_detail_var.get() if period_type != "Annual" else None
    show_all = all_periods_var.get()
    data, stock_valuation = get_dummy_profit_data(period_type, year, period_detail, show_all)
    print(f"Data returned: {data}, Stock valuation: {stock_valuation}")
    
    # Update stock valuation
    stock_valuation_var.set(f"Current Stock Valuation: ${stock_valuation:.2f}")
    
    if not data:
        no_records_label.grid(row=1, column=0, columnspan=2, sticky="nsew", pady=10)
        results_frame.pack_forget()
        tree_frame.pack_forget()
        gross_summary_var.set("")
        net_summary_var.set("")
        return
    
    no_records_label.grid_remove()
    if show_all:  # Show Treeview for all periods
        results_frame.pack_forget()
        tree_frame.pack(fill="both", expand=True, padx=10, pady=10)
        for row in data:
            tag = "profit" if row[3] >= 0 else "loss"
            tree.insert("", "end", values=(row[0], f"${row[1]:.2f}", f"${row[2]:.2f}", 
                                          f"${row[3]:.2f}", f"${row[5]:.2f}"), tags=(tag,))
        total_gross = sum(row[3] for row in data)
        total_net = sum(row[5] for row in data)
        period_text = f"{year}" if period_type == "Annual" else f"{period_type} Periods in {year}"
        gross_summary_var.set(f"Gross {'Profit' if total_gross >= 0 else 'Loss'} for {period_text}: ${abs(total_gross):.2f}")
        net_summary_var.set(f"Net {'Profit' if total_net >= 0 else 'Loss'} for {period_text}: ${abs(total_net):.2f}")
    else:  # Show labels for single period
        tree_frame.pack_forget()
        results_frame.pack(fill="x", padx=10, pady=10)
        row = data[0]
        period_label.config(text=f"Period: {row[0]}")
        revenue_label.config(text=f"Revenue: ${row[1]:.2f}")
        cost_label.config(text=f"Cost: ${row[2]:.2f}")
        gross_profit_label.config(text=f"Gross {'Profit' if row[3] >= 0 else 'Loss'}: ${abs(row[3]):.2f}", 
                                 fg="green" if row[3] >= 0 else "red")
        net_profit_label.config(text=f"Net {'Profit' if row[5] >= 0 else 'Loss'}: ${abs(row[5]):.2f}", 
                               fg="green" if row[5] >= 0 else "red")
        gross_summary_var.set("")  # No summary for single period
        net_summary_var.set("")

    # Configure Treeview tags
    tree.tag_configure("profit", foreground="green")
    tree.tag_configure("loss", foreground="red")

# Initial report
generate_report()

# --- Run Application ---
if __name__ == "__main__":
    root.mainloop()