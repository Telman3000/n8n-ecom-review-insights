"""Tests for rule-based fallback analyzer."""

import pytest

from service.analyzer_fallback import FallbackAnalyzer
from service.schemas import Priority, ReviewInput, Sentiment


@pytest.fixture
def analyzer():
    """Create fallback analyzer instance."""
    return FallbackAnalyzer()


def test_sentiment_positive_keywords(analyzer):
    """Test positive sentiment detection from keywords."""
    review = ReviewInput(
        id="1", text="Отличный товар! Качественный и прекрасный. Рекомендую!", rating=None
    )
    sentiment = analyzer.analyze_sentiment(review)
    assert sentiment == Sentiment.POSITIVE


def test_sentiment_negative_keywords(analyzer):
    """Test negative sentiment detection from keywords."""
    review = ReviewInput(
        id="2", text="Ужасная покупка! Плохое качество, разочарован. Брак!", rating=None
    )
    sentiment = analyzer.analyze_sentiment(review)
    assert sentiment == Sentiment.NEGATIVE


def test_sentiment_from_rating_high(analyzer):
    """Test sentiment detection from high rating."""
    review = ReviewInput(id="3", text="Нормально", rating=5)
    sentiment = analyzer.analyze_sentiment(review)
    assert sentiment == Sentiment.POSITIVE


def test_sentiment_from_rating_low(analyzer):
    """Test sentiment detection from low rating."""
    review = ReviewInput(id="4", text="Нормально", rating=1)
    sentiment = analyzer.analyze_sentiment(review)
    assert sentiment == Sentiment.NEGATIVE


def test_sentiment_neutral(analyzer):
    """Test neutral sentiment detection."""
    review = ReviewInput(id="5", text="Обычный товар, ничего особенного.", rating=3)
    sentiment = analyzer.analyze_sentiment(review)
    assert sentiment == Sentiment.NEUTRAL


def test_extract_topics_delivery(analyzer):
    """Test delivery topic extraction."""
    text = "Быстрая доставка, курьер привез вовремя."
    topics = analyzer.extract_topics(text)
    assert "доставка" in topics


def test_extract_topics_quality(analyzer):
    """Test quality topic extraction."""
    text = "Качество материала отличное, хорошая сборка."
    topics = analyzer.extract_topics(text)
    assert "качество" in topics


def test_extract_topics_price(analyzer):
    """Test price topic extraction."""
    text = "Цена завышена, слишком дорого для такого качества."
    topics = analyzer.extract_topics(text)
    assert "цена" in topics


def test_extract_topics_multiple(analyzer):
    """Test extraction of multiple topics."""
    text = "Быстрая доставка, хорошее качество, адекватная цена."
    topics = analyzer.extract_topics(text)
    assert len(topics) >= 2
    assert "доставка" in topics or "качество" in topics or "цена" in topics


def test_extract_complaints(analyzer):
    """Test complaint extraction."""
    text = "Товар не работает, сломался через день. Не пришла инструкция."
    complaints = analyzer.extract_complaints(text)
    assert len(complaints) > 0


def test_priority_critical(analyzer):
    """Test critical priority for negative sentiment with multiple complaints."""
    sentiment = Sentiment.NEGATIVE
    complaints = ["не работает", "сломался"]
    priority = analyzer.determine_priority(sentiment, complaints)
    assert priority == Priority.CRITICAL


def test_priority_high(analyzer):
    """Test high priority for negative sentiment with one complaint."""
    sentiment = Sentiment.NEGATIVE
    complaints = ["не работает"]
    priority = analyzer.determine_priority(sentiment, complaints)
    assert priority == Priority.HIGH


def test_priority_low(analyzer):
    """Test low priority for positive sentiment."""
    sentiment = Sentiment.POSITIVE
    complaints = []
    priority = analyzer.determine_priority(sentiment, complaints)
    assert priority == Priority.LOW


def test_analyze_single_review(analyzer):
    """Test complete analysis of a single review."""
    review = ReviewInput(
        id="test1",
        text="Отличный товар! Быстрая доставка, качество супер. Рекомендую!",
        rating=5,
    )
    result = analyzer.analyze(review)

    assert result["id"] == "test1"
    assert result["sentiment"] == Sentiment.POSITIVE
    assert isinstance(result["topics"], list)
    assert isinstance(result["complaints"], list)
    assert result["priority"] == Priority.LOW


def test_analyze_batch(analyzer):
    """Test batch analysis with summary."""
    reviews = [
        ReviewInput(id="1", text="Отличный товар!", rating=5),
        ReviewInput(id="2", text="Ужасное качество!", rating=1),
        ReviewInput(id="3", text="Нормально", rating=3),
    ]

    results, summary = analyzer.analyze_batch(reviews)

    assert len(results) == 3
    assert summary["total_reviews"] == 3
    assert "sentiment_distribution" in summary
    assert "priority_distribution" in summary
    assert "top_topics" in summary
    assert "top_complaints" in summary
