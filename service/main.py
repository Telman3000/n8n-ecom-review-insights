"""FastAPI application for marketplace review analysis."""

import logging

from fastapi import FastAPI, HTTPException

from service.analyzer_fallback import FallbackAnalyzer
from service.analyzer_llm import LLMAnalyzer
from service.config import settings
from service.schemas import (
    AnalysisResponse,
    BatchSummary,
    HealthResponse,
    ReviewAnalysisRequest,
    ReviewAnalysisResult,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Marketplace Review Analyzer",
    description="Service for analyzing marketplace product reviews with sentiment and topic extraction",
    version="0.1.0",
)

# Initialize analyzers
fallback_analyzer = FallbackAnalyzer()
llm_analyzer = LLMAnalyzer() if LLMAnalyzer.is_available() else None

if llm_analyzer:
    logger.info("LLM analyzer initialized with %s", settings.openai_base_url)
else:
    logger.info("Running in fallback mode (no API key configured)")


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        llm_available=llm_analyzer is not None,
        mode="llm" if llm_analyzer else "fallback",
    )


@app.post("/analyze", response_model=AnalysisResponse)
async def analyze_reviews(request: ReviewAnalysisRequest):
    """
    Analyze marketplace product reviews.

    Returns sentiment, topics, complaints, and priority for each review,
    plus batch-level summary statistics.
    """
    try:
        # Try LLM analyzer first if available
        if llm_analyzer:
            try:
                results, summary_dict = await llm_analyzer.analyze_batch(request.reviews)
                logger.info("Analyzed %d reviews using LLM", len(request.reviews))
            except Exception as e:
                logger.warning("LLM analysis failed, falling back to rules: %s", e)
                results, summary_dict = fallback_analyzer.analyze_batch(request.reviews)
                logger.info("Analyzed %d reviews using fallback", len(request.reviews))
        else:
            # Use fallback analyzer
            results, summary_dict = fallback_analyzer.analyze_batch(request.reviews)
            logger.info("Analyzed %d reviews using fallback", len(request.reviews))

        # Convert to response models
        review_results = [ReviewAnalysisResult(**result) for result in results]
        summary = BatchSummary(**summary_dict)

        return AnalysisResponse(results=review_results, summary=summary)

    except Exception as e:
        logger.error("Analysis failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}") from e


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=settings.service_host, port=settings.service_port)
