"""
CineCheck - Review Detector Module Interface
Provides direct functional interface for review analysis, prediction, and feature attribution.
Developer: Advesh Tambat (Roll No: 23108A0013)
"""

import sys
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from ml.predict import (
    predict_single_review,
    predict_batch_dataframe,
    get_selected_model,
    load_artifacts
)
from ml.explainability import (
    explain_prediction,
    analyze_batch_similarity,
    get_ethical_limitations_notice
)
from ml.preprocessing import (
    clean_text,
    extract_linguistic_signals
)

# Standard aliases
analyze_review = predict_single_review
analyze_batch = predict_batch_dataframe
