"""Insights endpoint — AI powered operational intelligence."""

from fastapi import APIRouter
from pydantic import BaseModel

from ..ml import score_store
from ..ml.insights import aggregate_scores, generate_insights

router = APIRouter()


class Insight(BaseModel):
    title: str
    body: str
    category: str
    confidence: str


class InsightsResponse(BaseModel):
    insights: list[Insight]
    total_scores_analysed: int


class AggregatesResponse(BaseModel):
    aggregates: dict


@router.get("/generate", response_model=InsightsResponse)
async def get_insights():
    """Generate AI powered insights from recent scoring patterns."""
    insights = await generate_insights()
    return InsightsResponse(
        insights=[Insight(**i) for i in insights],
        total_scores_analysed=score_store.count(),
    )


@router.get("/aggregates", response_model=AggregatesResponse)
async def get_aggregates():
    """Raw aggregates without LLM analysis (for dashboards)."""
    return AggregatesResponse(aggregates=aggregate_scores())
