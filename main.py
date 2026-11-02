import json
import os
import hashlib
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, FloatPrompt
from rich.layout import Layout
from rich.align import Align
from rich import box
from rich.text import Text
import time

# ---------- SETUP ----------
console = Console()
DATA_FILE = os.path.join(os.path.dirname(__file__), "data.json")

# CHASE COLORS (For normal users)
CHASE_BLUE_HEX = "on #004E9A"
CHASE_DARK = "bold #0B2A4A"
CHASE_LINK = "bold #0060A9"
MONEY_GREEN = "bold #1E8E3E"
MONEY_RED = "bold #D93025"
TEXT_WHITE = "white"

# ADMIN COLORS (For Admin Panel)
ADMIN_BG = "on #1A1A1A"
ADMIN_GOLD = "bold #FFD700"
ADMIN_RED = "bold #FF4444"
ADMIN_GREEN = "bold #00C851"

# ---------- DATA LAYER ----------
def load_data():
    if not os.path.exists(DATA_FILE):
        return {"users": {}}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

# ---------- UI HELPERS ----------
def clear():
    os.system("clear")

def fake_loading(text="Loading"):
    with console.status(f"[bold {CHASE_LINK}]{text}...[/]", spinner="dots"):
        time.sleep(1)

def pause():
    Prompt.ask(f"\n[dim #666666]Press Enter to continue...[/]", default="")

# ---------- DRAWING FUNCTIONS ----------
def draw_user_header(user):
    greeting = "Good morning," if datetime.now().hour < 12 else "Good afternoon," if datetime.now().hour < 18 else "Good evening,"
    header_grid = Table.grid(expand=True)
    header_grid.add_column(justify="left")
    header_grid.add_column(justify="right")
    
    header_grid.add_row(f"[bold white]CHASE [white]🔷[/]", "[white]🔔  👤[/]")
    header_grid.add_row(f"[white]{greeting}[/]\n[bold white]{user['full_name']} >[/]", "")
    
    console.print(Panel(header_grid, style=CHASE_BLUE_HEX, border_style=CHASE_BLUE_HEX, padding=(0, 1), expand=True))

def draw_admin_header():
    admin_ascii = """
[bold #FFD700]
    ██████╗ ██╗███████╗███████╗██╗   ██╗    ███████╗██╗   ██╗███████╗
    ██╔══██╗██║╚══███╔╝╚══███╔╝╚██╗ ██╔╝    ██╔════╝╚██╗ ██╔╝██╔════╝
    ██████╔╝██║  ███╔╝   ███╔╝  ╚████╔╝     ███████╗ ╚████╔╝ ███████╗
    ██╔═══╝ ██║ ███╔╝   ███╔╝    ╚██╔╝      ╚════██║  ╚██╔╝  ╚════██║
    ██║     ██║███████╗███████╗   ██║       ███████║   ██║   ███████║
    ╚═╝     ╚═╝╚══════╝╚══════╝   ╚═╝       ╚══════╝   ╚═╝   ╚══════╝[/]
    """
    console.print(Panel(Align.center(admin_ascii), title="[bold white]PIZZY BANK CONTROL PANEL[/]", border_style="red", style=ADMIN_BG))

# ---------- AUTH SCREENS ----------
def welcome():
    while True:
        clear()
        logo = """
[bold #004E9A]
   ██████╗██╗  ██╗ █████╗ ███████╗███████╗
  ██╔════╝██║  ██║██╔══██╗██╔════╝██╔════╝
  ██║     ███████║███████║███████╗█████╗  
  ██║     ██╔══██║██╔══██║╚════██║██╔══╝  
  ╚██████╗██║  ██║██║  ██║███████║███████╗
   ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚══════╝
[/]
        """
        console.print(Align.center(logo))
        
        menu = Table.grid(padding=(0, 2))
        menu.add_column(justify="center")
        menu.add_row(f"[{CHASE_LINK}]1.[/] Log In")
        menu.add_row(f"[{CHASE_LINK}]2.[/] Create an Account")
        menu.add_row(f"[{CHASE_LINK}]3.[/] Exit")
        console.print(Align.center(menu))
        
        choice = Prompt.ask(f"\n[bold {CHASE_LINK}]Select[/]", choices=["1", "2", "3"])
        
        if choice == "1":
            user = login()
            if user:
                if user == "admin":
                    admin_dashboard()
                else:
                    user_dashboard(user)
        elif choice == "2":
            register()
        else:
            break

def register():
    clear()
    console.print(f"[bold {CHASE_DARK}]Create your Pizzy Bank Account[/]\n")
    username = Prompt.ask("Username").strip().lower()
    
    if username == "admin":
        console.print(f"[{MONEY_RED}]That username is reserved.[/]"); pause(); return

    full_name = Prompt.ask("Full Name")
    password = Prompt.ask("Password", password=True)
    
    data = load_data()
    if username in data["users"]:
        console.print(f"[{MONEY_RED}]Username taken.[/]"); pause(); return

    data["users"][username] = {
        "password": hash_password(password),
        "full_name": full_name,
        "checking": 0.00,
        "savings": 0.00,
        "account_no": f"...{1000 + len(data['users']) + 1}",
        "transactions": [],
        "created": datetime.now().strftime("%b %d, %Y"),
    }
    
    fake_loading("Opening account")
    save_data(data)
    
    console.print(Panel(f"[bold {MONEY_GREEN}]✓ Account Successfully Opened![/]\nAccount #: {data['users'][username]['account_no']}\nWelcome to Chase.", border_style=MONEY_GREEN))
    pause()

def login():
    clear()
    console.print(f"[bold {CHASE_DARK}]Log In[/]\n")
    username = Prompt.ask("Username").strip().lower()
    password = Prompt.ask("Password", password=True)
    
    fake_loading("Authenticating")
    
    data = load_data()
    
    if username == "admin" and password == "admin123":
        return "admin"
        
    user = data["users"].get(username)

    if not user or user["password"] != hash_password(password):
        console.print(f"[{MONEY_RED}]Invalid credentials.[/]"); pause(); return None

    return username

# ---------- USER DASHBOARD (CHASE UI) ----------
def user_dashboard(username):
    while True:
        clear()
        data = load_data()
        user = data["users"][username]
        
        draw_user_header(user)
        
        card_grid = Table.grid(expand=True, padding=(0, 1))
        card_grid.add_column(justify="left")
        card_grid.add_column(justify="right")
        
        card_grid.add_row(f"[bold {CHASE_DARK}]Chase Total Checking®[/]", "[dim #666666]>[/]")
        card_grid.add_row(f"[dim #666666]{user['account_no']}[/]", "")
        card_grid.add_row(f"\n[bold {CHASE_DARK}]${user['checking']:,.2f}[/]", "")
        card_grid.add_row(f"[dim #666666]Available balance ⓘ[/]\n", "")
        
        actions = Table.grid(expand=True)
        actions.add_column(justify="center"); actions.add_column(justify="center")
        actions.add_column(justify="center"); actions.add_column(justify="center")
        actions.add_row("🔄", "💵", "📱", "•••")
        actions.add_row(f"[dim]Transfer[/]", f"[dim]Deposit[/]", f"[dim]Pay bills[/]", f"[dim]More[/]")
        card_grid.add_row(actions, "")
        
        console.print(Panel(card_grid, border_style="white", style="on white", padding=(0, 1)))
        
        tx_grid = Table.grid(expand=True, padding=(0, 1))
        tx_grid.add_column(justify="left")
        tx_grid.add_column(justify="right")
        tx_grid.add_row(f"[bold {CHASE_DARK}]Recent transactions[/]", f"[{CHASE_LINK}]See all >[/]")
        
        txs = user["transactions"][-4:][::-1]
        if not txs:
            tx_grid.add_row("[dim #666666]No recent transactions[/]", "")
        else:
            for tx in txs:
                amt_color = MONEY_GREEN if tx["amount"] >= 0 else CHASE_DARK
                sign = "+" if tx["amount"] >= 0 else "-"
                amount_str = f"[{amt_color}]{sign}${abs(tx['amount']):,.2f}[/]"
                left_side = f"{tx['icon']} [bold {CHASE_DARK}]{tx['type']}[/]\n   [dim #666666]{tx['date']}[/]"
                tx_grid.add_row(left_side, f"\n{amount_str}")
                tx_grid.add_row("[dim #E0E0E0]────────────────────────────────────[/]", "")
            
        console.print(Panel(tx_grid, border_style="white", style="on white", padding=(0, 1)))
        
        console.print(f"\n[bold {CHASE_LINK}]1.[/] Home  [bold {CHASE_LINK}]2.[/] Accounts  [dim]3. Transfer[/]  [bold {CHASE_LINK}]4.[/] Settings  [bold {CHASE_LINK}]5.[/] Log Out")
        
        choice = Prompt.ask(f"\n[bold {CHASE_LINK}]Select[/]", choices=["1", "2", "3", "4", "5"])
        
        if choice == "1": continue
        elif choice == "2": show_accounts(username)
        elif choice == "3": 
            console.print(f"[{MONEY_RED}]Transfers are currently disabled by Admin.[/]"); pause()
        elif choice == "4": user_settings(username)
        elif choice == "5": return

def show_accounts(username):
    clear()
    user = load_data()["users"][username]
    draw_user_header(user)
    
    grid = Table.grid(expand=True, padding=(0, 2))
    grid.add_row(f"[bold {CHASE_DARK}]Checking ({user['account_no']})[/]")
    grid.add_row(f"[bold {CHASE_DARK}]${user['checking']:,.2f}[/]\n")
    grid.add_row(f"[bold {CHASE_DARK}]Savings[/]")
    grid.add_row(f"[bold {CHASE_DARK}]${user['savings']:,.2f}[/]\n")
    
    console.print(Panel(grid, border_style="white", style="on white", padding=(1, 2)))
    pause()

def user_settings(username):
    clear()
    console.print(f"[bold {CHASE_DARK}]Settings[/]\n")
    console.print("1. Change Password")
    console.print("2. Back")
    c = Prompt.ask("Select", choices=["1", "2"])
    if c == "1":
        data = load_data()
        new = Prompt.ask("New Password", password=True)
        data["users"][username]["password"] = hash_password(new)
        save_data(data)
        console.print(f"[{MONEY_GREEN}]✓ Password updated.[/]")
        pause()

# ---------- ADMIN DASHBOARD ----------
def admin_dashboard():
    while True:
        clear()
        draw_admin_header()
        data = load_data()
        
        total_users = len(data["users"])
        total_deposits = sum(u["checking"] + u["savings"] for u in data["users"].values())
        
        stats = Table.grid(expand=True, padding=(0, 5))
        stats.add_column(justify="center")
        stats.add_column(justify="center")
        stats.add_row(f"[{ADMIN_GOLD}]TOTAL USERS[/]\n[bold white]{total_users}[/]", f"[{ADMIN_GOLD}]BANK ASSETS[/]\n[bold white]${total_deposits:,.2f}[/]")
        console.print(Panel(Align.center(stats), style=ADMIN_BG, border_style="blue"))
        
        console.print("\n")
        menu = Table.grid(padding=(0, 3))
        menu.add_column(justify="center")
        menu.add_row(f"[{ADMIN_GOLD}]1.[/] View All Users")
        menu.add_row(f"[{ADMIN_GOLD}]2.[/] Edit User Balance (Deposit/Withdraw)")
        menu.add_row(f"[{ADMIN_GOLD}]3.[/] Delete User Account")
        menu.add_row(f"[{ADMIN_GOLD}]4.[/] Log Out")
        console.print(Align.center(Panel(menu, style=ADMIN_BG, border_style="white", expand=False, title="[bold red]ADMIN ACTIONS[/]")))
        
        choice = Prompt.ask(f"\n[{ADMIN_GOLD}]Admin Command[/]", choices=["1", "2", "3", "4"])
        
        if choice == "1": admin_view_users()
        elif choice == "2": admin_edit_balance()
        elif choice == "3": admin_delete_user()
        elif choice == "4": return

def admin_view_users():
    clear()
    draw_admin_header()
    data = load_data()
    
    t = Table(title="[bold white]ALL REGISTERED USERS[/]", box=box.ROUNDED, style=ADMIN_BG, border_style="blue")
    t.add_column("Username", style="cyan")
    t.add_column("Full Name", style="white")
    t.add_column("Checking", justify="right", style="green")
    t.add_column("Savings", justify="right", style="green")
    t.add_column("Joined", style="dim")
    
    for uname, info in data["users"].items():
        t.add_row(uname, info["full_name"], f"${info['checking']:,.2f}", f"${info['savings']:,.2f}", info["created"])
        
    console.print(t)
    pause()

def admin_edit_balance():
    clear()
    draw_admin_header()
    data = load_data()
    
    target = Prompt.ask("Enter Username to Edit").strip().lower()
    if target not in data["users"]:
        console.print(f"[{ADMIN_RED}]User not found.[/]"); pause(); return
        
    console.print(f"\nEditing: [bold cyan]{target}[/] ({data['users'][target]['full_name']})")
    console.print(f"Current Checking: [green]${data['users'][target]['checking']:,.2f}[/]")
    console.print(f"Current Savings:  [green]${data['users'][target]['savings']:,.2f}[/]\n")
    
    account = Prompt.ask("Which account to edit?", choices=["checking", "savings"])
    action = Prompt.ask("Action", choices=["deposit", "withdraw", "set"])
    amount = FloatPrompt.ask("Amount ($)")
    
    current_bal = data["users"][target][account]
    
    if action == "deposit":
        data["users"][target][account] += amount
        tx_type = "Direct Deposit"
        tx_icon = "⬇️"
        tx_amount = amount
    elif action == "withdraw":
        data["users"][target][account] -= amount
        tx_type = "Admin Withdrawal"
        tx_icon = "👑"
        tx_amount = -amount
    elif action == "set":
        data["users"][target][account] = amount
        tx_type = "Balance Adjustment"
        tx_icon = "👑"
        tx_amount = amount
    
    data["users"][target]["transactions"].append({
        "date": datetime.now().strftime("%b %d"), 
        "type": tx_type, 
        "amount": tx_amount, 
        "icon": tx_icon
    })
    
    save_data(data)
    console.print(f"\n[{ADMIN_GREEN}]✓ Successfully updated {target}'s {account} balance.[/]")
    console.print(f"New Balance: [bold green]${data['users'][target][account]:,.2f}[/]")
    pause()

def admin_delete_user():
    clear()
    draw_admin_header()
    data = load_data()
    
    target = Prompt.ask("[bold red]Enter Username to DELETE[/]").strip().lower()
    if target not in data["users"]:
        console.print(f"[{ADMIN_RED}]User not found.[/]"); pause(); return
        
    confirm = Prompt.ask(f"[bold red]Are you sure you want to delete {target}? This cannot be undone![/]", choices=["y", "n"])
    if confirm == "y":
        del data["users"][target]
        save_data(data)
        console.print(f"\n[{ADMIN_GREEN}]✓ User {target} deleted from the system.[/]")
    else:
        console.print("\n[dim]Deletion cancelled.[/]")
    pause()

# ---------- ENTRY POINT ----------
if __name__ == "__main__":
    try:
        welcome()
    except KeyboardInterrupt:
        console.print("\n[dim]Goodbye.[/]")
