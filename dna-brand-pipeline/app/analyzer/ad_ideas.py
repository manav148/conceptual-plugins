"""Ad idea generator — concepts → 4 AdIdeas per concept (Nano Banana ready).

This is the missing layer between concept generation and the visual prompt
package. The brief calls for ~20 ad ideas per brand (4-5 per concept) so
Meta's algorithm has the creative variety it rewards. Each idea must be:

  - Anchored in one specific concept (the strategic foundation)
  - Distinct in angle from the other ideas in the same concept
  - Free of every trap that produced the V2 image disasters:
      no hex codes, no bracketed labels, no font names, no quoted
      taglines, no trend slugs in the prompt body, no mentions of
      "ad" or "advertisement" (image models render those as text)
  - Spatially composed for Meta's 9:16 mobile-first crop, with the
    top sixth and bottom fifth deliberately reserved as quiet bands
    for headline + CTA + logo overlay added in post

The module uses Claude Sonnet with forced tool-use, batched per concept
(one API call per concept = 5 calls per brand). The tool schema enforces
exactly 4 ideas per call across 4 distinct angles, so the structure is
guaranteed by the API before the model even responds.
"""

from __future__ import annotations

import json
from typing import Any

from anthropic import Anthropic

from app.analyzer.llm import SONNET, _client, _extract_tool_input
from app.models.schemas import (
    AdIdea,
    BrandAnalysis,
    BusinessDNA,
    ConceptDirection,
)


# ─── System prompt ──────────────────────────────────────────────────────────

_AD_IDEAS_SYSTEM = """\
You are a senior creative director generating four Meta-ready ad ideas
for one concept direction inside a Business DNA project.

You will receive:
  - The Business DNA (the brand's strategic operating system)
  - One concept direction (one of five)
  - The hook angles you must use (exactly four, one per idea)

Your job is to write four ad ideas that all live inside this concept
but speak from four different angles. Each idea has:

  1. A short headline (under 9 words)
  2. A first-line caption (the first thing the user sees in feed)
  3. A CTA button label (3-4 words)
  4. An image prompt — continuous prose describing what the image shows
  5. Composition notes — where the hero sits, where the headline overlay
     goes, where the CTA + logo overlay goes
  6. A natural-language palette description

The image prompts are the most important part of your output, and there
are HARD RULES you MUST follow. These rules exist because past attempts
produced unusable images where the model rendered hex codes, font names,
and bracket labels as visible text on the canvas:

NEVER include any of these in image_prompt:
  - hex color codes (no "#0033A0", no "#FFFFFF")
  - bracket labels (no "[CONCEPT]", "[PALETTE]", etc.)
  - font names (no "Tiempos Today", "Söhne", "Helvetica")
  - the words "ad", "advertisement", "banner", "Instagram", "Meta",
    "Facebook", or "social media" — these become text on the canvas
  - quoted taglines or slogans
  - rendered text of any kind ("the headline reads...", "with text saying...")
  - design tool names ("Photoshop", "Figma")
  - the brand name as a logo to render
  - more than ONE hero subject per composition

ALWAYS include in image_prompt:
  - A single hero subject described concretely (an object, an
    illustration, a still life)
  - The mood / lighting / texture in plain English
  - Composition language describing the central safe area, the quiet
    top sixth, and the quiet bottom fifth (these become the overlay zones)
  - A description of palette in plain English ("warm cream paper", "deep
    navy ink", "single amber accent") — never as hex
  - The word "vertical" or "9:16" or similar to anchor the format

Think of the image_prompt as one paragraph a designer would dictate to
another designer over coffee. No labels, no metadata, just the picture.

The headline is added LATER by a layout step — never asked the image
model to render it. Same for the CTA and logo. Reserve the space, but
do not render the text.

You MUST respond by calling the `record_ad_ideas` tool exactly once,
with exactly four ideas, in the order of the four angles you were given.
"""


# ─── Tool schema ────────────────────────────────────────────────────────────

def _ad_ideas_tool(concept_id: str, angles: list[str]) -> dict[str, Any]:
    """Tool schema sized to exactly len(angles) ideas (always 4 in practice).

    The schema enforces minItems=maxItems so the API rejects any other
    count before the model even responds.
    """
    n = len(angles)
    return {
        "name": "record_ad_ideas",
        "description": (
            f"Record exactly {n} ad ideas for concept {concept_id!r}, "
            f"one per angle in the order: {', '.join(angles)}."
        ),
        "input_schema": {
            "type": "object",
            "required": ["ideas"],
            "properties": {
                "ideas": {
                    "type": "array",
                    "minItems": n,
                    "maxItems": n,
                    "items": {
                        "type": "object",
                        "required": [
                            "angle", "headline", "primary_text_first_line",
                            "cta_label", "image_prompt", "composition_notes",
                            "palette_words", "palette_hexes",
                        ],
                        "properties": {
                            "angle": {
                                "type": "string",
                                "enum": list(set(angles)),
                                "description": "The hook angle for this idea.",
                            },
                            "headline": {
                                "type": "string",
                                "description": "Under 9 words, the on-image headline.",
                            },
                            "primary_text_first_line": {
                                "type": "string",
                                "description": "The first line of the Meta caption.",
                            },
                            "cta_label": {
                                "type": "string",
                                "description": "3-4 words, the CTA button label.",
                            },
                            "image_prompt": {
                                "type": "string",
                                "description": (
                                    "Continuous prose. NO hex codes. NO bracket "
                                    "labels. NO font names. NO quoted text. "
                                    "ONE hero subject. Spatial composition that "
                                    "reserves the top sixth and bottom fifth as "
                                    "quiet bands for overlay."
                                ),
                            },
                            "composition_notes": {
                                "type": "string",
                                "description": "Where the hero, headline overlay, and CTA overlay live.",
                            },
                            "palette_words": {
                                "type": "string",
                                "description": "Natural-language palette description (NEVER hex).",
                            },
                            "palette_hexes": {
                                "type": "array",
                                "items": {
                                    "type": "string",
                                    "pattern": "^#[0-9A-Fa-f]{6}$",
                                },
                                "minItems": 2,
                                "maxItems": 5,
                                "description": "2-5 hex codes for the renderer (NOT in the prompt body).",
                            },
                        },
                    },
                }
            },
        },
    }


# ─── Defaults ───────────────────────────────────────────────────────────────

DEFAULT_ANGLES: tuple[str, ...] = (
    "hook",
    "proof_point",
    "identity_callout",
    "demonstration",
)


# ─── Public API ─────────────────────────────────────────────────────────────

def generate_ideas_for_concept(
    dna: BusinessDNA,
    analysis: BrandAnalysis,
    concept: ConceptDirection,
    *,
    angles: tuple[str, ...] = DEFAULT_ANGLES,
    model: str = SONNET,
    max_tokens: int = 4000,
    client: Anthropic | None = None,
) -> list[AdIdea]:
    """Generate exactly len(angles) AdIdeas for one concept.

    The default angles produce 4 ideas: hook, proof_point, identity_callout,
    demonstration. Pass a different tuple to override.
    """
    payload = {
        "business_dna": dna.model_dump(mode="json"),
        "brand_analysis_summary": analysis.summary,
        "concept": concept.model_dump(mode="json"),
        "required_angles": list(angles),
    }

    msg = (client or _client()).messages.create(
        model=model,
        max_tokens=max_tokens,
        system=_AD_IDEAS_SYSTEM,
        tools=[_ad_ideas_tool(concept.id, list(angles))],
        tool_choice={"type": "tool", "name": "record_ad_ideas"},
        messages=[
            {
                "role": "user",
                "content": (
                    f"Generate exactly {len(angles)} ad ideas for the concept "
                    f"{concept.name!r} in the brand {dna.brand_name!r}. The "
                    f"required angles are, in order: {', '.join(angles)}. "
                    f"Use only the data below — do not invent facts.\n\n"
                    f"```json\n{json.dumps(payload, indent=2)[:30000]}\n```"
                ),
            }
        ],
    )

    raw = _extract_tool_input(msg, "record_ad_ideas")
    raw_ideas = raw["ideas"]
    if len(raw_ideas) != len(angles):
        raise RuntimeError(
            f"ad_ideas: expected {len(angles)} ideas for concept "
            f"{concept.id!r}, got {len(raw_ideas)}."
        )

    ideas: list[AdIdea] = []
    for i, raw_idea in enumerate(raw_ideas):
        angle = raw_idea.get("angle", angles[i])
        idea = AdIdea(
            id=f"{concept.id}_{i+1:02d}_{angle}",
            concept_id=concept.id,
            angle=angle,  # type: ignore[arg-type]
            headline=raw_idea["headline"],
            primary_text_first_line=raw_idea["primary_text_first_line"],
            cta_label=raw_idea["cta_label"],
            image_prompt=raw_idea["image_prompt"],
            composition_notes=raw_idea["composition_notes"],
            palette_words=raw_idea["palette_words"],
            palette_hexes=raw_idea["palette_hexes"],
            trend_slugs=concept.trend_slugs,  # inherit from concept
        )
        ideas.append(idea)
    return ideas


def generate_ad_ideas(
    dna: BusinessDNA,
    analysis: BrandAnalysis,
    concepts: list[ConceptDirection],
    *,
    angles: tuple[str, ...] = DEFAULT_ANGLES,
    model: str = SONNET,
    client: Anthropic | None = None,
) -> list[tuple[ConceptDirection, list[AdIdea]]]:
    """Generate ad ideas for every concept in one batch.

    Returns a list of (concept, ideas) tuples ready to feed directly to
    build_visual_prompt_package().

    Cost: one Sonnet call per concept (5 calls for a standard 5-concept
    project). Each call returns 4 fully-validated AdIdeas.
    """
    out: list[tuple[ConceptDirection, list[AdIdea]]] = []
    for concept in concepts:
        ideas = generate_ideas_for_concept(
            dna, analysis, concept,
            angles=angles, model=model, client=client,
        )
        out.append((concept, ideas))
    return out
