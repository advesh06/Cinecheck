"""
CineCheck - API End-to-End Tests
Tests Flask REST API endpoints using Flask test client.
"""

import sys
import os
import unittest
import json
import io

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from backend.app import create_app


class TestCineCheckAPI(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.client = cls.app.test_client()

    def test_health_endpoint(self):
        res = self.client.get("/api/health")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["status"], "healthy")
        self.assertEqual(data["version"], "1.0.0")

    def test_datasets_list(self):
        res = self.client.get("/api/datasets")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("datasets", data)

    def test_single_review_analysis_api(self):
        payload = {
            "movie_title": "War 2",
            "review_text": "ALL TIME BLOCKBUSTER GO BOOK TICKETS NOW!! 10/10 PAISA VASOOL!",
            "rating": 5.0,
            "model_choice": "best"
        }
        res = self.client.post(
            "/api/reviews/analyse",
            data=json.dumps(payload),
            content_type="application/json"
        )
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["predicted_category"], "Potentially Suspicious")
        self.assertIn("suspicion_score", data)
        self.assertIn("explanation", data)

    def test_analytics_summary_api(self):
        res = self.client.get("/api/analytics/summary")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("total_reviews", data)
        self.assertIn("suspicious_percentage", data)
        self.assertIn("rating_distribution", data)

    def test_model_evaluation_api(self):
        res = self.client.get("/api/model/evaluation")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("logistic_regression", data)
        self.assertIn("naive_bayes", data)
        self.assertIn("comparison", data)

    def test_upload_invalid_file_format(self):
        data = {
            "file": (io.BytesIO(b"fake content"), "malicious.exe")
        }
        res = self.client.post(
            "/api/datasets/upload",
            data=data,
            content_type="multipart/form-data"
        )
        self.assertEqual(res.status_code, 400)
        json_data = res.get_json()
        self.assertIn("error", json_data)


if __name__ == "__main__":
    unittest.main()
