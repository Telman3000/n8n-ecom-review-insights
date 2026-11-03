"""Tests for LLM analyzer with mocked client."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from service.analyzer_llm import LLMAnalyzer
from service.schemas import Priority, ReviewInput, Sentiment


@pytest.fixture
def mock_openai_response():
    """Create mock OpenAI response."""
    mock_response = MagicMock()
    mock_choice = MagicMock()
    mock_message = MagicMock()
    mock_message.content = """{
        "sentiment": "positive",
        "topics": ["доставка", "качество"],
        "complaints": [],
        "priority": "low"
    }"""
    mock_choice.message = mock_message
    mock_response.choices = [mock_choice]
    return mock_response


@pytest.fixture
def mock_openai_client(mock_openai_response):
    """Create mocked OpenAI client."""
    mock_client = MagicMock()
    mock_client.chat = MagicMock()
    mock_client.chat.completions = MagicMock()
    mock_client.chat.completions.create = AsyncMock(return_value=mock_openai_response)
    return mock_client


@pytest.mark.asyncio
async def test_llm_analyze_single_review(mock_openai_client):
    """Test LLM analysis of a single review."""
    analyzer = LLMAnalyzer()
    analyzer.client = mock_openai_client

    review = ReviewInput(
        id="test1", text="Отличный товар! Быстрая доставка.", rating=5
    )

    result = await analyzer.analyze(review)

    assert result["id"] == "test1"
    assert result["sentiment"] == Sentiment.POSITIVE
    assert "доставка" in result["topics"]
    assert result["priority"] == Priority.LOW
    mock_openai_client.chat.completions.create.assert_called_once()


@pytest.mark.asyncio
async def test_llm_analyze_with_markdown_wrapped_json(mock_openai_client):
    """Test LLM response with JSON wrapped in markdown code block."""
    # Modify mock to return markdown-wrapped JSON
    mock_response = MagicMock()
    mock_choice = MagicMock()
    mock_message = MagicMock()
    mock_message.content = """```json
{
    "sentiment": "negative",
    "topics": ["качество"],
    "complaints": ["сломался", "брак"],
    "priority": "critical"
}
```"""
    mock_choice.message = mock_message
    mock_response.choices = [mock_choice]
    mock_openai_client.chat.completions.create = AsyncMock(return_value=mock_response)

    analyzer = LLMAnalyzer()
    analyzer.client = mock_openai_client

    review = ReviewInput(id="test2", text="Ужасное качество! Сломался.", rating=1)

    result = await analyzer.analyze(review)

    assert result["sentiment"] == Sentiment.NEGATIVE
    assert result["priority"] == Priority.CRITICAL
    assert len(result["complaints"]) == 2


@pytest.mark.asyncio
async def test_llm_analyze_batch(mock_openai_client):
    """Test LLM batch analysis."""
    analyzer = LLMAnalyzer()
    analyzer.client = mock_openai_client

    reviews = [
        ReviewInput(id="1", text="Отличный товар!", rating=5),
        ReviewInput(id="2", text="Нормально", rating=3),
    ]

    results, summary = await analyzer.analyze_batch(reviews)

    assert len(results) == 2
    assert summary["total_reviews"] == 2
    assert "sentiment_distribution" in summary
    assert "priority_distribution" in summary
    assert mock_openai_client.chat.completions.create.call_count == 2


@pytest.mark.asyncio
async def test_llm_analyze_batch_failure():
    """Test LLM batch analysis with failure."""
    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(
        side_effect=Exception("API error")
    )

    analyzer = LLMAnalyzer()
    analyzer.client = mock_client

    reviews = [ReviewInput(id="1", text="Test", rating=5)]

    with pytest.raises(RuntimeError, match="LLM analysis failed"):
        await analyzer.analyze_batch(reviews)


def test_llm_is_available_with_key():
    """Test LLM availability check when key is present."""
    with patch("service.analyzer_llm.settings") as mock_settings:
        mock_settings.openai_api_key = "test-key"
        assert LLMAnalyzer.is_available() is True


def test_llm_is_available_without_key():
    """Test LLM availability check when key is missing."""
    with patch("service.analyzer_llm.settings") as mock_settings:
        mock_settings.openai_api_key = ""
        assert LLMAnalyzer.is_available() is False
