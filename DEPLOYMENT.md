# 🚀 Deployment Guide - Budget Planner App

## Free Deployment Options

### 1. Render (Recommended - Easiest)

**Steps:**
1. Create account at [render.com](https://render.com)
2. Connect your GitHub repository
3. Create a new Web Service
4. Configure:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
   - **Environment Variables**:
     - `SECRET_KEY`: Generate a strong secret key
     - `DATABASE_PATH`: `/opt/render/project/src/data`

**Pros:**
- Free tier: 750 hours/month
- Automatic deployments
- Easy setup
- Good documentation

**Cons:**
- Sleeps after 15 minutes of inactivity
- Limited database storage

### 2. Railway

**Steps:**
1. Create account at [railway.app](https://railway.app)
2. Connect your GitHub repository
3. Add PostgreSQL database
4. Set environment variables:
   - `SECRET_KEY`: Your secret key
   - `DATABASE_URL`: Railway will provide this

**Pros:**
- $5 free credit monthly
- Very easy setup
- Good performance

### 3. PythonAnywhere

**Steps:**
1. Create account at [pythonanywhere.com](https://pythonanywhere.com)
2. Upload your files
3. Set up virtual environment
4. Configure WSGI file

**Pros:**
- Python-focused
- Good for beginners
- Free tier available

**Cons:**
- Limited resources
- SQLite only (no PostgreSQL)

## Database Migration for Production

For production, consider migrating from SQLite to PostgreSQL:

1. **Install psycopg2**: Add to requirements.txt
2. **Update database connection**: Use DATABASE_URL environment variable
3. **Migrate data**: Export from SQLite, import to PostgreSQL

## Environment Variables

Set these in your deployment platform:

```bash
SECRET_KEY=your-strong-secret-key-here
DATABASE_PATH=/path/to/database/files
FLASK_ENV=production
```

## Security Considerations

1. **Change default secret key** in production
2. **Use HTTPS** (most platforms provide this)
3. **Set up proper environment variables**
4. **Regular backups** of your database
5. **Monitor application logs**

## Local Testing

Test your deployment configuration locally:

```bash
export SECRET_KEY="test-secret-key"
export DATABASE_PATH="data"
python app.py
```

## Troubleshooting

### Common Issues:
1. **Database not found**: Check DATABASE_PATH environment variable
2. **Static files not loading**: Ensure static folder is properly configured
3. **Session issues**: Verify SECRET_KEY is set
4. **Import errors**: Check all dependencies are in requirements.txt

### Logs:
- Check application logs in your deployment platform
- Use `print()` statements for debugging (remove in production)
- Monitor error pages and user feedback 