"""
CineCheck - Main Flask Application Server
Runs REST API backend and serves GUI frontend web pages.
"""

import os
import sys
from flask import Flask, send_from_directory, render_template, redirect, url_for
from flask_cors import CORS

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from backend.config import Config
from backend.routes import api_bp
from backend.database import init_db, seed_default_dataset_if_empty


def create_app():
    app = Flask(
        __name__,
        static_folder=Config.FRONTEND_DIR,
        static_url_path=""
    )
    app.config.from_object(Config)

    # Enable CORS for flexible local development
    CORS(app)

    # Register API Blueprint
    app.register_blueprint(api_bp)

    # Seed Database on initial setup
    with app.app_context():
        init_db()
        try:
            seed_default_dataset_if_empty()
        except Exception as e:
            app.logger.warning(f"Default dataset seeding note: {e}")

    # Frontend Navigation Routes
    @app.route("/")
    def index():
        return send_from_directory(Config.FRONTEND_DIR, "index.html")

    @app.route("/dashboard")
    @app.route("/dashboard.html")
    def dashboard():
        return send_from_directory(Config.FRONTEND_DIR, "dashboard.html")

    @app.route("/analyse")
    @app.route("/analyse.html")
    def analyse():
        return send_from_directory(Config.FRONTEND_DIR, "analyse.html")

    @app.route("/batch")
    @app.route("/batch_analysis")
    @app.route("/batch_analysis.html")
    def batch_analysis():
        return send_from_directory(Config.FRONTEND_DIR, "batch_analysis.html")

    @app.route("/evaluation")
    @app.route("/model_evaluation")
    @app.route("/model_evaluation.html")
    def model_evaluation():
        return send_from_directory(Config.FRONTEND_DIR, "model_evaluation.html")

    @app.route("/datasets")
    @app.route("/dataset_management")
    @app.route("/dataset_management.html")
    def dataset_management():
        return send_from_directory(Config.FRONTEND_DIR, "dataset_management.html")

    @app.route("/history")
    @app.route("/history.html")
    def history():
        return send_from_directory(Config.FRONTEND_DIR, "history.html")

    @app.route("/about")
    @app.route("/about.html")
    def about():
        return send_from_directory(Config.FRONTEND_DIR, "about.html")

    @app.route("/movie/<path:movie_id>")
    def movie_page(movie_id):
        from flask import request
        if request.headers.get("Accept") == "application/json" or request.args.get("format") == "json":
            return redirect(f"/api/movie/{movie_id}")
        return send_from_directory(Config.FRONTEND_DIR, "analyse.html")

    # Static CSS and JS file handlers
    @app.route("/css/<path:filename>")
    def css_static(filename):
        return send_from_directory(os.path.join(Config.FRONTEND_DIR, "css"), filename)

    @app.route("/js/<path:filename>")
    def js_static(filename):
        return send_from_directory(os.path.join(Config.FRONTEND_DIR, "js"), filename)

    return app


if __name__ == "__main__":
    app = create_app()
    port = int(os.environ.get("PORT", 5000))
    print("=" * 60)
    print(f" * CineCheck Server starting at http://127.0.0.1:{port}")
    print(f" * REST API available at http://127.0.0.1:{port}/api/health")
    print("=" * 60)
    app.run(host="127.0.0.1", port=port, debug=True)
