#!/usr/bin/env python3
"""
PythonAnywhere Deployment Setup Script
Run this on PythonAnywhere to set up your budget planner app
"""

import os
import subprocess
import sys

def setup_pythonanywhere():
    """Set up the budget planner app on PythonAnywhere"""
    
    print("🚀 Setting up Budget Planner on PythonAnywhere...")
    
    # Create necessary directories
    os.makedirs('data', exist_ok=True)
    os.makedirs('static', exist_ok=True)
    os.makedirs('templates', exist_ok=True)
    
    print("✅ Directories created")
    
    # Install dependencies
    print("📦 Installing dependencies...")
    subprocess.run([sys.executable, '-m', 'pip', 'install', 'flask'], check=True)
    
    print("✅ Dependencies installed")
    
    # Test the app
    print("🧪 Testing the app...")
    try:
        from app import app
        print("✅ App imports successfully")
    except Exception as e:
        print(f"❌ App import failed: {e}")
        return False
    
    print("\n🎉 Setup complete!")
    print("\n📋 Next steps:")
    print("1. Go to Web tab in PythonAnywhere")
    print("2. Add a new web app")
    print("3. Choose 'Flask' and Python 3.9")
    print("4. Set source code to: /home/YOUR_USERNAME/budget-planner")
    print("5. Set working directory to: /home/YOUR_USERNAME/budget-planner")
    print("6. Set WSGI configuration file to: /var/www/YOUR_USERNAME_pythonanywhere_com_wsgi.py")
    
    return True

if __name__ == "__main__":
    setup_pythonanywhere() 