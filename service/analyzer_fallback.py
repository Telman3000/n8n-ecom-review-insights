"""Rule-based fallback analyzer that works without LLM."""

import re
from collections import Counter

from service.schemas import AnalysisMode, Priority, ReviewInput, Sentiment


class FallbackAnalyzer:
    """Rule-based analyzer using keyword matching for Russian reviews."""

    # Russian sentiment keywords
    POSITIVE_KEYWORDS = [
        "отличн",
        "хорош",
        "супер",
        "замечательн",
        "прекрасн",
        "качественн",
        "рекомендую",
        "доволен",
        "довольна",
        "понравил",
        "превосходн",
        "классн",
    ]

    NEGATIVE_KEYWORDS = [
        "плох",
        "ужасн",
        "разочарова",
        "не рекомендую",
        "не советую",
        "брак",
        "поддел",
        "обман",
        "жалоб",
        "верну",
        "возврат",
        "некачественн",
    ]

    # Topic patterns
    TOPIC_PATTERNS = {
        "доставка": [r"доставк", r"курьер", r"привез", r"пришл"],
        "качество": [r"качеств", r"материал", r"сборк"],
        "цена": [r"цен", r"стоимост", r"дорог", r"дешев"],
        "упаковка": [r"упаковк", r"коробк"],
        "размер": [r"размер", r"маломерк", r"большемерк"],
        "обслуживание": [r"обслужива", r"менеджер", r"консультац"],
        "внешний вид": [r"внешн", r"выгляд", r"красив"],
    }

    # Complaint patterns
    COMPLAINT_PATTERNS = [
        r"не работа",
        r"сломал",
        r"не пришл",
        r"опоздал",
        r"не соответству",
        r"брак",
        r"поврежден",
        r"не так",
        r"проблем",
    ]

    def analyze_sentiment(self, review: ReviewInput) -> Sentiment:
        """Determine sentiment from text and rating."""
        text_lower = review.text.lower()

        # If rating is available, use it as primary signal
        if review.rating:
            if review.rating >= 4:
                return Sentiment.POSITIVE
            elif review.rating <= 2:
                return Sentiment.NEGATIVE
            else:
                return Sentiment.NEUTRAL

        # Count positive and negative keywords
        positive_count = sum(1 for keyword in self.POSITIVE_KEYWORDS if keyword in text_lower)
        negative_count = sum(1 for keyword in self.NEGATIVE_KEYWORDS if keyword in text_lower)

        if positive_count > negative_count:
            return Sentiment.POSITIVE
        elif negative_count > positive_count:
            return Sentiment.NEGATIVE
        else:
            return Sentiment.NEUTRAL

    def extract_topics(self, text: str) -> list[str]:
        """Extract topics from review text."""
        text_lower = text.lower()
        found_topics = []

        for topic, patterns in self.TOPIC_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    found_topics.append(topic)
                    break

        return found_topics

    def extract_complaints(self, text: str) -> list[str]:
        """Extract complaint phrases from review text."""
        text_lower = text.lower()
        complaints = []

        for pattern in self.COMPLAINT_PATTERNS:
            matches = re.finditer(pattern, text_lower)
            for match in matches:
                # Extract surrounding context
                start = max(0, match.start() - 20)
                end = min(len(text), match.end() + 30)
                context = text[start:end].strip()
                complaints.append(context)

        return complaints[:3]  # Limit to top 3 complaints

    def determine_priority(self, sentiment: Sentiment, complaints: list[str]) -> Priority:
        """Determine priority based on sentiment and complaints."""
        if sentiment == Sentiment.NEGATIVE and len(complaints) >= 2:
            return Priority.CRITICAL
        elif sentiment == Sentiment.NEGATIVE and len(complaints) == 1:
            return Priority.HIGH
        elif sentiment == Sentiment.NEGATIVE or len(complaints) > 0:
            return Priority.MEDIUM
        else:
            return Priority.LOW

    def analyze(self, review: ReviewInput) -> dict:
        """Analyze a single review."""
        sentiment = self.analyze_sentiment(review)
        topics = self.extract_topics(review.text)
        complaints = self.extract_complaints(review.text)
        priority = self.determine_priority(sentiment, complaints)

        return {
            "id": review.id,
            "sentiment": sentiment,
            "topics": topics,
            "complaints": complaints,
            "priority": priority,
            "mode": AnalysisMode.RULES,
        }

    def analyze_batch(self, reviews: list[ReviewInput]) -> tuple[list[dict], dict]:
        """Analyze multiple reviews and generate summary."""
        results = [self.analyze(review) for review in reviews]

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
