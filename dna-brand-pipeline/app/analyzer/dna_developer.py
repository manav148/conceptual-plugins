"""DNA & Concepts Developer — transforms perception data into strategy.

Input: Brand perception JSON
Output: Full Business DNA + 5 Strategic Concepts (schema_version 1.1)
"""

from __future__ import annotations

import json
from typing import Any

from anthropic import Anthropic

from app.analyzer.llm import OPUS, _client, _extract_tool_input


_DNA_DEVELOPMENT_SYSTEM = """\
You are a strategic brand architect. Your job is to transform brand perception
research into a rigorous Business DNA and five distinct strategic concepts.

Input: Perception data (how people see the brand, feelings, positioning, tone)
Output: Structured DNA (purpose, personality, positioning, promise, unique_space, essence)

Be specific. Avoid generic language. Every field must be defensible and rooted
in the perception data provided. Do not invent facts.
"""


_DNA_TOOL: dict[str, Any] = {
    "name": "record_dna",
    "description": "Record the Business DNA derived from perception data.",
    "input_schema": {
        "type": "object",
        "required": ["purpose", "personality", "positioning", "promise", "unique_space", "essence"],
        "properties": {
            "purpose": {
                "type": "string",
                "description": "Why does this brand exist? (2-3 sentences, rooted in perception)",
            },
            "personality": {
                "type": "array",
                "items": {"type": "string"},
                "minItems": 3,
                "maxItems": 5,
                "description": "3-5 personality traits (e.g., 'confident', 'approachable')",
            },
            "positioning": {
                "type": "string",
                "description": "What unique market position does it own? (2-3 sentences)",
            },
            "promise": {
                "type": "string",
                "description": "What is the core promise to customers? (1-2 sentences)",
            },
            "unique_space": {
                "type": "string",
                "description": "What territory can only this brand own? (2-3 sentences)",
            },
            "essence": {
                "type": "string",
                "description": "One sentence distillation of the entire DNA",
            },
        },
    },
}


_CONCEPTS_TOOL: dict[str, Any] = {
    "name": "record_concepts",
    "description": "Record five distinct strategic concept directions.",
    "input_schema": {
        "type": "object",
        "required": ["concepts"],
        "properties": {
            "concepts": {
                "type": "array",
                "minItems": 5,
                "maxItems": 5,
                "items": {
                    "type": "object",
                    "required": [
                        "id", "title", "tagline", "strategic_insight", "core_promise",
                        "visual_world", "verbal_world", "copy_constraints", "how_it_challenges_norms"
                    ],
                    "properties": {
                        "id": {"type": "string", "pattern": "^C0[1-5]$"},
                        "title": {"type": "string"},
                        "tagline": {"type": "string", "maxLength": 80},
                        "strategic_insight": {"type": "string"},
                        "core_promise": {"type": "string"},
                        "visual_world": {
                            "type": "object",
                            "required": ["archetype", "colors", "typography", "imagery", "mood"],
                            "properties": {
                                "archetype": {"type": "string"},
                                "colors": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "minItems": 2,
                                },
                                "typography": {"type": "string"},
                                "imagery": {"type": "string"},
                                "mood": {"type": "string"},
                            },
                        },
                        "verbal_world": {
                            "type": "object",
                            "required": ["tone", "use", "avoid", "example"],
                            "properties": {
                                "tone": {"type": "string"},
                                "use": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "minItems": 3,
                                },
                                "avoid": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "minItems": 3,
                                },
                                "example": {"type": "string"},
                            },
                        },
                        "copy_constraints": {
                            "type": "object",
                            "required": ["max_headline_words", "banned_patterns", "required_tone"],
                            "properties": {
                                "max_headline_words": {"type": "integer", "minimum": 3},
                                "banned_patterns": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                },
                                "required_tone": {"type": "string"},
                            },
                        },
                        "how_it_challenges_norms": {"type": "string"},
                    },
                },
            },
        },
    },
}


def develop_dna_and_concepts(
    brand_name: str,
    perception_data: dict[str, Any],
    *,
    model: str = OPUS,
    client: Anthropic | None = None,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Develop DNA and 5 concepts from perception data.

    Returns:
        (dna_dict, [concept1, ..., concept5])
    """
    c = client or _client()

    perception_json = json.dumps(perception_data, indent=2)

    # Step 1: Develop DNA
    msg1 = c.messages.create(
        model=model,
        max_tokens=2000,
        system=_DNA_DEVELOPMENT_SYSTEM,
        tools=[_DNA_TOOL],
        tool_choice={"type": "tool", "name": "record_dna"},
        messages=[
            {
                "role": "user",
                "content": (
                    f"Develop the Business DNA for '{brand_name}' based on this perception data:\n\n"
                    f"```json\n{perception_json}\n```\n\n"
                    f"Be specific and rooted in the data. Avoid generic language."
                ),
            }
        ],
    )

    dna_raw = _extract_tool_input(msg1, "record_dna")
    dna = {
        "purpose": dna_raw["purpose"],
        "personality": dna_raw["personality"],
        "positioning": dna_raw["positioning"],
        "promise": dna_raw["promise"],
        "unique_space": dna_raw["unique_space"],
        "essence": dna_raw["essence"],
    }

    # Step 2: Develop 5 Concepts
    dna_json = json.dumps(dna, indent=2)
    msg2 = c.messages.create(
        model=model,
        max_tokens=6000,
        system=_DNA_DEVELOPMENT_SYSTEM,
        tools=[_CONCEPTS_TOOL],
        tool_choice={"type": "tool", "name": "record_concepts"},
        messages=[
            {
                "role": "user",
                "content": (
                    f"Develop FIVE distinct strategic concept directions for '{brand_name}'.\n\n"
                    f"Business DNA:\n```json\n{dna_json}\n```\n\n"
                    f"Perception data:\n```json\n{perception_json}\n```\n\n"
                    f"Rules:\n"
                    f"1. Each concept must be MUTUALLY EXCLUSIVE — executing one makes the other impossible\n"
                    f"2. All rooted in the DNA\n"
                    f"3. Each breaks 2+ industry norms\n"
                    f"4. Avoid generic language ('innovative', 'premium', 'where X meets Y')\n"
                    f"5. Each concept owns uncontested territory\n\n"
                    f"Generate IDs as C01, C02, C03, C04, C05."
                ),
            }
        ],
    )

    concepts_raw = _extract_tool_input(msg2, "record_concepts")
    concepts = concepts_raw["concepts"]

    return dna, concepts
