from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import psycopg2
import psycopg2.extras
from datetime import datetime, timedelta
import os
import hashlib
import secrets
from config import Config

app = Flask(__name__, static_folder='static')

# Configuration
app.config.from_object(Config)

# Add custom headers to suppress warnings
@app.after_request
def add_security_headers(response):
    """Add security headers and suppress deprecated warnings"""
    response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
    return response

# Database connection function
def get_db_connection():
    """Get PostgreSQL database connection"""
    try:
        # For Railway deployment
        if os.getenv('DATABASE_URL'):
            conn = psycopg2.connect(os.getenv('DATABASE_URL'))
        else:
            # For local development
            conn = psycopg2.connect(
                host=os.getenv('DB_HOST', 'localhost'),
                database=os.getenv('DB_NAME', 'budget_planner'),
                user=os.getenv('DB_USER', 'postgres'),
                password=os.getenv('DB_PASSWORD', ''),
                port=os.getenv('DB_PORT', '5432')
            )
        return conn
    except Exception as e:
        print(f"Database connection error: {e}")
        return None

def init_db():
    """Initialize PostgreSQL database tables"""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cur = conn.cursor()
        
        # Create users table
        cur.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create transactions table
        cur.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id),
                date DATE NOT NULL,
                amount DECIMAL(10,2) NOT NULL,
                category VARCHAR(100) NOT NULL,
                description TEXT,
                type VARCHAR(20) DEFAULT 'expense',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create categories table
        cur.execute('''
            CREATE TABLE IF NOT EXISTS categories (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id),
                name VARCHAR(100) NOT NULL,
                type VARCHAR(20) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create expected_expenses table
        cur.execute('''
            CREATE TABLE IF NOT EXISTS expected_expenses (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id),
                category VARCHAR(100) NOT NULL,
                amount DECIMAL(10,2) NOT NULL,
                month_year VARCHAR(7) NOT NULL,
                is_template BOOLEAN DEFAULT FALSE,
                template_name VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create budget_templates table
        cur.execute('''
            CREATE TABLE IF NOT EXISTS budget_templates (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id),
                name VARCHAR(100) NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        cur.close()
        conn.close()
        print("✅ Database tables created successfully")
        return True
        
    except Exception as e:
        print(f"❌ Database initialization error: {e}")
        return False

def hash_password(password):
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def login_required(f):
    """Decorator to require login"""
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            flash('Please log in to access this page', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@app.route('/')
@login_required
def index():
    """Home page with dashboard"""
    conn = get_db_connection()
    if not conn:
        flash('Database connection error', 'error')
        return render_template('index.html',
                           recent_transactions=[],
                           total_income=0,
                           total_expenses=0,
                           monthly_data=[],
                           category_data=[],
                           spendable_money=0,
                           balance=0,
                           total_expected=0)
    
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # Get user ID
        cur.execute('SELECT id FROM users WHERE username = %s', (session['username'],))
        user = cur.fetchone()
        if not user:
            flash('User not found', 'error')
            return redirect(url_for('logout'))
        
        user_id = user['id']
        
        # Get current month data
        current_month = datetime.now().strftime('%Y-%m')
        
        # Recent transactions (last 5)
        cur.execute('''
            SELECT * FROM transactions 
            WHERE user_id = %s 
            ORDER BY date DESC, id DESC 
            LIMIT 5
        ''', (user_id,))
        recent_transactions = cur.fetchall()
        
        # Monthly totals
        cur.execute('''
            SELECT 
                SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END) as total_income,
                SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END) as total_expenses
            FROM transactions 
            WHERE user_id = %s AND DATE_TRUNC('month', date) = DATE_TRUNC('month', CURRENT_DATE)
        ''', (user_id,))
        totals = cur.fetchone()
        
        total_income = float(totals['total_income'] or 0)
        total_expenses = float(totals['total_expenses'] or 0)
        
        # Expected expenses for current month
        cur.execute('''
            SELECT SUM(amount) as total_expected
            FROM expected_expenses 
            WHERE user_id = %s AND month_year = %s AND is_template = FALSE
        ''', (user_id, current_month))
        expected_result = cur.fetchone()
        total_expected = float(expected_result['total_expected'] or 0)
        
        # Calculate spendable money
        spendable_money = total_income - total_expenses - total_expected
        
        # Calculate balance (income - expenses, without expected expenses)
        balance = total_income - total_expenses
        
        # Monthly data for charts (last 6 months)
        cur.execute('''
            SELECT 
                TO_CHAR(date, 'YYYY-MM') as month,
                SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END) as income,
                SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END) as expenses
            FROM transactions 
            WHERE user_id = %s AND date >= CURRENT_DATE - INTERVAL '6 months'
            GROUP BY TO_CHAR(date, 'YYYY-MM')
            ORDER BY month
        ''', (user_id,))
        monthly_data = cur.fetchall()
        
        # Category data for current month
        cur.execute('''
            SELECT category, SUM(amount) as total
            FROM transactions 
            WHERE user_id = %s AND type = 'expense' 
            AND DATE_TRUNC('month', date) = DATE_TRUNC('month', CURRENT_DATE)
            GROUP BY category
            ORDER BY total DESC
        ''', (user_id,))
        category_data = cur.fetchall()
        
        cur.close()
        conn.close()
        
        return render_template('index.html',
                           recent_transactions=recent_transactions,
                           total_income=total_income,
                           total_expenses=total_expenses,
                           monthly_data=monthly_data,
                           category_data=category_data,
                           spendable_money=spendable_money,
                           balance=balance,
                           total_expected=total_expected)
                           
    except Exception as e:
        print(f"Error in index route: {e}")
        flash('Error loading dashboard', 'error')
        return render_template('index.html',
                           recent_transactions=[],
                           total_income=0,
                           total_expenses=0,
                           monthly_data=[],
                           category_data=[],
                           spendable_money=0,
                           balance=0,
                           total_expected=0)

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        if not conn:
            flash('Database connection error', 'error')
            return render_template('login.html')
        
        try:
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute('SELECT * FROM users WHERE username = %s', (username,))
            user = cur.fetchone()
            
            if user and user['password_hash'] == hash_password(password):
                session['username'] = username
                flash('Login successful!', 'success')
                return redirect(url_for('index'))
            else:
                flash('Invalid username or password', 'error')
                
        except Exception as e:
            print(f"Login error: {e}")
            flash('Login error', 'error')
        finally:
            cur.close()
            conn.close()
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Registration page"""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('register.html')
        
        conn = get_db_connection()
        if not conn:
            flash('Database connection error', 'error')
            return render_template('register.html')
        
        try:
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            
            # Check if username exists
            cur.execute('SELECT id FROM users WHERE username = %s', (username,))
            if cur.fetchone():
                flash('Username already exists', 'error')
                return render_template('register.html')
            
            # Create new user
            cur.execute('''
                INSERT INTO users (username, password_hash) 
                VALUES (%s, %s) RETURNING id
            ''', (username, hash_password(password)))
            
            user_id = cur.fetchone()['id']
            
            # Insert default categories for the user
            default_categories = [
                ('Salary', 'income'),
                ('Freelance', 'income'),
                ('Investment', 'income'),
                ('Food', 'expense'),
                ('Transport', 'expense'),
                ('Shopping', 'expense'),
                ('Bills', 'expense'),
                ('Entertainment', 'expense'),
                ('Healthcare', 'expense')
            ]
            
            for category_name, category_type in default_categories:
                cur.execute('''
                    INSERT INTO categories (user_id, name, type) 
                    VALUES (%s, %s, %s)
                ''', (user_id, category_name, category_type))
            
            conn.commit()
            cur.close()
            conn.close()
            
            session['username'] = username
            flash('Registration successful!', 'success')
            return redirect(url_for('index'))
            
        except Exception as e:
            print(f"Registration error: {e}")
            flash('Registration error', 'error')
            conn.rollback()
            cur.close()
            conn.close()
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    """Logout user"""
    session.pop('username', None)
    flash('Logged out successfully', 'success')
    return redirect(url_for('login'))

@app.route('/add', methods=['GET', 'POST'])
@login_required
def add_transaction():
    """Add transaction page"""
    if request.method == 'POST':
        date = request.form['date']
        amount = float(request.form['amount'])
        category = request.form['category']
        description = request.form['description']
        transaction_type = request.form.get('type', 'expense')
        
        conn = get_db_connection()
        if not conn:
            flash('Database connection error', 'error')
            return render_template('add_transaction.html')
        
        try:
            cur = conn.cursor()
            
            # Get user ID
            cur.execute('SELECT id FROM users WHERE username = %s', (session['username'],))
            user_id = cur.fetchone()[0]
            
            # Insert transaction
            cur.execute('''
                INSERT INTO transactions (user_id, date, amount, category, description, type)
                VALUES (%s, %s, %s, %s, %s, %s)
            ''', (user_id, date, amount, category, description, transaction_type))
            
            conn.commit()
            cur.close()
            conn.close()
            
            flash('Transaction added successfully!', 'success')
            return redirect(url_for('index'))
            
        except Exception as e:
            print(f"Add transaction error: {e}")
            flash('Error adding transaction', 'error')
            conn.rollback()
            cur.close()
            conn.close()
    
    return render_template('add_transaction.html')

@app.route('/api/categories')
@login_required
def get_categories():
    """API endpoint to get categories by type"""
    category_type = request.args.get('type', 'expense')
    
    conn = get_db_connection()
    if not conn:
        return jsonify([])
    
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # Get user ID
        cur.execute('SELECT id FROM users WHERE username = %s', (session['username'],))
        user_id = cur.fetchone()[0]
        
        # Get categories by type
        cur.execute('''
            SELECT name FROM categories 
            WHERE user_id = %s AND type = %s 
            ORDER BY name
        ''', (user_id, category_type))
        
        categories = [row['name'] for row in cur.fetchall()]
        cur.close()
        conn.close()
        
        return jsonify(categories)
        
    except Exception as e:
        print(f"Get categories error: {e}")
        return jsonify([])

@app.route('/delete/<int:transaction_id>', methods=['POST'])
@login_required
def delete_transaction(transaction_id):
    """Delete a transaction"""
    conn = get_db_connection()
    if not conn:
        flash('Database connection error', 'error')
        return redirect(url_for('index'))
    
    try:
        cur = conn.cursor()
        
        # Get user ID
        cur.execute('SELECT id FROM users WHERE username = %s', (session['username'],))
        user_id = cur.fetchone()[0]
        
        # Delete transaction
        cur.execute('''
            DELETE FROM transactions 
            WHERE id = %s AND user_id = %s
        ''', (transaction_id, user_id))
        
        conn.commit()
        cur.close()
        conn.close()
        
        flash('Transaction deleted successfully!', 'success')
        return redirect(url_for('index'))
        
    except Exception as e:
        print(f"Delete transaction error: {e}")
        flash('Error deleting transaction', 'error')
        conn.rollback()
        cur.close()
        conn.close()
        return redirect(url_for('index'))

@app.route('/expected_expenses')
@login_required
def expected_expenses():
    """Expected expenses page"""
    conn = get_db_connection()
    if not conn:
        flash('Database connection error', 'error')
        return render_template('expected_expenses.html')
    
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # Get user ID
        cur.execute('SELECT id FROM users WHERE username = %s', (session['username'],))
        user_id = cur.fetchone()[0]
        
        # Get current month
        current_month = datetime.now().strftime('%Y-%m')
        
        # Get expected expenses for current month
        cur.execute('''
            SELECT * FROM expected_expenses 
            WHERE user_id = %s AND month_year = %s AND is_template = FALSE
            ORDER BY category
        ''', (user_id, current_month))
        expected_expenses = cur.fetchall()
        
        # Get templates
        cur.execute('''
            SELECT * FROM budget_templates 
            WHERE user_id = %s 
            ORDER BY name
        ''', (user_id,))
        templates = cur.fetchall()
        
        cur.close()
        conn.close()
        
        return render_template('expected_expenses.html',
                           expected_expenses=expected_expenses,
                           templates=templates,
                           current_month=current_month)
                           
    except Exception as e:
        print(f"Expected expenses error: {e}")
        flash('Error loading expected expenses', 'error')
        return render_template('expected_expenses.html')

@app.route('/add_expected_expense', methods=['GET', 'POST'])
@login_required
def add_expected_expense():
    """Add expected expense page"""
    if request.method == 'POST':
        category = request.form['category']
        amount = float(request.form['amount'])
        month_year = request.form['month_year']
        
        conn = get_db_connection()
        if not conn:
            flash('Database connection error', 'error')
            return render_template('add_expected_expense.html')
        
        try:
            cur = conn.cursor()
            
            # Get user ID
            cur.execute('SELECT id FROM users WHERE username = %s', (session['username'],))
            user_id = cur.fetchone()[0]
            
            # Insert expected expense
            cur.execute('''
                INSERT INTO expected_expenses (user_id, category, amount, month_year)
                VALUES (%s, %s, %s, %s)
            ''', (user_id, category, amount, month_year))
            
            conn.commit()
            cur.close()
            conn.close()
            
            flash('Expected expense added successfully!', 'success')
            return redirect(url_for('expected_expenses'))
            
        except Exception as e:
            print(f"Add expected expense error: {e}")
            flash('Error adding expected expense', 'error')
            conn.rollback()
            cur.close()
            conn.close()
    
    return render_template('add_expected_expense.html')

@app.route('/delete_expected_expense/<int:expense_id>', methods=['POST'])
@login_required
def delete_expected_expense(expense_id):
    """Delete an expected expense"""
    conn = get_db_connection()
    if not conn:
        flash('Database connection error', 'error')
        return redirect(url_for('expected_expenses'))
    
    try:
        cur = conn.cursor()
        
        # Get user ID
        cur.execute('SELECT id FROM users WHERE username = %s', (session['username'],))
        user_id = cur.fetchone()[0]
        
        # Delete expected expense
        cur.execute('''
            DELETE FROM expected_expenses 
            WHERE id = %s AND user_id = %s
        ''', (expense_id, user_id))
        
        conn.commit()
        cur.close()
        conn.close()
        
        flash('Expected expense deleted successfully!', 'success')
        return redirect(url_for('expected_expenses'))
        
    except Exception as e:
        print(f"Delete expected expense error: {e}")
        flash('Error deleting expected expense', 'error')
        conn.rollback()
        cur.close()
        conn.close()
        return redirect(url_for('expected_expenses'))

@app.route('/apply_template/<int:template_id>', methods=['POST'])
@login_required
def apply_template(template_id):
    """Apply a budget template to current month"""
    conn = get_db_connection()
    if not conn:
        flash('Database connection error', 'error')
        return redirect(url_for('expected_expenses'))
    
    try:
        cur = conn.cursor()
        
        # Get user ID
        cur.execute('SELECT id FROM users WHERE username = %s', (session['username'],))
        user_id = cur.fetchone()[0]
        
        # Get template name
        cur.execute('SELECT name FROM budget_templates WHERE id = %s AND user_id = %s', (template_id, user_id))
        template = cur.fetchone()
        if not template:
            flash('Template not found', 'error')
            return redirect(url_for('expected_expenses'))
        
        template_name = template[0]
        
        # Get template expenses
        cur.execute('''
            SELECT category, amount FROM expected_expenses 
            WHERE user_id = %s AND template_name = %s
        ''', (user_id, template_name))
        template_expenses = cur.fetchall()
        
        # Get current month
        current_month = datetime.now().strftime('%Y-%m')
        
        # Insert template expenses for current month
        for category, amount in template_expenses:
            cur.execute('''
                INSERT INTO expected_expenses (user_id, category, amount, month_year, is_template)
                VALUES (%s, %s, %s, %s, FALSE)
            ''', (user_id, category, amount, current_month))
        
        conn.commit()
        cur.close()
        conn.close()
        
        flash('Template applied successfully!', 'success')
        return redirect(url_for('expected_expenses'))
        
    except Exception as e:
        print(f"Apply template error: {e}")
        flash('Error applying template', 'error')
        conn.rollback()
        cur.close()
        conn.close()
        return redirect(url_for('expected_expenses'))

@app.route('/templates')
@login_required
def templates():
    """Budget templates page"""
    conn = get_db_connection()
    if not conn:
        flash('Database connection error', 'error')
        return render_template('templates.html')
    
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # Get user ID
        cur.execute('SELECT id FROM users WHERE username = %s', (session['username'],))
        user_id = cur.fetchone()[0]
        
        # Get templates
        cur.execute('''
            SELECT * FROM budget_templates 
            WHERE user_id = %s 
            ORDER BY name
        ''', (user_id,))
        templates = cur.fetchall()
        
        cur.close()
        conn.close()
        
        return render_template('templates.html', templates=templates)
        
    except Exception as e:
        print(f"Templates error: {e}")
        flash('Error loading templates', 'error')
        return render_template('templates.html')

@app.route('/add_template', methods=['GET', 'POST'])
@login_required
def add_template():
    """Add budget template page"""
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        
        conn = get_db_connection()
        if not conn:
            flash('Database connection error', 'error')
            return render_template('add_template.html')
        
        try:
            cur = conn.cursor()
            
            # Get user ID
            cur.execute('SELECT id FROM users WHERE username = %s', (session['username'],))
            user_id = cur.fetchone()[0]
            
            # Get current month's expected expenses
            current_month = datetime.now().strftime('%Y-%m')
            cur.execute('''
                SELECT category, amount FROM expected_expenses 
                WHERE user_id = %s AND month_year = %s AND is_template = FALSE
            ''', (user_id, current_month))
            current_expenses = cur.fetchall()
            
            if not current_expenses:
                flash('No expected expenses found for current month', 'error')
                return render_template('add_template.html')
            
            # Create template
            cur.execute('''
                INSERT INTO budget_templates (user_id, name, description)
                VALUES (%s, %s, %s) RETURNING id
            ''', (user_id, name, description))
            
            # Insert template expenses
            for category, amount in current_expenses:
                cur.execute('''
                    INSERT INTO expected_expenses (user_id, category, amount, month_year, is_template, template_name)
                    VALUES (%s, %s, %s, %s, TRUE, %s)
                ''', (user_id, category, amount, current_month, name))
            
            conn.commit()
            cur.close()
            conn.close()
            
            flash('Template created successfully!', 'success')
            return redirect(url_for('templates'))
            
        except Exception as e:
            print(f"Add template error: {e}")
            flash('Error creating template', 'error')
            conn.rollback()
            cur.close()
            conn.close()
    
    return render_template('add_template.html')

@app.route('/delete_template/<int:template_id>', methods=['POST'])
@login_required
def delete_template(template_id):
    """Delete a budget template"""
    conn = get_db_connection()
    if not conn:
        flash('Database connection error', 'error')
        return redirect(url_for('templates'))
    
    try:
        cur = conn.cursor()
        
        # Get user ID
        cur.execute('SELECT id FROM users WHERE username = %s', (session['username'],))
        user_id = cur.fetchone()[0]
        
        # Get template name
        cur.execute('SELECT name FROM budget_templates WHERE id = %s AND user_id = %s', (template_id, user_id))
        template = cur.fetchone()
        if not template:
            flash('Template not found', 'error')
            return redirect(url_for('templates'))
        
        template_name = template[0]
        
        # Delete template expenses
        cur.execute('''
            DELETE FROM expected_expenses 
            WHERE user_id = %s AND template_name = %s
        ''', (user_id, template_name))
        
        # Delete template
        cur.execute('''
            DELETE FROM budget_templates 
            WHERE id = %s AND user_id = %s
        ''', (template_id, user_id))
        
        conn.commit()
        cur.close()
        conn.close()
        
        flash('Template deleted successfully!', 'success')
        return redirect(url_for('templates'))
        
    except Exception as e:
        print(f"Delete template error: {e}")
        flash('Error deleting template', 'error')
        conn.rollback()
        cur.close()
        conn.close()
        return redirect(url_for('templates'))

@app.route('/categories')
@login_required
def categories():
    """Categories management page"""
    conn = get_db_connection()
    if not conn:
        flash('Database connection error', 'error')
        return render_template('categories.html')
    
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # Get user ID
        cur.execute('SELECT id FROM users WHERE username = %s', (session['username'],))
        user_result = cur.fetchone()
        if not user_result:
            flash('User not found', 'error')
            return redirect(url_for('logout'))
        user_id = user_result['id']
        
        # Get categories
        cur.execute('''
            SELECT * FROM categories 
            WHERE user_id = %s 
            ORDER BY type, name
        ''', (user_id,))
        categories = cur.fetchall()
        
        cur.close()
        conn.close()
        
        return render_template('categories.html', categories=categories)
        
    except Exception as e:
        print(f"Categories error: {e}")
        flash('Error loading categories', 'error')
        return render_template('categories.html')

@app.route('/add_category', methods=['GET', 'POST'])
@login_required
def add_category():
    """Add category page"""
    if request.method == 'POST':
        name = request.form['name']
        category_type = request.form['type']
        
        conn = get_db_connection()
        if not conn:
            flash('Database connection error', 'error')
            return render_template('add_category.html')
        
        try:
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            
            # Get user ID
            cur.execute('SELECT id FROM users WHERE username = %s', (session['username'],))
            user_result = cur.fetchone()
            if not user_result:
                flash('User not found', 'error')
                return redirect(url_for('logout'))
            user_id = user_result['id']
            
            # Insert category
            cur.execute('''
                INSERT INTO categories (user_id, name, type)
                VALUES (%s, %s, %s)
            ''', (user_id, name, category_type))
            
            conn.commit()
            cur.close()
            conn.close()
            
            flash('Category added successfully!', 'success')
            return redirect(url_for('categories'))
            
        except Exception as e:
            print(f"Add category error: {e}")
            flash('Error adding category', 'error')
            conn.rollback()
            cur.close()
            conn.close()
    
    return render_template('add_category.html')

@app.route('/delete_category/<int:category_id>', methods=['POST'])
@login_required
def delete_category(category_id):
    """Delete a category"""
    conn = get_db_connection()
    if not conn:
        flash('Database connection error', 'error')
        return redirect(url_for('categories'))
    
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # Get user ID
        cur.execute('SELECT id FROM users WHERE username = %s', (session['username'],))
        user_result = cur.fetchone()
        if not user_result:
            flash('User not found', 'error')
            return redirect(url_for('logout'))
        user_id = user_result['id']
        
        # Delete category
        cur.execute('''
            DELETE FROM categories 
            WHERE id = %s AND user_id = %s
        ''', (category_id, user_id))
        
        conn.commit()
        cur.close()
        conn.close()
        
        flash('Category deleted successfully!', 'success')
        return redirect(url_for('categories'))
        
    except Exception as e:
        print(f"Delete category error: {e}")
        flash('Error deleting category', 'error')
        conn.rollback()
        cur.close()
        conn.close()
        return redirect(url_for('categories'))

@app.route('/transactions')
@login_required
def all_transactions():
    """All transactions page with filters"""
    conn = get_db_connection()
    if not conn:
        flash('Database connection error', 'error')
        return render_template('all_transactions.html')
    
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # Get user ID
        cur.execute('SELECT id FROM users WHERE username = %s', (session['username'],))
        user_result = cur.fetchone()
        if not user_result:
            flash('User not found', 'error')
            return redirect(url_for('logout'))
        user_id = user_result['id']
        
        # Get filter parameters
        month_filter = request.args.get('month', '')
        week_filter = request.args.get('week', '')
        category_filter = request.args.get('category', '')
        type_filter = request.args.get('type', '')
        
        # Build query
        query = '''
            SELECT * FROM transactions 
            WHERE user_id = %s
        '''
        params = [user_id]
        
        if month_filter:
            query += ' AND DATE_TRUNC(\'month\', date) = DATE_TRUNC(\'month\', %s::date)'
            params.append(month_filter + '-01')
        
        if week_filter:
            query += ' AND DATE_TRUNC(\'week\', date) = DATE_TRUNC(\'week\', %s::date)'
            params.append(week_filter)
        
        if category_filter:
            query += ' AND category = %s'
            params.append(category_filter)
        
        if type_filter:
            query += ' AND type = %s'
            params.append(type_filter)
        
        query += ' ORDER BY date DESC, id DESC'
        
        cur.execute(query, params)
        transactions = cur.fetchall()
        
        # Get categories for filter
        cur.execute('''
            SELECT DISTINCT name FROM categories 
            WHERE user_id = %s 
            ORDER BY name
        ''', (user_id,))
        categories = [row['name'] for row in cur.fetchall()]
        
        # Get available months and weeks for filters
        cur.execute('''
            SELECT DISTINCT TO_CHAR(date, 'YYYY-MM') as month 
            FROM transactions 
            WHERE user_id = %s 
            ORDER BY month DESC
        ''', (user_id,))
        available_months = [row['month'] for row in cur.fetchall()]
        
        cur.execute('''
            SELECT DISTINCT TO_CHAR(date, 'YYYY-"W"IW') as week 
            FROM transactions 
            WHERE user_id = %s 
            ORDER BY week DESC
        ''', (user_id,))
        available_weeks = [row['week'] for row in cur.fetchall()]
        
        cur.execute('''
            SELECT DISTINCT category 
            FROM transactions 
            WHERE user_id = %s 
            ORDER BY category
        ''', (user_id,))
        available_categories = [row['category'] for row in cur.fetchall()]
        
        cur.close()
        conn.close()
        
        return render_template('all_transactions.html',
                           transactions=transactions,
                           categories=categories,
                           available_months=available_months,
                           available_weeks=available_weeks,
                           available_categories=available_categories,
                           month_filter=month_filter,
                           week_filter=week_filter,
                           category_filter=category_filter,
                           type_filter=type_filter,
                           current_filters={
                               'month': month_filter,
                               'week': week_filter,
                               'category': category_filter,
                               'type': type_filter
                           })
                           
    except Exception as e:
        print(f"All transactions error: {e}")
        flash('Error loading transactions', 'error')
        return render_template('all_transactions.html')

@app.route('/api/chart-data')
@login_required
def chart_data():
    """API endpoint for chart data"""
    conn = get_db_connection()
    if not conn:
        print("❌ Database connection failed in chart_data")
        return jsonify({})
    
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # Get user ID
        cur.execute('SELECT id FROM users WHERE username = %s', (session['username'],))
        user_result = cur.fetchone()
        if not user_result:
            print(f"❌ User not found: {session['username']}")
            return jsonify({})
        
        user_id = user_result['id']
        print(f"✅ User ID: {user_id}")
        
        # Monthly data for line chart
        cur.execute('''
            SELECT 
                TO_CHAR(date, 'YYYY-MM') as month,
                SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END) as income,
                SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END) as expenses
            FROM transactions 
            WHERE user_id = %s AND date >= CURRENT_DATE - INTERVAL '6 months'
            GROUP BY TO_CHAR(date, 'YYYY-MM')
            ORDER BY month
        ''', (user_id,))
        monthly_data = cur.fetchall()
        print(f"📊 Monthly data rows: {len(monthly_data)}")
        
        # Category data for doughnut chart
        cur.execute('''
            SELECT category, SUM(amount) as total
            FROM transactions 
            WHERE user_id = %s AND type = 'expense' 
            AND DATE_TRUNC('month', date) = DATE_TRUNC('month', CURRENT_DATE)
            GROUP BY category
            ORDER BY total DESC
        ''', (user_id,))
        category_data = cur.fetchall()
        print(f"📊 Category data rows: {len(category_data)}")
        
        # Create response data
        response_data = {
            'monthly': {
                'labels': [row['month'] for row in monthly_data],
                'income': [float(row['income'] or 0) for row in monthly_data],
                'expenses': [float(row['expenses'] or 0) for row in monthly_data]
            },
            'categories': {
                'labels': [row['category'] for row in category_data],
                'data': [float(row['total'] or 0) for row in category_data]
            }
        }
        
        print(f"📊 Response data: {response_data}")
        
        cur.close()
        conn.close()
        
        return jsonify(response_data)
        
    except Exception as e:
        print(f"❌ Chart data error: {e}")
        return jsonify({})

if __name__ == '__main__':
    # Initialize database on startup
    if init_db():
        print("✅ Database initialized successfully")
    else:
        print("❌ Database initialization failed")
    
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000))) 