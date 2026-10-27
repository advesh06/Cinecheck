"""
CineCheck - Database Storage Interface
Provides direct functional interface to SQLite data access layer.
Developer: Advesh Tambat (Roll No: 23108A0013)
"""

import sys
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from backend.database import *
