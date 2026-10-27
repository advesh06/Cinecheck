"""
CineCheck - Unit Tests for Prediction Pipeline
Tests single inference, edge cases, batch inference, and similarity detection.
"""

import sys
import os
import unittest
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from ml.predict import predict_single_review, predict_batch_dataframe


class TestPredictionPipeline(unittest.TestCase):

    def test_empty_or_short_review_insufficient_evidence(self):
        res = predict_single_review("", movie_title="Test")
        self.assertEqual(res["predicted_category"], "Insufficient Evidence")
        self.assertEqual(res["suspicion_score"], 0.0)

        res_short = predict_single_review("ok", movie_title="Test")
        self.assertEqual(res_short["predicted_category"], "Insufficient Evidence")

    def test_suspicious_hype_review(self):
        hype = "ALL TIME HISTORIC BLOCKBUSTER RECORD BREAKER!! GO BOOK TICKETS RIGHT NOW! 🔥🔥🔥 10/10 MASTERPIECE PAISA VASOOL!"
        res = predict_single_review(hype, movie_title="War 2", rating=5.0)
        self.assertEqual(res["predicted_category"], "Potentially Suspicious")
        self.assertGreaterEqual(res["suspicion_score"], 0.50)
        self.assertTrue(len(res["warning_indicators"]) > 0)
        self.assertIn("top_suspicious_features", res["explanation"])

    def test_genuine_critical_review(self):
        genuine = (
            "The cinematography and visual scale are truly commendable. While the second half drags slightly in pacing, "
            "the lead actor delivers a commanding performance that keeps you invested until the climax."
        )
        res = predict_single_review(genuine, movie_title="Chhaava", rating=3.5)
        self.assertEqual(res["predicted_category"], "More Likely Genuine")
        self.assertLess(res["suspicion_score"], 0.50)
        self.assertIn("top_genuine_features", res["explanation"])

    def test_batch_prediction_dataframe(self):
        sample_data = pd.DataFrame([
            {
                "review_id": "TEST-01",
                "movie_title": "Chhaava",
                "review_text": "A well-crafted theatrical experience with impressive sound design and tight screenplay.",
                "rating": 4.0
            },
            {
                "review_id": "TEST-02",
                "movie_title": "War 2",
                "review_text": "ALL TIME BLOCKBUSTER GO BOOK TICKETS NOW 🔥🔥 10/10 PAISA VASOOL!",
                "rating": 5.0
            },
            {
                "review_id": "TEST-03",
                "movie_title": "Fateh",
                "review_text": "", # Empty row
                "rating": 3.0
            }
        ])

        out_df, summary = predict_batch_dataframe(sample_data, model_choice="best")
        
        self.assertEqual(len(out_df), 3)
        self.assertIn("predicted_label", out_df.columns)
        self.assertIn("suspicion_score", out_df.columns)
        self.assertIn("warning_indicators", out_df.columns)

        self.assertEqual(summary["total_analyzed"], 3)
        self.assertEqual(out_df.loc[0, "predicted_label"], "More Likely Genuine")
        self.assertEqual(out_df.loc[1, "predicted_label"], "Potentially Suspicious")
        self.assertEqual(out_df.loc[2, "predicted_label"], "Insufficient Evidence")


if __name__ == "__main__":
    unittest.main()
