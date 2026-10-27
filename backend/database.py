"""
CineCheck - Database Layer (SQLite)
Manages datasets, reviews, batch analyses, prediction results, and audit history.
Uses parameterized queries to safeguard data integrity.
"""

import os
import sqlite3
import pandas as pd
from typing import Optional, List, Dict, Any
from backend.config import Config

DB_PATH = Config.DATABASE_PATH


def get_db_connection() -> sqlite3.Connection:
    db_path = Config.DATABASE_PATH
    db_dir = os.path.dirname(os.path.abspath(db_path))
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Initializes tables in SQLite database if they do not exist."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Datasets Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS datasets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filename TEXT NOT NULL,
        file_type TEXT NOT NULL,
        total_rows INTEGER NOT NULL DEFAULT 0,
        valid_rows INTEGER NOT NULL DEFAULT 0,
        invalid_rows INTEGER NOT NULL DEFAULT 0,
        uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        status TEXT NOT NULL DEFAULT 'ready'
    )
    """)

    # 2. Reviews Table (Raw uploaded records)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS reviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        dataset_id INTEGER NOT NULL,
        review_id TEXT NOT NULL,
        movie_title TEXT NOT NULL,
        movie_release_date TEXT,
        review_date TEXT,
        review_text TEXT NOT NULL,
        rating REAL,
        label TEXT,
        source TEXT,
        FOREIGN KEY (dataset_id) REFERENCES datasets(id) ON DELETE CASCADE
    )
    """)

    # 3. Batch Analyses Table (Batch run summaries)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS batch_analyses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        dataset_id INTEGER NOT NULL,
        dataset_name TEXT NOT NULL,
        model_used TEXT NOT NULL,
        total_analyzed INTEGER NOT NULL,
        suspicious_count INTEGER NOT NULL,
        genuine_count INTEGER NOT NULL,
        insufficient_count INTEGER NOT NULL,
        avg_suspicion_score REAL NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (dataset_id) REFERENCES datasets(id) ON DELETE CASCADE
    )
    """)

    # 4. Analysis Results Table (Detailed per-review inference results)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS analysis_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        batch_analysis_id INTEGER NOT NULL,
        review_id TEXT NOT NULL,
        movie_title TEXT NOT NULL,
        movie_release_date TEXT,
        review_date TEXT,
        review_text TEXT NOT NULL,
        rating REAL,
        ground_truth_label TEXT,
        predicted_label TEXT NOT NULL,
        suspicion_score REAL NOT NULL,
        warning_indicators TEXT,
        similarity_flag INTEGER DEFAULT 0,
        similarity_score REAL DEFAULT 0.0,
        FOREIGN KEY (batch_analysis_id) REFERENCES batch_analyses(id) ON DELETE CASCADE
    )
    """)

    # 5. Single Analyses Table (Manual review audit history)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS single_analyses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        movie_title TEXT NOT NULL,
        review_text TEXT NOT NULL,
        rating REAL,
        predicted_label TEXT NOT NULL,
        suspicion_score REAL NOT NULL,
        confidence REAL NOT NULL,
        warning_indicators TEXT,
        model_used TEXT NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()


def insert_dataset(filename: str, file_type: str, total_rows: int, valid_rows: int, invalid_rows: int) -> int:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO datasets (filename, file_type, total_rows, valid_rows, invalid_rows)
        VALUES (?, ?, ?, ?, ?)
    """, (filename, file_type, total_rows, valid_rows, invalid_rows))
    dataset_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return dataset_id


def insert_reviews(dataset_id: int, records: List[Dict[str, Any]]):
    conn = get_db_connection()
    cursor = conn.cursor()
    insert_data = [
        (
            dataset_id,
            str(r.get("review_id", f"REV-{i+1}")),
            str(r.get("movie_title", "Unknown Movie")),
            str(r.get("movie_release_date", "")) if pd.notna(r.get("movie_release_date")) else "",
            str(r.get("review_date", "")) if pd.notna(r.get("review_date")) else "",
            str(r.get("review_text", "")),
            float(r["rating"]) if pd.notna(r.get("rating")) else None,
            str(r.get("label", "")) if pd.notna(r.get("label")) else "",
            str(r.get("source", "upload")) if pd.notna(r.get("source")) else "upload"
        )
        for i, r in enumerate(records)
    ]
    cursor.executemany("""
        INSERT INTO reviews (dataset_id, review_id, movie_title, movie_release_date, review_date, review_text, rating, label, source)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, insert_data)
    conn.commit()
    conn.close()


def get_all_datasets() -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT d.*, 
               (SELECT COUNT(*) FROM batch_analyses b WHERE b.dataset_id = d.id) as analysis_count
        FROM datasets d
        ORDER BY d.uploaded_at DESC
    """)
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


def get_dataset_by_id(dataset_id: int) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM datasets WHERE id = ?", (dataset_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_reviews_by_dataset(dataset_id: int, movie_title: Optional[str] = None, limit: Optional[int] = None) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    query = "SELECT * FROM reviews WHERE dataset_id = ?"
    params = [dataset_id]
    if movie_title and movie_title.lower() != "all":
        query += " AND movie_title = ?"
        params.append(movie_title)
    query += " ORDER BY id ASC"
    if limit:
        query += " LIMIT ?"
        params.append(limit)
    cursor.execute(query, params)
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


def delete_dataset(dataset_id: int) -> bool:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM datasets WHERE id = ?", (dataset_id,))
    affected = cursor.rowcount
    conn.commit()
    conn.close()
    return affected > 0


def save_batch_analysis(dataset_id: int, dataset_name: str, model_used: str, summary: Dict[str, Any], results_df: pd.DataFrame) -> int:
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO batch_analyses (dataset_id, dataset_name, model_used, total_analyzed, suspicious_count, genuine_count, insufficient_count, avg_suspicion_score)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        dataset_id,
        dataset_name,
        model_used,
        summary["total_analyzed"],
        summary["suspicious_count"],
        summary["genuine_count"],
        summary["insufficient_count"],
        summary["average_suspicion_score"]
    ))
    batch_id = cursor.lastrowid

    # Insert individual results
    insert_data = []
    for _, row in results_df.iterrows():
        insert_data.append((
            batch_id,
            str(row.get("review_id", "")),
            str(row.get("movie_title", "Unknown")),
            str(row.get("movie_release_date", "")),
            str(row.get("review_date", "")),
            str(row.get("review_text", "")),
            float(row["rating"]) if pd.notna(row.get("rating")) else None,
            str(row.get("label", "")) if pd.notna(row.get("label")) else "",
            str(row.get("predicted_label", "More Likely Genuine")),
            float(row.get("suspicion_score", 0.0)),
            str(row.get("warning_indicators", "")),
            1 if row.get("similarity_flag") else 0,
            float(row.get("similarity_score", 0.0))
        ))

    cursor.executemany("""
        INSERT INTO analysis_results (
            batch_analysis_id, review_id, movie_title, movie_release_date, review_date,
            review_text, rating, ground_truth_label, predicted_label, suspicion_score,
            warning_indicators, similarity_flag, similarity_score
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, insert_data)

    conn.commit()
    conn.close()
    return batch_id


def get_all_batch_analyses() -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT b.*,
               ROUND((CAST(b.suspicious_count AS REAL) / b.total_analyzed) * 100, 1) as suspicious_percentage
        FROM batch_analyses b
        ORDER BY b.created_at DESC
    """)
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


def get_batch_analysis_by_id(analysis_id: int) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM batch_analyses WHERE id = ?", (analysis_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_analysis_results(
    analysis_id: int,
    movie: Optional[str] = None,
    category: Optional[str] = None,
    search: Optional[str] = None,
    page: int = 1,
    per_page: int = 50
) -> Dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()

    base_query = "FROM analysis_results WHERE batch_analysis_id = ?"
    params: List[Any] = [analysis_id]

    if movie and movie.lower() != "all":
        base_query += " AND movie_title = ?"
        params.append(movie)

    if category and category.lower() != "all":
        base_query += " AND predicted_label = ?"
        params.append(category)

    if search and search.strip():
        base_query += " AND (review_text LIKE ? OR review_id LIKE ?)"
        s_term = f"%{search.strip()}%"
        params.extend([s_term, s_term])

    # Count total
    cursor.execute(f"SELECT COUNT(*) {base_query}", params)
    total_records = cursor.fetchone()[0]

    # Paginated select
    offset = (page - 1) * per_page
    select_query = f"SELECT * {base_query} ORDER BY id ASC LIMIT ? OFFSET ?"
    cursor.execute(select_query, params + [per_page, offset])
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()

    return {
        "records": rows,
        "total": total_records,
        "page": page,
        "per_page": per_page,
        "total_pages": max(1, (total_records + per_page - 1) // per_page)
    }


def get_all_analysis_results_raw(analysis_id: int) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM analysis_results WHERE batch_analysis_id = ? ORDER BY id ASC", (analysis_id,))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


def delete_batch_analysis(analysis_id: int) -> bool:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM batch_analyses WHERE id = ?", (analysis_id,))
    affected = cursor.rowcount
    conn.commit()
    conn.close()
    return affected > 0


def save_single_analysis(movie_title: str, review_text: str, rating: Optional[float], pred: Dict[str, Any]) -> int:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO single_analyses (movie_title, review_text, rating, predicted_label, suspicion_score, confidence, warning_indicators, model_used)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        movie_title,
        review_text,
        rating,
        pred.get("predicted_category", ""),
        pred.get("suspicion_score", 0.0),
        pred.get("confidence_percentage", 0.0),
        "; ".join(pred.get("warning_indicators", [])),
        pred.get("model_used", "Best")
    ))
    single_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return single_id


def get_recent_single_analyses(limit: int = 15) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM single_analyses ORDER BY created_at DESC LIMIT ?", (limit,))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


def get_analytics_summary(movie: Optional[str] = None, date_from: Optional[str] = None, date_to: Optional[str] = None) -> Dict[str, Any]:
    """
    Computes dashboard analytics strictly from actual database records in analysis_results.
    No hardcoded statistics. Supports movie and date range filters.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    where_clauses = ["1=1"]
    params: List[Any] = []

    if movie and movie.lower() != "all":
        where_clauses.append("movie_title = ?")
        params.append(movie)

    if date_from and date_from.strip():
        where_clauses.append("review_date >= ?")
        params.append(date_from.strip())

    if date_to and date_to.strip():
        where_clauses.append("review_date <= ?")
        params.append(date_to.strip())

    where_sql = " AND ".join(where_clauses)

    # 1. Overall Aggregates
    cursor.execute(f"""
        SELECT 
            COUNT(*) as total_reviews,
            SUM(CASE WHEN predicted_label = 'Potentially Suspicious' THEN 1 ELSE 0 END) as suspicious_count,
            SUM(CASE WHEN predicted_label = 'More Likely Genuine' THEN 1 ELSE 0 END) as genuine_count,
            SUM(CASE WHEN predicted_label = 'Insufficient Evidence' THEN 1 ELSE 0 END) as insufficient_count,
            AVG(rating) as avg_rating,
            AVG(suspicion_score) as avg_suspicion_score
        FROM analysis_results
        WHERE {where_sql}
    """, params)
    overall = dict(cursor.fetchone() or {})
    total = overall.get("total_reviews") or 0
    suspicious = overall.get("suspicious_count") or 0
    genuine = overall.get("genuine_count") or 0
    insufficient = overall.get("insufficient_count") or 0
    avg_rating = round(overall.get("avg_rating") or 0.0, 2)
    avg_susp = round(overall.get("avg_suspicion_score") or 0.0, 3)
    susp_pct = round((suspicious / total) * 100, 2) if total > 0 else 0.0

    # 2. Rating Distribution (1 to 5)
    cursor.execute(f"""
        SELECT 
            ROUND(rating) as star_bucket,
            COUNT(*) as count
        FROM analysis_results
        WHERE {where_sql} AND rating IS NOT NULL
        GROUP BY ROUND(rating)
        ORDER BY star_bucket ASC
    """, params)
    rating_dist = {int(r["star_bucket"]): r["count"] for r in cursor.fetchall() if r["star_bucket"] is not None}
    rating_data = [rating_dist.get(star, 0) for star in [1, 2, 3, 4, 5]]

    # 3. Movie-wise Breakdown
    cursor.execute(f"""
        SELECT 
            movie_title,
            COUNT(*) as total,
            SUM(CASE WHEN predicted_label = 'Potentially Suspicious' THEN 1 ELSE 0 END) as suspicious,
            SUM(CASE WHEN predicted_label = 'More Likely Genuine' THEN 1 ELSE 0 END) as genuine,
            AVG(rating) as avg_rating,
            ROUND(AVG(suspicion_score), 3) as avg_score
        FROM analysis_results
        WHERE {where_sql}
        GROUP BY movie_title
        ORDER BY total DESC
    """, params)
    movie_breakdown = []
    for r in cursor.fetchall():
        m_tot = r["total"]
        m_susp = r["suspicious"]
        m_pct = round((m_susp / m_tot) * 100, 1) if m_tot > 0 else 0.0
        movie_breakdown.append({
            "movie_title": r["movie_title"],
            "total_reviews": m_tot,
            "suspicious_count": m_susp,
            "genuine_count": r["genuine"],
            "suspicious_percentage": m_pct,
            "avg_rating": round(r["avg_rating"] or 0.0, 1),
            "avg_suspicion_score": r["avg_score"]
        })

    # 4. Review Trends Over Time (Group by month or date)
    cursor.execute(f"""
        SELECT 
            SUBSTR(review_date, 1, 7) as month_period,
            COUNT(*) as total_count,
            SUM(CASE WHEN predicted_label = 'Potentially Suspicious' THEN 1 ELSE 0 END) as susp_count
        FROM analysis_results
        WHERE {where_sql} AND review_date IS NOT NULL AND review_date != ''
        GROUP BY SUBSTR(review_date, 1, 7)
        ORDER BY month_period ASC
    """, params)
    timeline_rows = cursor.fetchall()
    timeline = {
        "labels": [r["month_period"] for r in timeline_rows],
        "total_series": [r["total_count"] for r in timeline_rows],
        "suspicious_series": [r["susp_count"] for r in timeline_rows]
    }

    conn.close()

    return {
        "total_reviews": total,
        "suspicious_count": suspicious,
        "genuine_count": genuine,
        "insufficient_count": insufficient,
        "suspicious_percentage": susp_pct,
        "average_rating": avg_rating,
        "average_suspicion_score": avg_susp,
        "rating_distribution": {
            "labels": ["1 Star", "2 Stars", "3 Stars", "4 Stars", "5 Stars"],
            "counts": rating_data
        },
        "movie_breakdown": movie_breakdown,
        "timeline": timeline,
        "ethical_disclaimer": (
            "Caution: Suspicious review percentage reflects algorithmic classification flags on the analysed "
            "dataset. It does not constitute verified legal proof of fraudulent bot operation."
        )
    }


def get_all_movies() -> List[str]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT movie_title FROM analysis_results WHERE movie_title IS NOT NULL AND movie_title != '' ORDER BY movie_title ASC")
    movies = [r[0] for r in cursor.fetchall()]
    if not movies:
        cursor.execute("SELECT DISTINCT movie_title FROM reviews WHERE movie_title IS NOT NULL AND movie_title != '' ORDER BY movie_title ASC")
        movies = [r[0] for r in cursor.fetchall()]
    conn.close()
    return movies


def seed_default_dataset_if_empty():
    """
    On cold start, if the database has 0 datasets, automatically seeds the curated
    benchmark dataset (cinecheck_reviews.csv) and runs an initial batch analysis
    so all charts, tables, and statistics are immediately populated with real calculated data!
    """
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM datasets")
    count = cursor.fetchone()[0]
    conn.close()

    if count == 0:
        csv_path = os.path.join(Config.BASE_DIR, "data", "cinecheck_reviews.csv")
        if os.path.exists(csv_path):
            print("[CineCheck DB] Seeding default benchmark dataset from cinecheck_reviews.csv...")
            df = pd.read_csv(csv_path)
            ds_id = insert_dataset(
                filename="cinecheck_reviews.csv (Curated Benchmark)",
                file_type="csv",
                total_rows=len(df),
                valid_rows=len(df),
                invalid_rows=0
            )
            insert_reviews(ds_id, df.to_dict(orient="records"))
            
            # Run initial batch analysis to populate analysis_results
            from ml.predict import predict_batch_dataframe
            print("[CineCheck DB] Running initial baseline batch analysis on seeded dataset...")
            results_df, summary = predict_batch_dataframe(df, model_choice="best")
            save_batch_analysis(
                dataset_id=ds_id,
                dataset_name="cinecheck_reviews.csv (Curated Benchmark)",
                model_used=summary["model_used"],
                summary=summary,
                results_df=results_df
            )
            print("[CineCheck DB] Seeding complete with initial batch analysis!")
