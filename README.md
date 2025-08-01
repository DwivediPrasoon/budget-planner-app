# Budget Planner App

A Flask-based budget planning application deployed on Railway with PostgreSQL.

## 🚀 Features

- **User Authentication**: Secure login/register system
- **Transaction Management**: Add, edit, and delete transactions
- **Category Management**: Organize expenses by categories
- **Payment Methods**: Track cash, credit card, debit card, UPI, and bank transfers
- **Credit Card Tracking**: Automatic expected expense creation for credit card payments
- **Expected Expenses**: Plan and track monthly expected expenses
- **Budget Templates**: Save and reuse budget templates
- **Analytics**: Charts and insights for spending patterns
- **PWA Support**: Progressive Web App with offline capabilities

## 🛠️ Technology Stack

- **Backend**: Flask (Python)
- **Database**: PostgreSQL
- **Deployment**: Railway
- **Frontend**: HTML, CSS, JavaScript, Chart.js
- **Authentication**: Session-based with password hashing

## 📁 Project Structure

```
budget-planner-2/
├── app_postgres.py          # Main Flask application
├── templates/               # HTML templates
│   ├── index.html          # Dashboard
│   ├── login.html          # Login page
│   ├── register.html       # Registration page
│   ├── add_transaction.html # Add transaction form
│   ├── categories.html     # Category management
│   ├── expected_expenses.html # Expected expenses
│   ├── all_transactions.html # Transaction history
│   └── ...                 # Other templates
├── static/                 # Static files
│   ├── manifest.json       # PWA manifest
│   ├── sw.js              # Service worker
│   └── favicon.ico        # Favicon
├── railway.json           # Railway deployment config
├── requirements.txt       # Python dependencies
├── runtime.txt           # Python version
└── RAILWAY_DEPLOYMENT.md # Deployment guide
```

## 🚀 Deployment

This app is deployed on Railway with PostgreSQL. See `RAILWAY_DEPLOYMENT.md` for detailed deployment instructions.

## 🔧 Key Features

### Credit Card Accounting
- Credit card transactions don't reduce current account balance
- Automatic expected expense creation for next month's payment
- Clear separation between borrowing (credit card) and actual spending (payment)

### Payment Methods
- Cash, Credit Card, Debit Card, Bank Transfer, UPI
- Better categorization: Transport (Credit Card) vs Transport (Cash)

### User Management
- Separate database per user
- Secure password hashing
- Session-based authentication

## 📊 Dashboard Features

- Monthly income vs expenses
- Credit card balance tracking
- Expected expenses vs actual spending
- Category-wise spending analysis
- Recent transactions
- Interactive charts and analytics

## 🔐 Security

- Password hashing with SHA-256
- Session-based authentication
- SQL injection protection with parameterized queries
- CSRF protection with Flask sessions

## 📱 PWA Features

- Offline capability
- Installable as mobile app
- Service worker for caching
- Responsive design

## 🎯 Usage

1. Register/Login to your account
2. Add transactions with categories and payment methods
3. Set up expected expenses for better planning
4. Track your spending with analytics
5. Use credit card tracking for better financial management

---

**Deployed on Railway**: https://web-production-c70bf.up.railway.app/ 