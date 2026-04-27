"""Pydantic schemas for the Business DNA pipeline.

These objects are the contract between every layer of the system:
scraping → parsing → analysis → DNA → concepts → visuals → dashboard.

Names match the data objects called out in the project brief
(client_profile, brand_analysis, competitor_map, red_ocean_findings,
blue_ocean_opportunities, business_dna, concept_pillars, concept_directions,
visual_prompt_package, dashboard_summary).
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field, HttpUrl, field_validator


SignalStrength = Literal["strong", "moderate", "weak"]

# Hex color regex used by BrandPalette + ConceptDirection.palette
_HEX_RE = re.compile(r"^#([0-9a-fA-F]{6}|[0-9a-fA-F]{3})$")


class BrandPalette(BaseModel):
    """Disciplined brand color palette used by every visual prompt.

    The brief calls for visuals to feel ownable and brand-aligned, not
    generic. The palette is the floor of that discipline: every prompt
    locks to these hexes plus an explicit accent. Prompts cannot ask
    for colors outside this set without breaking the design system.
    """
    primary: str           # the dominant brand hex
    secondary: str         # supporting brand hex
    accent: str            # one accent color, used sparingly
    background: str = "#FFFFFF"
    notes: Optional[str] = None

    @field_validator("primary", "secondary", "accent", "background")
    @classmethod
    def _hex(cls, v: str) -> str:
        if not _HEX_RE.match(v):
            raise ValueError(f"{v!r} is not a valid hex color (#RGB or #RRGGBB)")
        return v.upper()


# ─── 1. Client intake ────────────────────────────────────────────────────────

class ClientProfile(BaseModel):
    brand_name: str
    website: HttpUrl
    category: Optional[str] = None
    geo: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ─── 2. Brand analysis (from scraped signals → interpreted) ──────────────────

class ClassifiedSignal(BaseModel):
    bucket: Literal[
        "brand_identity", "tone_of_voice", "visual_language",
        "offers", "audience_signals", "positioning",
        "trust_markers", "emotional_value", "functional_value",
    ]
    value: str
    evidence: str  # raw quote/excerpt that justifies the classification
    strength: SignalStrength


class BrandAnalysis(BaseModel):
    brand_name: str
    summary: str
    messaging_patterns: list[str]
    tone_of_voice: list[str]
    value_propositions: list[str]
    promises: list[str]
    audience_cues: list[str]
    positioning_language: list[str]
    trust_markers: list[str]
    visual_clues: list[str]
    strengths: list[str]
    weaknesses: list[str]
    contradictions: list[str] = Field(default_factory=list)
    classified_signals: list[ClassifiedSignal] = Field(default_factory=list)


# ─── 3. Competitor map ───────────────────────────────────────────────────────

class Competitor(BaseModel):
    name: str
    website: Optional[HttpUrl] = None
    summary: Optional[str] = None
    messaging_themes: list[str] = Field(default_factory=list)
    visual_style: list[str] = Field(default_factory=list)
    tone: list[str] = Field(default_factory=list)
    claimed_space: Optional[str] = None
    strength: SignalStrength = "moderate"


class CompetitorMap(BaseModel):
    competitors: list[Competitor]
    overlap_themes: list[str]                  # what everyone is saying
    saturation_score: float = Field(ge=0, le=1)  # 0=blue, 1=red
    copycat_patterns: list[str] = Field(default_factory=list)


# ─── 4. Red / Blue ocean ─────────────────────────────────────────────────────

class RedOceanFindings(BaseModel):
    over_invested_factors: list[str]   # what the industry over-competes on
    saturated_messages: list[str]
    repetitive_visuals: list[str]
    common_audience_assumptions: list[str]
    value_cost_tradeoff: str           # the trap the industry is stuck in


class FourActions(BaseModel):
    """Blue Ocean Four Actions Framework."""
    eliminate: list[str]
    reduce: list[str]
    raise_: list[str] = Field(alias="raise")
    create: list[str]

    model_config = {"populate_by_name": True}


class BlueOceanOpportunities(BaseModel):
    uncontested_space: str
    four_actions: FourActions
    new_demand_hypothesis: str
    defensibility_window_months: int = 12
    fits_capabilities: bool = True
    rationale: str


# ─── 5. Business DNA ─────────────────────────────────────────────────────────

class BusinessDNA(BaseModel):
    """The one-page strategic foundation. Readable in <2 minutes."""
    brand_name: str
    purpose: str            # why it exists
    personality: str        # how it behaves
    positioning: str        # where it stands
    promise: str            # what it commits to
    uncontested_space: str  # the territory it can own
    one_line_summary: str
    palette: Optional[BrandPalette] = None
    version: int = 1
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ─── 6. Concept pillars (foundational, shared across the 5 directions) ──────

class ConceptPillars(BaseModel):
    identity: str
    tone: str
    visuals: str
    message: str
    experience: str


# ─── 7. The five concept directions ──────────────────────────────────────────

class ApplicationMap(BaseModel):
    marketing: str
    content: str
    sales: str
    internal_comms: str
    customer_experience: str
    future_campaigns: str


class VisualGuidance(BaseModel):
    color_mood: str
    style_principles: list[str]
    typography_direction: Optional[str] = None
    imagery_direction: str
    dos: list[str]
    donts: list[str]


class VerbalGuidance(BaseModel):
    tone_of_voice: str
    message_framing: str
    signature_phrases: list[str] = Field(default_factory=list)
    dos: list[str]
    donts: list[str]


class ConceptDirection(BaseModel):
    """One of the five distinct concept worlds."""
    id: str                            # short slug, e.g. "quiet_rebellion"
    name: str
    tagline: str
    strategic_rationale: str           # why this exists
    narrative: str                     # the world it builds
    visual_logic: str
    verbal_logic: str
    mood: str
    application_examples: list[str]
    market_change: str                 # what it changes in the market
    distinctiveness_note: str          # why it differs from the other 4
    visual_guidance: VisualGuidance
    verbal_guidance: VerbalGuidance
    application_map: ApplicationMap
    creative_defense: str              # the "I would defend this in front of the client" paragraph
    confidence: float = Field(ge=0, le=1)
    # Aesthetic execution layer (independent of strategy):
    trend_slugs: list[str] = Field(default_factory=list)  # 1-3 from app.design.trends
    palette_override: Optional[BrandPalette] = None       # if this concept reframes brand colors


# ─── 8. Visual prompt package (NanoBanana Pro hand-off) ──────────────────────

# ─── Ad ideas (Nano Banana / Meta 2026 era) ──────────────────────────────────

AdAngle = Literal[
    "hook",                # pattern-interrupt visual that stops the scroll
    "proof_point",         # anchored in a defensible, real claim
    "identity_callout",    # speaks directly to a specific patient identity
    "demonstration",       # shows the mechanism, the product, or a single fact
    "social_proof",        # third-party validation / testimonial pattern
    "before_after",        # only when the concept explicitly invites it
]

AdFormat = Literal[
    "9:16_1080x1920",      # Meta primary (Reels / Stories / Feed crop)
    "4:5_1080x1350",       # Meta secondary (Feed)
    "1:1_1080x1080",       # Meta tertiary (legacy Feed)
]


class AdIdea(BaseModel):
    """One ad execution within a concept's ad set.

    Each concept produces multiple ideas across different hook angles
    so Meta has the creative variety its algorithm rewards. The image
    prompt is continuous prose (no hex codes, no labels, no font names)
    so an image model can render it cleanly. Hex codes and format
    metadata live in their own fields and are passed to the renderer
    as parameters, never as prompt text.
    """
    id: str                            # e.g. "quiet_authority_01_hook"
    concept_id: str
    angle: AdAngle

    # Copy layer (added in post by the layout step, NOT rendered by the model)
    headline: str                      # ~6 words, the on-image headline
    primary_text_first_line: str       # the first visible caption line in feed
    cta_label: str                     # button text e.g. "Talk to your doctor"

    # Image generation
    image_prompt: str                  # continuous prose, no labels, no hex
    composition_notes: str             # spatial: hero zone, logo zone, cta zone, safe area
    palette_words: str                 # natural-language palette description (not hex)
    palette_hexes: list[str] = Field(default_factory=list)
    negative_prompt: Optional[str] = None

    # Format + trends
    format: AdFormat = "9:16_1080x1920"
    trend_slugs: list[str] = Field(default_factory=list)


class ConceptAdSet(BaseModel):
    """All ad ideas for one concept direction (typically 4-5)."""
    concept_id: str
    concept_name: str
    ideas: list[AdIdea]


class VisualPromptPackage(BaseModel):
    """The full creative ad-set library for the dashboard."""
    ad_sets: list[ConceptAdSet]        # one per concept (typically 5)
    format_default: AdFormat = "9:16_1080x1920"
    target_platform: str = "meta_2026"


# Deprecated alias kept for one release so callers don't break.
# New code should use AdIdea / ConceptAdSet directly.
class VisualPrompt(BaseModel):
    concept_id: str
    concept_name: str
    square_ad_prompt: str
    key_constraints: list[str] = Field(default_factory=list)
    brand_alignment_notes: str = ""
    negative_prompt: Optional[str] = None
    trend_slugs: list[str] = Field(default_factory=list)
    palette_hexes: list[str] = Field(default_factory=list)


# ─── 9. Self-interrogation protocol result ───────────────────────────────────

class InterrogationAnswer(BaseModel):
    question_id: int                   # 1..100
    category: str
    question: str
    answer: str
    pass_: bool = Field(alias="pass")

    model_config = {"populate_by_name": True}


class InterrogationReport(BaseModel):
    answers: list[InterrogationAnswer]
    total: int = 100
    passed: int
    failed_questions: list[int]
    overall_pass: bool
    notes: str


# ─── 10. Dashboard payload (the thing the UI renders) ────────────────────────

class DashboardSummary(BaseModel):
    client: ClientProfile
    business_dna: BusinessDNA
    concept_pillars: ConceptPillars
    concepts: list[ConceptDirection]
    visual_prompts: VisualPromptPackage
    # Filled in by the competitor/ocean layer when it lands.
    competitor_map: Optional[CompetitorMap] = None
    red_ocean: Optional[RedOceanFindings] = None
    blue_ocean: Optional[BlueOceanOpportunities] = None
    interrogation: Optional[InterrogationReport] = None
    generated_at: datetime = Field(default_factory=datetime.utcnow)
