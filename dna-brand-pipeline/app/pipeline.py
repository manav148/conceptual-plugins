"""Pipeline orchestrator — chains every layer into one DashboardSummary.

This is the function the FastAPI route calls (and the function any
future Laravel job will call). It is intentionally thin: each layer
is already self-contained and Pydantic-validated, so the orchestrator's
only job is to wire them together in the right order, fail loudly on
the first error, and stamp the result with timing/version metadata.

Stage map (matches the project pipeline in DOCS/...overview_prompt.md):

  3.1   intake          ← ClientProfile (caller-supplied)
  3.2   acquisition     ← scrape_website()
  3.3-4 parse + analyze ← analyze_brand()
  3.7   DNA             ← build_dna()
  3.8-11 concepts       ← generate_concepts()
  3.9   QC gate         ← run_interrogation() with ClaudeBackend
  3.12  visual prompts  ← build_visual_prompt_package()
  3.15  dashboard       ← DashboardSummary

Stages 3.5 (competitor intel) and 3.6 (red/blue ocean) are filled in
by the next layer; the DashboardSummary fields for them are Optional.

The orchestrator does NOT swallow exceptions. The brief is explicit
that we never invent unsupported facts and never present uncertainty
as fact — so a failure in any stage must surface to the caller, who
decides whether to retry, downgrade, or hand off to a human.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Optional

from app.analyzer.ad_ideas import generate_ad_ideas
from app.analyzer.concepts import generate_concepts
from app.analyzer.llm import analyze_brand, build_dna
from app.analyzer.visual_prompts import build_visual_prompt_package
from app.interrogation.claude_backend import ClaudeBackend
from app.interrogation.runner import (
    InterrogationBackend,
    StubBackend,
    run_interrogation,
)
from app.models.schemas import (
    AdIdea,
    BrandAnalysis,
    BusinessDNA,
    ClientProfile,
    ConceptDirection,
    ConceptPillars,
    DashboardSummary,
    InterrogationReport,
    VisualPromptPackage,
)
from app.scrapers.website import WebsiteSignals, scrape_website

logger = logging.getLogger(__name__)


@dataclass
class StageTimings:
    """Wall-clock time per stage. Useful for the cost/latency dashboard."""
    scrape_ms: int = 0
    analyze_ms: int = 0
    dna_ms: int = 0
    concepts_ms: int = 0
    ad_ideas_ms: int = 0
    interrogation_ms: int = 0
    visual_prompts_ms: int = 0
    total_ms: int = 0


@dataclass
class PipelineResult:
    summary: DashboardSummary
    timings: StageTimings
    raw_signals: WebsiteSignals
    brand_analysis: BrandAnalysis


def _ms_since(t0: float) -> int:
    return int((time.perf_counter() - t0) * 1000)


def run_pipeline(
    client: ClientProfile,
    *,
    interrogation_backend: Optional[InterrogationBackend] = None,
    skip_interrogation: bool = False,
    stealth_scrape: bool = False,
) -> PipelineResult:
    """Run the full Business DNA pipeline for one client.

    Args:
        client: validated intake (brand_name + website).
        interrogation_backend: override the QC backend. Defaults to
            ClaudeBackend in production. Tests can inject a fake.
        skip_interrogation: if True, the QC gate is bypassed entirely.
            Use ONLY for plumbing tests — the brief makes the gate
            mandatory before shipping.
        stealth_scrape: if True, use Scrapling's StealthyFetcher (browser).
            Use only when the static fetch returns thin/blocked content.

    Returns:
        PipelineResult with the dashboard payload, per-stage timings,
        and the raw signals + brand analysis (kept for debugging /
        internal dashboards).

    Raises:
        Any exception from any stage — failures are not swallowed.
    """
    overall_t0 = time.perf_counter()
    timings = StageTimings()

    # ── 3.2 acquisition ────────────────────────────────────────────────
    t0 = time.perf_counter()
    logger.info("scrape: %s", client.website)
    signals = scrape_website(str(client.website), stealth=stealth_scrape)
    timings.scrape_ms = _ms_since(t0)
    if signals.status >= 400:
        raise RuntimeError(
            f"Scrape failed for {client.website} with status {signals.status}"
        )

    # ── 3.3-4 parse + analyze ──────────────────────────────────────────
    t0 = time.perf_counter()
    logger.info("analyze: %s", client.brand_name)
    analysis: BrandAnalysis = analyze_brand(client.brand_name, signals)
    timings.analyze_ms = _ms_since(t0)

    # ── 3.7 DNA ────────────────────────────────────────────────────────
    t0 = time.perf_counter()
    logger.info("dna: %s", client.brand_name)
    dna: BusinessDNA = build_dna(analysis)
    timings.dna_ms = _ms_since(t0)

    # ── 3.8-3.11 concept generation ────────────────────────────────────
    t0 = time.perf_counter()
    logger.info("concepts: %s", client.brand_name)
    pillars: ConceptPillars
    concepts: list[ConceptDirection]
    pillars, concepts = generate_concepts(dna, analysis)
    timings.concepts_ms = _ms_since(t0)

    # ── 3.11.5 ad idea generation (4 ideas × 5 concepts = 20) ──────────
    t0 = time.perf_counter()
    logger.info("ad_ideas: %s", client.brand_name)
    concepts_with_ideas: list[tuple[ConceptDirection, list[AdIdea]]] = (
        generate_ad_ideas(dna, analysis, concepts)
    )
    timings.ad_ideas_ms = _ms_since(t0)

    # ── 3.9 QC gate ────────────────────────────────────────────────────
    interrogation: Optional[InterrogationReport] = None
    if not skip_interrogation:
        t0 = time.perf_counter()
        logger.info("interrogation: %s", client.brand_name)
        backend = interrogation_backend or ClaudeBackend()
        interrogation = run_interrogation(dna, concepts, backend=backend)
        timings.interrogation_ms = _ms_since(t0)
        if not interrogation.overall_pass:
            logger.warning(
                "100Q gate failed for %s: %d failures, notes=%r",
                client.brand_name,
                len(interrogation.failed_questions),
                interrogation.notes,
            )

    # ── 3.12 visual prompts (deterministic; wraps the LLM-authored ideas)
    t0 = time.perf_counter()
    visual_prompts: VisualPromptPackage = build_visual_prompt_package(
        dna, concepts_with_ideas
    )
    timings.visual_prompts_ms = _ms_since(t0)

    timings.total_ms = _ms_since(overall_t0)

    summary = DashboardSummary(
        client=client,
        business_dna=dna,
        concept_pillars=pillars,
        concepts=concepts,
        visual_prompts=visual_prompts,
        interrogation=interrogation,
    )

    return PipelineResult(
        summary=summary,
        timings=timings,
        raw_signals=signals,
        brand_analysis=analysis,
    )
