"""Simple brand perception pipeline.

Input: brand_name + website
Output: JSON with brand perception data

This is a 1-shot pipeline: scrape → analyze perception → return JSON
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from app.analyzer.brand_perception import analyze_brand_perception
from app.scrapers.website import WebsiteSignals, scrape_website

logger = logging.getLogger(__name__)


@dataclass
class SimplePipelineResult:
    """Output from the simple pipeline."""
    brand_name: str
    website: str
    perception: dict
    scrape_status: int


def run_simple_pipeline(
    brand_name: str,
    website: str,
) -> SimplePipelineResult:
    """Run the simple brand perception pipeline.

    Args:
        brand_name: Brand name
        website: Brand website URL

    Returns:
        SimplePipelineResult with brand perception JSON

    Raises:
        RuntimeError: if scrape fails (status >= 400)
    """
    logger.info("Scraping: %s", website)
    signals = scrape_website(website)
    if signals.status >= 400:
        raise RuntimeError(
            f"Scrape failed for {website} with status {signals.status}"
        )

    logger.info("Analyzing perception: %s", brand_name)
    perception = analyze_brand_perception(brand_name, signals)

    return SimplePipelineResult(
        brand_name=brand_name,
        website=website,
        perception=perception,
        scrape_status=signals.status,
    )
