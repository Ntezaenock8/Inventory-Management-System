import tkinter as tk
from tkinter import ttk

root = tk.Tk()
root.title("Profits and Reporting")
root.geometry("900x600")

# Style setup
style = ttk.Style()
style.theme_use("default")
style.configure("Treeview.Heading", font=("Arial", 11, "bold"), background="#f0f0f0", relief="groove")
style.configure("Treeview", font=("Arial", 10), rowheight=28)

# ----- Summary Frame -----
summary_frame = tk.Frame(root)
summary_frame.pack(pady=10)

def summary_card(parent, label, value, bg_color):
    card = tk.Frame(parent, bg=bg_color, padx=20, pady=10)
    card.pack(side=tk.LEFT, padx=10)
    tk.Label(card, text=label, font=("Arial", 11, "bold"), bg=bg_color, fg="white").pack()
    tk.Label(card, text=value, font=("Arial", 14, "bold"), bg=bg_color, fg="white").pack()

summary_card(summary_frame, "Total Revenue", "UGX 5,000,000", "#4CAF50")
summary_card(summary_frame, "Total Cost", "UGX 3,000,000", "#2196F3")
summary_card(summary_frame, "Profit", "UGX 2,000,000", "#FF9800")

# ----- Filter Section -----
filter_frame = tk.Frame(root)
filter_frame.pack(pady=10)

tk.Label(filter_frame, text="Start Date (YYYY-MM-DD):", font=("Arial", 10)).pack(side=tk.LEFT, padx=5)
start_entry = tk.Entry(filter_frame, width=15)
start_entry.pack(side=tk.LEFT, padx=5)

tk.Label(filter_frame, text="End Date (YYYY-MM-DD):", font=("Arial", 10)).pack(side=tk.LEFT, padx=5)
end_entry = tk.Entry(filter_frame, width=15)
end_entry.pack(side=tk.LEFT, padx=5)

tk.Button(filter_frame, text="Generate Report", width=15).pack(side=tk.LEFT, padx=10)

# ----- Treeview Table -----
columns = ("date", "revenue", "cost", "profit")

tree = ttk.Treeview(root, columns=columns, show="headings", selectmode="browse")
tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

for col in columns:
    tree.heading(col, text=col.title())
    tree.column(col, anchor="center", width=180)

# Scrollbar
scrollbar = ttk.Scrollbar(root, orient="vertical", command=tree.yview)
tree.configure(yscrollcommand=scrollbar.set)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

# Insert sample data
sample_data = [
    ("2025-05-20", "UGX 500,000", "UGX 300,000", "UGX 200,000"),
    ("2025-05-21", "UGX 750,000", "UGX 400,000", "UGX 350,000"),
    ("2025-05-22", "UGX 400,000", "UGX 250,000", "UGX 150,000"),
]
for row in sample_data:
    tree.insert("", "end", values=row)

root.mainloop()
