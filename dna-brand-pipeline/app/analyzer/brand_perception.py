"""Brand perception analyzer — extract how people see a brand online.

Simple single-shot LLM analysis of brand signals.
Input: Brand name + website signals
Output: JSON with brand perception data (feelings, sentiment, positioning, tone)
"""

from __future__ import annotations

import json
from typing import Any

from anthropic import Anthropic

from app.analyzer.llm import SONNET, _client, _extract_tool_input
from app.models.schemas import BrandAnalysis
from app.scrapers.website import WebsiteSignals


_PERCEPTION_SYSTEM = """\
You are a brand perception analyst. Your job is to read raw website signals
and extract how people are likely seeing and feeling about this brand online.

Do not invent facts. Only use what the website actually says and shows.
Extract the core feelings, sentiment, positioning, and tone people would
experience encountering this brand.

Respond by calling the `record_brand_perception` tool with your analysis.
"""


_PERCEPTION_TOOL: dict[str, Any] = {
    "name": "record_brand_perception",
    "description": "Record brand perception data extracted from website signals.",
    "input_schema": {
        "type": "object",
        "required": [
            "brand_name",
            "primary_feelings",
            "sentiment_score",
            "positioning",
            "tone_of_voice",
            "perceived_audience",
            "key_promises",
            "brand_personality",
            "visual_first_impression",
            "how_people_see_it",
        ],
        "properties": {
            "brand_name": {
                "type": "string",
                "description": "The brand name",
            },
            "primary_feelings": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Top 3-5 feelings people get from this brand (e.g., 'trustworthy', 'innovative', 'accessible')",
            },
            "sentiment_score": {
                "type": "number",
                "minimum": -1,
                "maximum": 1,
                "description": "Overall sentiment: -1 (negative), 0 (neutral), 1 (positive)",
            },
            "positioning": {
                "type": "string",
                "description": "How does the brand position itself in the market? (1-2 sentences)",
            },
            "tone_of_voice": {
                "type": "string",
                "description": "The tone people experience: formal/casual, friendly/professional, bold/subtle, etc.",
            },
            "perceived_audience": {
                "type": "string",
                "description": "Who does this brand seem to target? (1 sentence)",
            },
            "key_promises": {
                "type": "array",
                "items": {"type": "string"},
                "description": "3-5 main promises/claims the brand makes",
            },
            "brand_personality": {
                "type": "string",
                "description": "If this brand were a person, what would it be like? (1-2 sentences)",
            },
            "visual_first_impression": {
                "type": "string",
                "description": "What do the visuals (colors, design, imagery) communicate? (1 sentence)",
            },
            "how_people_see_it": {
                "type": "string",
                "description": "How are people online likely seeing/talking about this brand? What's the sentiment? (2-3 sentences)",
            },
        },
    },
}


def analyze_brand_perception(
    brand_name: str,
    signals: WebsiteSignals,
    *,
    model: str = SONNET,
    max_tokens: int = 2000,
    client: Anthropic | None = None,
) -> dict[str, Any]:
    """Analyze brand perception from website signals.

    Returns:
        dict with brand perception data

    Raises:
        RuntimeError: if the model fails to call the required tool.
        pydantic.ValidationError: if the returned shape does not match.
    """
    c = client or _client()

    # Truncate signals to avoid token limit (keep most important parts)
    signals_dict = signals.to_dict()
    signals_json = json.dumps(signals_dict, indent=2)

    # Limit to 50K chars to stay under token limits
    if len(signals_json) > 50000:
        signals_json = signals_json[:50000] + "\n... [content truncated] ..."

    msg = c.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=_PERCEPTION_SYSTEM,
        tools=[_PERCEPTION_TOOL],
        tool_choice={"type": "tool", "name": "record_brand_perception"},
        messages=[
            {
                "role": "user",
                "content": (
                    f"Analyze how people are seeing the brand '{brand_name}' "
                    f"based on these website signals:\n\n"
                    f"```json\n{signals_json}\n```\n\n"
                    f"Extract the feelings, sentiment, positioning, and tone. "
                    f"How are people likely perceiving this brand online?"
                ),
            }
        ],
    )

    raw = _extract_tool_input(msg, "record_brand_perception")
    return raw
