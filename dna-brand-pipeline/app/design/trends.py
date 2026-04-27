"""Graphic design trends layer.

This module is the source of truth for the visual vocabulary the
prompt builder draws from. It exists because the brief is explicit
that visual outputs must avoid LLM-default territory and feel current,
ownable, and graphic-design-aware — not stock-pharma or generic-tech.

Each trend is a structured object with:
  - name: human-readable label
  - slug: stable identifier used by concepts to opt in
  - year_window: when the trend is in its peak relevance window
  - one_line: a single sentence the prompt can quote directly
  - vocabulary: phrases that can be slotted into image prompts
  - dos / donts: sharp guidance for the model
  - aliases: concept-side labels that automatically map to this trend
  - tension: the cliché this trend exists to push against

The list below reflects the curated March-April 2026 trend report
provided to the project. When trends shift, update this file (it is
the *only* place trends should live), and every prompt downstream
adapts automatically.

Concepts opt into 1-3 trends via their `visual_logic` / `mood` /
`style_principles` fields, which the prompt builder maps to slugs
through `trends_for_concept()`. This keeps the strategic content
(the concept) and the aesthetic execution (the trend) decoupled —
the same concept can be re-rendered against next quarter's trends
without rewriting the strategy.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Iterable


@dataclass(frozen=True)
class DesignTrend:
    slug: str
    name: str
    year_window: str
    one_line: str
    vocabulary: tuple[str, ...]
    dos: tuple[str, ...]
    donts: tuple[str, ...]
    aliases: tuple[str, ...]
    tension: str

    def to_dict(self) -> dict:
        return asdict(self)


# ─── Curated trend catalog (March–April 2026) ───────────────────────────────

TRENDS: tuple[DesignTrend, ...] = (
    DesignTrend(
        slug="hyper_bold_typography",
        name="Hyper-bold & experimental typography",
        year_window="2025-Q4 → 2026-Q3",
        one_line=(
            "Oversized, mixed-font collages with exaggerated, playful, wavy, "
            "or distorted letterforms — type as the hero element."
        ),
        vocabulary=(
            "oversized display type",
            "type collage",
            "kinetic lettering",
            "high-contrast type pairings",
            "letterforms set above eye-level scale",
            "type as hero element",
            "stretched and condensed mix",
            "type that breaks the frame",
        ),
        dos=(
            "let one word fill 60% of the surface",
            "pair a wide display serif with a narrow grotesk",
            "treat the period as a design element",
            "let letterforms touch or overlap the edges of the frame",
        ),
        donts=(
            "no centered all-caps headlines on white",
            "no system-font helvetica safety",
            "no decorative scripts as the primary face",
        ),
        aliases=(
            "type-driven", "monumental type", "editorial type",
            "type as monument", "bold typography",
        ),
        tension=(
            "the entire pharma category sets type at 18pt centered. "
            "This trend refuses that the second the headline is set."
        ),
    ),
    DesignTrend(
        slug="grain_and_tactile",
        name="Grainy blur + tactile/imperfect textures",
        year_window="2025-Q3 → 2026-Q4",
        one_line=(
            "Soft-focus grain, scratchy linework, rough overlays, dust, "
            "fingerprints, and uneven fills that counter the polished AI look."
        ),
        vocabulary=(
            "35mm grain",
            "soft analog blur",
            "uneven ink fill",
            "tactile paper texture",
            "scratchy linework",
            "dust and fiber overlay",
            "imperfect halftone",
            "warm photochemical degradation",
        ),
        dos=(
            "introduce visible grain across the entire frame",
            "let edges bloom and blur slightly",
            "use ink fill that looks hand-pulled",
            "leave fingerprints, dust, scratches in the background",
        ),
        donts=(
            "no clean vector gradients",
            "no glossy product render",
            "no AI-look chrome and glass",
        ),
        aliases=(
            "grain", "tactile", "analog", "imperfect",
            "warm imperfection", "photochemical",
        ),
        tension=(
            "the wellness and pharma categories have over-corrected into "
            "polished AI aesthetics. Tactile imperfection signals 'made by "
            "a person' in 0.4 seconds of scroll time."
        ),
    ),
    DesignTrend(
        slug="naive_handdrawn_mixed",
        name="Naive/hand-drawn & mixed-media illustrations",
        year_window="2025-Q4 → 2026-Q3",
        one_line=(
            "Wobbly doodles, hand-rendered elements, and collages of photos, "
            "brush textures and doodles — messy-but-intentional."
        ),
        vocabulary=(
            "hand-rendered linework",
            "deliberate wobble",
            "torn-paper collage",
            "brush texture overlay",
            "doodled annotation",
            "mixed-media composition",
            "marker on photo",
            "scribbled callouts",
        ),
        dos=(
            "annotate the hero with hand-drawn arrows",
            "collage two media together (photograph + pencil sketch)",
            "let shapes look drawn, not vectored",
            "use hand-cut paper as a layer",
        ),
        donts=(
            "no clip-art doodles",
            "no preset Photoshop brushes that read as 'fake hand-drawn'",
            "no fake handwriting fonts as substitutes for real marks",
        ),
        aliases=(
            "naive", "hand-drawn", "mixed-media", "collage",
            "annotated", "messy-but-intentional",
        ),
        tension=(
            "humanism is the only credible counterweight to the AI-generated "
            "look that has flooded every category. Doodles read as honesty."
        ),
    ),
    DesignTrend(
        slug="3d_motion_signal",
        name="Immersive 3D, motion & signal graphics",
        year_window="2026-Q1 → 2026-Q4",
        one_line=(
            "Subtle 3D depth, micro-animations, kinetic typography, and "
            "explosive 90s/Y2K-inspired shapes and lines."
        ),
        vocabulary=(
            "subtle 3D extrusion",
            "motion-implied still",
            "kinetic frame",
            "Y2K signal graphic",
            "90s broadcast lower-third",
            "data-viz chevron",
            "extruded hero element",
            "implied parallax",
        ),
        dos=(
            "give the hero element real depth (not a drop shadow)",
            "compose as if the still were a single frame of an animation",
            "use signal-graphic motifs from 90s broadcast design",
        ),
        donts=(
            "no fake 3D bevel",
            "no overuse of motion blur",
            "no metaverse-cliché chrome figures",
        ),
        aliases=(
            "3D", "motion", "kinetic", "signal graphic",
            "broadcast", "Y2K", "extruded",
        ),
        tension=(
            "still images compete with TikTok. Stillness has to imply motion "
            "or it loses the scroll fight."
        ),
    ),
    DesignTrend(
        slug="vibrant_high_contrast",
        name="Vibrant, high-energy palettes with high contrast",
        year_window="2025-Q4 → 2026-Q3",
        one_line=(
            "Saturated neons mixed with earthy tones, bold gradients, and "
            "maximalist layering — scroll-stopping energy that still respects "
            "brand and accessibility."
        ),
        vocabulary=(
            "saturated neon paired with deep earth",
            "high-contrast brand palette",
            "color block as architecture",
            "duotone with a third accent",
            "maximalist color layering",
            "WCAG-passing high-contrast",
        ),
        dos=(
            "lock to two brand colors plus one accent — no more",
            "use color as structure, not decoration",
            "pass AA contrast for any text or hero element",
        ),
        donts=(
            "no rainbow gradients",
            "no pastel washes",
            "no five-color minimum-viable-brand palettes",
        ),
        aliases=(
            "vibrant", "high contrast", "neon", "color block",
            "saturated", "duotone",
        ),
        tension=(
            "the entire health category is awash in pastel teal. Saturated, "
            "structural color is what cuts through that wash."
        ),
    ),
    DesignTrend(
        slug="surreal_absurdist",
        name="Surreal, absurdist & playful imagery",
        year_window="2025-Q3 → 2026-Q4",
        one_line=(
            "Dreamlike collages, exaggerated scale, visual jokes, and "
            "unexpected juxtapositions — humor and memorability."
        ),
        vocabulary=(
            "scale violation",
            "object out of context",
            "dreamlike collage",
            "visual non-sequitur",
            "uncanny juxtaposition",
            "deadpan still life",
            "single absurd gesture",
        ),
        dos=(
            "make one element ten times its expected size",
            "place one object somewhere it does not belong",
            "use deadpan composition for the absurd subject",
        ),
        donts=(
            "no zany comic-relief stock",
            "no ironic emoji",
            "no 'wacky' product mascots",
        ),
        aliases=(
            "surreal", "absurdist", "dreamlike", "uncanny",
            "scale violation", "deadpan",
        ),
        tension=(
            "memorability research is unambiguous: the absurd image gets "
            "remembered, the literal image gets scrolled past."
        ),
    ),
    DesignTrend(
        slug="organic_freeform",
        name="Organic / asymmetric freeform layouts",
        year_window="2025-Q4 → 2026-Q4",
        one_line=(
            "Anti-grid, flowing shapes, overlapping elements, zine-style "
            "chaos that replaces rigid structures with story-driven composition."
        ),
        vocabulary=(
            "anti-grid composition",
            "flowing organic shapes",
            "overlapping layers",
            "zine-style layout",
            "off-axis hero",
            "liquid baseline",
            "asymmetric weight",
        ),
        dos=(
            "let the hero break the implied grid",
            "overlap two layers with a torn or rough edge",
            "treat baseline as a curve, not a line",
        ),
        donts=(
            "no Bootstrap-style 12-column grid",
            "no centered, balanced, four-quadrant compositions",
            "no equal margins on every side",
        ),
        aliases=(
            "asymmetric", "freeform", "zine", "anti-grid", "organic",
        ),
        tension=(
            "perfect grids signal corporate. Imperfect ones signal author. "
            "Healthcare is the most over-gridded category in design."
        ),
    ),
    DesignTrend(
        slug="retro_futurism",
        name="Retro-futurism & distorted/nostalgic aesthetics",
        year_window="2025-Q4 → 2026-Q3",
        one_line=(
            "Y2K, punk grunge, blueprint schematics, distorted portraits "
            "with modern digital effects — nostalgic and futuristic at once."
        ),
        vocabulary=(
            "blueprint schematic",
            "Y2K iridescence",
            "halftone distortion",
            "CRT scan-line",
            "punk-zine xerox",
            "retro-futurist diagram",
            "broken-mirror portrait",
        ),
        dos=(
            "use a real schematic (anatomical, mechanical, architectural) as a layer",
            "introduce one distortion across the whole frame",
            "let one nostalgic element anchor the future-feeling rest",
        ),
        donts=(
            "no full-on 80s pastiche",
            "no synthwave grid floors",
            "no neon pink-and-cyan as a substitute for ideas",
        ),
        aliases=(
            "retro-futurism", "blueprint", "schematic", "Y2K",
            "distorted", "punk grunge",
        ),
        tension=(
            "blueprint schematics are the one nostalgic visual vocabulary "
            "the medical category can credibly use. Almost no one is."
        ),
    ),
    DesignTrend(
        slug="ai_assisted_human_curated",
        name="AI-assisted personalization, human-curated",
        year_window="2026-Q1 → ongoing",
        one_line=(
            "Modular adaptive creative generated at scale, but with original "
            "human curation, quirky illustration, and authentic storytelling "
            "preventing AI sameness."
        ),
        vocabulary=(
            "modular adaptive creative",
            "human-curated edge cases",
            "non-AI imperfections layered on AI base",
            "quirky illustration on systematic base",
            "small intentional flaws",
        ),
        dos=(
            "introduce a small intentional human flaw (a real scribble, "
            "a real photograph, a real hand) on top of the systematic base",
            "use AI for variation, never for the hero gesture",
        ),
        donts=(
            "no fully AI-generated hero imagery",
            "no obvious midjourney tropes (chrome figures, glowing women)",
            "no algorithm-only color choices",
        ),
        aliases=(
            "human-in-the-loop", "AI-assisted", "human curation",
            "modular", "adaptive",
        ),
        tension=(
            "the fastest way to look generic in 2026 is to look like an "
            "untouched AI render. Brands that win add visible humanity on top."
        ),
    ),
)

# ─── Lookup helpers ──────────────────────────────────────────────────────────

_BY_SLUG: dict[str, DesignTrend] = {t.slug: t for t in TRENDS}

# Build the alias index lazily so concept-side labels (e.g. 'editorial type',
# 'tactile', 'asymmetric') auto-map to the right trend slug.
_ALIAS_INDEX: dict[str, str] = {}
for _t in TRENDS:
    _ALIAS_INDEX[_t.slug] = _t.slug
    for _a in _t.aliases:
        _ALIAS_INDEX[_a.lower()] = _t.slug


def get_trend(slug: str) -> DesignTrend:
    """Look up a trend by slug. Raises KeyError on miss."""
    return _BY_SLUG[slug]


def all_trends() -> tuple[DesignTrend, ...]:
    return TRENDS


def trends_from_labels(labels: Iterable[str]) -> list[DesignTrend]:
    """Map free-text labels (from concept fields) to DesignTrend objects.

    De-duplicates and preserves the order of first appearance, so the
    most important trend ends up first in the prompt.
    """
    out: list[DesignTrend] = []
    seen: set[str] = set()
    for label in labels:
        if not label:
            continue
        slug = _ALIAS_INDEX.get(label.lower().strip())
        if slug and slug not in seen:
            out.append(_BY_SLUG[slug])
            seen.add(slug)
    return out
