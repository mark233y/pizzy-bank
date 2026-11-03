from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
import hashlib
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = "pizzy_bank_super_secret_key"

# --- DATABASE SETUP ---
# Use the absolute path for the database file so it works on Render
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'pizzybank.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- DATABASE MODELS ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    full_name = db.Column(db.String(120), nullable=False)
    password = db.Column(db.String(200), nullable=False)
    checking = db.Column(db.Float, default=0.00)
    savings = db.Column(db.Float, default=0.00)
    loan = db.Column(db.Float, default=0.00)
    account_no = db.Column(db.String(50), nullable=False)
    card_no = db.Column(db.String(50), nullable=False)
    created = db.Column(db.String(50), nullable=False)

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.String(50), nullable=False)
    type = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    icon = db.Column(db.String(10), nullable=False)

# Create the database tables if they don't exist
with app.app_context():
    db.create_all()

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

    if username == "admin" and password == "admin123":
        session['user'] = "admin"
        return redirect(url_for('admin'))

    user = User.query.filter_by(username=username).first()
    if user and user.password == hash_password(password):
        session['user'] = username
        return redirect(url_for('dashboard'))
    
    flash("Invalid username or password", "error")
    return redirect(url_for('index'))

@app.route('/register', methods=['POST'])
def register():
    username = request.form['username'].lower()
    fullname = request.form['fullname']
    password = request.form['password']

    if User.query.filter_by(username=username).first() or username == "admin":
        flash("Username already taken", "error")
        return redirect(url_for('index'))

    # Create new user in database
    new_user = User(
        username=username,
        full_name=fullname,
        password=hash_password(password),
        account_no=f"...{1000 + User.query.count() + 1}",
        card_no=f"4532 88** **** {1000 + User.query.count() + 1}",
        created=datetime.now().strftime("%b %d, %Y")
    )
    db.session.add(new_user)
    db.session.commit()

    # Add welcome transaction
    tx = Transaction(user_id=new_user.id, date=datetime.now().strftime("%b %d"), type="Account Opened", amount=0, icon="✨")
    db.session.add(tx)
    db.session.commit()

    session['user'] = username
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
def dashboard():
    if 'user' not in session or session['user'] == 'admin':
        return redirect(url_for('index'))
    
    user = User.query.filter_by(username=session['user']).first()
    # Get transactions (newest first)
    transactions = Transaction.query.filter_by(user_id=user.id).order_by(Transaction.id.desc()).all()
    
    return render_template('dashboard.html', user=user, transactions=transactions, username=session['user'])

@app.route('/admin')
def admin():
    if session.get('user') != 'admin':
        return redirect(url_for('index'))
    users = User.query.all()
    return render_template('admin.html', users=users)

@app.route('/admin/edit', methods=['POST'])
def admin_edit():
    if session.get('user') != 'admin': return redirect(url_for('index'))
    target = request.form['target']
    action = request.form['action']
    amount = float(request.form['amount'])
    
    user = User.query.filter_by(username=target).first()
    if user:
        if action == "deposit":
            user.checking += amount
            tx_type = "Direct Deposit"
            tx_icon = "⬇️"
            tx_amount = amount
        elif action == "withdraw":
            user.checking -= amount
            tx_type = "Admin Withdrawal"
            tx_icon = "👑"
            tx_amount = -amount
        elif action == "set":
            user.checking = amount
            tx_type = "Balance Adjustment"
            tx_icon = "👑"
            tx_amount = amount
        
        tx = Transaction(user_id=user.id, date=datetime.now().strftime("%b %d"), type=tx_type, amount=tx_amount, icon=tx_icon)
        db.session.add(tx)
        db.session.commit()
        flash(f"Updated {target}'s balance.", "success")
    return redirect(url_for('admin'))

@app.route('/admin/transactions/<username>')
def admin_manage_transactions(username):
    if session.get('user') != 'admin': return redirect(url_for('index'))
    user = User.query.filter_by(username=username).first()
    if not user: return redirect(url_for('admin'))
    
    transactions = Transaction.query.filter_by(user_id=user.id).order_by(Transaction.id.desc()).all()
    return render_template('admin_tx.html', user=user, transactions=transactions, username=username)

@app.route('/admin/delete_tx/<username>/<int:tx_id>')
def admin_delete_tx(username, tx_id):
    if session.get('user') != 'admin': return redirect(url_for('index'))
    tx = Transaction.query.get(tx_id)
    user = User.query.filter_by(username=username).first()
    
    if tx and user:
        # Reverse the balance
        user.checking -= tx.amount
        db.session.delete(tx)
        db.session.commit()
        flash("Transaction deleted and balance reversed.", "success")
    return redirect(url_for('admin_manage_transactions', username=username))

@app.route('/admin/edit_tx/<username>/<int:tx_id>', methods=['POST'])
def admin_edit_tx(username, tx_id):
    if session.get('user') != 'admin': return redirect(url_for('index'))
    tx = Transaction.query.get(tx_id)
    user = User.query.filter_by(username=username).first()
    
    if tx and user:
        new_amount = float(request.form['amount'])
        # Adjust balance
        user.checking -= tx.amount
        user.checking += new_amount
        
        tx.date = request.form['date']
        tx.type = request.form['type']
        tx.amount = new_amount
        
        db.session.commit()
        flash("Transaction updated successfully.", "success")
    return redirect(url_for('admin_manage_transactions', username=username))

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
