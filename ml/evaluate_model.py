"""
CineCheck - Model Evaluation Module
Covers TWSMA Module 2.1 & Module 2.3:
- Retrieves held-out test evaluation metrics
- Compares Logistic Regression vs Multinomial Naive Bayes
- Generates Confusion Matrix Breakdown (TN, FP, FN, TP)
- Performs subgroup/bias analysis across ratings
"""

import os
import sys
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

EVAL_PATH = os.path.join(BASE_DIR, "ml", "saved_models", "evaluation_results.json")


def get_evaluation_metrics() -> dict:
    """
    Returns precomputed held-out test evaluation metrics.
    If not yet saved, invokes training pipeline to generate them.
    """
    if not os.path.exists(EVAL_PATH):
        from ml.train_model import train_models
        return train_models()

    with open(EVAL_PATH, "r") as f:
        return json.load(f)


def print_evaluation_summary():
    metrics = get_evaluation_metrics()
    print("=" * 65)
    print("       CINECHECK - MODEL EVALUATION & COMPARISON REPORT")
    print("=" * 65)
    print(f"Selected Best Classifier: {metrics['selected_best_model']}")
    print(f"Training Samples: {metrics['train_sample_size']} | Held-out Test Samples: {metrics['test_sample_size']}")
    print(f"TF-IDF Vocabulary Size: {metrics['vocabulary_size']} features\n")

    print("-" * 65)
    print(f"{'Metric':<20} | {'Logistic Regression':<20} | {'Naive Bayes':<20}")
    print("-" * 65)
    for row in metrics["comparison"]:
        print(f"{row['metric']:<20} | {row['logistic_regression']:<20.4f} | {row['naive_bayes']:<20.4f}")
    print("-" * 65)

    print("\n[Confusion Matrix - Logistic Regression]")
    lr_cm = metrics["logistic_regression"]["confusion_matrix_breakdown"]
    print(f"  True Genuine: {lr_cm['true_genuine']:<4} | False Suspicious (FP): {lr_cm['false_suspicious']:<4}")
    print(f"  False Genuine (FN): {lr_cm['false_genuine']:<4} | True Suspicious: {lr_cm['true_suspicious']:<4}")

    print("\n[Bias / Subgroup Disparity Analysis]")
    for grp, data in metrics["bias_analysis"]["rating_subgroups"].items():
        print(f"  - {grp}: N={data['sample_count']}, Acc={data['accuracy']}, F1={data['f1_score']}")

    print("\n[Responsible AI Notice]")
    print(metrics["ethical_safeguard_note"])
    print("=" * 65)


if __name__ == "__main__":
    print_evaluation_summary()
