"""
Live Travel Disruption News Service.

Fetches real-time travel and disruption news via Google News RSS:
https://news.google.com/rss/search?q=<query>&hl=<lang>&gl=<region>&ceid=<ceid>

NOTE: This RSS integration is designed for educational, research, and personal use.
Review Google News terms of service prior to commercial distribution.
The provider architecture is swappable (e.g. GNews, NewsAPI, MockNewsProvider)
to support commercial or high-scale fallbacks.
"""

import time
import re
import urllib.parse
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import httpx
import feedparser
from bs4 import BeautifulSoup

from app.core.config import settings
from app.core.logger import logger

def _clean_html(raw_html: str) -> str:
    """Strip HTML tags and unescape entities into clean plain text."""
    if not raw_html:
        return ""
    try:
        soup = BeautifulSoup(raw_html, "html.parser")
        text = soup.get_text(separator=" ")
        # Collapse extra whitespaces
        return re.sub(r"\s+", " ", text).strip()
    except Exception:
        # Fallback regex strip
        clean = re.sub(r"<[^>]+>", " ", raw_html)
        return re.sub(r"\s+", " ", clean).strip()

def _detect_category(title: str, snippet: str) -> str:
    """Categorize disruption news based on keywords."""
    combined = f"{title} {snippet}".lower()
    if any(k in combined for k in ["fog", "rain", "storm", "cyclone", "snow", "weather", "visibility", "typhoon"]):
        return "WEATHER"
    if any(k in combined for k in ["strike", "protest", "walkout", "industrial action", "staff shortage"]):
        return "STRIKE"
    if any(k in combined for k in ["airport", "runway", "terminal", "air traffic", "atc", "security line"]):
        return "AIRPORT"
    if any(k in combined for k in ["rule", "policy", "dgca", "compensation", "refund", "dot", "faa", "caa", "eu261", "charter"]):
        return "POLICY"
    if any(k in combined for k in ["airline", "flight", "pilot", "cabin crew", "boeing", "airbus", "indigo", "air india", "spicejet", "akasa"]):
        return "AIRLINE"
    return "DISRUPTION"

class BaseNewsProvider(ABC):
    """Abstract swappable news provider interface."""
    
    @abstractmethod
    async def fetch_news(
        self,
        query: str,
        airline: Optional[str] = None,
        airport: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        pass

class GoogleNewsRSSProvider(BaseNewsProvider):
    """Fetches real-time headlines from Google News RSS."""
    
    def __init__(self):
        self.base_url = settings.NEWS_FEED_URL
        self.region = settings.NEWS_FEED_REGION
        self.language = settings.NEWS_FEED_LANGUAGE
        self.ceid = settings.NEWS_FEED_CEID
        self.timeout = settings.NEWS_TIMEOUT_SECONDS

    def build_url(self, search_term: str) -> str:
        encoded_q = urllib.parse.quote_plus(search_term.strip())
        return f"{self.base_url}?q={encoded_q}&hl={self.language}&gl={self.region}&ceid={self.ceid}"

    async def fetch_news(
        self,
        query: str,
        airline: Optional[str] = None,
        airport: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        # Construct combined query if airline/airport provided
        query_parts = []
        if query:
            query_parts.append(query)
        if airline:
            query_parts.append(airline)
        if airport:
            query_parts.append(airport)
        
        full_query = " ".join(query_parts) if query_parts else "flight disruption airport delay airline cancellation"
        rss_url = self.build_url(full_query)
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 AeroAI/1.0",
            "Accept": "application/rss+xml, application/xml, text/xml, */*"
        }
        
        logger.info(f"Fetching Google News RSS: {rss_url}")
        
        async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
            resp = await client.get(rss_url, headers=headers)
            if resp.status_code != 200:
                raise RuntimeError(f"Google News RSS returned HTTP status {resp.status_code}")
            xml_content = resp.text

        feed = feedparser.parse(xml_content)
        if feed.bozo and not feed.entries:
            raise RuntimeError(f"RSS Feed parsing failure: {feed.get('bozo_exception', 'Malformed XML')}")

        items: List[Dict[str, Any]] = []
        for entry in feed.entries:
            title = entry.get("title", "")
            # Google news titles often have " - Source Name" at the end
            source = "Google News"
            if " - " in title:
                parts = title.rsplit(" - ", 1)
                headline = parts[0].strip()
                source = parts[1].strip()
            else:
                headline = title.strip()

            link = entry.get("link", "")
            raw_summary = entry.get("summary", "") or entry.get("description", "")
            snippet = _clean_html(raw_summary)
            if not snippet or snippet == headline:
                snippet = f"Latest travel disruption update regarding {headline} reported by {source}."

            published = entry.get("published", "")
            published_parsed = entry.get("published_parsed")
            if published_parsed:
                try:
                    dt = datetime(*published_parsed[:6], tzinfo=timezone.utc)
                    published_iso = dt.isoformat()
                except Exception:
                    published_iso = published
            else:
                published_iso = published or datetime.now(timezone.utc).isoformat()

            items.append({
                "id": str(hash(f"{headline}_{link}")),
                "title": headline,
                "source": source,
                "published_time": published_iso,
                "link": link,
                "snippet": snippet,
                "category": _detect_category(headline, snippet),
                "raw_query": full_query
            })

        return items

class FallbackMockNewsProvider(BaseNewsProvider):
    """Resilient fallback provider offering simulated real-time disruption alerts when network is offline."""
    
    async def fetch_news(
        self,
        query: str,
        airline: Optional[str] = None,
        airport: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        now_iso = datetime.now(timezone.utc).isoformat()
        airline_name = airline or "Air India"
        airport_name = airport or "Delhi (DEL)"
        
        return [
            {
                "id": "mock-news-1",
                "title": f"Air Traffic Control Congestion Delays Flights at {airport_name}",
                "source": "Aviation Herald India",
                "published_time": now_iso,
                "link": "https://news.google.com/search?q=airport+delay",
                "snippet": f"Heavy air traffic and runway slot constraints at {airport_name} have led to average departure delays of 45-90 minutes across all domestic carriers.",
                "category": "AIRPORT",
                "raw_query": query
            },
            {
                "id": "mock-news-2",
                "title": f"{airline_name} Issues Weather Advisory for Northern Corridor Operations",
                "source": "Press Trust of India",
                "published_time": now_iso,
                "link": "https://news.google.com/search?q=airline+weather+advisory",
                "snippet": f"{airline_name} advised passengers traveling through Delhi and northern hubs to check flight status as dense winter fog and low visibility impact operations.",
                "category": "WEATHER",
                "raw_query": query
            },
            {
                "id": "mock-news-3",
                "title": "DGCA Tightens Passenger Facilitation Mandate for Flight Delays Beyond 2 Hours",
                "source": "Civil Aviation Monitor",
                "published_time": now_iso,
                "link": "https://news.google.com/search?q=dgca+passenger+compensation",
                "snippet": "Directorate General of Civil Aviation reiterates CAR Section 3 Series M Part IV requirements: airlines must provide refreshments and free rebooking for major delays.",
                "category": "POLICY",
                "raw_query": query
            },
            {
                "id": "mock-news-4",
                "title": f"Ground Crew & Refueling Maintenance Window Causes Gate Holds at {airport_name}",
                "source": "Airport Operations Dispatch",
                "published_time": now_iso,
                "link": "https://news.google.com/search?q=airport+ground+operations",
                "snippet": f"Scheduled ramp resurfacing and high-density apron congestion at {airport_name} result in cascading delays for incoming and connecting flights.",
                "category": "AIRLINE",
                "raw_query": query
            }
        ]

class NewsService:
    """
    Central news service with multi-level TTL caching, deduplication,
    journey context integration, and provider fallback.
    """
    
    def __init__(self, provider: Optional[BaseNewsProvider] = None):
        self.provider = provider or GoogleNewsRSSProvider()
        self.fallback_provider = FallbackMockNewsProvider()
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.cache_ttl = settings.NEWS_CACHE_TTL_SECONDS

    def _normalize_title(self, title: str) -> str:
        """Normalized string for deduplication."""
        return re.sub(r"[^a-zA-Z0-9]", "", title.lower())

    def _get_cache_key(self, query: str, airline: Optional[str], airport: Optional[str]) -> str:
        parts = [query or "", airline or "", airport or ""]
        return "::".join(p.strip().lower() for p in parts)

    async def get_news(
        self,
        q: Optional[str] = None,
        airline: Optional[str] = None,
        airport: Optional[str] = None,
        limit: int = 20,
        force_refresh: bool = False
    ) -> Dict[str, Any]:
        search_query = q or "flight disruption airport delay airline cancellation"
        cache_key = self._get_cache_key(search_query, airline, airport)
        now = time.time()

        # 1. Check in-memory TTL cache
        if not force_refresh and cache_key in self.cache:
            entry = self.cache[cache_key]
            if now - entry["timestamp"] < self.cache_ttl:
                logger.info(f"Returning cached news feed for key: '{cache_key}' (age: {int(now - entry['timestamp'])}s)")
                return {
                    "status": "success",
                    "cached": True,
                    "cache_age_seconds": int(now - entry["timestamp"]),
                    "count": len(entry["items"]),
                    "query": search_query,
                    "airline": airline,
                    "airport": airport,
                    "articles": entry["items"][:limit]
                }

        # 2. Fetch from live provider with graceful fallback
        articles: List[Dict[str, Any]] = []
        is_fallback = False
        error_msg = None

        try:
            articles = await self.provider.fetch_news(search_query, airline, airport)
        except Exception as e:
            logger.warning(f"Live Google News RSS fetch failed: {e}. Attempting cache recovery or fallback provider.")
            error_msg = str(e)
            
            # If we have an expired cache copy, prefer it over cold fallback
            if cache_key in self.cache:
                cached_items = self.cache[cache_key]["items"]
                logger.info(f"Serving stale cached news feed ({len(cached_items)} articles) due to upstream error.")
                return {
                    "status": "degraded",
                    "cached": True,
                    "warning": f"Serving stale cache due to upstream provider error: {error_msg}",
                    "count": len(cached_items),
                    "query": search_query,
                    "articles": cached_items[:limit]
                }
            
            # Otherwise use fallback mock provider
            articles = await self.fallback_provider.fetch_news(search_query, airline, airport)
            is_fallback = True

        # 3. Deduplicate by normalized title
        seen_titles = set()
        deduped: List[Dict[str, Any]] = []
        for item in articles:
            norm = self._normalize_title(item.get("title", ""))
            if not norm or norm in seen_titles:
                continue
            seen_titles.add(norm)
            deduped.append(item)

        # 4. Sort newest first (by ISO timestamp if parseable)
        def _sort_key(art):
            pub = art.get("published_time", "")
            try:
                return datetime.fromisoformat(pub.replace("Z", "+00:00"))
            except Exception:
                return datetime.min.replace(tzinfo=timezone.utc)

        try:
            deduped.sort(key=_sort_key, reverse=True)
        except Exception:
            pass

        final_items = deduped[:limit]

        # 5. Store in cache
        self.cache[cache_key] = {
            "timestamp": now,
            "items": final_items
        }

        return {
            "status": "fallback" if is_fallback else "success",
            "cached": False,
            "provider": "MockFallback" if is_fallback else "GoogleNewsRSS",
            "warning": error_msg,
            "count": len(final_items),
            "query": search_query,
            "airline": airline,
            "airport": airport,
            "articles": final_items
        }

# Global singleton
news_service = NewsService()
