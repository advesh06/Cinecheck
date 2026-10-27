"""
CineCheck - Standalone Model Training Script
Usage: python scripts/train_model.py
Developer: Advesh Tambat (Roll No: 23108A0013)
"""

import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from ml.train_model import train_models

if __name__ == "__main__":
    train_models()
