"""Trends scraper — Google Trends layer via pytrends-modern.

Feeds the Future Trends Layer of the Business DNA pipeline. Used to surface:
- relative interest over time for brand/category keywords
- related rising queries (cultural shift signals)
- regional interest (geographic concentration of demand)
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Optional

from pytrends_modern import TrendsScraper


@dataclass
class TrendSignals:
    keywords: list[str]
    timeframe: str
    geo: str
    interest_over_time: dict = field(default_factory=dict)
    related_rising: dict = field(default_factory=dict)
    related_top: dict = field(default_factory=dict)
    interest_by_region: dict = field(default_factory=dict)
    error: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)


def fetch_trends(
    keywords: list[str],
    *,
    timeframe: str = "today 12-m",
    geo: str = "",
) -> TrendSignals:
    """Pull Google Trends signals for up to 5 keywords.

    Args:
        keywords: 1-5 search terms (brand, category, competitors).
        timeframe: pytrends-style window (e.g., "today 12-m", "today 5-y").
        geo: ISO country code ("" = worldwide, "US", "ES", etc.).
    """
    if not keywords:
        return TrendSignals(keywords=[], timeframe=timeframe, geo=geo,
                            error="no keywords provided")
    if len(keywords) > 5:
        keywords = keywords[:5]

    signals = TrendSignals(keywords=keywords, timeframe=timeframe, geo=geo)
    try:
        scraper = TrendsScraper()
        scraper.build_payload(keywords, timeframe=timeframe, geo=geo)

        iot = scraper.interest_over_time()
        if iot is not None and not iot.empty:
            signals.interest_over_time = iot.reset_index().to_dict(orient="list")

        related = scraper.related_queries() or {}
        for kw, payload in related.items():
            if not payload:
                continue
            if (rising := payload.get("rising")) is not None and not rising.empty:
                signals.related_rising[kw] = rising.head(15).to_dict(orient="records")
            if (top := payload.get("top")) is not None and not top.empty:
                signals.related_top[kw] = top.head(15).to_dict(orient="records")

        ibr = scraper.interest_by_region()
        if ibr is not None and not ibr.empty:
            signals.interest_by_region = (
                ibr.sort_values(by=keywords[0], ascending=False)
                   .head(15)
                   .to_dict(orient="index")
            )
    except Exception as e:  # pragma: no cover — network/driver failure
        signals.error = f"{type(e).__name__}: {e}"

    return signals
