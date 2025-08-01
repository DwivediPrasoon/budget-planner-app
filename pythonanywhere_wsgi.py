#!/usr/bin/env python3
"""
WSGI configuration for Budget Planner on PythonAnywhere
"""

import sys
import os

# Add your project directory to the sys.path
path = '/home/YOUR_USERNAME/budget-planner'
if path not in sys.path:
    sys.path.append(path)

# Set environment variables
os.environ['SECRET_KEY'] = '7b1eeabcd208616a73edadcc5b91e9dd56503f2487d9077e22d81ba84ccb1c43'
os.environ['DATABASE_PATH'] = '/home/YOUR_USERNAME/budget-planner/data'

# Import your Flask app
from app import app as application

if __name__ == "__main__":
    application.run() 