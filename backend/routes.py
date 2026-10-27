"""
CineCheck - REST API Routes & Endpoints
Implements endpoints for health checks, dataset management, single & batch analysis,
analytics summaries, model evaluations, and CSV/XLSX export downloads.
"""

import os
import sys
import uuid
import pandas as pd
from flask import Blueprint, request, jsonify, send_file, current_app
from werkzeug.utils import secure_filename

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from backend.config import Config
from backend import database as db
from ml.predict import predict_single_review, predict_batch_dataframe
from ml.evaluate_model import get_evaluation_metrics
from ml.explainability import get_ethical_limitations_notice

api_bp = Blueprint("api", __name__, url_prefix="/api")


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in Config.ALLOWED_EXTENSIONS


# -------------------------------------------------------------
# 1. Health & System Status
# -------------------------------------------------------------
@api_bp.route("/health", methods=["GET"])
def health_check():
    from ml.predict import load_artifacts
    try:
        load_artifacts()
        model_status = "loaded"
    except Exception as e:
        model_status = f"error: {str(e)}"

    return jsonify({
        "status": "healthy",
        "system": "CineCheck - Fake Movie Review Detection System",
        "developer": "Advesh Tambat",
        "roll_number": "23108A0013",
        "subject": "Text, Web and Social Media Analytics (TWSMA)",
        "platform_focus": "BookMyShow-inspired movie review screening",
        "version": "1.0.0",
        "model_status": model_status,
        "database": os.path.exists(Config.DATABASE_PATH)
    }), 200


# -------------------------------------------------------------
# 2. Dataset Management Endpoints
# -------------------------------------------------------------
@api_bp.route("/datasets/upload", methods=["POST"])
def upload_dataset():
    """
    Accepts CSV or XLSX dataset file, validates schema and data types,
    handles missing and duplicate records, reports valid and invalid counts,
    and inserts records into the database.
    """
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded in the request."}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No file selected."}), 400

    if not allowed_file(file.filename):
        return jsonify({
            "error": "Unsupported file format. Please upload a CSV (.csv) or Excel (.xlsx, .xls) file."
        }), 400

    filename = secure_filename(file.filename)
    unique_name = f"{uuid.uuid4().hex[:8]}_{filename}"
    save_path = os.path.join(Config.UPLOAD_FOLDER, unique_name)
    file.save(save_path)

    # Read and validate dataset
    try:
        file_ext = filename.rsplit(".", 1)[1].lower()
        if file_ext == "csv":
            df = pd.read_csv(save_path)
        else:
            df = pd.read_excel(save_path)
    except Exception as e:
        if os.path.exists(save_path):
            os.remove(save_path)
        return jsonify({"error": f"Failed to parse file: {str(e)}"}), 400

    total_rows = len(df)
    if total_rows == 0:
        return jsonify({"error": "Uploaded file is completely empty."}), 400

    # Column Validation
    # Required core column: review_text
    if "review_text" not in df.columns:
        # Check case-insensitive match
        matched_col = None
        for col in df.columns:
            if col.strip().lower() in ["review_text", "review", "reviewtext", "text"]:
                matched_col = col
                break
        if matched_col:
            df.rename(columns={matched_col: "review_text"}, inplace=True)
        else:
            return jsonify({
                "error": "Missing mandatory column: 'review_text'. Please check the dataset schema.",
                "provided_columns": list(df.columns)
            }), 400

    # Fill optional columns if missing
    if "review_id" not in df.columns:
        df["review_id"] = [f"REV-UP-{i+1}" for i in range(len(df))]
    if "movie_title" not in df.columns:
        df["movie_title"] = "General"
    if "rating" not in df.columns:
        df["rating"] = None
    if "label" not in df.columns:
        df["label"] = ""
    if "source" not in df.columns:
        df["source"] = "user_upload"

    # Identify valid vs invalid rows
    valid_mask = df["review_text"].notna() & (df["review_text"].astype(str).str.strip() != "")
    invalid_rows_count = int((~valid_mask).sum())
    valid_df = df[valid_mask].copy()

    # Track duplicates
    duplicates_count = int(valid_df.duplicated(subset=["review_text"]).sum())

    # Insert into SQLite
    valid_rows_count = len(valid_df)
    dataset_id = db.insert_dataset(
        filename=filename,
        file_type=file_ext,
        total_rows=total_rows,
        valid_rows=valid_rows_count,
        invalid_rows=invalid_rows_count
    )

    records = valid_df.to_dict(orient="records")
    db.insert_reviews(dataset_id, records)

    # Preview sample (up to 5 rows)
    preview = valid_df.head(5).to_dict(orient="records")

    return jsonify({
        "message": "Dataset uploaded and validated successfully.",
        "dataset_id": dataset_id,
        "filename": filename,
        "total_rows": total_rows,
        "valid_rows": valid_rows_count,
        "invalid_rows": invalid_rows_count,
        "duplicate_rows": duplicates_count,
        "movies_detected": sorted(valid_df["movie_title"].dropna().unique().tolist()),
        "preview": preview
    }), 201


@api_bp.route("/datasets", methods=["GET"])
def list_datasets():
    datasets = db.get_all_datasets()
    return jsonify({"datasets": datasets}), 200


@api_bp.route("/datasets/<int:dataset_id>", methods=["GET"])
def get_dataset_detail(dataset_id: int):
    dataset = db.get_dataset_by_id(dataset_id)
    if not dataset:
        return jsonify({"error": "Dataset not found."}), 404

    # Fetch reviews preview
    movie_filter = request.args.get("movie")
    limit = int(request.args.get("limit", 50))
    reviews = db.get_reviews_by_dataset(dataset_id, movie_title=movie_filter, limit=limit)

    return jsonify({
        "dataset": dataset,
        "reviews_sample": reviews,
        "sample_count": len(reviews)
    }), 200


@api_bp.route("/datasets/<int:dataset_id>", methods=["DELETE"])
def delete_dataset(dataset_id: int):
    success = db.delete_dataset(dataset_id)
    if not success:
        return jsonify({"error": "Dataset not found or could not be deleted."}), 404
    return jsonify({"message": f"Dataset #{dataset_id} and associated records successfully deleted."}), 200


# -------------------------------------------------------------
# 3. Individual Review Analysis Endpoint
# -------------------------------------------------------------
@api_bp.route("/reviews/analyse", methods=["POST"])
@api_bp.route("/analyze", methods=["POST"])
def analyse_individual_review():
    """
    Analyzes an individual review:
    Input JSON or Form: { review_text, movie_title, rating, model_choice }
    """
    data = request.get_json(silent=True) or request.form.to_dict() or {}
    review_text = data.get("review_text") or data.get("text") or data.get("review") or ""
    movie_title = data.get("movie_title") or data.get("movie") or data.get("title") or "Unspecified Movie"
    rating = data.get("rating")
    model_choice = data.get("model_choice") or data.get("model") or "best"

    if rating is not None and rating != "":
        try:
            rating = float(rating)
        except (ValueError, TypeError):
            rating = None

    result = predict_single_review(
        review_text=review_text,
        movie_title=movie_title,
        rating=rating,
        model_choice=model_choice
    )

    # Persist in single_analyses table for audit log
    if result.get("predicted_category") != "Insufficient Evidence":
        db.save_single_analysis(movie_title, review_text, rating, result)

    return jsonify(result), 200


# -------------------------------------------------------------
# 4. Batch Review Analysis Endpoint
# -------------------------------------------------------------
@api_bp.route("/reviews/batch-analyse", methods=["POST"])
def batch_analyse():
    """
    Runs batch detection over an existing dataset ID or directly uploaded file.
    Preserves original columns, appends predicted_label, suspicion_score, warning_indicators.
    Stores results in SQLite and returns execution summary.
    """
    data = request.get_json(silent=True) or {}
    dataset_id = data.get("dataset_id")
    movie_filter = data.get("movie_title")
    model_choice = data.get("model_choice", "best")

    if not dataset_id:
        return jsonify({"error": "dataset_id is required for batch analysis."}), 400

    dataset = db.get_dataset_by_id(dataset_id)
    if not dataset:
        return jsonify({"error": f"Dataset #{dataset_id} not found."}), 404

    # Fetch reviews
    reviews = db.get_reviews_by_dataset(dataset_id, movie_title=movie_filter)
    if not reviews:
        return jsonify({"error": "No reviews found in this dataset matching the criteria."}), 400

    df = pd.DataFrame(reviews)

    # Run ML batch prediction
    results_df, summary = predict_batch_dataframe(df, model_choice=model_choice)

    # Persist batch analysis and results in database
    analysis_id = db.save_batch_analysis(
        dataset_id=dataset_id,
        dataset_name=dataset["filename"],
        model_used=summary["model_used"],
        summary=summary,
        results_df=results_df
    )

    summary["analysis_id"] = analysis_id
    summary["dataset_id"] = dataset_id
    summary["dataset_name"] = dataset["filename"]

    return jsonify({
        "message": "Batch analysis completed successfully.",
        "summary": summary
    }), 200


# -------------------------------------------------------------
# 5. Analysis Results & Pagination Endpoint
# -------------------------------------------------------------
@api_bp.route("/analysis-results/<int:analysis_id>", methods=["GET"])
def get_analysis_results_paginated(analysis_id: int):
    movie = request.args.get("movie")
    category = request.args.get("category")
    search = request.args.get("search")
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 25))

    batch_meta = db.get_batch_analysis_by_id(analysis_id)
    if not batch_meta:
        return jsonify({"error": "Analysis not found."}), 404

    result = db.get_analysis_results(
        analysis_id=analysis_id,
        movie=movie,
        category=category,
        search=search,
        page=page,
        per_page=per_page
    )
    result["batch_metadata"] = batch_meta

    return jsonify(result), 200


# -------------------------------------------------------------
# 6. Analytics Dashboard Endpoints
# -------------------------------------------------------------
@api_bp.route("/analytics/summary", methods=["GET"])
@api_bp.route("/stats", methods=["GET"])
def get_analytics():
    movie = request.args.get("movie")
    date_from = request.args.get("date_from")
    date_to = request.args.get("date_to")

    summary = db.get_analytics_summary(movie=movie, date_from=date_from, date_to=date_to)
    return jsonify(summary), 200


@api_bp.route("/analytics/movies", methods=["GET"])
def get_movies():
    movies = db.get_all_movies()
    return jsonify({"movies": movies}), 200


@api_bp.route("/reviews", methods=["GET", "POST"])
def handle_reviews():
    """
    GET: Returns list of reviews with optional movie or limit filter.
    POST: Submits a review for analysis and persistence.
    """
    if request.method == "POST":
        return analyse_individual_review()
    movie = request.args.get("movie")
    limit = int(request.args.get("limit", 50))
    datasets = db.get_all_datasets()
    dataset_id = datasets[0]["id"] if datasets else 1
    reviews = db.get_reviews_by_dataset(dataset_id, movie_title=movie, limit=limit)
    return jsonify({
        "total": len(reviews),
        "dataset_id": dataset_id,
        "movie_filter": movie or "all",
        "reviews": reviews
    }), 200


@api_bp.route("/movie/<path:movie_id>", methods=["GET"])
def movie_api(movie_id):
    """
    Returns movie-specific analytics and sample reviews.
    """
    movie_name = movie_id.strip()
    summary = db.get_analytics_summary(movie=movie_name)
    datasets = db.get_all_datasets()
    dataset_id = datasets[0]["id"] if datasets else 1
    reviews = db.get_reviews_by_dataset(dataset_id, movie_title=movie_name, limit=20)
    return jsonify({
        "movie_id": movie_id,
        "movie_title": movie_name,
        "summary": summary,
        "reviews": reviews
    }), 200


# -------------------------------------------------------------
# 7. Model Evaluation & Training Endpoints
# -------------------------------------------------------------
@api_bp.route("/model/evaluation", methods=["GET"])
@api_bp.route("/model", methods=["GET"])
def model_evaluation():
    metrics = get_evaluation_metrics()
    return jsonify(metrics), 200


@api_bp.route("/train", methods=["GET", "POST"])
def train_model_endpoint():
    """
    GET: Returns training status and dataset size.
    POST: Trains or retrains models on the benchmark dataset safely.
    """
    if request.method == "POST":
        from ml.train_model import train_models
        from ml.predict import _models_cache
        try:
            metrics = train_models()
            _models_cache.clear()
            return jsonify({
                "message": "Model retrained successfully.",
                "evaluation": metrics
            }), 200
        except Exception as e:
            return jsonify({"error": f"Training failed safely: {str(e)}"}), 500
    metrics = get_evaluation_metrics()
    return jsonify({
        "status": "ready",
        "selected_model": metrics.get("selected_best_model", "Logistic Regression"),
        "train_samples": metrics.get("train_sample_size", 0),
        "test_samples": metrics.get("test_sample_size", 0),
        "action": "Send POST request to /api/train to trigger model training."
    }), 200


# -------------------------------------------------------------
# 7b. Server-Side Visualisation (Matplotlib)
# -------------------------------------------------------------
@api_bp.route("/stats/chart.png", methods=["GET"])
@api_bp.route("/analytics/chart.png", methods=["GET"])
def get_analytics_chart():
    """Generates a server-side analytics visualisation using Matplotlib."""
    import io
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    summary = db.get_analytics_summary()
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4), facecolor="#0B0F19")
    
    # Rating distribution
    ratings = summary.get("rating_distribution", {}).get("labels", ["1★", "2★", "3★", "4★", "5★"])
    counts = summary.get("rating_distribution", {}).get("counts", [0, 0, 0, 0, 0])
    ax1.set_facecolor("#151E32")
    ax1.bar(ratings, counts, color="#6366F1", edgecolor="#23304D")
    ax1.set_title("Rating Distribution", color="#F8FAFC", fontsize=11, fontweight="bold")
    ax1.tick_params(colors="#94A3B8")
    for spine in ax1.spines.values():
        spine.set_color("#23304D")
        
    # Classification breakdown
    susp = summary.get("suspicious_count", 0)
    gen = summary.get("genuine_count", 0)
    ins = summary.get("insufficient_count", 0)
    ax2.set_facecolor("#151E32")
    if susp + gen + ins > 0:
        wedges, texts, autotexts = ax2.pie(
            [susp, gen, ins],
            labels=["Suspicious", "Genuine", "Insufficient"],
            colors=["#EF4444", "#10B981", "#64748B"],
            autopct="%1.1f%%",
            textprops={"color": "#94A3B8", "fontsize": 9}
        )
        for at in autotexts:
            at.set_color("#F8FAFC")
    ax2.set_title("Classification Breakdown", color="#F8FAFC", fontsize=11, fontweight="bold")

    plt.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=120, facecolor=fig.get_facecolor(), edgecolor="none")
    plt.close(fig)
    buf.seek(0)
    return send_file(buf, mimetype="image/png")


# -------------------------------------------------------------
# 8. History & Audit Endpoints
# -------------------------------------------------------------
@api_bp.route("/history", methods=["GET"])
def get_history():
    batch_analyses = db.get_all_batch_analyses()
    single_analyses = db.get_recent_single_analyses(limit=25)
    return jsonify({
        "batch_analyses": batch_analyses,
        "recent_single_analyses": single_analyses
    }), 200


@api_bp.route("/history/<int:analysis_id>", methods=["DELETE"])
def delete_history_item(analysis_id: int):
    success = db.delete_batch_analysis(analysis_id)
    if not success:
        return jsonify({"error": "Analysis record not found."}), 404
    return jsonify({"message": f"Analysis #{analysis_id} deleted successfully."}), 200


# -------------------------------------------------------------
# 9. Export Download Endpoint (CSV / Excel)
# -------------------------------------------------------------
@api_bp.route("/exports/<int:analysis_id>", methods=["GET"])
def export_analysis_results(analysis_id: int):
    """
    Exports analysed dataset with predicted labels, suspicion scores, and warning indicators
    as either CSV or XLSX format.
    """
    export_format = request.args.get("format", "csv").lower()
    batch_meta = db.get_batch_analysis_by_id(analysis_id)
    if not batch_meta:
        return jsonify({"error": "Analysis record not found."}), 404

    records = db.get_all_analysis_results_raw(analysis_id)
    if not records:
        return jsonify({"error": "No records found for this analysis."}), 404

    export_df = pd.DataFrame(records)
    # Remove internal primary key columns for clean export
    export_df = export_df.drop(columns=["id", "batch_analysis_id"], errors="ignore")

    sanitized_filename = secure_filename(f"cinecheck_analysis_{analysis_id}_{batch_meta['dataset_name']}")
    if sanitized_filename.endswith(".csv") or sanitized_filename.endswith(".xlsx"):
        sanitized_filename = sanitized_filename.rsplit(".", 1)[0]

    if export_format in ["excel", "xlsx"]:
        file_path = os.path.join(Config.EXPORT_FOLDER, f"{sanitized_filename}.xlsx")
        export_df.to_excel(file_path, index=False)
        mimetype = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        download_name = f"{sanitized_filename}.xlsx"
    else:
        file_path = os.path.join(Config.EXPORT_FOLDER, f"{sanitized_filename}.csv")
        export_df.to_csv(file_path, index=False)
        mimetype = "text/csv"
        download_name = f"{sanitized_filename}.csv"

    return send_file(
        file_path,
        mimetype=mimetype,
        as_attachment=True,
        download_name=download_name
    )

