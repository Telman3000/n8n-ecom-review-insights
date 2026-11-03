"""Pydantic schemas for API requests and responses."""

from enum import Enum

from pydantic import BaseModel, Field


class Sentiment(str, Enum):
    """Review sentiment classification."""

    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"


class Priority(str, Enum):
    """Issue priority level."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ReviewInput(BaseModel):
    """Single review input."""

    id: str = Field(..., description="Unique review identifier")
    text: str = Field(..., description="Review text content")
    rating: int | None = Field(None, ge=1, le=5, description="Rating 1-5 stars")


class ReviewAnalysisRequest(BaseModel):
    """Request for analyzing multiple reviews."""

    reviews: list[ReviewInput] = Field(..., min_length=1, description="List of reviews to analyze")


class ReviewAnalysisResult(BaseModel):
    """Analysis result for a single review."""

    id: str = Field(..., description="Review identifier")
    sentiment: Sentiment = Field(..., description="Detected sentiment")
    topics: list[str] = Field(
        default_factory=list, description="Extracted topics (e.g., доставка, качество)"
    )
    complaints: list[str] = Field(
        default_factory=list, description="Identified complaints or issues"
    )
    priority: Priority = Field(..., description="Priority level for addressing issues")


class BatchSummary(BaseModel):
    """Summary statistics for the batch of reviews."""

    total_reviews: int = Field(..., description="Total number of reviews analyzed")
    sentiment_distribution: dict[Sentiment, int] = Field(
        ..., description="Count of reviews per sentiment"
    )
    priority_distribution: dict[Priority, int] = Field(
        ..., description="Count of reviews per priority"
    )
    top_topics: list[str] = Field(..., description="Most frequently mentioned topics")
    top_complaints: list[str] = Field(..., description="Most frequent complaints")


class AnalysisResponse(BaseModel):
    """Complete analysis response."""

    results: list[ReviewAnalysisResult] = Field(..., description="Per-review analysis")
    summary: BatchSummary = Field(..., description="Batch-level summary")


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = Field(default="healthy")
    llm_available: bool = Field(..., description="Whether LLM analyzer is available")
    mode: str = Field(..., description="Current analyzer mode (llm or fallback)")
