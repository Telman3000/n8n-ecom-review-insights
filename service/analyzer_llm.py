"""LLM-based analyzer using OpenAI-compatible API."""

import json
from collections import Counter

from openai import AsyncOpenAI

from service.config import settings
from service.schemas import AnalysisMode, Priority, ReviewInput, Sentiment


class LLMAnalyzer:
    """Analyzer using OpenAI-compatible LLM."""

    def __init__(self):
        """Initialize LLM client."""
        self.client = AsyncOpenAI(
            api_key=settings.openai_api_key, base_url=settings.openai_base_url
        )
        self.model = settings.openai_model

    async def analyze(self, review: ReviewInput) -> dict:
        """Analyze a single review using LLM."""
        prompt = f"""Проанализируй отзыв о товаре с маркетплейса и верни JSON с полями:
- sentiment: "positive", "neutral" или "negative"
- topics: список тем (доставка, качество, цена, упаковка, размер, обслуживание, внешний вид)
- complaints: список конкретных жалоб/проблем (если есть)
- priority: "low", "medium", "high" или "critical" (критичность проблем)

Отзыв: {review.text}
{"Оценка: " + str(review.rating) + " из 5" if review.rating else ""}

Отвечай только валидным JSON без дополнительного текста."""

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=500,
        )

        content = response.choices[0].message.content.strip()

        # Try to extract JSON if wrapped in markdown
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
            content = content.strip()

        analysis = json.loads(content)

        return {
            "id": review.id,
            "sentiment": Sentiment(analysis["sentiment"]),
            "topics": analysis.get("topics", []),
            "complaints": analysis.get("complaints", []),
            "priority": Priority(analysis["priority"]),
            "mode": AnalysisMode.LLM,
        }

    async def analyze_batch(self, reviews: list[ReviewInput]) -> tuple[list[dict], dict]:
        """Analyze multiple reviews and generate summary."""
        results = []
        for review in reviews:
            try:
                result = await self.analyze(review)
                results.append(result)
            except Exception as e:
                # If LLM fails for any review, raise to trigger fallback
                raise RuntimeError(f"LLM analysis failed for review {review.id}: {e}") from e

        # Calculate summary statistics
        sentiments = [r["sentiment"] for r in results]
        priorities = [r["priority"] for r in results]
        modes = [r["mode"] for r in results]
        all_topics = [topic for r in results for topic in r["topics"]]
        all_complaints = [complaint for r in results for complaint in r["complaints"]]

        sentiment_counts = Counter(sentiments)
        priority_counts = Counter(priorities)
        mode_counts = Counter(modes)
        topic_counts = Counter(all_topics)
        complaint_counts = Counter(all_complaints)

        summary = {
            "total_reviews": len(reviews),
            "sentiment_distribution": dict(sentiment_counts),
            "priority_distribution": dict(priority_counts),
            "mode_distribution": dict(mode_counts),
            "top_topics": [topic for topic, _ in topic_counts.most_common(5)],
            "top_complaints": [complaint for complaint, _ in complaint_counts.most_common(5)],
        }

        return results, summary

    @staticmethod
    def is_available() -> bool:
        """Check if LLM analyzer is available."""
        return bool(settings.openai_api_key)
