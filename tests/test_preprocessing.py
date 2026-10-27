"""
CineCheck - Unit Tests for NLP Preprocessing Pipeline
Tests tokenization, normalization, negation preservation, and signal extraction.
"""

import sys
import os
import unittest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from ml.preprocessing import (
    clean_text,
    normalize_repeated_characters,
    normalize_excessive_punctuation,
    extract_linguistic_signals
)


class TestNLPPreprocessing(unittest.TestCase):

    def test_empty_and_none_text(self):
        self.assertEqual(clean_text(""), "")
        self.assertEqual(clean_text(None), "")
        self.assertEqual(clean_text("   "), "")

    def test_repeated_characters_normalization(self):
        raw = "sooooo goooood"
        normalized = normalize_repeated_characters(raw)
        # Should compress repetitions > 2 down to 2
        self.assertEqual(normalized, "soo good")

    def test_excessive_punctuation_normalization(self):
        raw = "Amazing movie!!!!!! Really?????"
        normalized = normalize_excessive_punctuation(raw)
        self.assertIn("!", normalized)
        self.assertNotIn("!!!!!!", normalized)

    def test_negation_preservation(self):
        # Crucial TWSMA requirement: Do NOT remove meaningful negation words
        text = "This film is not good and never works without proper pacing"
        cleaned = clean_text(text, preserve_negations=True)
        tokens = cleaned.split()
        self.assertIn("not", tokens)
        self.assertIn("never", tokens)
        self.assertIn("without", tokens)

    def test_url_and_email_stripping(self):
        text = "Visit https://bookmyshow.com or mail pr@studio.com for bookings"
        cleaned = clean_text(text)
        self.assertNotIn("http", cleaned)
        self.assertNotIn("bookmyshow.com", cleaned)
        self.assertNotIn("pr@studio.com", cleaned)

    def test_linguistic_signals_extraction(self):
        shouting_spam = "ALL TIME BLOCKBUSTER GO BOOK TICKETS NOW!!!!! BEST MOVIE EVER!!!"
        signals = extract_linguistic_signals(shouting_spam, rating=5.0)

        self.assertFalse(signals["is_empty"])
        self.assertGreater(signals["uppercase_ratio"], 0.5)
        self.assertGreaterEqual(signals["exclamation_count"], 5)
        self.assertTrue(len(signals["warning_indicators"]) > 0)
        self.assertTrue(any("capitalization" in w.lower() or "exclamation" in w.lower() for w in signals["warning_indicators"]))

    def test_rating_sentiment_dissonance(self):
        # 1-star rating with blockbuster praise
        praise_text = "ALL TIME BLOCKBUSTER MASTERPIECE MUST WATCH GO BOOK TICKETS"
        signals = extract_linguistic_signals(praise_text, rating=1.0)
        self.assertTrue(signals["rating_dissonance"])
        self.assertTrue(any("mismatch" in w.lower() for w in signals["warning_indicators"]))


if __name__ == "__main__":
    unittest.main()
