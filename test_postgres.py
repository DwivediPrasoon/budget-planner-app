#!/usr/bin/env python3
"""
Test script for PostgreSQL connection and database setup
"""

import os
import sys

# Add current directory to path
sys.path.append('.')

def test_postgres_connection():
    """Test PostgreSQL connection and database setup"""
    
    print("🧪 Testing PostgreSQL setup...")
    
    # Test 1: Check if psycopg2 is available
    try:
        import psycopg2
        print("✅ psycopg2 imported successfully")
    except ImportError as e:
        print(f"❌ psycopg2 import failed: {e}")
        print("💡 Try: pip install psycopg2-binary")
        return False
    
    # Test 2: Check environment variables
    print("\n📋 Environment Variables:")
    print(f"SECRET_KEY: {'Set' if os.getenv('SECRET_KEY') else 'Not set'}")
    print(f"DATABASE_URL: {'Set' if os.getenv('DATABASE_URL') else 'Not set'}")
    print(f"DB_HOST: {os.getenv('DB_HOST', 'Not set')}")
    print(f"DB_NAME: {os.getenv('DB_NAME', 'Not set')}")
    print(f"DB_USER: {os.getenv('DB_USER', 'Not set')}")
    
    # Test 3: Try to import the app
    try:
        from app_postgres import get_db_connection, init_db
        print("✅ app_postgres imported successfully")
    except Exception as e:
        print(f"❌ app_postgres import failed: {e}")
        return False
    
    # Test 4: Test database connection
    try:
        conn = get_db_connection()
        if conn:
            print("✅ Database connection successful")
            conn.close()
        else:
            print("❌ Database connection failed")
            return False
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        return False
    
    # Test 5: Test database initialization
    try:
        if init_db():
            print("✅ Database initialization successful")
        else:
            print("❌ Database initialization failed")
            return False
    except Exception as e:
        print(f"❌ Database initialization error: {e}")
        return False
    
    print("\n🎉 All tests passed! PostgreSQL setup is working correctly.")
    return True

if __name__ == "__main__":
    test_postgres_connection() 