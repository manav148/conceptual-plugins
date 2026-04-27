"""Claude analyzer — turns scraped signals into BrandAnalysis and BusinessDNA.

Model routing follows the project's recipe book:
  - Sonnet 4.6 for brand analysis (default reasoning, mid cost)
  - Opus  4.6 for DNA construction (architectural decision, error compounds)

Both calls use Anthropic's tool-use mechanism to force structured output
that conforms to the Pydantic schemas. We never parse free-form prose —
the model fills in the schema or the call fails loudly.

The brief's anti-generic principle is non-negotiable: the system prompts
explicitly forbid LLM-default territory and require evidence anchoring
to the scraped signals.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from anthropic import Anthropic
from dotenv import load_dotenv

from app.models.schemas import BrandAnalysis, BusinessDNA
from app.scrapers.website import WebsiteSignals


# Auto-load python_service/.env so the API key is available without
# requiring callers to export it. The .env file is gitignored.
_DOTENV = Path(__file__).resolve().parents[2] / ".env"
if _DOTENV.exists():
    load_dotenv(_DOTENV)


# ─── Model identifiers (verified against Anthropic API 2026-04) ──────────────
SONNET = "claude-sonnet-4-5"
OPUS = "claude-opus-4-5"
HAIKU = "claude-haiku-4-5-20251001"


# ─── System prompts ──────────────────────────────────────────────────────────

_ANALYZER_SYSTEM = """\
You are a senior brand strategist working inside the Business DNA pipeline.

Your job: convert raw scraped website signals into a rigorous BrandAnalysis.

Hard rules — these are not negotiable:
1. Anchor every claim in the scraped evidence. If the website does not
   support a claim, do not make it. Hallucination here poisons the DNA.
2. Interpret, do not paraphrase. The brief is explicit: do not summarize
   the site, interpret it. Surface what is *implied*, not just what is said.
3. Flag contradictions. Mismatches between tone and offer, between
   promise and proof, between visual cues and copy — name them.
4. Tag signal strength honestly. A single CTA is a weak signal. A
   repeated phrase across hero, nav, and footer is a strong signal.
5. Avoid generic archetypes ("trustworthy", "innovative", "premium")
   unless the evidence is overwhelming. Prefer specific, defensible
   language the client could actually own.

You will receive scraped website signals as JSON. You MUST respond by
calling the `record_brand_analysis` tool exactly once, filling every field.
"""

_DNA_SYSTEM = """\
You are the lead strategist constructing a Business DNA.

The Business DNA is the operating system for everything the brand will
ever produce. It must be readable in under two minutes and impossible
to confuse with any competitor's foundation.

Hard rules:
1. The five fields (purpose, personality, positioning, promise,
   uncontested_space) must each be one tight paragraph. No filler.
2. The uncontested_space must describe a territory the brand can actually
   own — not a slogan, not a value, but a *position competitors are
   leaving on the table*. If you cannot defend why it is uncontested,
   rewrite it.
3. Personality must feel like a specific human, not an archetype.
   "Bold and innovative" is a failure. "The friend who tells you the
   thing nobody else will, then helps you fix it" is a pass.
4. Every element must trace back to evidence in the BrandAnalysis you
   are given. No new facts. No invented history.
5. The one_line_summary must be a sentence the client could put on a
   wall and a competitor could not steal.

You will receive a BrandAnalysis as JSON. Respond by calling the
`record_business_dna` tool exactly once.
"""


# ─── Tool schemas (force structured output) ──────────────────────────────────

_BRAND_ANALYSIS_TOOL: dict[str, Any] = {
    "name": "record_brand_analysis",
    "description": "Record the structured brand analysis derived from scraped signals.",
    "input_schema": {
        "type": "object",
        "required": [
            "brand_name", "summary", "messaging_patterns", "tone_of_voice",
            "value_propositions", "promises", "audience_cues",
            "positioning_language", "trust_markers", "visual_clues",
            "strengths", "weaknesses",
        ],
        "properties": {
            "brand_name": {"type": "string"},
            "summary": {"type": "string", "description": "2-4 sentences interpreting (not paraphrasing) the brand."},
            "messaging_patterns": {"type": "array", "items": {"type": "string"}},
            "tone_of_voice": {"type": "array", "items": {"type": "string"}},
            "value_propositions": {"type": "array", "items": {"type": "string"}},
            "promises": {"type": "array", "items": {"type": "string"}},
            "audience_cues": {"type": "array", "items": {"type": "string"}},
            "positioning_language": {"type": "array", "items": {"type": "string"}},
            "trust_markers": {"type": "array", "items": {"type": "string"}},
            "visual_clues": {"type": "array", "items": {"type": "string"}},
            "strengths": {"type": "array", "items": {"type": "string"}},
            "weaknesses": {"type": "array", "items": {"type": "string"}},
            "contradictions": {"type": "array", "items": {"type": "string"}},
            "classified_signals": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["bucket", "value", "evidence", "strength"],
                    "properties": {
                        "bucket": {
                            "type": "string",
                            "enum": [
                                "brand_identity", "tone_of_voice",
                                "visual_language", "offers",
                                "audience_signals", "positioning",
                                "trust_markers", "emotional_value",
                                "functional_value",
                            ],
                        },
                        "value": {"type": "string"},
                        "evidence": {"type": "string"},
                        "strength": {
                            "type": "string",
                            "enum": ["strong", "moderate", "weak"],
                        },
                    },
                },
            },
        },
    },
}

_DNA_TOOL: dict[str, Any] = {
    "name": "record_business_dna",
    "description": "Record the one-page Business DNA derived from the BrandAnalysis.",
    "input_schema": {
        "type": "object",
        "required": [
            "brand_name", "purpose", "personality", "positioning",
            "promise", "uncontested_space", "one_line_summary",
        ],
        "properties": {
            "brand_name": {"type": "string"},
            "purpose": {"type": "string"},
            "personality": {"type": "string"},
            "positioning": {"type": "string"},
            "promise": {"type": "string"},
            "uncontested_space": {"type": "string"},
            "one_line_summary": {"type": "string"},
        },
    },
}


# ─── Client + helpers ────────────────────────────────────────────────────────

def _client() -> Anthropic:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError(
            "ANTHROPIC_API_KEY is not set. Export it before calling the analyzer."
        )
    return Anthropic(api_key=api_key)


def _extract_tool_input(message: Any, tool_name: str) -> dict:
    """Pull the tool_use block out of a Claude response, fail loudly if absent."""
    for block in message.content:
        if getattr(block, "type", None) == "tool_use" and block.name == tool_name:
            return block.input  # type: ignore[return-value]
    raise RuntimeError(
        f"Model did not call required tool '{tool_name}'. "
        f"Stop reason: {message.stop_reason}"
    )


# ─── Public API ──────────────────────────────────────────────────────────────

def analyze_brand(
    brand_name: str,
    signals: WebsiteSignals,
    *,
    model: str = SONNET,
    max_tokens: int = 4096,
) -> BrandAnalysis:
    """Run the Brand Analysis layer (3.4) on scraped signals."""
    payload = {"brand_name": brand_name, "signals": signals.to_dict()}

    msg = _client().messages.create(
        model=model,
        max_tokens=max_tokens,
        system=_ANALYZER_SYSTEM,
        tools=[_BRAND_ANALYSIS_TOOL],
        tool_choice={"type": "tool", "name": "record_brand_analysis"},
        messages=[
            {
                "role": "user",
                "content": (
                    "Analyze the following scraped website signals for "
                    f"the brand '{brand_name}'. Interpret, do not summarize. "
                    "Anchor every claim in the evidence.\n\n"
                    f"```json\n{json.dumps(payload, indent=2)[:30000]}\n```"
                ),
            }
        ],
    )

    return BrandAnalysis.model_validate(_extract_tool_input(msg, "record_brand_analysis"))


def build_dna(
    analysis: BrandAnalysis,
    *,
    model: str = OPUS,
    max_tokens: int = 2048,
) -> BusinessDNA:
    """Run the Business DNA generation layer (3.7) on a BrandAnalysis."""
    msg = _client().messages.create(
        model=model,
        max_tokens=max_tokens,
        system=_DNA_SYSTEM,
        tools=[_DNA_TOOL],
        tool_choice={"type": "tool", "name": "record_business_dna"},
        messages=[
            {
                "role": "user",
                "content": (
                    "Construct the Business DNA from the following BrandAnalysis. "
                    "Every field must trace back to the evidence below.\n\n"
                    f"```json\n{analysis.model_dump_json(indent=2)}\n```"
                ),
            }
        ],
    )

    return BusinessDNA.model_validate(_extract_tool_input(msg, "record_business_dna"))
