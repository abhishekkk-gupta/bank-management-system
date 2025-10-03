import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import os
import sys
import io

# Fix Windows console encoding for print statements
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

class BankManagementSystem:
    def __init__(self):
        self.conn = None
        self.cursor = None
        self.setup_database()
        
    def setup_database(self):
        """Connect to SQLite and create tables if they don't exist"""
        try:
            # Connect to SQLite database (creates file if doesn't exist)
            self.conn = sqlite3.connect('bank_system.db')
            self.cursor = self.conn.cursor()
            
            # Create users table
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    account_number INTEGER PRIMARY KEY AUTOINCREMENT,
                    full_name TEXT NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    phone TEXT NOT NULL,
                    password TEXT NOT NULL,
                    balance REAL DEFAULT 0.00,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create transactions table
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS transactions (
                    transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    account_number INTEGER NOT NULL,
                    transaction_type TEXT NOT NULL,
                    amount REAL NOT NULL,
                    balance_after REAL NOT NULL,
                    transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (account_number) REFERENCES users(account_number)
                )
            """)
            
            self.conn.commit()
            print("[OK] Database setup successful!")
            
        except sqlite3.Error as err:
            messagebox.showerror("Database Error", f"Error: {err}")
            
    def register_user(self, full_name, email, phone, password, initial_deposit):
        """Register a new user"""
        try:
            query = """INSERT INTO users (full_name, email, phone, password, balance) 
                       VALUES (?, ?, ?, ?, ?)"""
            self.cursor.execute(query, (full_name, email, phone, password, initial_deposit))
            self.conn.commit()
            
            # Get the account number
            account_number = self.cursor.lastrowid
            
            # Record initial deposit as transaction if > 0
            if initial_deposit > 0:
                self.record_transaction(account_number, 'Deposit', initial_deposit, initial_deposit)
            
            return account_number
        except sqlite3.IntegrityError:
            return None
        except sqlite3.Error as err:
            messagebox.showerror("Error", f"Registration failed: {err}")
            return None
            
    def login_user(self, email, password):
        """Authenticate user login"""
        try:
            query = "SELECT account_number, full_name, balance FROM users WHERE email = ? AND password = ?"
            self.cursor.execute(query, (email, password))
            result = self.cursor.fetchone()
            return result
        except sqlite3.Error as err:
            messagebox.showerror("Error", f"Login failed: {err}")
            return None
            
    def deposit_money(self, account_number, amount):
        """Deposit money into account"""
        try:
            # Update balance
            query = "UPDATE users SET balance = balance + ? WHERE account_number = ?"
            self.cursor.execute(query, (amount, account_number))
            
            # Get new balance
            self.cursor.execute("SELECT balance FROM users WHERE account_number = ?", (account_number,))
            new_balance = self.cursor.fetchone()[0]
            
            # Record transaction
            self.record_transaction(account_number, 'Deposit', amount, new_balance)
            
            self.conn.commit()
            return new_balance
        except sqlite3.Error as err:
            messagebox.showerror("Error", f"Deposit failed: {err}")
            return None
            
    def withdraw_money(self, account_number, amount):
        """Withdraw money from account"""
        try:
            # Check current balance
            self.cursor.execute("SELECT balance FROM users WHERE account_number = ?", (account_number,))
            current_balance = self.cursor.fetchone()[0]
            
            if current_balance < amount:
                return None, "Insufficient funds"
            
            # Update balance
            query = "UPDATE users SET balance = balance - ? WHERE account_number = ?"
            self.cursor.execute(query, (amount, account_number))
            
            # Get new balance
            new_balance = current_balance - amount
            
            # Record transaction
            self.record_transaction(account_number, 'Withdrawal', amount, new_balance)
            
            self.conn.commit()
            return new_balance, "Success"
        except sqlite3.Error as err:
            messagebox.showerror("Error", f"Withdrawal failed: {err}")
            return None, str(err)
            
    def get_balance(self, account_number):
        """Get current balance"""
        try:
            query = "SELECT balance FROM users WHERE account_number = ?"
            self.cursor.execute(query, (account_number,))
            return self.cursor.fetchone()[0]
        except sqlite3.Error as err:
            messagebox.showerror("Error", f"Failed to fetch balance: {err}")
            return None
            
    def record_transaction(self, account_number, trans_type, amount, balance_after):
        """Record a transaction"""
        try:
            query = """INSERT INTO transactions (account_number, transaction_type, amount, balance_after) 
                       VALUES (?, ?, ?, ?)"""
            self.cursor.execute(query, (account_number, trans_type, amount, balance_after))
        except sqlite3.Error as err:
            print(f"Transaction recording failed: {err}")
            
    def get_transaction_history(self, account_number):
        """Get transaction history"""
        try:
            query = """SELECT transaction_type, amount, balance_after, transaction_date 
                       FROM transactions WHERE account_number = ? 
                       ORDER BY transaction_date DESC"""
            self.cursor.execute(query, (account_number,))
            return self.cursor.fetchall()
        except sqlite3.Error as err:
            messagebox.showerror("Error", f"Failed to fetch transactions: {err}")
            return []


class ModernButton(tk.Canvas):
    """Custom modern button with hover effects"""
    def __init__(self, parent, text, command, bg_color="#4CAF50", hover_color="#45a049", 
                 fg_color="white", width=200, height=50, **kwargs):
        super().__init__(parent, width=width, height=height, bg=parent['bg'], 
                        highlightthickness=0, **kwargs)
        
        self.command = command
        self.bg_color = bg_color
        self.hover_color = hover_color
        self.fg_color = fg_color
        self.text = text
        self.width = width
        self.height = height
        
        # Draw button
        self.button_id = self.create_rectangle(0, 0, width, height, fill=bg_color, 
                                               outline="", tags="button")
        self.text_id = self.create_text(width/2, height/2, text=text, fill=fg_color, 
                                       font=("Segoe UI", 11, "bold"), tags="button")
        
        # Bind events
        self.tag_bind("button", "<Enter>", self.on_enter)
        self.tag_bind("button", "<Leave>", self.on_leave)
        self.tag_bind("button", "<Button-1>", self.on_click)
        
    def on_enter(self, e):
        self.itemconfig(self.button_id, fill=self.hover_color)
        self.config(cursor="hand2")
        
    def on_leave(self, e):
        self.itemconfig(self.button_id, fill=self.bg_color)
        self.config(cursor="")
        
    def on_click(self, e):
        if self.command:
            self.command()


class ModernEntry(tk.Frame):
    """Custom modern entry field"""
    def __init__(self, parent, placeholder="", show=None, **kwargs):
        super().__init__(parent, bg=parent['bg'])
        
        self.entry = tk.Entry(self, font=("Segoe UI", 11), relief="flat", 
                             bg="#f5f5f5", fg="#333", insertbackground="#333",
                             show=show, **kwargs)
        self.entry.pack(fill="x", ipady=8, ipadx=10)
        
        # Add bottom border
        border = tk.Frame(self, height=2, bg="#ddd")
        border.pack(fill="x")
        
        # Focus effects
        self.entry.bind("<FocusIn>", lambda e: border.config(bg="#2196F3"))
        self.entry.bind("<FocusOut>", lambda e: border.config(bg="#ddd"))
        
    def get(self):
        return self.entry.get()
    
    def delete(self, first, last):
        self.entry.delete(first, last)


class BankGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Modern Bank Management System")
        self.root.geometry("1000x650")
        
        # Set theme colors
        self.bg_color = "#f0f2f5"
        self.card_bg = "#ffffff"
        self.primary_color = "#1a73e8"
        self.success_color = "#34a853"
        self.warning_color = "#fbbc04"
        self.danger_color = "#ea4335"
        
        self.root.configure(bg=self.bg_color)
        
        self.bank_system = BankManagementSystem()
        self.current_user = None
        
        # Show login screen initially
        self.show_login_screen()
        
    def clear_screen(self):
        """Clear all widgets from screen"""
        for widget in self.root.winfo_children():
            widget.destroy()
            
    def create_card(self, parent, **kwargs):
        """Create a modern card-style frame"""
        card = tk.Frame(parent, bg=self.card_bg, **kwargs)
        # Add shadow effect by creating a slightly larger darker frame behind
        return card
        
    def show_login_screen(self):
        """Display modern login screen"""
        self.clear_screen()
        
        # Left side - Branding
        left_frame = tk.Frame(self.root, bg="#1a73e8")
        left_frame.place(x=0, y=0, relwidth=0.45, relheight=1)
        
        branding = tk.Frame(left_frame, bg="#1a73e8")
        branding.place(relx=0.5, rely=0.5, anchor="center")
        
        tk.Label(branding, text="BANK", font=("Segoe UI", 48, "bold"), 
                bg="#1a73e8", fg="white").pack()
        tk.Label(branding, text="Management System", font=("Segoe UI", 16), 
                bg="#1a73e8", fg="#bbdefb").pack()
        
        tk.Label(branding, text="Secure • Fast • Reliable", font=("Segoe UI", 11), 
                bg="#1a73e8", fg="#90caf9", pady=30).pack()
        
        # Right side - Login form
        right_frame = tk.Frame(self.root, bg=self.bg_color)
        right_frame.place(relx=0.45, y=0, relwidth=0.55, relheight=1)
        
        login_container = tk.Frame(right_frame, bg=self.bg_color)
        login_container.place(relx=0.5, rely=0.5, anchor="center")
        
        # Login card
        login_card = self.create_card(login_container)
        login_card.pack(padx=40, pady=20)
        
        content = tk.Frame(login_card, bg=self.card_bg, padx=50, pady=40)
        content.pack()
        
        tk.Label(content, text="Welcome Back", font=("Segoe UI", 24, "bold"), 
                bg=self.card_bg, fg="#202124").pack(anchor="w", pady=(0, 5))
        
        tk.Label(content, text="Login to your account", font=("Segoe UI", 11), 
                bg=self.card_bg, fg="#5f6368").pack(anchor="w", pady=(0, 30))
        
        # Email field
        tk.Label(content, text="Email Address", font=("Segoe UI", 10), 
                bg=self.card_bg, fg="#5f6368").pack(anchor="w", pady=(0, 5))
        email_entry = ModernEntry(content, width=35)
        email_entry.pack(fill="x", pady=(0, 20))
        
        # Password field
        tk.Label(content, text="Password", font=("Segoe UI", 10), 
                bg=self.card_bg, fg="#5f6368").pack(anchor="w", pady=(0, 5))
        password_entry = ModernEntry(content, show="*", width=35)
        password_entry.pack(fill="x", pady=(0, 30))
        
        def login():
            email = email_entry.get().strip()
            password = password_entry.get().strip()
            
            if not email or not password:
                messagebox.showwarning("Input Error", "Please fill all fields")
                return
                
            user = self.bank_system.login_user(email, password)
            if user:
                self.current_user = {
                    'account_number': user[0],
                    'name': user[1],
                    'balance': user[2]
                }
                self.show_dashboard()
            else:
                messagebox.showerror("Login Failed", "Invalid email or password")
        
        # Login button
        ModernButton(content, "Sign In", login, bg_color=self.primary_color, 
                    hover_color="#1557b0", width=300, height=45).pack(pady=(0, 20))
        
        # Register link
        register_frame = tk.Frame(content, bg=self.card_bg)
        register_frame.pack()
        
        tk.Label(register_frame, text="Don't have an account?", font=("Segoe UI", 10), 
                bg=self.card_bg, fg="#5f6368").pack(side="left", padx=(0, 5))
        
        register_btn = tk.Label(register_frame, text="Create Account", font=("Segoe UI", 10, "bold"), 
                               bg=self.card_bg, fg=self.primary_color, cursor="hand2")
        register_btn.pack(side="left")
        register_btn.bind("<Button-1>", lambda e: self.show_register_screen())
        
    def show_register_screen(self):
        """Display modern registration screen"""
        self.clear_screen()
        
        # Header
        header = tk.Frame(self.root, bg=self.card_bg, height=70)
        header.pack(fill="x")
        header.pack_propagate(False)
        
        tk.Label(header, text="Create New Account", font=("Segoe UI", 20, "bold"), 
                bg=self.card_bg, fg="#202124").pack(side="left", padx=30, pady=20)
        
        back_btn = tk.Label(header, text="< Back to Login", font=("Segoe UI", 10), 
                           bg=self.card_bg, fg=self.primary_color, cursor="hand2")
        back_btn.pack(side="right", padx=30)
        back_btn.bind("<Button-1>", lambda e: self.show_login_screen())
        
        # Main content
        content = tk.Frame(self.root, bg=self.bg_color)
        content.pack(fill="both", expand=True, padx=50, pady=30)
        
        # Registration card
        reg_card = self.create_card(content)
        reg_card.place(relx=0.5, rely=0.5, anchor="center")
        
        form = tk.Frame(reg_card, bg=self.card_bg, padx=60, pady=40)
        form.pack()
        
        # Form fields
        fields = [
            ("Full Name", "text"),
            ("Email Address", "text"),
            ("Phone Number", "text"),
            ("Password", "password"),
            ("Initial Deposit (Rs)", "text")
        ]
        
        entries = {}
        for label, field_type in fields:
            tk.Label(form, text=label, font=("Segoe UI", 10), 
                    bg=self.card_bg, fg="#5f6368").pack(anchor="w", pady=(10, 5))
            entry = ModernEntry(form, show="*" if field_type == "password" else None, width=40)
            entry.pack(fill="x", pady=(0, 10))
            entries[label] = entry
        
        def register():
            full_name = entries["Full Name"].get().strip()
            email = entries["Email Address"].get().strip()
            phone = entries["Phone Number"].get().strip()
            password = entries["Password"].get().strip()
            initial_deposit = entries["Initial Deposit (Rs)"].get().strip()
            
            if not all([full_name, email, phone, password, initial_deposit]):
                messagebox.showwarning("Input Error", "Please fill all fields")
                return
                
            try:
                initial_deposit = float(initial_deposit)
                if initial_deposit < 0:
                    messagebox.showwarning("Invalid Amount", "Initial deposit cannot be negative")
                    return
            except ValueError:
                messagebox.showwarning("Invalid Amount", "Please enter a valid amount")
                return
                
            account_number = self.bank_system.register_user(full_name, email, phone, password, initial_deposit)
            
            if account_number:
                messagebox.showinfo("Success", f"Account created successfully!\nYour Account Number: {account_number}")
                self.show_login_screen()
            else:
                messagebox.showerror("Registration Failed", "Email already exists or registration failed")
        
        ModernButton(form, "Create Account", register, bg_color=self.success_color, 
                    hover_color="#2d8e47", width=350, height=45).pack(pady=(20, 0))
        
    def show_dashboard(self):
        """Display modern dashboard"""
        self.clear_screen()
        
        # Top Navigation Bar
        navbar = tk.Frame(self.root, bg=self.card_bg, height=70)
        navbar.pack(fill="x")
        navbar.pack_propagate(False)
        
        # Logo and title
        logo_frame = tk.Frame(navbar, bg=self.card_bg)
        logo_frame.pack(side="left", padx=30, pady=15)
        
        tk.Label(logo_frame, text="BANK", font=("Segoe UI", 16, "bold"), 
                bg=self.card_bg, fg=self.primary_color).pack(side="left")
        
        # User info
        user_frame = tk.Frame(navbar, bg=self.card_bg)
        user_frame.pack(side="right", padx=30)
        
        tk.Label(user_frame, text=f"Welcome, {self.current_user['name']}", 
                font=("Segoe UI", 11), bg=self.card_bg, fg="#202124").pack(side="left", padx=(0, 20))
        
        tk.Label(user_frame, text=f"A/C: {self.current_user['account_number']}", 
                font=("Segoe UI", 9), bg=self.card_bg, fg="#5f6368").pack(side="left", padx=(0, 20))
        
        logout_btn = tk.Label(user_frame, text="Logout", font=("Segoe UI", 10, "bold"), 
                             bg=self.card_bg, fg=self.danger_color, cursor="hand2")
        logout_btn.pack(side="left")
        logout_btn.bind("<Button-1>", lambda e: self.show_login_screen())
        
        # Main content area
        content = tk.Frame(self.root, bg=self.bg_color)
        content.pack(fill="both", expand=True, padx=40, pady=30)
        
        # Balance Card
        balance_card = self.create_card(content)
        balance_card.pack(fill="x", pady=(0, 30))
        
        balance_content = tk.Frame(balance_card, bg=self.card_bg, padx=40, pady=30)
        balance_content.pack(fill="x")
        
        tk.Label(balance_content, text="Total Balance", font=("Segoe UI", 12), 
                bg=self.card_bg, fg="#5f6368").pack(anchor="w")
        
        balance = self.bank_system.get_balance(self.current_user['account_number'])
        tk.Label(balance_content, text=f"Rs {balance:,.2f}", font=("Segoe UI", 36, "bold"), 
                bg=self.card_bg, fg="#202124").pack(anchor="w", pady=(5, 0))
        
        # Action Cards
        actions_frame = tk.Frame(content, bg=self.bg_color)
        actions_frame.pack(fill="both", expand=True)
        
        # Configure grid
        actions_frame.columnconfigure(0, weight=1)
        actions_frame.columnconfigure(1, weight=1)
        actions_frame.columnconfigure(2, weight=1)
        
        actions = [
            ("Deposit", "Add money to\nyour account", self.success_color, self.show_deposit_screen),
            ("Withdraw", "Withdraw money\nfrom account", self.warning_color, self.show_withdraw_screen),
            ("History", "View transaction\nhistory", self.primary_color, self.show_transaction_history),
        ]
        
        for i, (title, subtitle, color, command) in enumerate(actions):
            card = self.create_card(actions_frame)
            card.grid(row=0, column=i, padx=10, sticky="nsew")
            
            card_content = tk.Frame(card, bg=self.card_bg, padx=30, pady=30)
            card_content.pack(fill="both", expand=True)
            
            # Icon placeholder (colored circle)
            icon_canvas = tk.Canvas(card_content, width=60, height=60, bg=self.card_bg, 
                                   highlightthickness=0)
            icon_canvas.pack(pady=(0, 15))
            icon_canvas.create_oval(10, 10, 50, 50, fill=color, outline="")
            
            tk.Label(card_content, text=title, font=("Segoe UI", 16, "bold"), 
                    bg=self.card_bg, fg="#202124").pack()
            
            tk.Label(card_content, text=subtitle, font=("Segoe UI", 10), 
                    bg=self.card_bg, fg="#5f6368", justify="center").pack(pady=(5, 20))
            
            ModernButton(card_content, "Open", command, bg_color=color, 
                        hover_color=color, width=150, height=40).pack()
        
    def show_deposit_screen(self):
        """Display modern deposit screen"""
        self.clear_screen()
        self.create_transaction_screen("Deposit", self.success_color)
        
    def show_withdraw_screen(self):
        """Display modern withdrawal screen"""
        self.clear_screen()
        self.create_transaction_screen("Withdraw", self.warning_color)
        
    def create_transaction_screen(self, trans_type, color):
        """Create modern transaction screen"""
        # Header
        header = tk.Frame(self.root, bg=self.card_bg, height=70)
        header.pack(fill="x")
        header.pack_propagate(False)
        
        tk.Label(header, text=f"{trans_type} Money", font=("Segoe UI", 20, "bold"), 
                bg=self.card_bg, fg="#202124").pack(side="left", padx=30, pady=20)
        
        back_btn = tk.Label(header, text="< Back to Dashboard", font=("Segoe UI", 10), 
                           bg=self.card_bg, fg=self.primary_color, cursor="hand2")
        back_btn.pack(side="right", padx=30)
        back_btn.bind("<Button-1>", lambda e: self.show_dashboard())
        
        # Main content
        content = tk.Frame(self.root, bg=self.bg_color)
        content.pack(fill="both", expand=True)
        
        # Transaction card
        trans_card = self.create_card(content)
        trans_card.place(relx=0.5, rely=0.5, anchor="center")
        
        form = tk.Frame(trans_card, bg=self.card_bg, padx=60, pady=50)
        form.pack()
        
        # Icon
        icon_canvas = tk.Canvas(form, width=80, height=80, bg=self.card_bg, 
                               highlightthickness=0)
        icon_canvas.pack(pady=(0, 20))
        icon_canvas.create_oval(10, 10, 70, 70, fill=color, outline="")
        
        tk.Label(form, text=f"{trans_type} Amount", font=("Segoe UI", 20, "bold"), 
                bg=self.card_bg, fg="#202124").pack(pady=(0, 30))
        
        tk.Label(form, text="Enter Amount (Rs)", font=("Segoe UI", 10), 
                bg=self.card_bg, fg="#5f6368").pack(anchor="w", pady=(0, 5))
        
        amount_entry = ModernEntry(form, width=35)
        amount_entry.pack(fill="x", pady=(0, 30))
        
        def process_transaction():
            try:
                amount = float(amount_entry.get().strip())
                if amount <= 0:
                    messagebox.showwarning("Invalid Amount", "Amount must be greater than 0")
                    return
                    
                if trans_type == "Deposit":
                    new_balance = self.bank_system.deposit_money(self.current_user['account_number'], amount)
                    if new_balance is not None:
                        messagebox.showinfo("Success", f"Rs {amount:,.2f} deposited successfully!\nNew Balance: Rs {new_balance:,.2f}")
                        self.show_dashboard()
                else:  # Withdrawal
                    new_balance, message = self.bank_system.withdraw_money(self.current_user['account_number'], amount)
                    if new_balance is not None:
                        messagebox.showinfo("Success", f"Rs {amount:,.2f} withdrawn successfully!\nNew Balance: Rs {new_balance:,.2f}")
                        self.show_dashboard()
                    else:
                        messagebox.showerror("Transaction Failed", message)
                        
            except ValueError:
                messagebox.showwarning("Invalid Input", "Please enter a valid amount")
        
        ModernButton(form, f"Confirm {trans_type}", process_transaction, 
                    bg_color=color, hover_color=color, width=350, height=45).pack()
        
    def show_transaction_history(self):
        """Display modern transaction history"""
        self.clear_screen()
        
        # Header
        header = tk.Frame(self.root, bg=self.card_bg, height=70)
        header.pack(fill="x")
        header.pack_propagate(False)
        
        tk.Label(header, text="Transaction History", font=("Segoe UI", 20, "bold"), 
                bg=self.card_bg, fg="#202124").pack(side="left", padx=30, pady=20)
        
        # Export button in header
        export_btn = tk.Label(header, text="Export PDF", font=("Segoe UI", 10, "bold"), 
                             bg=self.success_color, fg="white", cursor="hand2", 
                             padx=20, pady=8)
        export_btn.pack(side="right", padx=30)
        export_btn.bind("<Button-1>", lambda e: self.export_to_pdf())
        
        back_btn = tk.Label(header, text="< Back to Dashboard", font=("Segoe UI", 10), 
                           bg=self.card_bg, fg=self.primary_color, cursor="hand2")
        back_btn.pack(side="right", padx=20)
        back_btn.bind("<Button-1>", lambda e: self.show_dashboard())
        
        # Main content
        content = tk.Frame(self.root, bg=self.bg_color)
        content.pack(fill="both", expand=True, padx=40, pady=30)
        
        # Table card
        table_card = self.create_card(content)
        table_card.pack(fill="both", expand=True)
        
        # Style for treeview
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", 
                       background=self.card_bg,
                       foreground="#202124",
                       fieldbackground=self.card_bg,
                       borderwidth=0,
                       font=("Segoe UI", 10))
        style.configure("Treeview.Heading",
                       background="#f8f9fa",
                       foreground="#202124",
                       borderwidth=0,
                       font=("Segoe UI", 11, "bold"))
        style.map("Treeview", background=[("selected", self.primary_color)])
        
        # Treeview
        tree_frame = tk.Frame(table_card, bg=self.card_bg)
        tree_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        scrollbar = ttk.Scrollbar(tree_frame)
        scrollbar.pack(side="right", fill="y")
        
        columns = ("Type", "Amount", "Balance After", "Date & Time")
        tree = ttk.Treeview(tree_frame, columns=columns, show="headings", 
                           yscrollcommand=scrollbar.set, height=15)
        scrollbar.config(command=tree.yview)
        
        # Column configuration
        tree.column("Type", width=150, anchor="center")
        tree.column("Amount", width=200, anchor="center")
        tree.column("Balance After", width=200, anchor="center")
        tree.column("Date & Time", width=250, anchor="center")
        
        for col in columns:
            tree.heading(col, text=col)
        
        # Fetch and display transactions
        transactions = self.bank_system.get_transaction_history(self.current_user['account_number'])
        
        for trans in transactions:
            trans_type, amount, balance_after, trans_date = trans
            tree.insert("", "end", values=(
                trans_type,
                f"Rs {amount:,.2f}",
                f"Rs {balance_after:,.2f}",
                trans_date
            ))
        
        tree.pack(fill="both", expand=True)
        
        if not transactions:
            empty_label = tk.Label(tree_frame, text="No transactions yet", 
                    font=("Segoe UI", 14), bg=self.card_bg, fg="#5f6368")
            empty_label.place(relx=0.5, rely=0.5, anchor="center")
    
    def export_to_pdf(self):
        """Export transaction history to PDF"""
        try:
            transactions = self.bank_system.get_transaction_history(self.current_user['account_number'])
            
            if not transactions:
                messagebox.showinfo("No Data", "No transactions to export")
                return
            
            # Create PDF
            filename = f"statement_{self.current_user['account_number']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            c = canvas.Canvas(filename, pagesize=letter)
            
            # Header
            c.setFont("Helvetica-Bold", 16)
            c.drawString(200, 750, "Bank Transaction Statement")
            
            c.setFont("Helvetica", 12)
            c.drawString(50, 720, f"Account Number: {self.current_user['account_number']}")
            c.drawString(50, 700, f"Account Holder: {self.current_user['name']}")
            c.drawString(50, 680, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Table header
            y = 640
            c.setFont("Helvetica-Bold", 10)
            c.drawString(50, y, "Type")
            c.drawString(150, y, "Amount")
            c.drawString(250, y, "Balance After")
            c.drawString(370, y, "Date")
            
            # Draw line
            c.line(50, y-5, 550, y-5)
            
            # Transactions
            c.setFont("Helvetica", 10)
            y -= 25
            
            for trans in transactions:
                if y < 50:  # New page if needed
                    c.showPage()
                    y = 750
                    
                trans_type, amount, balance_after, trans_date = trans
                c.drawString(50, y, trans_type)
                c.drawString(150, y, f"Rs {amount:,.2f}")
                c.drawString(250, y, f"Rs {balance_after:,.2f}")
                c.drawString(370, y, str(trans_date))
                y -= 20
            
            c.save()
            messagebox.showinfo("Success", f"Statement exported successfully!\nSaved as: {filename}")
            
        except Exception as e:
            messagebox.showerror("Export Failed", f"Failed to export PDF: {str(e)}")


if __name__ == "__main__":
    root = tk.Tk()
    app = BankGUI(root)
    root.mainloop()