from flask import Flask, render_template, request, redirect, session, url_for
import sqlite3
from flask_mail import Mail, Message

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# ----------------- Database Setup -----------------
def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            first_name TEXT,
            last_name TEXT,
            email TEXT,
            phone TEXT,
            address TEXT,
            balance REAL DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# ----------------- Mail Config (Namecheap Private Email) -----------------
app.config['MAIL_SERVER'] = 'mail.privateemail.com'  # ✅ Namecheap SMTP
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True   # ✅ TLS on 587
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = 'info@globalriseblockchain.online'
app.config['MAIL_PASSWORD'] = 'fZN2hhQA@U*=.MP'  # ⚠️ Move this into .env for security
app.config['MAIL_DEFAULT_SENDER'] = ('Global Rise Blockchain', 'info@globalriseblockchain.online')

mail = Mail(app)

# ----------------- Helper -----------------
def get_user(username):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE username = ?', (username,))
    user = c.fetchone()
    conn.close()
    return user

# ----------------- Routes -----------------
@app.route('/')
def landing_page():
    return render_template('home.html')

@app.route('/recover')
def recover():
    return render_template('recover.html')

@app.route('/support')
def support():
    return render_template('support.html')

@app.route('/payment')
def payment():
    return render_template('payment.html')

@app.route('/404')
def page_404():
    return render_template('404.html')

# ----------------- Login -----------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username == 'admin' and password == 'admin123':
            session['user'] = 'admin'
            return redirect('/admin')

        user = get_user(username)
        if user and user[2] == password:
            session['user'] = username
            return redirect('/dashboard')
        else:
            return 'Invalid login'

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/login')

# ----------------- Register -----------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        phone = request.form['phone']
        address = request.form['address']

        if username == 'admin':
            return 'Username "admin" is reserved.'

        try:
            conn = sqlite3.connect('database.db')
            c = conn.cursor()
            c.execute('''
                INSERT INTO users 
                (username, password, first_name, last_name, email, phone, address)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (username, password, first_name, last_name, email, phone, address))
            conn.commit()
            conn.close()
            return redirect('/login')
        except:
            return 'User already exists or error occurred.'

    return render_template('register.html')

# ----------------- Dashboard -----------------
@app.route('/dashboard')
def dashboard():
    if 'user' not in session or session['user'] == 'admin':
        return redirect('/login')

    user = get_user(session['user'])
    return render_template('dashboard.html', username=user[1], balance=user[8])

# ----------------- Withdraw -----------------
# ----------------- Withdraw -----------------
@app.route('/withdraw', methods=["GET", "POST"])
def withdraw():
    if 'user' not in session or session['user'] == 'admin':
        return redirect('/login')

    if request.method == "POST":
        fullname = request.form.get("fullname")
        account_number = request.form.get("account_number")
        bank_name = request.form.get("bank_name")
        amount = request.form.get("amount")
        user_email = request.form.get("email")  # ✅ Now coming from form

        # ✅ Validate email
        if not user_email or "@" not in user_email:
            return "❌ Invalid email address. Please enter a valid email."

        # --- Send mail to Admin ---
        try:
            admin_msg = Message(
                subject="🔔 New Withdrawal Request",
                recipients=["benefactoredoho@gmail.com"],  # Admin inbox
                body=f"""
Dear Admin,

A new withdrawal request has been submitted.

• Name: {fullname}
• Email: {user_email}
• Account Number: {account_number}
• Bank Name: {bank_name}
• Amount: {amount}

Please review and process this request promptly.

Regards,
Global Rise Blockchain System
"""
            )
            mail.send(admin_msg)

            # --- Send confirmation to User ---
            user_msg = Message(
                subject="✅ Withdrawal Request Received",
                recipients=[user_email],
                body=f"""
Dear {fullname},

We have received your withdrawal request with the following details:

• Account Number: {account_number}
• Bank Name: {bank_name}
• Amount: {amount}

Our team is reviewing your request.
You will be notified once the transaction has been processed.

Best regards,  
Support Team  
Global Rise Blockchain
"""
            )
            mail.send(user_msg)

        except Exception as e:
            return f"⚠️ Mail sending failed: {str(e)}"

        return redirect(url_for("next"))

    return render_template("withdraw.html", message="Welcome to the Withdraw Page")

# ----------------- Admin -----------------
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if session.get('user') != 'admin':
        return redirect('/login')

    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    if request.method == 'POST':
        user_id = request.form['user_id']
        amount = float(request.form['amount'])
        action = request.form['action']

        if action == "send":
            c.execute('UPDATE users SET balance = balance + ? WHERE id = ?', (amount, user_id))
        elif action == "withdraw":
            c.execute('UPDATE users SET balance = balance - ? WHERE id = ?', (amount, user_id))

        conn.commit()

    c.execute('SELECT id, username, balance FROM users')
    users = c.fetchall()
    conn.close()
    return render_template('admin.html', users=users)

# ----------------- Next Page -----------------
@app.route('/next')
def next():
    return render_template('next.html')

# ----------------- Run -----------------
# Only run this block when running locally
# if __name__ == '__main__':
#     app.run(debug=True)
