"""Visual prompt builder — concepts → VisualPromptPackage (Nano Banana era).

v3 design goals (informed by failed v2 renders):

Image generators like Nano Banana / Imagen 4 / Ideogram render quoted
strings, hex codes, font names, and bracketed labels as TEXT on the
canvas. v2 used structured clauses with `[CONCEPT]`, `[PALETTE]`, hex
codes like `#0033A0`, and font names like "Tiempos Today" — and the
model rendered all of those as visible text. The output was unusable.

v3 rules (every one of these is a hard constraint, not a guideline):

  1. NO hex codes anywhere in the prompt body. Colors are described in
     natural language ("deep navy"), and the hex codes travel as a
     separate parameter the renderer can use as a side channel.

  2. NO bracket labels, NO ALL-CAPS section markers. The prompt is
     continuous prose that reads like a designer briefing another
     designer over coffee.

  3. NO font names. "An editorial bold serif" — never "Tiempos Today".
     Named typefaces become rendered text 100% of the time.

  4. NO trend slug names, NO concept slug names, NO project terminology.
     If it's a string the brief invented, the model will paint it.

  5. NO quoted taglines unless the concept *explicitly* needs one
     rendered word, in which case it goes through `text_overlay` as a
     separate field — not embedded in the image prompt.

  6. SAFE ZONES are described spatially in plain English so the model
     leaves room for the headline, the logo, and the CTA button. The
     copy and the brand mark are added in post-production.

  7. ONE focal point per ad. Every prompt has a single hero subject
     in the central safe zone. Multiple-element compositions are
     hallucination risk.

  8. The default format is 9:16 vertical (1080×1920) — Meta-first per
     2026 best practice. The composition rules also crop cleanly to
     4:5 and 1:1 because the hero lives in the central safe zone.

  9. The negative prompt is a sentence, not a comma-soup of keywords.
     Image models handle plain prose better than tag lists.

The build script authors the actual AdIdea objects (with the headline,
the hook angle, the spatial direction). This module's job is to take
each idea and emit a clean, lossless prompt + metadata wrapper.
"""

from __future__ import annotations

from app.models.schemas import (
    AdIdea,
    BrandPalette,
    BusinessDNA,
    ConceptAdSet,
    ConceptDirection,
    VisualPromptPackage,
)


# ─── Anti-cliché negative prompt (continuous prose, not tag soup) ────────────

NEGATIVE_PROMPT_PROSE = (
    "Avoid these visual tropes entirely: smiling stock models facing the "
    "camera, hands holding a single pill, soft teal pharma gradients, "
    "lab coats with stethoscopes, decorative DNA helixes, glowing chrome "
    "figures, isometric 3D product floats in space, bokeh sunrises, "
    "tropical leaves, marble textures, lifestyle yoga mats, fake handwriting, "
    "Midjourney chrome women, generic AI gradient backgrounds, watermarks, "
    "logos, brand marks, rendered hex codes, rendered URLs, rendered email "
    "addresses, captions, subtitles, comic-book speech bubbles, before-and-"
    "after split screens, low contrast composition, cluttered competing "
    "elements, repeated identical objects."
)


# ─── Format presets (Meta 2026 — vertical first) ────────────────────────────

FORMAT_DIMS: dict[str, tuple[int, int]] = {
    "9:16_1080x1920": (1080, 1920),
    "4:5_1080x1350": (1080, 1350),
    "1:1_1080x1080": (1080, 1080),
}


def format_dimensions(fmt: str) -> tuple[int, int]:
    return FORMAT_DIMS.get(fmt, (1080, 1920))


# ─── Composition language (the safe-zone vocabulary) ────────────────────────

# Meta crops aggressively. The central safe zone is roughly the middle
# 60% of the frame vertically, with the top ~14% reserved for headline
# and the bottom ~20% reserved for CTA + logo.
META_SAFE_ZONE_PROSE = (
    "Compose the image as a vertical 9:16 frame for a mobile phone. "
    "Reserve the top sixth of the frame as a quiet, uncluttered area "
    "where a headline will be added later in post. Reserve the bottom "
    "fifth as a calm band where a call-to-action button and a small "
    "logo will be added later. The single hero subject sits in the "
    "central safe area, generously framed, with breathing room on every "
    "side. Nothing critical touches the edges of the frame."
)


# ─── Prompt assembly ────────────────────────────────────────────────────────

def assemble_prompt(idea: AdIdea, dna: BusinessDNA) -> str:
    """Wrap a hand-authored AdIdea image_prompt with the universal frame.

    The build script provides the *creative* sentences (subject, mood,
    visual logic). This function adds the universal scaffolding that
    every Nano Banana prompt needs: format, safe zones, palette in
    plain English, single-focal-point discipline, and the negative
    prose at the end.

    The output is one continuous paragraph, no labels, no hex.
    """
    return (
        f"{idea.image_prompt.strip()} "
        f"{META_SAFE_ZONE_PROSE} "
        f"The palette is {idea.palette_words.strip()}. "
        f"One single hero subject, one focal point, no repeated elements. "
        f"Editorial graphic design execution, made by a human designer, "
        f"not generic AI imagery. The visual is for {dna.brand_name}, "
        f"a brand whose territory is {dna.uncontested_space.strip().rstrip('.')}. "
        f"{NEGATIVE_PROMPT_PROSE}"
    )


# ─── Public API ─────────────────────────────────────────────────────────────

def build_ad_idea_prompt(idea: AdIdea, dna: BusinessDNA) -> AdIdea:
    """Return a copy of the AdIdea with the image_prompt fully assembled.

    The input idea carries the *seed* image_prompt (the creative core
    written by the build script). This function wraps it with the
    universal Meta safe-zone language and negative prose, and ensures
    palette_hexes flow through but are NEVER embedded in the prompt body.
    """
    assembled = assemble_prompt(idea, dna)
    return idea.model_copy(update={
        "image_prompt": assembled,
        "negative_prompt": idea.negative_prompt or NEGATIVE_PROMPT_PROSE,
    })


def build_concept_ad_set(
    dna: BusinessDNA,
    concept: ConceptDirection,
    ideas: list[AdIdea],
) -> ConceptAdSet:
    """Wrap a list of AdIdeas (already authored for one concept) into a set."""
    if not ideas:
        raise ValueError(
            f"Concept {concept.id!r} has no ad ideas. Each concept must "
            "carry at least one AdIdea."
        )
    for idea in ideas:
        if idea.concept_id != concept.id:
            raise ValueError(
                f"AdIdea {idea.id!r} has concept_id {idea.concept_id!r} "
                f"but was attached to concept {concept.id!r}."
            )
    finalized = [build_ad_idea_prompt(i, dna) for i in ideas]
    return ConceptAdSet(
        concept_id=concept.id,
        concept_name=concept.name,
        ideas=finalized,
    )


def build_visual_prompt_package(
    dna: BusinessDNA,
    concepts_with_ideas: list[tuple[ConceptDirection, list[AdIdea]]],
) -> VisualPromptPackage:
    """Build a full VisualPromptPackage from concepts paired with ad ideas.

    The build script (per brand) is responsible for authoring the
    AdIdea seeds for each concept. This function pairs them, runs them
    through the universal assembler, and returns the wrapped package.
    """
    if not concepts_with_ideas:
        raise ValueError("Cannot build a visual prompt package from no concepts.")
    ad_sets = [
        build_concept_ad_set(dna, concept, ideas)
        for concept, ideas in concepts_with_ideas
    ]
    return VisualPromptPackage(ad_sets=ad_sets)
