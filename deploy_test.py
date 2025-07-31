#!/usr/bin/env python3
"""
Test script to verify deployment configuration
"""
import os
import sys

def test_deployment_config():
    """Test if the app can start with deployment configuration"""
    
    # Set deployment environment variables
    os.environ['SECRET_KEY'] = 'test-secret-key-for-deployment'
    os.environ['DATABASE_PATH'] = 'data'
    os.environ['FLASK_ENV'] = 'production'
    
    print("🔧 Testing deployment configuration...")
    
    try:
        # Test imports
        from flask import Flask
        print("✅ Flask import successful")
        
        # Test app creation
        from app import app
        print("✅ App creation successful")
        
        # Test database initialization
        from app import init_main_db
        init_main_db()
        print("✅ Database initialization successful")
        
        print("\n🎉 Deployment configuration test passed!")
        print("Your app is ready for deployment.")
        
    except Exception as e:
        print(f"❌ Deployment test failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    test_deployment_config() 