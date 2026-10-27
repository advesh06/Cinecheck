"""
CineCheck - Main Application Entrypoint for Local Execution and Render WSGI
Developer: Advesh Tambat (Roll No: 23108A0013)
Subject: Text, Web and Social Media Analytics (TWSMA)
"""

import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from backend.app import create_app

# Expose app object for Gunicorn (gunicorn app:app)
app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    print("=" * 60)
    print(f" * CineCheck Server starting at http://0.0.0.0:{port}")
    print(f" * Production WSGI command: gunicorn app:app")
    print(f" * Developer: Advesh Tambat (23108A0013)")
    print("=" * 60)
    app.run(host="0.0.0.0", port=port, debug=debug)
