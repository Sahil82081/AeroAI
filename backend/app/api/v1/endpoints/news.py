from fastapi import APIRouter, Query, Depends, HTTPException
from typing import Optional
from app.modules.news.news_service import news_service

router = APIRouter(prefix="/news", tags=["Travel News Feed"])

@router.get("", summary="Get Real-Time Travel & Disruption News")
async def get_travel_news(
    q: Optional[str] = Query(None, description="General search keywords (e.g. flight delay, strike)"),
    airline: Optional[str] = Query(None, description="Airline name filter (e.g. Air India, IndiGo)"),
    airport: Optional[str] = Query(None, description="Airport or city filter (e.g. Delhi DEL, Mumbai BOM)"),
    limit: int = Query(20, ge=1, le=50, description="Maximum number of articles to return"),
    force_refresh: bool = Query(False, description="Bypass cache and force refresh from Google News RSS")
):
    """
    Fetches real-time travel disruption news from Google News RSS with 15-minute caching,
    title deduplication, category tagging, and automatic fallback.
    """
    try:
        return await news_service.get_news(
            q=q,
            airline=airline,
            airport=airport,
            limit=limit,
            force_refresh=force_refresh
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch news feed: {str(e)}")
