"""
CineCheck - Backend Configuration
"""

import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class Config:
    BASE_DIR = BASE_DIR
    SECRET_KEY = os.environ.get("SECRET_KEY", "cinecheck-twsma-secret-key-2025")
    DATABASE_PATH = os.environ.get("DATABASE_PATH", os.path.join(BASE_DIR, "backend", "cinecheck.db"))
    UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", os.path.join(BASE_DIR, "data", "uploads"))
    EXPORT_FOLDER = os.environ.get("EXPORT_FOLDER", os.path.join(BASE_DIR, "data", "exports"))
    ALLOWED_EXTENSIONS = {"csv", "xlsx", "xls"}
    MAX_CONTENT_LENGTH = 32 * 1024 * 1024  # 32 MB max upload
    FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")

os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
os.makedirs(Config.EXPORT_FOLDER, exist_ok=True)
