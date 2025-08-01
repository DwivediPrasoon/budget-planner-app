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
        return render_template('index.html')
    
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
                           total_expected=total_expected)
                           
    except Exception as e:
        print(f"Error in index route: {e}")
        flash('Error loading dashboard', 'error')
        return render_template('index.html')

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

@app.route('/api/chart-data')
@login_required
def chart_data():
    """API endpoint for chart data"""
    conn = get_db_connection()
    if not conn:
        return jsonify({})
    
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # Get user ID
        cur.execute('SELECT id FROM users WHERE username = %s', (session['username'],))
        user_id = cur.fetchone()[0]
        
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
        
        cur.close()
        conn.close()
        
        return jsonify({
            'monthly': {
                'labels': [row['month'] for row in monthly_data],
                'income': [float(row['income'] or 0) for row in monthly_data],
                'expenses': [float(row['expenses'] or 0) for row in monthly_data]
            },
            'categories': {
                'labels': [row['category'] for row in category_data],
                'data': [float(row['total'] or 0) for row in category_data]
            }
        })
        
    except Exception as e:
        print(f"Chart data error: {e}")
        return jsonify({})

if __name__ == '__main__':
    # Initialize database on startup
    if init_db():
        print("✅ Database initialized successfully")
    else:
        print("❌ Database initialization failed")
    
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000))) 