"""FastAPI entrypoint for the Business DNA Python microservice.

Laravel posts brand intake here; this service runs the full Business
DNA pipeline (scrape → analyze → DNA → concepts → 100Q gate → visual
prompts) and returns a DashboardSummary the UI can render directly.
"""

from __future__ import annotations

import logging
from dataclasses import asdict

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl

from app.models.schemas import ClientProfile, DashboardSummary
from app.pipeline import run_pipeline
from app.scrapers.trends import fetch_trends
from app.scrapers.website import scrape_website
from app.simple_pipeline import run_simple_pipeline
from app.analyzer.dna_developer import develop_dna_and_concepts

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="Business DNA Service", version="0.2.0")


# ─── Request models ──────────────────────────────────────────────────────────

class IntakeRequest(BaseModel):
    brand_name: str
    website: HttpUrl
    category: str | None = None
    geo: str = ""


class TrendsRequest(BaseModel):
    keywords: list[str]
    timeframe: str = "today 12-m"
    geo: str = ""


class PipelineRequest(BaseModel):
    brand_name: str
    website: HttpUrl
    category: str | None = None
    geo: str | None = None
    notes: str | None = None
    skip_interrogation: bool = False
    stealth_scrape: bool = False


class PipelineResponse(BaseModel):
    summary: DashboardSummary
    timings: dict
    debug: dict


# ─── Routes ──────────────────────────────────────────────────────────────────

@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "business-dna", "version": app.version}


@app.post("/scrape/website")
def scrape(req: IntakeRequest) -> dict:
    signals = scrape_website(str(req.website))
    if signals.status >= 400:
        raise HTTPException(
            status_code=502, detail=f"upstream returned {signals.status}"
        )
    return {"brand": req.brand_name, "signals": signals.to_dict()}


@app.post("/scrape/trends")
def trends(req: TrendsRequest) -> dict:
    return fetch_trends(
        req.keywords, timeframe=req.timeframe, geo=req.geo
    ).to_dict()


@app.post("/pipeline/run", response_model=PipelineResponse)
def pipeline_run(req: PipelineRequest) -> PipelineResponse:
    """Run the full Business DNA pipeline for one client.

    Returns the DashboardSummary plus per-stage timings. Failures from
    any stage surface as 502s — the pipeline never silently degrades.
    """
    client = ClientProfile(
        brand_name=req.brand_name,
        website=req.website,
        category=req.category,
        geo=req.geo,
        notes=req.notes,
    )
    try:
        result = run_pipeline(
            client,
            skip_interrogation=req.skip_interrogation,
            stealth_scrape=req.stealth_scrape,
        )
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e)) from e
    except Exception as e:  # noqa: BLE001 — surface all stage failures
        raise HTTPException(
            status_code=500, detail=f"{type(e).__name__}: {e}"
        ) from e

    return PipelineResponse(
        summary=result.summary,
        timings=asdict(result.timings),
        debug={
            "scrape_url": str(client.website),
            "scrape_status": result.raw_signals.status,
            "analysis_brand": result.brand_analysis.brand_name,
        },
    )


@app.post("/perception/analyze")
def perception_analyze(req: IntakeRequest) -> dict:
    """Simple brand perception analysis.

    Returns how people are seeing the brand online (feelings, sentiment, positioning, tone).
    """
    try:
        result = run_simple_pipeline(
            brand_name=req.brand_name,
            website=str(req.website),
        )
        return {
            "brand_name": result.brand_name,
            "website": result.website,
            "perception": result.perception,
            "scrape_status": result.scrape_status,
        }
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"{type(e).__name__}: {e}"
        ) from e


@app.post("/strategy/develop")
def strategy_develop(req: IntakeRequest) -> dict:
    """Develop DNA + 5 Strategic Concepts from brand perception.

    Takes brand name + website, analyzes perception, then develops full DNA and concepts.
    Returns schema_version 1.1 compatible output.
    """
    try:
        # Step 1: Get perception
        result = run_simple_pipeline(
            brand_name=req.brand_name,
            website=str(req.website),
        )

        # Step 2: Develop DNA + Concepts from perception
        dna, concepts = develop_dna_and_concepts(
            brand_name=result.brand_name,
            perception_data=result.perception,
        )

        return {
            "schema_version": "1.1",
            "brand_name": result.brand_name,
            "website": result.website,
            "dna": dna,
            "concepts": concepts,
            "perception": result.perception,
        }
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"{type(e).__name__}: {e}"
        ) from e
