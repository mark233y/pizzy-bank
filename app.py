from flask import Flask, render_template, request, redirect, url_for, session, flash
import json, os, hashlib
from datetime import datetime

app = Flask(__name__)
app.secret_key = "pizzy_bank_super_secret_key"

DATA_FILE = os.path.join(os.path.dirname(__file__), "data.json")

# --- DATA HELPERS ---
def load_data():
    if not os.path.exists(DATA_FILE):
        return {"users": {}}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# --- ROUTES ---
@app.route('/')
def index():
    if 'user' in session:
        return redirect(url_for('dashboard') if session['user'] != 'admin' else url_for('admin'))
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username'].lower()
    password = request.form['password']
    data = load_data()

    if username == "admin" and password == "admin123":
        session['user'] = "admin"
        return redirect(url_for('admin'))

    user = data["users"].get(username)
    if user and user["password"] == hash_password(password):
        session['user'] = username
        return redirect(url_for('dashboard'))
    
    flash("Invalid username or password", "error")
    return redirect(url_for('index'))

@app.route('/register', methods=['POST'])
def register():
    username = request.form['username'].lower()
    fullname = request.form['fullname']
    password = request.form['password']
    data = load_data()

    if username in data["users"] or username == "admin":
        flash("Username already taken", "error")
        return redirect(url_for('index'))

    data["users"][username] = {
        "password": hash_password(password),
        "full_name": fullname,
        "checking": 0.00,
        "savings": 0.00,
        "loan": 0.00,
        "account_no": f"...{1000 + len(data['users']) + 1}",
        "card_no": f"4532 88** **** {1000 + len(data['users']) + 1}",
        "transactions": [{"date": datetime.now().strftime("%b %d"), "type": "Account Opened", "amount": 0, "icon": "✨"}],
        "created": datetime.now().strftime("%b %d, %Y"),
    }
    save_data(data)
    session['user'] = username
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
def dashboard():
    if 'user' not in session or session['user'] == 'admin':
        return redirect(url_for('index'))
    
    data = load_data()
    user = data["users"][session['user']]
    return render_template('dashboard.html', user=user, username=session['user'])

@app.route('/admin')
def admin():
    if session.get('user') != 'admin':
        return redirect(url_for('index'))
    data = load_data()
    return render_template('admin.html', users=data["users"])

@app.route('/admin/edit', methods=['POST'])
def admin_edit():
    if session.get('user') != 'admin': return redirect(url_for('index'))
    target = request.form['target']
    action = request.form['action']
    amount = float(request.form['amount'])
    
    data = load_data()
    if target in data["users"]:
        if action == "deposit":
            data["users"][target]["checking"] += amount
            tx_type = "Direct Deposit"
            tx_icon = "⬇️"
            tx_amount = amount
        elif action == "withdraw":
            data["users"][target]["checking"] -= amount
            tx_type = "Admin Withdrawal"
            tx_icon = "👑"
            tx_amount = -amount
        elif action == "set":
            data["users"][target]["checking"] = amount
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
        flash(f"Updated {target}'s balance.", "success")
    return redirect(url_for('admin'))

# --- NEW: MANAGE TRANSACTIONS ---
@app.route('/admin/transactions/<username>')
def admin_manage_transactions(username):
    if session.get('user') != 'admin': return redirect(url_for('index'))
    data = load_data()
    if username not in data["users"]: return redirect(url_for('admin'))
    
    user = data["users"][username]
    return render_template('admin_tx.html', user=user, username=username)

@app.route('/admin/delete_tx/<username>/<int:tx_index>')
def admin_delete_tx(username, tx_index):
    if session.get('user') != 'admin': return redirect(url_for('index'))
    data = load_data()
    if username in data["users"]:
        try:
            # Reverse the balance change before deleting the transaction
            tx = data["users"][username]["transactions"][tx_index]
            data["users"][username]["checking"] -= tx["amount"]
            del data["users"][username]["transactions"][tx_index]
            save_data(data)
            flash("Transaction deleted and balance reversed.", "success")
        except Exception as e:
            flash("Error deleting transaction.", "error")
    return redirect(url_for('admin_manage_transactions', username=username))

@app.route('/admin/edit_tx/<username>/<int:tx_index>', methods=['POST'])
def admin_edit_tx(username, tx_index):
    if session.get('user') != 'admin': return redirect(url_for('index'))
    data = load_data()
    if username in data["users"]:
        try:
            new_date = request.form['date']
            new_type = request.form['type']
            new_amount = float(request.form['amount'])
            
            # Revert old amount, apply new amount
            old_amount = data["users"][username]["transactions"][tx_index]["amount"]
            data["users"][username]["checking"] -= old_amount
            data["users"][username]["checking"] += new_amount
            
            # Update the transaction details
            data["users"][username]["transactions"][tx_index]["date"] = new_date
            data["users"][username]["transactions"][tx_index]["type"] = new_type
            data["users"][username]["transactions"][tx_index]["amount"] = new_amount
            
            save_data(data)
            flash("Transaction updated successfully.", "success")
        except Exception as e:
            flash("Error updating transaction.", "error")
    return redirect(url_for('admin_manage_transactions', username=username))

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
