"""Insight generation using Claude Sonnet.

Aggregates recent scoring data and asks Sonnet to surface actionable patterns
for the ops team. Works from day one — no outcomes needed.
"""

from __future__ import annotations

import json
import os
from collections import Counter
from datetime import datetime

import anthropic

from . import score_store

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

SYSTEM_PROMPT = """You are an operations analyst for a UAE hospital network. You analyse appointment no-show risk scoring patterns and surface actionable insights for the operations team.

Rules:
- Return exactly 3 to 5 insights
- Each insight must be specific and actionable (what to do, not just what happened)
- Reference specific specialties, time slots, areas, or patient segments
- Be direct and concise — this is for busy hospital ops staff
- Never use hyphens in your text
- Format as JSON array with objects: {"title": "...", "body": "...", "category": "scheduling|capacity|risk_pattern|intervention", "confidence": "high|medium|low"}
- Only return the JSON array, no other text"""


def aggregate_scores() -> dict:
    """Build an aggregate summary from recent scores."""
    scores = score_store.recent(500)
    if not scores:
        return {}

    total = len(scores)
    risk_dist = Counter(s.risk_band for s in scores)

    # By specialty
    by_specialty: dict[str, list[float]] = {}
    for s in scores:
        by_specialty.setdefault(s.specialty, []).append(s.probability)

    specialty_summary = {
        k: {"count": len(v), "avg_risk": round(sum(v) / len(v), 3)}
        for k, v in by_specialty.items()
    }

    # By time of day
    by_tod: dict[str, list[float]] = {}
    for s in scores:
        by_tod.setdefault(s.time_of_day_band, []).append(s.probability)

    tod_summary = {
        k: {"count": len(v), "avg_risk": round(sum(v) / len(v), 3)}
        for k, v in by_tod.items()
    }

    # By patient area (top 10)
    by_area: dict[str, list[float]] = {}
    for s in scores:
        if s.patient_area:
            by_area.setdefault(s.patient_area, []).append(s.probability)

    area_summary = {
        k: {"count": len(v), "avg_risk": round(sum(v) / len(v), 3)}
        for k, v in sorted(by_area.items(), key=lambda x: len(x[1]), reverse=True)[:10]
    }

    # By booking channel
    by_channel: dict[str, list[float]] = {}
    for s in scores:
        by_channel.setdefault(s.booking_channel, []).append(s.probability)

    channel_summary = {
        k: {"count": len(v), "avg_risk": round(sum(v) / len(v), 3)}
        for k, v in by_channel.items()
    }

    # Distance analysis
    distances = [s.distance_km for s in scores if s.distance_km is not None]
    distance_summary = {}
    if distances:
        distance_summary = {
            "avg_km": round(sum(distances) / len(distances), 1),
            "max_km": round(max(distances), 1),
            "pct_over_30km": round(sum(1 for d in distances if d > 30) / len(distances) * 100, 1),
        }

    # Top contributing factors across all scores
    factor_counts: Counter = Counter()
    for s in scores:
        for f in s.top_factors:
            factor_counts[f.get("feature", "")] += 1

    return {
        "period": "recent",
        "total_scored": total,
        "generated_at": datetime.utcnow().isoformat(),
        "risk_distribution": dict(risk_dist),
        "by_specialty": specialty_summary,
        "by_time_of_day": tod_summary,
        "by_patient_area": area_summary,
        "by_booking_channel": channel_summary,
        "distance": distance_summary,
        "top_risk_factors": dict(factor_counts.most_common(5)),
    }


async def generate_insights() -> list[dict]:
    """Call Sonnet to generate operational insights from scoring patterns."""
    aggregates = aggregate_scores()

    if not aggregates:
        return [
            {
                "title": "Insufficient data",
                "body": "Score more appointments to generate operational insights. Minimum 10 scores needed.",
                "category": "risk_pattern",
                "confidence": "low",
            }
        ]

    if not ANTHROPIC_API_KEY:
        return [
            {
                "title": "LLM not configured",
                "body": "Set ANTHROPIC_API_KEY environment variable to enable AI powered insights.",
                "category": "risk_pattern",
                "confidence": "low",
            }
        ]

    client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)

    user_msg = f"""Here are the aggregated no-show risk scoring patterns for our hospital:

{json.dumps(aggregates, indent=2)}

Analyse these patterns and provide actionable insights for our operations team."""

    response = await client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_msg}],
    )

    text = response.content[0].text.strip()

    # Parse JSON from response
    try:
        # Handle case where model wraps in markdown code block
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        insights = json.loads(text)
        if isinstance(insights, list):
            return insights[:5]
    except (json.JSONDecodeError, IndexError):
        pass

    return [
        {
            "title": "Analysis complete",
            "body": text[:500],
            "category": "risk_pattern",
            "confidence": "medium",
        }
    ]
