#!/usr/bin/env python3
"""
Web server for Kalshi Mention Market Research Tool
"""

import os
import sys
from flask import Flask

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.web_interface import app

if __name__ == '__main__':
    print("🚀 Starting Kalshi Mention Market Research Tool Web Server")
    print("📊 Web Interface: http://localhost:5001")
    print("🔧 Terminal Interface: python main.py")
    print("=" * 60)
    
    app.run(debug=True, host='0.0.0.0', port=5001)
