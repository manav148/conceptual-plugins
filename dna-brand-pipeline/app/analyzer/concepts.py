"""Concept generator — turns a Business DNA into five distinct concept worlds.

This is the creative engine of the pipeline (project pipeline 3.8 → 3.11).
Following the brief:

  - Five concepts, not three, not seven.
  - Each must feel as if a different top-tier creative team proposed it.
  - All five must trace back to the same DNA, with zero overlap.
  - No LLM-default territory. No five-variations-of-one-idea.
  - Each concept must be defendable: the model fills in a creative_defense
    field that explains *why* the concept exists, not just *what* it is.

We use forced tool-use in batched calls (2-3 concepts per call) instead of
a single monolithic call. This reduces API payload complexity while keeping
distinctiveness validation per batch. The system prompt encodes the anti-generic
and distinctiveness rules; the user message hands over the DNA + analysis.

Model routing per the project's recipe book:
  - Sonnet for the generation pass (creative breadth, mid-cost)
  - Batched max_tokens to keep payloads manageable
"""

from __future__ import annotations

import json
import time
from typing import Any

from anthropic import Anthropic

from app.analyzer.llm import SONNET, _client, _extract_tool_input
from app.models.schemas import (
    BrandAnalysis,
    BusinessDNA,
    ConceptDirection,
    ConceptPillars,
)


# ─── System prompt ───────────────────────────────────────────────────────────

_CONCEPT_SYSTEM = """\
You are a creative director generating five distinct strategic concept
directions for a brand whose Business DNA you have already received.

Your output is the most important moment in the entire pipeline. The
client will see these five concepts side by side and pick one. Each
concept will become an entire creative world for the next 6-12 months.

You must obey these hard rules. They are not stylistic suggestions —
they are how the system stays useful:

1. Each concept must feel like it came from a different top-tier
   creative team. If two could plausibly have been written by the
   same designer, you have failed and must rewrite.

2. All concepts must be rooted in the same Business DNA. The DNA is the
   operating system. Concepts are different applications of it.

3. NO variations of one theme. If concept A is "minimalist luxury" and
   concept B is "minimalist luxury with color", that is one concept,
   not two. Each concept must occupy a different quadrant of the
   strategic space.

4. NO LLM-default territory. Refuse "innovative", "premium",
   "human-centered", "bold and modern", "where tradition meets
   innovation". These are filler. Find the specific, defensible alternative.

5. Each concept must be NAMED with intent. The name should be a phrase
   the brand could actually own. Not a category descriptor.

6. Each concept must DEFEND ITSELF. The creative_defense field is the
   paragraph you would say out loud if a client asked "why this?". If
   you cannot answer, the concept is not ready.

7. Each concept must be ACTIONABLE. The application_map describes how
   the concept behaves in marketing, content, sales, internal comms,
   customer experience, and future campaigns. Vague answers forbidden.

8. Each concept must be DISTINCT. The distinctiveness_note explains
   specifically what makes it different from others. "It's more bold"
   is not distinctiveness.

9. Tension is mandatory. A concept with no tension — nothing to
   challenge, no convention to break — is decoration, not strategy.

If you're generating pillars, respond with the `record_concept_pillars` tool.
If you're generating concepts, respond with the `record_concept_batch` tool.
You will receive the BusinessDNA and the BrandAnalysis as context.
"""


# ─── Sub-schemas (referenced inside the main tool) ───────────────────────────

_VISUAL_GUIDANCE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["color_mood", "style_principles", "imagery_direction", "dos", "donts"],
    "properties": {
        "color_mood": {"type": "string"},
        "style_principles": {"type": "array", "items": {"type": "string"}},
        "typography_direction": {"type": "string"},
        "imagery_direction": {"type": "string"},
        "dos": {"type": "array", "items": {"type": "string"}},
        "donts": {"type": "array", "items": {"type": "string"}},
    },
}

_VERBAL_GUIDANCE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["tone_of_voice", "message_framing", "dos", "donts"],
    "properties": {
        "tone_of_voice": {"type": "string"},
        "message_framing": {"type": "string"},
        "signature_phrases": {"type": "array", "items": {"type": "string"}},
        "dos": {"type": "array", "items": {"type": "string"}},
        "donts": {"type": "array", "items": {"type": "string"}},
    },
}

_APPLICATION_MAP_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": [
        "marketing", "content", "sales",
        "internal_comms", "customer_experience", "future_campaigns",
    ],
    "properties": {
        "marketing": {"type": "string"},
        "content": {"type": "string"},
        "sales": {"type": "string"},
        "internal_comms": {"type": "string"},
        "customer_experience": {"type": "string"},
        "future_campaigns": {"type": "string"},
    },
}

_CONCEPT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": [
        "id", "name", "tagline", "strategic_rationale", "narrative",
        "visual_logic", "verbal_logic", "mood", "application_examples",
        "market_change", "distinctiveness_note", "visual_guidance",
        "verbal_guidance", "application_map", "creative_defense", "confidence",
    ],
    "properties": {
        "id": {
            "type": "string",
            "description": "Short snake_case slug, e.g. 'quiet_rebellion'.",
        },
        "name": {"type": "string"},
        "tagline": {"type": "string"},
        "strategic_rationale": {
            "type": "string",
            "description": "Why this concept exists, anchored in the DNA.",
        },
        "narrative": {
            "type": "string",
            "description": "The world the concept builds. 2-4 sentences.",
        },
        "visual_logic": {"type": "string"},
        "verbal_logic": {"type": "string"},
        "mood": {"type": "string"},
        "application_examples": {
            "type": "array",
            "items": {"type": "string"},
            "minItems": 3,
        },
        "market_change": {
            "type": "string",
            "description": "What this concept changes in the market.",
        },
        "distinctiveness_note": {
            "type": "string",
            "description": "Specifically how this differs from the other four.",
        },
        "visual_guidance": _VISUAL_GUIDANCE_SCHEMA,
        "verbal_guidance": _VERBAL_GUIDANCE_SCHEMA,
        "application_map": _APPLICATION_MAP_SCHEMA,
        "creative_defense": {
            "type": "string",
            "description": "The paragraph you would say out loud to defend this concept to the client.",
        },
        "confidence": {
            "type": "number",
            "minimum": 0,
            "maximum": 1,
            "description": "Your honest confidence that this concept is original AND defensible.",
        },
    },
}

_PILLARS_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["identity", "tone", "visuals", "message", "experience"],
    "properties": {
        "identity": {"type": "string"},
        "tone": {"type": "string"},
        "visuals": {"type": "string"},
        "message": {"type": "string"},
        "experience": {"type": "string"},
    },
}

_PILLARS_TOOL: dict[str, Any] = {
    "name": "record_concept_pillars",
    "description": "Record the foundational concept pillars for this brand.",
    "input_schema": {
        "type": "object",
        "required": ["pillars"],
        "properties": {
            "pillars": _PILLARS_SCHEMA,
        },
    },
}

_BATCH_CONCEPTS_TOOL: dict[str, Any] = {
    "name": "record_concept_batch",
    "description": "Record a batch of 2-3 concept directions. Later batches must be distinct from earlier ones.",
    "input_schema": {
        "type": "object",
        "required": ["concepts"],
        "properties": {
            "concepts": {
                "type": "array",
                "minItems": 2,
                "maxItems": 3,
                "items": _CONCEPT_SCHEMA,
            },
        },
    },
}


# ─── Public API ──────────────────────────────────────────────────────────────

def generate_concepts(
    dna: BusinessDNA,
    analysis: BrandAnalysis,
    *,
    model: str = SONNET,
    max_tokens: int = 10000,
    client: Anthropic | None = None,
) -> tuple[ConceptPillars, list[ConceptDirection]]:
    """Generate five distinct concept directions from a Business DNA.

    Uses batched API calls (3 concepts + 2 concepts) instead of a single
    monolithic call to reduce API payload complexity and timeout risk.

    Returns:
        (pillars, [concept1, ..., concept5])

    Raises:
        RuntimeError: if the model fails to call the required tool.
        pydantic.ValidationError: if the returned shape does not match.
        ValueError: if the model returns anything other than 5 concepts
            or if any two concepts share the same id (an obvious sign
            of variation-not-distinction).
    """
    c = client or _client()
    payload = {
        "business_dna": dna.model_dump(mode="json"),
        "brand_analysis": analysis.model_dump(mode="json"),
    }

    # ── First call: pillars + first 3 concepts ────────────────────────
    msg1 = c.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=_CONCEPT_SYSTEM,
        tools=[_PILLARS_TOOL, _BATCH_CONCEPTS_TOOL],
        tool_choice={"type": "tool", "name": "record_concept_pillars"},
        messages=[
            {
                "role": "user",
                "content": (
                    f"Generate the concept PILLARS for '{dna.brand_name}'. "
                    f"These are the foundational themes (identity, tone, visuals, "
                    f"message, experience) that all five concepts will build from. "
                    f"Use only the data below.\n\n"
                    f"```json\n{json.dumps(payload, indent=2)[:35000]}\n```"
                ),
            }
        ],
    )
    pillars_raw = _extract_tool_input(msg1, "record_concept_pillars")
    pillars = ConceptPillars.model_validate(pillars_raw["pillars"])

    # ── Second call: first 3 concepts ──────────────────────────────────
    time.sleep(1)  # Rate limit mitigation
    msg2 = c.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=_CONCEPT_SYSTEM,
        tools=[_BATCH_CONCEPTS_TOOL],
        tool_choice={"type": "tool", "name": "record_concept_batch"},
        messages=[
            {
                "role": "user",
                "content": (
                    f"Generate exactly THREE distinct concept directions for "
                    f"'{dna.brand_name}' based on these pillars: "
                    f"{json.dumps(pillars.model_dump(mode='json'), indent=2)}\n\n"
                    f"Use only the data below. No invented facts.\n\n"
                    f"```json\n{json.dumps(payload, indent=2)[:35000]}\n```"
                ),
            }
        ],
    )
    batch1_raw = _extract_tool_input(msg2, "record_concept_batch")
    concepts_1_3 = [ConceptDirection.model_validate(c) for c in batch1_raw["concepts"]]

    # ── Third call: final 2 concepts (aware of first 3) ────────────────
    time.sleep(1)  # Rate limit mitigation
    concepts_1_3_summary = "\n".join(
        f"- {c.name} ({c.id}): {c.strategic_rationale[:100]}"
        for c in concepts_1_3
    )
    msg3 = c.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=_CONCEPT_SYSTEM,
        tools=[_BATCH_CONCEPTS_TOOL],
        tool_choice={"type": "tool", "name": "record_concept_batch"},
        messages=[
            {
                "role": "user",
                "content": (
                    f"Generate exactly TWO more distinct concept directions for "
                    f"'{dna.brand_name}'. These must be DISTINCT from the three "
                    f"already created:\n\n{concepts_1_3_summary}\n\n"
                    f"Pillars to follow: {json.dumps(pillars.model_dump(mode='json'))}\n\n"
                    f"Data source:\n```json\n{json.dumps(payload, indent=2)[:35000]}\n```"
                ),
            }
        ],
    )
    batch2_raw = _extract_tool_input(msg3, "record_concept_batch")
    concepts_4_5 = [ConceptDirection.model_validate(c) for c in batch2_raw["concepts"]]

    concepts = concepts_1_3 + concepts_4_5

    if len(concepts) != 5:
        raise ValueError(
            f"Concept generator must return exactly 5 directions, got {len(concepts)}."
        )
    ids = [c.id for c in concepts]
    if len(set(ids)) != 5:
        raise ValueError(
            f"Concept directions must have unique ids, got duplicates: {ids}"
        )

    return pillars, concepts
