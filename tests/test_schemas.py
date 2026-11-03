"""Tests for Pydantic schemas."""

import pytest
from pydantic import ValidationError

from service.schemas import (
    AnalysisResponse,
    BatchSummary,
    Priority,
    ReviewAnalysisRequest,
    ReviewAnalysisResult,
    ReviewInput,
    Sentiment,
)


def test_review_input_valid():
    """Test valid ReviewInput creation."""
    review = ReviewInput(id="test1", text="Отличный товар!", rating=5)
    assert review.id == "test1"
    assert review.text == "Отличный товар!"
    assert review.rating == 5


def test_review_input_without_rating():
    """Test ReviewInput without rating."""
    review = ReviewInput(id="test1", text="Отличный товар!")
    assert review.id == "test1"
    assert review.rating is None


def test_review_input_invalid_rating_too_high():
    """Test ReviewInput with rating too high."""
    with pytest.raises(ValidationError):
        ReviewInput(id="test1", text="Test", rating=6)


def test_review_input_invalid_rating_too_low():
    """Test ReviewInput with rating too low."""
    with pytest.raises(ValidationError):
        ReviewInput(id="test1", text="Test", rating=0)


def test_review_input_missing_id():
    """Test ReviewInput without id."""
    with pytest.raises(ValidationError):
        ReviewInput(text="Test")


def test_review_input_missing_text():
    """Test ReviewInput without text."""
    with pytest.raises(ValidationError):
        ReviewInput(id="test1")


def test_review_analysis_request_valid():
    """Test valid ReviewAnalysisRequest."""
    request = ReviewAnalysisRequest(reviews=[ReviewInput(id="1", text="Test", rating=5)])
    assert len(request.reviews) == 1


def test_review_analysis_request_empty_list():
    """Test ReviewAnalysisRequest with empty reviews list."""
    with pytest.raises(ValidationError):
        ReviewAnalysisRequest(reviews=[])


def test_review_analysis_result_valid():
    """Test valid ReviewAnalysisResult."""
    result = ReviewAnalysisResult(
        id="test1",
        sentiment=Sentiment.POSITIVE,
        topics=["доставка", "качество"],
        complaints=["не пришла инструкция"],
        priority=Priority.MEDIUM,
    )
    assert result.id == "test1"
    assert result.sentiment == Sentiment.POSITIVE
    assert len(result.topics) == 2
    assert len(result.complaints) == 1
    assert result.priority == Priority.MEDIUM


def test_review_analysis_result_default_lists():
    """Test ReviewAnalysisResult with default empty lists."""
    result = ReviewAnalysisResult(id="test1", sentiment=Sentiment.NEUTRAL, priority=Priority.LOW)
    assert result.topics == []
    assert result.complaints == []


def test_batch_summary_valid():
    """Test valid BatchSummary."""
    summary = BatchSummary(
        total_reviews=10,
        sentiment_distribution={
            Sentiment.POSITIVE: 5,
            Sentiment.NEUTRAL: 3,
            Sentiment.NEGATIVE: 2,
        },
        priority_distribution={
            Priority.LOW: 5,
            Priority.MEDIUM: 3,
            Priority.HIGH: 1,
            Priority.CRITICAL: 1,
        },
        top_topics=["доставка", "качество", "цена"],
        top_complaints=["не пришла инструкция"],
    )
    assert summary.total_reviews == 10
    assert len(summary.sentiment_distribution) == 3
    assert len(summary.top_topics) == 3


def test_analysis_response_valid():
    """Test valid AnalysisResponse."""
    results = [
        ReviewAnalysisResult(id="1", sentiment=Sentiment.POSITIVE, priority=Priority.LOW),
        ReviewAnalysisResult(id="2", sentiment=Sentiment.NEGATIVE, priority=Priority.HIGH),
    ]
    summary = BatchSummary(
        total_reviews=2,
        sentiment_distribution={Sentiment.POSITIVE: 1, Sentiment.NEGATIVE: 1},
        priority_distribution={Priority.LOW: 1, Priority.HIGH: 1},
        top_topics=["доставка"],
        top_complaints=["сломался"],
    )
    response = AnalysisResponse(results=results, summary=summary)
    assert len(response.results) == 2
    assert response.summary.total_reviews == 2


def test_sentiment_enum_values():
    """Test Sentiment enum values."""
    assert Sentiment.POSITIVE.value == "positive"
    assert Sentiment.NEUTRAL.value == "neutral"
    assert Sentiment.NEGATIVE.value == "negative"


def test_priority_enum_values():
    """Test Priority enum values."""
    assert Priority.LOW.value == "low"
    assert Priority.MEDIUM.value == "medium"
    assert Priority.HIGH.value == "high"
    assert Priority.CRITICAL.value == "critical"
