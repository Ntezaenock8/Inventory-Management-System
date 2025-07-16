import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

class SalesModule:
    def __init__(self, root):
        self.root = root
        self.root.title("Sales Management Module")
        self.root.geometry("900x600")

        # ---------------- Style ----------------
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview.Heading", font=("Arial", 11, "bold"), background="#f0f0f0", relief="groove")
        style.configure("Treeview", font=("Arial", 10), rowheight=28)

        # ---------------- Form Frame ----------------
        form_frame = tk.Frame(self.root)
        form_frame.pack(pady=10)

        # Date
        tk.Label(form_frame, text="Date:", font=("Arial", 10)).grid(row=0, column=0, padx=5, pady=5)
        self.date_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        tk.Entry(form_frame, textvariable=self.date_var, font=("Arial", 10), state='readonly', width=15).grid(row=0, column=1, padx=5, pady=5)

        # Item
        tk.Label(form_frame, text="Item:", font=("Arial", 10)).grid(row=0, column=2, padx=5, pady=5)
        self.item_var = tk.StringVar()
        self.item_combo = ttk.Combobox(form_frame, textvariable=self.item_var, width=20)
        self.item_combo['values'] = ["Cement", "Paint", "Iron Sheets", "Bricks", "Sand"]
        self.item_combo.grid(row=0, column=3, padx=5, pady=5)

        # Quantity
        tk.Label(form_frame, text="Quantity:", font=("Arial", 10)).grid(row=1, column=0, padx=5, pady=5)
        self.quantity_var = tk.StringVar()
        tk.Entry(form_frame, textvariable=self.quantity_var, font=("Arial", 10), width=10).grid(row=1, column=1, padx=5, pady=5)

        # Price
        tk.Label(form_frame, text="Price per Unit:", font=("Arial", 10)).grid(row=1, column=2, padx=5, pady=5)
        self.price_var = tk.StringVar()
        tk.Entry(form_frame, textvariable=self.price_var, font=("Arial", 10), width=15).grid(row=1, column=3, padx=5, pady=5)

        # ---------------- Treeview ----------------
        columns = ("date", "item", "quantity", "price", "total")
        self.tree = ttk.Treeview(self.root, columns=columns, show="headings", selectmode="browse")
        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        for col in columns:
            self.tree.heading(col, text=col.title())
            self.tree.column(col, anchor="w", width=140)

        scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # ---------------- Buttons ----------------
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=10)

        tk.Button(btn_frame, text="Add", command=self.add_row, width=15).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Edit", command=self.edit_row, width=15).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Delete", command=self.delete_row, width=15).pack(side=tk.LEFT, padx=5)

    def is_number(self, s):
        try:
            float(s)
            return True
        except ValueError:
            return False

    def clear_form(self):
        self.date_var.set(datetime.now().strftime("%Y-%m-%d"))
        self.item_var.set("")
        self.quantity_var.set("")
        self.price_var.set("")

    def add_row(self):
        date = self.date_var.get()
        item = self.item_var.get()
        quantity = self.quantity_var.get()
        price = self.price_var.get()

        if not item or not quantity or not price:
            messagebox.showerror("Input Error", "Please fill in all fields.")
            return
        if not self.is_number(quantity) or not self.is_number(price):
            messagebox.showerror("Input Error", "Quantity and Price must be numbers.")
            return

        total = round(float(quantity) * float(price), 2)
        self.tree.insert("", "end", values=(date, item, quantity, price, total))
        self.clear_form()

    def edit_row(self):
        selected = self.tree.selection()
        if not selected:
            return
        item = self.tree.item(selected[0])["values"]
        if item:
            self.date_var.set(item[0])
            self.item_var.set(item[1])
            self.quantity_var.set(item[2])
            self.price_var.set(item[3])
            self.tree.delete(selected[0])

    def delete_row(self):
        selected = self.tree.selection()
        if selected:
            self.tree.delete(selected[0])
            self.clear_form()


if __name__ == "__main__":
    root = tk.Tk()
    app = SalesModule(root)
    root.mainloop()
