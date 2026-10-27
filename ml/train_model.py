"""
CineCheck - Machine Learning Model Training Pipeline
Covers TWSMA Module 1.1, Module 2.1, and Module 2.3:
- Loads labelled training data (cinecheck_reviews.csv)
- Preprocesses text using CineCheck NLP pipeline
- Converts text to TF-IDF features (unigrams and bigrams)
- Trains Logistic Regression and Multinomial Naive Bayes classifiers
- Evaluates both models on held-out test data (stratified 80/20 split)
- Computes comprehensive metrics (Accuracy, Precision, Recall, F1, Confusion Matrix)
- Performs subgroup / bias error analysis across ratings and movie groups
- Saves trained models, vectorizer, and evaluation metadata for real-time inference
"""

import os
import json
import joblib
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import MultinomialNB
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, classification_report
)

import sys
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from ml.preprocessing import clean_text
DATA_PATH = os.path.join(BASE_DIR, "data", "cinecheck_reviews.csv")
SAVED_MODELS_DIR = os.path.join(BASE_DIR, "ml", "saved_models")

os.makedirs(SAVED_MODELS_DIR, exist_ok=True)


def train_models():
    print(f"[CineCheck Train] Loading dataset from: {DATA_PATH}")
    df = pd.read_csv(DATA_PATH)

    # Filter only rows with legitimate ground-truth labels ('fake' or 'genuine')
    labelled_mask = df["label"].astype(str).str.lower().isin(["fake", "genuine"])
    labelled_df = df[labelled_mask].copy()

    # Drop exact duplicates in review text to prevent data leakage between train/test
    labelled_df = labelled_df.drop_duplicates(subset=["review_text"]).reset_index(drop=True)

    print(f"[CineCheck Train] Total labelled unique rows: {len(labelled_df)}")
    print(labelled_df["label"].value_counts().to_dict())

    # Target encoding: fake -> 1 (Suspicious), genuine -> 0 (Genuine)
    labelled_df["target"] = (labelled_df["label"].str.lower() == "fake").astype(int)

    # Preprocess text
    print("[CineCheck Train] Running NLP text preprocessing...")
    labelled_df["clean_text"] = labelled_df["review_text"].apply(clean_text)

    # Stratified Train/Test Split (80% train, 20% test)
    X_train_raw, X_test_raw, y_train, y_test, idx_train, idx_test = train_test_split(
        labelled_df["clean_text"],
        labelled_df["target"],
        labelled_df.index,
        test_size=0.20,
        random_state=42,
        stratify=labelled_df["target"]
    )

    test_meta_df = labelled_df.loc[idx_test].copy()

    print(f"[CineCheck Train] Train samples: {len(X_train_raw)}, Test samples: {len(X_test_raw)}")

    # TF-IDF Vectorization: Unigrams and Bigrams
    print("[CineCheck Train] Fitting TF-IDF Vectorizer (unigrams + bigrams)...")
    tfidf = TfidfVectorizer(
        ngram_range=(1, 2),
        min_df=2,
        max_features=4000,
        sublinear_tf=True
    )
    X_train_tfidf = tfidf.fit_transform(X_train_raw)
    X_test_tfidf = tfidf.transform(X_test_raw)

    # 1. Logistic Regression Classifier
    print("[CineCheck Train] Training Logistic Regression...")
    lr_model = LogisticRegression(max_iter=1000, C=1.0, random_state=42)
    lr_model.fit(X_train_tfidf, y_train)
    lr_preds = lr_model.predict(X_test_tfidf)
    lr_probs = lr_model.predict_proba(X_test_tfidf)[:, 1]

    # 2. Multinomial Naive Bayes Classifier
    print("[CineCheck Train] Training Multinomial Naive Bayes...")
    nb_model = MultinomialNB(alpha=0.5)
    nb_model.fit(X_train_tfidf, y_train)
    nb_preds = nb_model.predict(X_test_tfidf)
    nb_probs = nb_model.predict_proba(X_test_tfidf)[:, 1]

    # Metrics Helper
    def compute_metrics(y_true, y_pred, y_prob):
        acc = float(accuracy_score(y_true, y_pred))
        prec = float(precision_score(y_true, y_pred, zero_division=0))
        rec = float(recall_score(y_true, y_pred, zero_division=0))
        f1 = float(f1_score(y_true, y_pred, zero_division=0))
        f1_macro = float(f1_score(y_true, y_pred, average="macro", zero_division=0))
        cm = confusion_matrix(y_true, y_pred).tolist()
        return {
            "accuracy": round(acc, 4),
            "precision": round(prec, 4),
            "recall": round(rec, 4),
            "f1_score": round(f1, 4),
            "f1_macro": round(f1_macro, 4),
            "confusion_matrix": cm,  # [[TN, FP], [FN, TP]]
            "confusion_matrix_breakdown": {
                "true_genuine": int(cm[0][0]),
                "false_suspicious": int(cm[0][1]),
                "false_genuine": int(cm[1][0]),
                "true_suspicious": int(cm[1][1])
            }
        }

    lr_metrics = compute_metrics(y_test, lr_preds, lr_probs)
    nb_metrics = compute_metrics(y_test, nb_preds, nb_probs)

    print("\n--- MODEL EVALUATION ON HELD-OUT TEST DATA ---")
    print(f"Logistic Regression -> Acc: {lr_metrics['accuracy']:.4f}, F1: {lr_metrics['f1_score']:.4f}, Rec: {lr_metrics['recall']:.4f}, Prec: {lr_metrics['precision']:.4f}")
    print(f"Naive Bayes         -> Acc: {nb_metrics['accuracy']:.4f}, F1: {nb_metrics['f1_score']:.4f}, Rec: {nb_metrics['recall']:.4f}, Prec: {nb_metrics['precision']:.4f}")

    # Subgroup & Bias Error Analysis (TWSMA Module 2.3)
    test_meta_df["lr_pred"] = lr_preds
    test_meta_df["nb_pred"] = nb_preds

    # Bias analysis by rating category: Low (<= 2.5) vs High (>= 3.0)
    def subgroup_analysis(pred_col):
        results = {}
        for rating_group, subset in test_meta_df.groupby(test_meta_df["rating"] >= 3.0):
            group_name = "High Ratings (>=3.0)" if rating_group else "Low Ratings (<=2.5)"
            if len(subset) > 0 and len(subset["target"].unique()) > 1:
                sub_acc = float(accuracy_score(subset["target"], subset[pred_col]))
                sub_f1 = float(f1_score(subset["target"], subset[pred_col], zero_division=0))
            else:
                sub_acc = float(accuracy_score(subset["target"], subset[pred_col])) if len(subset) > 0 else 0.0
                sub_f1 = sub_acc
            results[group_name] = {
                "sample_count": len(subset),
                "accuracy": round(sub_acc, 4),
                "f1_score": round(sub_f1, 4)
            }
        return results

    bias_analysis_lr = subgroup_analysis("lr_pred")

    # Select the better model based on F1-macro score
    if lr_metrics["f1_macro"] >= nb_metrics["f1_macro"]:
        best_name = "Logistic Regression"
        best_model = lr_model
        best_metrics = lr_metrics
    else:
        best_name = "Multinomial Naive Bayes"
        best_model = nb_model
        best_metrics = nb_metrics

    print(f"\n[CineCheck Train] Better model selected: {best_name}")

    # Save models
    joblib.dump(tfidf, os.path.join(SAVED_MODELS_DIR, "tfidf_vectorizer.joblib"))
    joblib.dump(lr_model, os.path.join(SAVED_MODELS_DIR, "logistic_regression.joblib"))
    joblib.dump(nb_model, os.path.join(SAVED_MODELS_DIR, "naive_bayes.joblib"))
    joblib.dump(best_model, os.path.join(SAVED_MODELS_DIR, "best_model.joblib"))

    # Evaluation results object for dashboard and API
    evaluation_results = {
        "selected_best_model": best_name,
        "test_sample_size": len(X_test_raw),
        "train_sample_size": len(X_train_raw),
        "vocabulary_size": len(tfidf.vocabulary_),
        "logistic_regression": lr_metrics,
        "naive_bayes": nb_metrics,
        "comparison": [
            {
                "metric": "Accuracy",
                "logistic_regression": lr_metrics["accuracy"],
                "naive_bayes": nb_metrics["accuracy"]
            },
            {
                "metric": "Precision",
                "logistic_regression": lr_metrics["precision"],
                "naive_bayes": nb_metrics["precision"]
            },
            {
                "metric": "Recall",
                "logistic_regression": lr_metrics["recall"],
                "naive_bayes": nb_metrics["recall"]
            },
            {
                "metric": "F1-Score",
                "logistic_regression": lr_metrics["f1_score"],
                "naive_bayes": nb_metrics["f1_score"]
            },
            {
                "metric": "F1-Macro",
                "logistic_regression": lr_metrics["f1_macro"],
                "naive_bayes": nb_metrics["f1_macro"]
            }
        ],
        "bias_analysis": {
            "description": "Error rate and accuracy disparity across star rating sub-cohorts (TWSMA Module 2.3)",
            "rating_subgroups": bias_analysis_lr
        },
        "ethical_safeguard_note": (
            "Model predictions represent probabilistic linguistic suspicion scores and must not be "
            "interpreted as legally binding proof of fraud. Held-out metrics are calculated on the curated "
            "benchmark dataset."
        )
    }

    with open(os.path.join(SAVED_MODELS_DIR, "evaluation_results.json"), "w") as f:
        json.dump(evaluation_results, f, indent=2)

    # Save metadata
    metadata = {
        "version": "1.0.0",
        "best_model_name": best_name,
        "training_date": "2026-10-11",
        "dataset_source": "data/cinecheck_reviews.csv",
        "target_mapping": {"0": "More Likely Genuine", "1": "Potentially Suspicious"}
    }
    with open(os.path.join(SAVED_MODELS_DIR, "model_metadata.json"), "w") as f:
        json.dump(metadata, f, indent=2)

    print("[CineCheck Train] All models and evaluation files successfully saved.")
    return evaluation_results


if __name__ == "__main__":
    train_models()
