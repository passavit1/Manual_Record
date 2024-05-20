import tkinter as tk
from tkinter import messagebox, ttk
import csv

def calculate_profit(entry_price, exit_price, quality):
    percentage_change = ((float(exit_price) - float(entry_price)) / float(entry_price)) * 100
    percentage_loss = percentage_change / 100
    actual_loss = percentage_loss * float(quality)
    return actual_loss


def calculate_percentage_profit(entry_price, exit_price):
    entry = float(entry_price)
    exit = float(exit_price)
    return ((exit - entry) / entry) * 100

def load_data(filter_symbol=None):
    try:
        with open('trading_data.csv', 'r', newline='') as file:
            reader = csv.reader(file)
            tree_data.delete(*tree_data.get_children())
            tree_summary.delete(*tree_summary.get_children())
            trade_count = 0
            total_profit = 0.0
            symbol_profit = {}
            symbol_trades = {}
            symbol_wins = {}
            
            for idx, row in enumerate(reader):
                if filter_symbol and row[0] != filter_symbol:
                    continue
                trade_count += 1
                profit = float(row[4])
                total_profit += profit
                percentage_profit = calculate_percentage_profit(row[2], row[3])
                
                if row[0] not in symbol_profit:
                    symbol_profit[row[0]] = 0
                    symbol_trades[row[0]] = 0
                    symbol_wins[row[0]] = 0
                
                symbol_profit[row[0]] += profit
                symbol_trades[row[0]] += 1
                if profit > 0:
                    symbol_wins[row[0]] += 1
                
                formatted_profit = f"{profit:.10f}"
                formatted_percentage = f"{percentage_profit:.2f}%"
                tree_data.insert('', 0, values=(row[0], row[1], row[2], row[3], formatted_profit, formatted_percentage))  
            
            trade_count_label.config(text=f"Number of Trades: {trade_count}")
            total_profit_label.config(text=f"Total Profit: {total_profit:.10f}")
            
            for symbol, profit in symbol_profit.items():
                win_rate = (symbol_wins[symbol] / symbol_trades[symbol]) * 100
                formatted_profit = f"{profit:.10f}"
                formatted_win_rate = f"{win_rate:.2f}%"
                tree_summary.insert('', tk.END, values=(symbol, formatted_profit, formatted_win_rate))
    except FileNotFoundError:
        with open('trading_data.csv', 'w', newline='') as file:
            pass  # Create file if it does not exist


def save_to_csv(data):
    with open('trading_data.csv', 'a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(data)
    load_data()
    update_filter_options()

def delete_selected():
    selection = tree_data.selection()
    if not selection:
        messagebox.showerror("Error", "No item selected")
        return
    item = tree_data.item(selection[0])
    values = list(item['values'])  # Ensure values are in list format
    with open('trading_data.csv', 'r', newline='') as file:
        reader = list(csv.reader(file))
    with open('trading_data.csv', 'w', newline='') as file:
        writer = csv.writer(file)
        for row in reader:
            # Convert CSV row values to float for comparison where applicable
            formatted_row = [
                row[0], row[1], row[2], row[3], f"{float(row[4]):.10f}", f"{calculate_percentage_profit(row[2], row[3]):.2f}%"
            ]
            if not all(str(a) == str(b) for a, b in zip(formatted_row, values)):
                writer.writerow(row)
    load_data()
    update_filter_options()


def on_submit():
    symbol = symbol_entry.get()
    quality = quality_entry.get()
    entry_price = entry_price_entry.get()
    exit_price = exit_price_entry.get()
    
    if not (symbol and quality and entry_price and exit_price):
        messagebox.showerror("Input Error", "All fields are required!")
        return
    
    try:
        profit = calculate_profit(entry_price, exit_price, quality)
        profit_label.config(text=f"Calculated Profit: {profit:.8f}")
        
        save_to_csv([symbol, quality, entry_price, exit_price, profit])
        
    except ValueError:
        messagebox.showerror("Input Error", "Please enter valid numbers for prices and quality")

def update_filter_options():
    symbols = set()
    try:
        with open('trading_data.csv', 'r', newline='') as file:
            reader = csv.reader(file)
            for row in reader:
                symbols.add(row[0])
    except FileNotFoundError:
        pass
    filter_symbol_menu['values'] = list(symbols)

def on_filter():
    filter_symbol = filter_symbol_menu.get()
    load_data(filter_symbol)

# Setting up the GUI
root = tk.Tk()
root.title("Trading Profit Calculator")
root.geometry("1200x400")

# Labels and entries for inputs
tk.Label(root, text="Symbol").grid(row=0, column=0)
symbol_entry = tk.Entry(root)
symbol_entry.grid(row=0, column=1)

tk.Label(root, text="Quality").grid(row=1, column=0)
quality_entry = tk.Entry(root)
quality_entry.grid(row=1, column=1)

tk.Label(root, text="Entry Price").grid(row=2, column=0)
entry_price_entry = tk.Entry(root)
entry_price_entry.grid(row=2, column=1)

tk.Label(root, text="Exit Price").grid(row=3, column=0)
exit_price_entry = tk.Entry(root)
exit_price_entry.grid(row=3, column=1)

# Submit button
submit_button = tk.Button(root, text="Calculate and Save", command=on_submit)
submit_button.grid(row=4, column=0, columnspan=2)

# Label to display profit
profit_label = tk.Label(root, text="Calculated Profit: ")
profit_label.grid(row=5, column=0, columnspan=2)

# Treeview to display CSV data
tree_data = ttk.Treeview(root, columns=('symbol', 'quality', 'entry_price', 'exit_price', 'profit', 'percentage'), show='headings', height=10)
tree_data.heading('symbol', text='Symbol')
tree_data.heading('quality', text='Quality')
tree_data.heading('entry_price', text='Entry Price')
tree_data.heading('exit_price', text='Exit Price')
tree_data.heading('profit', text='Profit')
tree_data.heading('percentage', text='Percentage')

# Set column widths
tree_data.column('symbol', width=80)
tree_data.column('quality', width=80)
tree_data.column('entry_price', width=80)
tree_data.column('exit_price', width=80)
tree_data.column('profit', width=100)
tree_data.column('percentage', width=80)

tree_data.grid(row=0, column=3, rowspan=6, padx=10 , pady=20)

# Add Treeview for displaying total profit by symbol
tree_summary = ttk.Treeview(root, columns=('symbol', 'total_profit', 'win_rate'), show='headings', height=10)
tree_summary.heading('symbol', text='Symbol')
tree_summary.heading('total_profit', text='Total Profit')
tree_summary.heading('win_rate', text='Win Rate')
tree_summary.column('symbol', width=100)
tree_summary.column('total_profit', width=100)
tree_summary.column('win_rate', width=100)
tree_summary.grid(row=0, column=4, rowspan=6, padx=10)

# Button to delete selected item
delete_button = tk.Button(root, text="Delete Selected", command=delete_selected)
delete_button.grid(row=6, column=3)

# Filter options and button
tk.Label(root, text="Filter by Symbol").grid(row=7, column=0)
filter_symbol_menu = ttk.Combobox(root)
filter_symbol_menu.grid(row=7, column=1)

filter_button = tk.Button(root, text="Apply Filter", command=on_filter)
filter_button.grid(row=7, column=2)

# Labels for trade count and total profit
trade_count_label = tk.Label(root, text="Number of Trades: ")
trade_count_label.grid(row=8, column=3)
total_profit_label = tk.Label(root, text="Total Profit: ")
total_profit_label.grid(row=9, column=3)

load_data()  # Initial load of data
update_filter_options()  # Load filter options
root.mainloop()
