from flask import Flask, render_template, request, redirect, url_for, send_from_directory, jsonify, session, flash
import sqlite3
import os
from datetime import datetime, timedelta
import json
import hashlib
import secrets

app = Flask(__name__, static_folder='static')

# Configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or secrets.token_hex(16)
app.config['DATABASE_PATH'] = os.environ.get('DATABASE_PATH') or 'data'

# Database files
def get_main_db_file():
    """Get the main database file path"""
    db_path = f"{app.config['DATABASE_PATH']}/main.db"
    print(f"DEBUG: Database path: {db_path}")
    print(f"DEBUG: DATABASE_PATH config: {app.config['DATABASE_PATH']}")
    return db_path

def get_user_db_file(username):
    """Get the database file for a specific user"""
    return f"{app.config['DATABASE_PATH']}/{username}_budget.db"

def init_main_db():
    """Initialize the main database for user management"""
    import os
    
    main_db_file = get_main_db_file()
    
    print(f"DEBUG: Initializing main database at: {main_db_file}")
    
    # Ensure data directory exists
    os.makedirs(os.path.dirname(main_db_file), exist_ok=True)
    
    conn = sqlite3.connect(main_db_file)
    c = conn.cursor()
    
    # Create users table
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_date TEXT DEFAULT CURRENT_DATE
        )
    ''')
    
    print(f"DEBUG: Users table created/verified successfully")
    
    conn.commit()
    conn.close()

# Ensure database exists and has the right table
def init_db(username=None):
    if username is None:
        return
    
    import os
    db_file = get_user_db_file(username)
    
    # Ensure data directory exists
    os.makedirs(os.path.dirname(db_file), exist_ok=True)
    
    conn = sqlite3.connect(db_file)
    c = conn.cursor()
    
    # Check if transactions table exists
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='transactions'")
    table_exists = c.fetchone()
    
    if not table_exists:
        # Create new table with type column
        c.execute('''
            CREATE TABLE transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                description TEXT,
                type TEXT DEFAULT 'expense'
            )
        ''')
    else:
        # Check if type column exists
        c.execute("PRAGMA table_info(transactions)")
        columns = [column[1] for column in c.fetchall()]
        
        if 'type' not in columns:
            # Add type column to existing table
            c.execute('ALTER TABLE transactions ADD COLUMN type TEXT DEFAULT "expense"')
    
    # Check if expected_expenses table exists
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='expected_expenses'")
    expected_expenses_table_exists = c.fetchone()
    
    if not expected_expenses_table_exists:
        # Create expected_expenses table
        c.execute('''
            CREATE TABLE expected_expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                amount REAL NOT NULL,
                month_year TEXT NOT NULL,
                is_template BOOLEAN DEFAULT 0,
                template_name TEXT,
                created_date TEXT DEFAULT CURRENT_DATE
            )
        ''')
    
    # Check if budget_templates table exists
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='budget_templates'")
    budget_templates_table_exists = c.fetchone()
    
    if not budget_templates_table_exists:
        # Create budget_templates table
        c.execute('''
            CREATE TABLE budget_templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT,
                created_date TEXT DEFAULT CURRENT_DATE
            )
        ''')
        
        # Insert default template
        c.execute('INSERT INTO budget_templates (name, description) VALUES (?, ?)', 
                  ('Default Monthly Budget', 'Standard monthly budget template'))
    
    # Check if budgets table exists (for backward compatibility)
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='budgets'")
    budgets_table_exists = c.fetchone()
    
    if budgets_table_exists:
        # Migrate old budgets to expected_expenses
        c.execute('SELECT category, monthly_limit FROM budgets')
        old_budgets = c.fetchall()
        
        for budget in old_budgets:
            c.execute('''
                INSERT INTO expected_expenses (category, amount, month_year, is_template, template_name)
                VALUES (?, ?, ?, ?, ?)
            ''', (budget[0], budget[1], datetime.now().strftime('%Y-%m'), 1, 'Default Monthly Budget'))
        
        # Drop old budgets table
        c.execute('DROP TABLE budgets')
    
    # Check if categories table exists
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='categories'")
    categories_table_exists = c.fetchone()
    
    if not categories_table_exists:
        # Create categories table
        c.execute('''
            CREATE TABLE categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                type TEXT NOT NULL DEFAULT 'expense',
                created_date TEXT DEFAULT CURRENT_DATE
            )
        ''')
        
        # Insert default categories
        default_expense_categories = ['Food', 'Transport', 'Shopping', 'Bills', 'Entertainment', 'Health', 'Education', 'Housing']
        default_income_categories = ['Salary', 'Freelance', 'Investment', 'Business', 'Gift', 'Other']
        
        for category in default_expense_categories:
            c.execute('INSERT INTO categories (name, type) VALUES (?, ?)', (category, 'expense'))
        
        for category in default_income_categories:
            c.execute('INSERT INTO categories (name, type) VALUES (?, ?)', (category, 'income'))
    
    conn.commit()
    conn.close()

def hash_password(password):
    """Hash a password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def login_required(f):
    """Decorator to require login for routes"""
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Ensure main database directory exists and initialize database
        import os
        main_db_file = get_main_db_file()
        os.makedirs(os.path.dirname(main_db_file), exist_ok=True)
        
        # Initialize main database (creates users table if it doesn't exist)
        init_main_db()
        
        conn = sqlite3.connect(main_db_file)
        c = conn.cursor()
        c.execute('SELECT password_hash FROM users WHERE username = ?', (username,))
        result = c.fetchone()
        conn.close()
        
        if result and result[0] == hash_password(password):
            session['username'] = username
            # Initialize user's database if it doesn't exist
            init_db(username)
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('register.html')
        
        if len(username) < 3:
            flash('Username must be at least 3 characters long', 'error')
            return render_template('register.html')
        
        if len(password) < 6:
            flash('Password must be at least 6 characters long', 'error')
            return render_template('register.html')
        
        # Ensure main database directory exists and initialize database
        import os
        main_db_file = get_main_db_file()
        os.makedirs(os.path.dirname(main_db_file), exist_ok=True)
        
        # Initialize main database (creates users table if it doesn't exist)
        init_main_db()
        
        conn = sqlite3.connect(main_db_file)
        c = conn.cursor()
        
        try:
            c.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)', 
                      (username, hash_password(password)))
            conn.commit()
            conn.close()
            
            # Initialize user's database
            init_db(username)
            
            session['username'] = username
            flash('Registration successful! Welcome to Budget Planner!', 'success')
            return redirect(url_for('index'))
        except sqlite3.IntegrityError:
            conn.close()
            flash('Username already exists', 'error')
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('You have been logged out', 'info')
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    db_file = get_user_db_file(session['username'])
    conn = sqlite3.connect(db_file)
    c = conn.cursor()
    
    # Get recent transactions (last 10)
    c.execute('SELECT id, date, amount, category, description, type FROM transactions ORDER BY date DESC LIMIT 10')
    recent_transactions = c.fetchall()
    
    # Get summary stats
    c.execute('SELECT SUM(amount) FROM transactions WHERE type = "income"')
    total_income = c.fetchone()[0] or 0
    
    c.execute('SELECT SUM(amount) FROM transactions WHERE type = "expense"')
    total_expenses = c.fetchone()[0] or 0
    
    # Get expected expenses for current month
    current_month = datetime.now().strftime('%Y-%m')
    c.execute('''
        SELECT category, amount 
        FROM expected_expenses 
        WHERE month_year = ? AND is_template = 0
    ''', (current_month,))
    expected_expenses = c.fetchall()
    
    # Calculate spendable money
    total_expected = sum(expense[1] for expense in expected_expenses)
    spendable_money = total_income - total_expected - total_expenses
    
    # Get expected vs actual spending for current month
    c.execute('''
        SELECT e.category, e.amount, COALESCE(SUM(t.amount), 0) as spent
        FROM expected_expenses e
        LEFT JOIN transactions t ON e.category = t.category 
            AND strftime('%Y-%m', t.date) = ? 
            AND t.type = 'expense'
        WHERE e.month_year = ? AND e.is_template = 0
        GROUP BY e.category, e.amount
    ''', (current_month, current_month))
    expected_vs_actual = c.fetchall()
    
    # Get monthly data for charts
    c.execute('''
        SELECT strftime('%Y-%m', date) as month, 
               SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END) as income,
               SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END) as expenses
        FROM transactions 
        WHERE date >= date('now', '-6 months')
        GROUP BY strftime('%Y-%m', date)
        ORDER BY month DESC
    ''')
    monthly_data = c.fetchall()
    
    # Get category breakdown
    c.execute('''
        SELECT category, SUM(amount) as total
        FROM transactions 
        WHERE type = 'expense'
        GROUP BY category 
        ORDER BY total DESC
        LIMIT 5
    ''')
    category_data = c.fetchall()
    
    conn.close()
    
    return render_template('index.html', 
                         recent_transactions=recent_transactions,
                         total_income=total_income,
                         total_expenses=total_expenses,
                         balance=total_income - total_expenses,
                         spendable_money=spendable_money,
                         total_expected=total_expected,
                         expected_vs_actual=expected_vs_actual,
                         monthly_data=monthly_data,
                         category_data=category_data)

@app.route('/add', methods=['GET', 'POST'])
@login_required
def add_transaction():
    if request.method == 'POST':
        date = request.form['date']
        amount = request.form['amount']
        category = request.form['category']
        description = request.form['description']
        transaction_type = request.form['type']
        db_file = get_user_db_file(session['username'])
        conn = sqlite3.connect(db_file)
        c = conn.cursor()
        c.execute('INSERT INTO transactions (date, amount, category, description, type) VALUES (?, ?, ?, ?, ?)',
                  (date, amount, category, description, transaction_type))
        conn.commit()
        conn.close()
        return redirect(url_for('index'))
    
    today = datetime.now().strftime('%Y-%m-%d')
    return render_template('add_transaction.html', today=today)

@app.route('/delete/<int:transaction_id>', methods=['POST'])
@login_required
def delete_transaction(transaction_id):
    db_file = get_user_db_file(session['username'])
    conn = sqlite3.connect(db_file)
    c = conn.cursor()
    c.execute('DELETE FROM transactions WHERE id = ?', (transaction_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/expected_expenses')
@login_required
def expected_expenses():
    db_file = get_user_db_file(session['username'])
    conn = sqlite3.connect(db_file)
    c = conn.cursor()
    
    # Get current month
    current_month = datetime.now().strftime('%Y-%m')
    
    # Get expected expenses for current month
    c.execute('''
        SELECT id, category, amount 
        FROM expected_expenses 
        WHERE month_year = ? AND is_template = 0
        ORDER BY category
    ''', (current_month,))
    expected_expenses = c.fetchall()
    
    # Get available templates
    c.execute('SELECT id, name, description FROM budget_templates ORDER BY name')
    templates = c.fetchall()
    
    conn.close()
    return render_template('expected_expenses.html', 
                         expected_expenses=expected_expenses,
                         templates=templates,
                         current_month=current_month)

@app.route('/add_expected_expense', methods=['GET', 'POST'])
@login_required
def add_expected_expense():
    if request.method == 'POST':
        category = request.form['category']
        amount = request.form['amount']
        month_year = request.form['month_year']
        db_file = get_user_db_file(session['username'])
        conn = sqlite3.connect(db_file)
        c = conn.cursor()
        c.execute('INSERT INTO expected_expenses (category, amount, month_year) VALUES (?, ?, ?)',
                  (category, amount, month_year))
        conn.commit()
        conn.close()
        return redirect(url_for('expected_expenses'))
    
    # Get available categories
    db_file = get_user_db_file(session['username'])
    conn = sqlite3.connect(db_file)
    c = conn.cursor()
    c.execute('SELECT name FROM categories WHERE type = "expense" ORDER BY name')
    categories = [row[0] for row in c.fetchall()]
    conn.close()
    
    return render_template('add_expected_expense.html', categories=categories)

@app.route('/delete_expected_expense/<int:expense_id>', methods=['POST'])
@login_required
def delete_expected_expense(expense_id):
    db_file = get_user_db_file(session['username'])
    conn = sqlite3.connect(db_file)
    c = conn.cursor()
    c.execute('DELETE FROM expected_expenses WHERE id = ?', (expense_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('expected_expenses'))

@app.route('/apply_template/<int:template_id>', methods=['POST'])
@login_required
def apply_template(template_id):
    db_file = get_user_db_file(session['username'])
    conn = sqlite3.connect(db_file)
    c = conn.cursor()
    
    # Get template name
    c.execute('SELECT name FROM budget_templates WHERE id = ?', (template_id,))
    template_name = c.fetchone()[0]
    
    # Get template expenses
    c.execute('''
        SELECT category, amount 
        FROM expected_expenses 
        WHERE template_name = ? AND is_template = 1
    ''', (template_name,))
    template_expenses = c.fetchall()
    
    # Get target month
    target_month = request.form.get('target_month', datetime.now().strftime('%Y-%m'))
    
    # Apply template to target month
    for expense in template_expenses:
        c.execute('''
            INSERT OR REPLACE INTO expected_expenses (category, amount, month_year, is_template, template_name)
            VALUES (?, ?, ?, 0, ?)
        ''', (expense[0], expense[1], target_month, template_name))
    
    conn.commit()
    conn.close()
    return redirect(url_for('expected_expenses'))

@app.route('/templates')
@login_required
def templates():
    db_file = get_user_db_file(session['username'])
    conn = sqlite3.connect(db_file)
    c = conn.cursor()
    c.execute('SELECT id, name, description FROM budget_templates ORDER BY name')
    templates = c.fetchall()
    conn.close()
    return render_template('templates.html', templates=templates)

@app.route('/add_template', methods=['GET', 'POST'])
@login_required
def add_template():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        db_file = get_user_db_file(session['username'])
        conn = sqlite3.connect(db_file)
        c = conn.cursor()
        try:
            c.execute('INSERT INTO budget_templates (name, description) VALUES (?, ?)', (name, description))
            template_id = c.lastrowid
            
            # Get current month's expected expenses and save as template
            current_month = datetime.now().strftime('%Y-%m')
            c.execute('''
                SELECT category, amount 
                FROM expected_expenses 
                WHERE month_year = ? AND is_template = 0
            ''', (current_month,))
            current_expenses = c.fetchall()
            
            for expense in current_expenses:
                c.execute('''
                    INSERT INTO expected_expenses (category, amount, month_year, is_template, template_name)
                    VALUES (?, ?, ?, 1, ?)
                ''', (expense[0], expense[1], current_month, name))
            
            conn.commit()
            conn.close()
            return redirect(url_for('templates'))
        except sqlite3.IntegrityError:
            conn.close()
            return "Template name already exists!", 400
    
    return render_template('add_template.html')

@app.route('/delete_template/<int:template_id>', methods=['POST'])
@login_required
def delete_template(template_id):
    db_file = get_user_db_file(session['username'])
    conn = sqlite3.connect(db_file)
    c = conn.cursor()
    
    # Get template name first
    c.execute('SELECT name FROM budget_templates WHERE id = ?', (template_id,))
    template_name = c.fetchone()[0]
    
    # Delete template expenses
    c.execute('DELETE FROM expected_expenses WHERE template_name = ?', (template_name,))
    
    # Delete template
    c.execute('DELETE FROM budget_templates WHERE id = ?', (template_id,))
    
    conn.commit()
    conn.close()
    return redirect(url_for('templates'))

@app.route('/categories')
@login_required
def categories():
    db_file = get_user_db_file(session['username'])
    conn = sqlite3.connect(db_file)
    c = conn.cursor()
    c.execute('SELECT id, name, type FROM categories ORDER BY type, name')
    categories = c.fetchall()
    conn.close()
    return render_template('categories.html', categories=categories)

@app.route('/add_category', methods=['GET', 'POST'])
@login_required
def add_category():
    if request.method == 'POST':
        name = request.form['name']
        category_type = request.form['type']
        db_file = get_user_db_file(session['username'])
        conn = sqlite3.connect(db_file)
        c = conn.cursor()
        try:
            c.execute('INSERT INTO categories (name, type) VALUES (?, ?)', (name, category_type))
            conn.commit()
            conn.close()
            return redirect(url_for('categories'))
        except sqlite3.IntegrityError:
            conn.close()
            return "Category already exists!", 400
    
    return render_template('add_category.html')

@app.route('/delete_category/<int:category_id>', methods=['POST'])
@login_required
def delete_category(category_id):
    db_file = get_user_db_file(session['username'])
    conn = sqlite3.connect(db_file)
    c = conn.cursor()
    c.execute('DELETE FROM categories WHERE id = ?', (category_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('categories'))

@app.route('/transactions')
@login_required
def all_transactions():
    db_file = get_user_db_file(session['username'])
    conn = sqlite3.connect(db_file)
    c = conn.cursor()
    
    # Get filter parameters
    month_filter = request.args.get('month', '')
    week_filter = request.args.get('week', '')
    category_filter = request.args.get('category', '')
    type_filter = request.args.get('type', '')
    
    # Build query with filters
    query = '''
        SELECT id, date, amount, category, description, type 
        FROM transactions 
        WHERE 1=1
    '''
    params = []
    
    if month_filter:
        query += ' AND strftime("%Y-%m", date) = ?'
        params.append(month_filter)
    
    if week_filter:
        query += ' AND strftime("%Y-W%W", date) = ?'
        params.append(week_filter)
    
    if category_filter:
        query += ' AND category = ?'
        params.append(category_filter)
    
    if type_filter:
        query += ' AND type = ?'
        params.append(type_filter)
    
    query += ' ORDER BY date DESC'
    
    c.execute(query, params)
    transactions = c.fetchall()
    
    # Get available months and weeks for filters
    c.execute('SELECT DISTINCT strftime("%Y-%m", date) as month FROM transactions ORDER BY month DESC')
    available_months = [row[0] for row in c.fetchall()]
    
    c.execute('SELECT DISTINCT strftime("%Y-W%W", date) as week FROM transactions ORDER BY week DESC')
    available_weeks = [row[0] for row in c.fetchall()]
    
    c.execute('SELECT DISTINCT category FROM transactions ORDER BY category')
    available_categories = [row[0] for row in c.fetchall()]
    
    conn.close()
    
    return render_template('all_transactions.html', 
                         transactions=transactions,
                         available_months=available_months,
                         available_weeks=available_weeks,
                         available_categories=available_categories,
                         current_filters={
                             'month': month_filter,
                             'week': week_filter,
                             'category': category_filter,
                             'type': type_filter
                         })

@app.route('/api/categories')
@login_required
def get_categories():
    db_file = get_user_db_file(session['username'])
    conn = sqlite3.connect(db_file)
    c = conn.cursor()
    category_type = request.args.get('type', 'expense')
    c.execute('SELECT name FROM categories WHERE type = ? ORDER BY name', (category_type,))
    categories = [row[0] for row in c.fetchall()]
    conn.close()
    return jsonify(categories)

@app.route('/api/chart-data')
@login_required
def chart_data():
    db_file = get_user_db_file(session['username'])
    conn = sqlite3.connect(db_file)
    c = conn.cursor()
    
    # Get monthly data for charts
    c.execute('''
        SELECT strftime('%Y-%m', date) as month, 
               SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END) as income,
               SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END) as expenses
        FROM transactions 
        WHERE date >= date('now', '-6 months')
        GROUP BY strftime('%Y-%m', date)
        ORDER BY month
    ''')
    monthly_data = c.fetchall()
    
    # Get category breakdown
    c.execute('''
        SELECT category, SUM(amount) as total
        FROM transactions 
        WHERE type = 'expense'
        GROUP BY category 
        ORDER BY total DESC
        LIMIT 8
    ''')
    category_data = c.fetchall()
    
    # Get expected vs actual data
    current_month = datetime.now().strftime('%Y-%m')
    c.execute('''
        SELECT e.category, e.amount, COALESCE(SUM(t.amount), 0) as spent
        FROM expected_expenses e
        LEFT JOIN transactions t ON e.category = t.category 
            AND strftime('%Y-%m', t.date) = ?
            AND t.type = 'expense'
        WHERE e.month_year = ? AND e.is_template = 0
        GROUP BY e.category, e.amount
    ''', (current_month, current_month))
    expected_data = c.fetchall()
    
    # Get weekly spending trend
    c.execute('''
        SELECT strftime('%Y-W%W', date) as week,
               SUM(amount) as amount
        FROM transactions 
        WHERE type = 'expense' 
        AND date >= date('now', '-8 weeks')
        GROUP BY strftime('%Y-W%W', date)
        ORDER BY week
    ''')
    weekly_data = c.fetchall()
    
    # Calculate savings rate
    c.execute('SELECT SUM(amount) FROM transactions WHERE type = "income"')
    total_income = c.fetchone()[0] or 0
    
    c.execute('SELECT SUM(amount) FROM transactions WHERE type = "expense"')
    total_expenses = c.fetchone()[0] or 0
    
    savings_rate = 0
    if total_income > 0:
        savings_rate = ((total_income - total_expenses) / total_income) * 100
    
    # Get category spending over time
    c.execute('''
        SELECT strftime('%Y-%m', date) as month,
               category,
               SUM(amount) as amount
        FROM transactions 
        WHERE type = 'expense'
        AND date >= date('now', '-6 months')
        GROUP BY strftime('%Y-%m', date), category
        ORDER BY month, amount DESC
    ''')
    category_trends_raw = c.fetchall()
    
    # Process category trends data
    category_trends = []
    if category_trends_raw:
        months = sorted(list(set(row[0] for row in category_trends_raw)))
        categories = list(set(row[1] for row in category_trends_raw))
        
        for month in months:
            month_data = {'month': month, 'categories': categories, 'amounts': []}
            for category in categories:
                amount = next((row[2] for row in category_trends_raw if row[0] == month and row[1] == category), 0)
                month_data['amounts'].append(amount)
            category_trends.append(month_data)
    
    conn.close()
    
    return jsonify({
        'monthly': [{'month': row[0], 'income': row[1], 'expenses': row[2]} for row in monthly_data],
        'categories': [{'category': row[0], 'total': row[1]} for row in category_data],
        'expected': [{'category': row[0], 'limit': row[1], 'spent': row[2]} for row in expected_data],
        'weekly': [{'week': row[0], 'amount': row[1]} for row in weekly_data],
        'savings': {'rate': savings_rate},
        'categoryTrends': category_trends
    })

if __name__ == '__main__':
    init_main_db()  # Initialize the main database for user management
    app.run(debug=True) 