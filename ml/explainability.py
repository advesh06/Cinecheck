"""
CineCheck - Explainability & Interpretability Module
Covers TWSMA Module 6.1 (Explainability) & Module 6.2 (Ethics / Safeguards):
- TF-IDF Feature importance & linear contribution decomposition
- Positive (Suspicious) vs Negative (Genuine) influential n-grams
- Stylistic warning indicators (Excessive punctuation, shouting, repetitive praise)
- TF-IDF Cosine similarity analysis for duplicate & template astroturfing campaigns
- Responsible AI disclaimers and limitation guardrails
"""

import os
import sys
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from ml.preprocessing import clean_text, extract_linguistic_signals


def explain_prediction(text: str, vectorizer, model, model_name: str = "Logistic Regression", rating: float = None, movie_title: str = None, top_k: int = 6) -> dict:
    """
    Decomposes the prediction into human-interpretable feature contributions:
    - Extracts TF-IDF tokens present in the review
    - Calculates the individual contribution of each word/bigram
    - Identifies top tokens pulling towards 'Suspicious' and towards 'Genuine'
    - Integrates heuristic stylistic warning indicators
    """
    signals = extract_linguistic_signals(text, rating=rating, movie_title=movie_title)
    
    if signals.get("is_empty"):
        return {
            "top_suspicious_features": [],
            "top_genuine_features": [],
            "warning_indicators": signals.get("warning_indicators", ["Empty review content"]),
            "heuristic_signals": signals,
            "explanation_summary": "Review contains no decipherable text content."
        }

    cleaned = clean_text(text)
    if not cleaned.strip():
        return {
            "top_suspicious_features": [],
            "top_genuine_features": [],
            "warning_indicators": ["Insufficient meaningful vocabulary after preprocessing"],
            "heuristic_signals": signals,
            "explanation_summary": "All tokens were removed during stopword/noise filtering."
        }

    # Vectorize single review
    x_vec = vectorizer.transform([cleaned])
    feature_names = np.array(vectorizer.get_feature_names_out())
    nonzero_indices = x_vec.indices
    nonzero_values = x_vec.data

    if len(nonzero_indices) == 0:
        return {
            "top_suspicious_features": [],
            "top_genuine_features": [],
            "warning_indicators": signals.get("warning_indicators", []),
            "heuristic_signals": signals,
            "explanation_summary": "Review vocabulary does not overlap with the model's learned TF-IDF feature space."
        }

    # Calculate feature contributions based on model architecture
    contributions = []
    if hasattr(model, "coef_"):
        # Logistic Regression: coef * tfidf_val
        coefs = model.coef_[0]
        for idx, val in zip(nonzero_indices, nonzero_values):
            feat_name = feature_names[idx]
            contrib = float(val * coefs[idx])
            contributions.append((feat_name, contrib))
    elif hasattr(model, "feature_log_prob_"):
        # Multinomial Naive Bayes: log(P(w|fake)) - log(P(w|genuine))
        diff_log_probs = model.feature_log_prob_[1] - model.feature_log_prob_[0]
        for idx, val in zip(nonzero_indices, nonzero_values):
            feat_name = feature_names[idx]
            contrib = float(val * diff_log_probs[idx])
            contributions.append((feat_name, contrib))
    else:
        for idx, val in zip(nonzero_indices, nonzero_values):
            contributions.append((feature_names[idx], 0.0))

    # Sort contributions
    suspicious_pull = [
        {"feature": feat, "weight": round(weight, 4), "impact": "Pulls toward Suspicious"}
        for feat, weight in sorted(contributions, key=lambda x: x[1], reverse=True)
        if weight > 0
    ][:top_k]

    genuine_pull = [
        {"feature": feat, "weight": round(abs(weight), 4), "impact": "Pulls toward Genuine"}
        for feat, weight in sorted(contributions, key=lambda x: x[1])
        if weight < 0
    ][:top_k]

    # Narrative explanation summary
    summary_parts = []
    if suspicious_pull:
        top_susp_words = [f"'{f['feature']}'" for f in suspicious_pull[:3]]
        summary_parts.append(f"Tokens {', '.join(top_susp_words)} increased the suspicion score.")
    if genuine_pull:
        top_gen_words = [f"'{f['feature']}'" for f in genuine_pull[:3]]
        summary_parts.append(f"Contextual elements like {', '.join(top_gen_words)} aligned with organic genuine patterns.")
    if signals["warning_indicators"]:
        summary_parts.append(f"Heuristic triggers: {'; '.join(signals['warning_indicators'][:2])}.")

    explanation_summary = " ".join(summary_parts) if summary_parts else "Balanced linguistic signals with moderate confidence."

    return {
        "top_suspicious_features": suspicious_pull,
        "top_genuine_features": genuine_pull,
        "warning_indicators": signals["warning_indicators"],
        "heuristic_signals": signals,
        "explanation_summary": explanation_summary
    }


def analyze_batch_similarity(texts: list, vectorizer, similarity_threshold: float = 0.82) -> list:
    """
    Computes TF-IDF Cosine Similarity across a batch of reviews to identify
    potential astroturfing campaigns, bot syndication, or copy-paste duplicates.
    Returns a list of dicts with similarity flags and max similarity scores.
    """
    if not texts:
        return []

    cleaned_texts = [clean_text(t) for t in texts]
    # Filter empty texts for matrix computation
    valid_indices = [i for i, t in enumerate(cleaned_texts) if t.strip()]
    
    results = [
        {
            "is_duplicate_or_near_duplicate": False,
            "max_similarity_score": 0.0,
            "similar_to_index": None
        }
        for _ in range(len(texts))
    ]

    if len(valid_indices) < 2:
        return results

    sub_texts = [cleaned_texts[i] for i in valid_indices]
    tfidf_matrix = vectorizer.transform(sub_texts)
    sim_matrix = cosine_similarity(tfidf_matrix)

    # Ignore self-similarity (diagonal)
    np.fill_diagonal(sim_matrix, 0.0)

    for sub_idx, original_idx in enumerate(valid_indices):
        max_sim = float(np.max(sim_matrix[sub_idx]))
        if max_sim >= similarity_threshold:
            best_match_sub = int(np.argmax(sim_matrix[sub_idx]))
            best_match_orig = valid_indices[best_match_sub]
            results[original_idx] = {
                "is_duplicate_or_near_duplicate": True,
                "max_similarity_score": round(max_sim, 3),
                "similar_to_index": best_match_orig
            }
        else:
            results[original_idx] = {
                "is_duplicate_or_near_duplicate": False,
                "max_similarity_score": round(max_sim, 3),
                "similar_to_index": None
            }

    return results


def get_ethical_limitations_notice() -> dict:
    """
    Provides clear responsible AI limitations for CineCheck (TWSMA Module 6.2).
    """
    return {
        "title": "Responsible AI & Operational Limitations",
        "guidance": (
            "1. Probabilistic Warning Only: A review flagged as 'Potentially Suspicious' represents an "
            "algorithmic pattern match (repetitive praise, extreme polarity, promotional keywords), not proof of deception.\n"
            "2. False Accusation Safeguards: Enthusiastic human viewers frequently use excited phrases and exclamation "
            "marks. Human moderation is mandatory before taking moderation or account actions.\n"
            "3. Bias Transparency: Statistical classifiers may show varying error rates across regional linguistic patterns, "
            "short reviews, or niche cinematic genres."
        )
    }
