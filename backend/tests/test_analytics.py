import pytest
from app.services.analytics import DocumentAnalyticsService

def test_analytics_empty_text():
    res = DocumentAnalyticsService.analyze_readability("")
    assert res["word_count"] == 0
    assert res["char_count"] == 0
    assert res["flesch_reading_ease"] == 100.0
    assert res["readability_level"] == "N/A"

def test_analytics_sample_text():
    text = "Lemma is an advanced academic text rewriting and plagiarism detection platform. It processes documents with high performance."
    res = DocumentAnalyticsService.analyze_readability(text, sentence_count=2)
    
    assert res["word_count"] > 10
    assert res["char_count"] == len(text)
    assert res["avg_sentence_length"] > 0
    assert 0 <= res["flesch_reading_ease"] <= 100
    assert res["readability_level"] != "N/A"
    assert res["reading_time_seconds"] > 0
