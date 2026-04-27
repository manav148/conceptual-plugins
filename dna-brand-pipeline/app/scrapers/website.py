"""Website scraper — extracts brand-relevant signals from a client URL.

Uses Scrapling's static Fetcher (curl_cffi) for speed; pass stealth=True
to use StealthyFetcher (Patchright) when JS rendering is required.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Optional
from urllib.parse import urlparse

from scrapling import Fetcher


@dataclass
class WebsiteSignals:
    """Raw structured signals extracted from a brand's website.

    Feeds the Brand Analysis layer (3.4) and downstream DNA build.
    """
    url: str
    status: int
    title: Optional[str] = None
    meta_description: Optional[str] = None
    headings: dict[str, list[str]] = field(default_factory=dict)
    body_text: str = ""
    ctas: list[str] = field(default_factory=list)
    nav_links: list[str] = field(default_factory=list)
    social_links: list[str] = field(default_factory=list)
    images: list[str] = field(default_factory=list)
    og_tags: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


SOCIAL_DOMAINS = (
    "instagram.com", "facebook.com", "twitter.com", "x.com",
    "linkedin.com", "tiktok.com", "youtube.com", "pinterest.com",
)

CTA_HINTS = (
    "buy", "shop", "get started", "sign up", "subscribe", "contact",
    "book", "try", "start", "join", "learn more", "request", "demo",
)


def _first_text(selectors) -> Optional[str]:
    if not selectors:
        return None
    t = selectors[0].text
    return str(t).strip() if t else None


def scrape_website(url: str, *, stealth: bool = False) -> WebsiteSignals:
    """Fetch a brand website and extract structured signals.

    Args:
        url: Target URL (must include scheme).
        stealth: If True, use Scrapling's StealthyFetcher (browser-based).
                 Use only when static fetch returns thin/blocked content.
    """
    if stealth:
        from scrapling import StealthyFetcher
        page = StealthyFetcher.fetch(url, headless=True)
    else:
        page = Fetcher.get(url, stealthy_headers=True, follow_redirects=True)

    if page.status >= 400:
        return WebsiteSignals(url=url, status=page.status)

    headings: dict[str, list[str]] = {}
    for level in ("h1", "h2", "h3"):
        items = []
        for el in page.css(level):
            t = str(el.text).strip() if el.text else ""
            if t:
                items.append(t)
        if items:
            headings[level] = items

    nav_links: list[str] = []
    social_links: list[str] = []
    for a in page.css("a"):
        href = a.attrib.get("href") or ""
        if not href or href.startswith("#") or href.startswith("javascript:"):
            continue
        if any(d in href for d in SOCIAL_DOMAINS):
            social_links.append(href)
        else:
            nav_links.append(href)

    ctas: list[str] = []
    for el in page.css("a, button"):
        raw = str(el.text).strip() if el.text else ""
        low = raw.lower()
        if raw and len(raw) < 60 and any(hint in low for hint in CTA_HINTS):
            ctas.append(raw)

    og_tags: dict[str, str] = {}
    for m in page.css('meta[property^="og:"]'):
        prop = m.attrib.get("property", "").replace("og:", "")
        content = m.attrib.get("content", "")
        if prop and content:
            og_tags[prop] = content

    try:
        body_text = " ".join(page.get_all_text().split())[:8000]
    except Exception:
        body_text = ""

    desc = page.css('meta[name="description"]')
    meta_description = desc[0].attrib.get("content") if desc else None

    return WebsiteSignals(
        url=url,
        status=page.status,
        title=_first_text(page.css("title")),
        meta_description=meta_description,
        headings=headings,
        body_text=body_text,
        ctas=list(dict.fromkeys(ctas))[:25],
        nav_links=list(dict.fromkeys(nav_links))[:50],
        social_links=list(dict.fromkeys(social_links))[:20],
        images=[img.attrib.get("src", "") for img in page.css("img")[:30]
                if img.attrib.get("src")],
        og_tags=og_tags,
    )


def domain_of(url: str) -> str:
    return urlparse(url).netloc.lower().lstrip("www.")
