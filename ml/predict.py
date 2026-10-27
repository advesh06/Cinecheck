"""
CineCheck - Prediction Pipeline
Provides single and batch inference with model loading, calibration,
linguistic signal extraction, explainability, and similarity clustering.
"""

import os
import sys
import joblib
import pandas as pd
import numpy as np

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from ml.preprocessing import clean_text, extract_linguistic_signals
from ml.explainability import explain_prediction, analyze_batch_similarity, get_ethical_limitations_notice

SAVED_MODELS_DIR = os.path.join(BASE_DIR, "ml", "saved_models")

# Cached models in memory
_models_cache = {}


def load_artifacts():
    """
    Loads saved vectorizer and classifier models from disk.
    Caches artifacts in memory for fast API performance.
    """
    global _models_cache
    if _models_cache:
        return _models_cache

    vectorizer_path = os.path.join(SAVED_MODELS_DIR, "tfidf_vectorizer.joblib")
    best_model_path = os.path.join(SAVED_MODELS_DIR, "best_model.joblib")
    lr_path = os.path.join(SAVED_MODELS_DIR, "logistic_regression.joblib")
    nb_path = os.path.join(SAVED_MODELS_DIR, "naive_bayes.joblib")

    if not os.path.exists(vectorizer_path) or not os.path.exists(best_model_path):
        try:
            from ml.train_model import train_models
            train_models()
        except Exception as e:
            raise FileNotFoundError(
                f"Model artifacts not found and automatic training failed: {str(e)}"
            )

    _models_cache["vectorizer"] = joblib.load(vectorizer_path)
    _models_cache["best"] = joblib.load(best_model_path)
    _models_cache["logistic_regression"] = joblib.load(lr_path) if os.path.exists(lr_path) else _models_cache["best"]
    _models_cache["naive_bayes"] = joblib.load(nb_path) if os.path.exists(nb_path) else _models_cache["best"]

    return _models_cache


def get_selected_model(model_choice: str = "best"):
    artifacts = load_artifacts()
    choice_key = str(model_choice).lower().strip()
    if "logistic" in choice_key or choice_key == "lr":
        return artifacts["logistic_regression"], "Logistic Regression", artifacts["vectorizer"]
    elif "naive" in choice_key or choice_key == "nb" or "bayes" in choice_key:
        return artifacts["naive_bayes"], "Multinomial Naive Bayes", artifacts["vectorizer"]
    else:
        return artifacts["best"], "Selected Best Model", artifacts["vectorizer"]


def predict_single_review(
    review_text: str,
    movie_title: str = "Unspecified Movie",
    rating: float = None,
    review_id: str = "REV-SINGLE",
    model_choice: str = "best"
) -> dict:
    """
    Analyzes an individual movie review:
    - Checks for minimum length / informative content
    - Preprocesses text
    - Vectorizes via TF-IDF
    - Computes calibrated suspicion score
    - Categorizes into: 'Potentially Suspicious', 'More Likely Genuine', or 'Insufficient Evidence'
    - Generates feature explanations and warning indicators
    """
    model, model_name, vectorizer = get_selected_model(model_choice)
    limitations = get_ethical_limitations_notice()

    # Handle empty or trivial text
    if not review_text or not isinstance(review_text, str) or len(review_text.strip()) < 4:
        return {
            "review_id": review_id,
            "movie_title": movie_title,
            "rating": rating,
            "predicted_category": "Insufficient Evidence",
            "suspicion_score": 0.0,
            "confidence_percentage": 0.0,
            "processed_text": "",
            "warning_indicators": ["Review text is empty or too short for meaningful analysis."],
            "explanation": {
                "top_suspicious_features": [],
                "top_genuine_features": [],
                "explanation_summary": "Insufficient content provided to perform NLP vectorization."
            },
            "model_used": model_name,
            "limitations_notice": limitations["guidance"]
        }

    cleaned = clean_text(review_text)
    words = cleaned.split()

    if len(words) < 2:
        return {
            "review_id": review_id,
            "movie_title": movie_title,
            "rating": rating,
            "predicted_category": "Insufficient Evidence",
            "suspicion_score": 0.0,
            "confidence_percentage": 0.0,
            "processed_text": cleaned,
            "warning_indicators": ["Insufficient informative words after stopword and noise filtering."],
            "explanation": {
                "top_suspicious_features": [],
                "top_genuine_features": [],
                "explanation_summary": "No domain-relevant vocabulary found in review."
            },
            "model_used": model_name,
            "limitations_notice": limitations["guidance"]
        }

    # Vectorize and predict
    x_tfidf = vectorizer.transform([cleaned])
    probs = model.predict_proba(x_tfidf)[0]  # [prob_genuine, prob_fake]
    fake_prob = float(probs[1])

    # Explainability breakdown
    explanation = explain_prediction(review_text, vectorizer, model, model_name=model_name, rating=rating, movie_title=movie_title)
    warning_indicators = explanation.get("warning_indicators", [])

    # Heuristic adjustment: if strong rating dissonance or extreme spam signals detected, bump suspicion slightly
    adjusted_score = fake_prob
    if explanation.get("heuristic_signals", {}).get("rating_dissonance"):
        adjusted_score = min(1.0, adjusted_score + 0.15)
    
    # Categorization
    if adjusted_score >= 0.50:
        category = "Potentially Suspicious"
        confidence = round(adjusted_score * 100, 1)
    else:
        category = "More Likely Genuine"
        confidence = round((1.0 - adjusted_score) * 100, 1)

    return {
        "review_id": review_id,
        "movie_title": movie_title,
        "rating": rating,
        "predicted_category": category,
        "suspicion_score": round(adjusted_score, 4),
        "confidence_percentage": confidence,
        "processed_text": cleaned,
        "warning_indicators": warning_indicators,
        "explanation": explanation,
        "model_used": model_name,
        "limitations_notice": limitations["guidance"]
    }


def predict_batch_dataframe(df: pd.DataFrame, model_choice: str = "best") -> tuple[pd.DataFrame, dict]:
    """
    Performs batch detection across an uploaded DataFrame.
    Appends predictions, scores, warnings, and cosine similarity indicators.
    Preserves all original input columns.
    """
    model, model_name, vectorizer = get_selected_model(model_choice)
    limitations = get_ethical_limitations_notice()

    out_df = df.copy()

    # Ensure required text column exists
    if "review_text" not in out_df.columns:
        raise ValueError("Dataset missing mandatory 'review_text' column.")

    # Fill missing columns gracefully if absent
    if "review_id" not in out_df.columns:
        out_df["review_id"] = [f"REV-ROW-{i+1}" for i in range(len(out_df))]
    if "movie_title" not in out_df.columns:
        out_df["movie_title"] = "General"
    if "rating" not in out_df.columns:
        out_df["rating"] = np.nan

    # Vectorized / batch text cleaning
    raw_texts = out_df["review_text"].fillna("").astype(str).tolist()
    cleaned_texts = [clean_text(t) for t in raw_texts]
    out_df["processed_text"] = cleaned_texts

    # Batch similarity detection for duplicate/astroturfing campaigns
    similarity_info = analyze_batch_similarity(raw_texts, vectorizer)
    out_df["similarity_flag"] = [s["is_duplicate_or_near_duplicate"] for s in similarity_info]
    out_df["similarity_score"] = [s["max_similarity_score"] for s in similarity_info]

    # Pre-allocate result lists
    predicted_labels = []
    suspicion_scores = []
    warning_list = []

    # Identify eligible rows for TF-IDF
    eligible_indices = []
    eligible_cleaned = []
    for idx, c in enumerate(cleaned_texts):
        words = c.split()
        if len(words) >= 2:
            eligible_indices.append(idx)
            eligible_cleaned.append(c)

    # Batch TF-IDF transform and predict
    prob_map = {}
    if eligible_cleaned:
        x_batch = vectorizer.transform(eligible_cleaned)
        batch_probs = model.predict_proba(x_batch)[:, 1]
        for orig_idx, p in zip(eligible_indices, batch_probs):
            prob_map[orig_idx] = float(p)

    # Process all rows
    for idx, row in out_df.iterrows():
        raw_text = raw_texts[idx]
        rating_val = row["rating"] if pd.notna(row["rating"]) else None
        
        # Linguistic signals
        sig = extract_linguistic_signals(raw_text, rating=rating_val)
        warnings = sig["warning_indicators"].copy()

        # Add similarity warning if flagged
        if out_df.at[idx, "similarity_flag"]:
            warnings.append(f"High TF-IDF cosine similarity ({out_df.at[idx, 'similarity_score']:.2f}) to another review in batch")

        if idx not in prob_map:
            predicted_labels.append("Insufficient Evidence")
            suspicion_scores.append(0.0)
            warning_list.append("; ".join(warnings) if warnings else "Insufficient review length")
        else:
            base_score = prob_map[idx]
            if sig.get("rating_dissonance"):
                base_score = min(1.0, base_score + 0.15)
            
            # Label assignment
            if base_score >= 0.50:
                label = "Potentially Suspicious"
            else:
                label = "More Likely Genuine"

            predicted_labels.append(label)
            suspicion_scores.append(round(base_score, 4))
            warning_list.append("; ".join(warnings) if warnings else "None")

    out_df["predicted_label"] = predicted_labels
    out_df["suspicion_score"] = suspicion_scores
    out_df["warning_indicators"] = warning_list

    # Calculate summary statistics
    total_count = len(out_df)
    suspicious_count = int((out_df["predicted_label"] == "Potentially Suspicious").sum())
    genuine_count = int((out_df["predicted_label"] == "More Likely Genuine").sum())
    insufficient_count = int((out_df["predicted_label"] == "Insufficient Evidence").sum())
    valid_scores = [s for s, l in zip(suspicion_scores, predicted_labels) if l != "Insufficient Evidence"]
    avg_score = float(np.mean(valid_scores)) if valid_scores else 0.0

    summary = {
        "total_analyzed": total_count,
        "suspicious_count": suspicious_count,
        "genuine_count": genuine_count,
        "insufficient_count": insufficient_count,
        "suspicious_percentage": round((suspicious_count / total_count) * 100, 2) if total_count > 0 else 0.0,
        "average_suspicion_score": round(avg_score, 4),
        "model_used": model_name
    }

    return out_df, summary
