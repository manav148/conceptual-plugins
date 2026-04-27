"""Streamlit dashboard — renders a DashboardSummary JSON file.

Usage (from python_service/):
    .venv/bin/streamlit run dashboard/app.py

Reads:
    data/<brand>/dashboard.json   (default: data/wegovy/dashboard.json)

The dashboard is intentionally read-only: it loads the JSON the
pipeline (or the build script) produced and renders it. The brief
calls for scanability, modular sections, and comparison clarity —
this layout follows that.
"""

from __future__ import annotations

import json
import os
import re
import sys
from dataclasses import asdict
from pathlib import Path

import streamlit as st

# Make `app.*` imports work when streamlit is launched from python_service/
_PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))


# ─── Page setup ──────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Business DNA Dashboard",
    page_icon="●",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ─── Data loading ────────────────────────────────────────────────────────────

DATA_ROOT = Path(__file__).resolve().parents[1] / "data"


@st.cache_data
def list_dashboards() -> list[Path]:
    if not DATA_ROOT.exists():
        return []
    return sorted(DATA_ROOT.glob("*/dashboard.json"))


@st.cache_data
def load_dashboard(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


# Image extensions the gallery will recognize, in priority order.
_IMAGE_EXTS = (".png", ".jpg", ".jpeg", ".webp", ".gif")


def find_concept_images(brand_dir: Path, concept_id: str) -> list[Path]:
    """Return all images in <brand>/images/ matching <concept_id>*.

    Convention:
        data/<brand>/images/<concept_id>.png        (single hero)
        data/<brand>/images/<concept_id>_01.png     (variant 01)
        data/<brand>/images/<concept_id>_alt.webp   (any suffix)

    Files are sorted by name so variants render in a stable order.
    """
    images_dir = brand_dir / "images"
    if not images_dir.exists():
        return []
    out: list[Path] = []
    for p in sorted(images_dir.iterdir()):
        if p.is_file() and p.suffix.lower() in _IMAGE_EXTS:
            stem = p.stem.lower()
            if stem == concept_id or stem.startswith(concept_id + "_"):
                out.append(p)
    return out


def render_palette_swatches(hexes: list[str]) -> None:
    """Render a row of hex color swatches with labels."""
    if not hexes:
        st.caption("No palette locked.")
        return
    cols = st.columns(len(hexes))
    for col, hex_code in zip(cols, hexes):
        with col:
            st.markdown(
                f"""
                <div style="
                    background:{hex_code};
                    height:48px;
                    border-radius:6px;
                    border:1px solid rgba(0,0,0,0.08);
                "></div>
                <div style="
                    font-family:monospace;
                    font-size:0.8em;
                    text-align:center;
                    margin-top:4px;
                ">{hex_code}</div>
                """,
                unsafe_allow_html=True,
            )


_SLUG_RE = re.compile(r"[^a-z0-9]+")


def slugify(name: str) -> str:
    """Turn 'Zepbound — Eli Lilly' into 'zepbound_eli_lilly'."""
    s = _SLUG_RE.sub("_", name.lower()).strip("_")
    return s or "brand"


def _run_brand_investigation(
    *,
    brand_name: str,
    website: str,
    category: str | None,
    geo: str | None,
    notes: str | None,
    api_key_override: str | None,
    skip_interrogation: bool,
) -> None:
    """Drive the full pipeline for a new brand with live progress UI.

    Runs synchronously inside the Streamlit process. The expensive
    LLM stages each take 4-30s; total wall-clock is 60-120s.
    """
    # ── Validation ───────────────────────────────────────────────────────
    errors: list[str] = []
    if not brand_name:
        errors.append("Brand name is required.")
    if not website:
        errors.append("Website URL is required.")
    elif not (website.startswith("http://") or website.startswith("https://")):
        errors.append("Website URL must start with http:// or https://")
    if errors:
        for e in errors:
            st.error(e)
        return

    slug = slugify(brand_name)
    out_dir = DATA_ROOT / slug

    if out_dir.exists() and (out_dir / "dashboard.json").exists():
        st.warning(
            f"A brand named `{slug}` already exists. Pick a different "
            "name or delete `data/" + slug + "/dashboard.json` first."
        )
        return

    # ── Set API key for this process if user supplied an override ────────
    if api_key_override:
        os.environ["ANTHROPIC_API_KEY"] = api_key_override
    if not os.environ.get("ANTHROPIC_API_KEY"):
        st.error(
            "No Anthropic API key found. Either paste one into the form "
            "above or set ANTHROPIC_API_KEY in `python_service/.env`."
        )
        return

    # ── Run pipeline with live status panel ──────────────────────────────
    from app.models.schemas import ClientProfile
    from app.pipeline import run_pipeline

    out_dir.mkdir(parents=True, exist_ok=True)

    with st.status(f"Investigating {brand_name}…", expanded=True) as status:
        try:
            client_profile = ClientProfile(
                brand_name=brand_name,
                website=website,
                category=category,
                geo=geo,
                notes=notes,
            )

            st.write(f"⏳  Scraping {website}")
            st.write("⏳  Analyzing brand voice (Sonnet)")
            st.write("⏳  Constructing Business DNA (Opus)")
            st.write("⏳  Generating 5 concept directions (Sonnet)")
            st.write("⏳  Generating 20 ad ideas (Sonnet × 5 calls)")
            if not skip_interrogation:
                st.write("⏳  Running 100Q self-interrogation (Sonnet × 10 calls)")
            st.write("⏳  Building visual prompt package")

            result = run_pipeline(
                client_profile,
                skip_interrogation=skip_interrogation,
            )

            # Save dashboard.json
            dashboard_path = out_dir / "dashboard.json"
            dashboard_path.write_text(
                result.summary.model_dump_json(indent=2),
                encoding="utf-8",
            )

            # Also save raw signals + the brand analysis for debug
            (out_dir / "signals.json").write_text(
                json.dumps(result.raw_signals.to_dict(), indent=2),
                encoding="utf-8",
            )
            (out_dir / "brand_analysis.json").write_text(
                result.brand_analysis.model_dump_json(indent=2),
                encoding="utf-8",
            )

            t = result.timings
            st.write(
                f"✅  Done — total {t.total_ms / 1000:.1f}s "
                f"(scrape {t.scrape_ms}ms · analyze {t.analyze_ms / 1000:.1f}s · "
                f"DNA {t.dna_ms / 1000:.1f}s · concepts {t.concepts_ms / 1000:.1f}s · "
                f"ad ideas {t.ad_ideas_ms / 1000:.1f}s · "
                f"100Q {t.interrogation_ms / 1000:.1f}s)"
            )

            num_ideas = sum(len(s.ideas) for s in result.summary.visual_prompts.ad_sets)
            st.write(
                f"📦  Saved {dashboard_path.name} — "
                f"{len(result.summary.concepts)} concepts, {num_ideas} ad ideas"
            )

            qc = result.summary.interrogation
            if qc:
                emoji = "✅" if qc.overall_pass else "⚠️"
                st.write(
                    f"{emoji}  100Q gate: {qc.passed}/100 "
                    f"({'PASS' if qc.overall_pass else 'BLOCK'})"
                )

            status.update(
                label=f"✅  {brand_name} ready", state="complete", expanded=False
            )

            # Mark for default selection on rerun + invalidate caches
            st.session_state.just_built = slug
            list_dashboards.clear()
            load_dashboard.clear()

            st.success(
                f"**{brand_name}** investigation complete. "
                "Pick it from the brand selector above."
            )

        except Exception as e:  # noqa: BLE001 — surface every failure
            status.update(
                label=f"❌  Failed: {type(e).__name__}",
                state="error",
                expanded=True,
            )
            st.error(f"**{type(e).__name__}**: {e}")
            with st.expander("Stack trace"):
                import traceback
                st.code(traceback.format_exc(), language="text")


def render_trend_chips(trend_slugs: list[str]) -> None:
    """Render trend slugs as small chips."""
    if not trend_slugs:
        st.caption("No trends assigned.")
        return
    chip_html = " ".join(
        f"""<span style="
            display:inline-block;
            padding:3px 10px;
            margin:2px 4px 2px 0;
            background:#1a1a1a;
            color:#fff;
            border-radius:12px;
            font-size:0.75em;
            font-family:monospace;
        ">{slug.replace('_', ' ')}</span>"""
        for slug in trend_slugs
    )
    st.markdown(chip_html, unsafe_allow_html=True)


# ─── Sidebar: dashboard picker ───────────────────────────────────────────────

with st.sidebar:
    st.markdown("### Business DNA")
    st.caption("Concept architect — demo dashboard")
    st.divider()

    dashboards = list_dashboards()
    if not dashboards:
        st.error(
            "No dashboards found.\n\n"
            "Run a build script first, e.g.\n"
            "`python scripts/build_wegovy_dashboard.py`"
        )
        st.stop()

    options = {p.parent.name: p for p in dashboards}
    # If a new brand was just built, prefer it on this rerun
    default_index = 0
    if "just_built" in st.session_state and st.session_state.just_built in options:
        default_index = list(options.keys()).index(st.session_state.just_built)
    chosen_name = st.selectbox(
        "Brand", list(options.keys()), index=default_index, key="brand_picker"
    )
    chosen_path = options[chosen_name]

    st.divider()
    st.caption("File")
    st.code(str(chosen_path.relative_to(DATA_ROOT.parent)), language="text")

    # ─── Add new brand form ──────────────────────────────────────────────
    st.divider()
    with st.expander("➕  Add new brand", expanded=False):
        st.caption(
            "The system will scrape the brand's site, build the Business "
            "DNA, generate 5 distinct concepts and 20 ad ideas, then run "
            "the 100Q quality gate. Wall-clock: about 60–90 seconds."
        )

        with st.form("add_brand_form", clear_on_submit=False):
            new_brand_name = st.text_input(
                "Brand name *", placeholder="e.g. Zepbound"
            )
            new_brand_url = st.text_input(
                "Website URL *", placeholder="https://www.example.com"
            )
            new_brand_category = st.text_input(
                "Category", placeholder="(optional, e.g. weight management)"
            )
            new_brand_geo = st.text_input(
                "Geo", placeholder="(optional, e.g. US)"
            )
            new_brand_notes = st.text_area(
                "Notes", placeholder="(optional, anything the system should know)",
                height=68,
            )
            api_key_override = st.text_input(
                "Anthropic API key",
                placeholder="(optional — uses .env by default)",
                type="password",
            )
            skip_qc = st.checkbox(
                "Skip 100Q gate (faster, less rigorous)",
                value=False,
                help="Saves ~30s and ~$0.30 but bypasses the QC protocol.",
            )

            submitted = st.form_submit_button(
                "Run investigation", type="primary", use_container_width=True
            )

        if submitted:
            _run_brand_investigation(
                brand_name=new_brand_name.strip(),
                website=new_brand_url.strip(),
                category=new_brand_category.strip() or None,
                geo=new_brand_geo.strip() or None,
                notes=new_brand_notes.strip() or None,
                api_key_override=api_key_override.strip() or None,
                skip_interrogation=skip_qc,
            )


data = load_dashboard(chosen_path)
brand_dir = chosen_path.parent
client = data["client"]
dna = data["business_dna"]
pillars = data["concept_pillars"]
concepts = data["concepts"]
ad_sets = data["visual_prompts"]["ad_sets"]
ad_sets_by_concept = {s["concept_id"]: s for s in ad_sets}
interrogation = data.get("interrogation")


def find_ad_images(brand_dir: Path, ad_id: str) -> list[Path]:
    """Return all images matching <ad_id>* anywhere in <brand>/images/.

    Searches recursively so V1/V2/V3 sub-folders work for free.
    """
    images_dir = brand_dir / "images"
    if not images_dir.exists():
        return []
    out: list[Path] = []
    for p in sorted(images_dir.rglob("*")):
        if not p.is_file() or p.suffix.lower() not in _IMAGE_EXTS:
            continue
        stem = p.stem.lower()
        if stem == ad_id or stem.startswith(ad_id + "_"):
            out.append(p)
    return out


def first_image_for_concept(brand_dir: Path, concept_id: str) -> Path | None:
    """Find the first available image for a concept.

    Tries (in priority order):
      1. Any AdIdea image whose stem matches an ad_id under that concept
      2. The legacy <concept_id>* hero image
    """
    images_dir = brand_dir / "images"
    if not images_dir.exists():
        return None
    for p in sorted(images_dir.rglob("*")):
        if not p.is_file() or p.suffix.lower() not in _IMAGE_EXTS:
            continue
        stem = p.stem.lower()
        if stem.startswith(concept_id):
            return p
    return None


# ─── Header ──────────────────────────────────────────────────────────────────

st.markdown(f"# {client['brand_name']}")
left, right = st.columns([3, 1])
with left:
    st.markdown(f"**{dna['one_line_summary']}**")
    st.caption(
        f"{client.get('category') or 'Uncategorized'} · "
        f"{client.get('geo') or 'Global'} · "
        f"[{client['website']}]({client['website']})"
    )
with right:
    st.metric("Concepts", len(concepts))
    if interrogation:
        st.metric(
            "100Q gate",
            f"{interrogation['passed']}/100",
            delta="PASS" if interrogation["overall_pass"] else "BLOCK",
        )
    else:
        st.caption("100Q gate: not run")

st.divider()


# ─── Tabs ────────────────────────────────────────────────────────────────────

tab_dna, tab_concepts, tab_gallery, tab_compare, tab_prompts, tab_raw = st.tabs(
    ["Business DNA", "Concepts", "Gallery", "Compare", "Visual Prompts", "Raw"]
)


# ─── Tab 1: Business DNA ─────────────────────────────────────────────────────

with tab_dna:
    st.markdown("## Business DNA")
    st.caption("The operating system behind every concept below.")

    rows = [
        ("Purpose", dna["purpose"]),
        ("Personality", dna["personality"]),
        ("Positioning", dna["positioning"]),
        ("Promise", dna["promise"]),
        ("Uncontested space", dna["uncontested_space"]),
    ]
    for label, body in rows:
        with st.container(border=True):
            st.markdown(f"**{label}**")
            st.markdown(body)

    if dna.get("palette"):
        st.markdown("### Brand palette")
        pal = dna["palette"]
        render_palette_swatches([
            pal["primary"], pal["secondary"], pal["accent"], pal["background"]
        ])
        if pal.get("notes"):
            st.caption(pal["notes"])

    st.markdown("### Concept pillars")
    pillar_cols = st.columns(5)
    for col, (label, key) in zip(
        pillar_cols,
        [
            ("Identity", "identity"),
            ("Tone", "tone"),
            ("Visuals", "visuals"),
            ("Message", "message"),
            ("Experience", "experience"),
        ],
    ):
        with col:
            with st.container(border=True):
                st.markdown(f"**{label}**")
                st.caption(pillars[key])


# ─── Tab 2: Concepts (one expander per concept) ──────────────────────────────

with tab_concepts:
    st.markdown("## Five concept directions")
    st.caption(
        "Each rooted in the same DNA. Each occupies a distinct strategic axis."
    )

    for i, c in enumerate(concepts, start=1):
        with st.expander(
            f"**{i}. {c['name']}**  —  *{c['tagline']}*",
            expanded=(i == 1),
        ):
            # Aesthetic execution row: ad-idea count + first hero image
            ad_set = ad_sets_by_concept.get(c["id"], {})
            ideas = ad_set.get("ideas", [])
            aest_l, aest_r = st.columns([3, 2])
            with aest_l:
                st.markdown(f"**Ad ideas**: {len(ideas)} executions")
                if ideas:
                    angles = [idea["angle"] for idea in ideas]
                    st.caption("Angles: " + " · ".join(angles))
                if ideas and ideas[0].get("palette_hexes"):
                    st.markdown("**Lead palette**")
                    render_palette_swatches(ideas[0]["palette_hexes"])
            with aest_r:
                hero = first_image_for_concept(brand_dir, c["id"])
                if hero:
                    st.image(
                        str(hero),
                        caption=hero.name,
                        use_container_width=True,
                    )
                else:
                    st.caption(
                        "No hero image yet — drop one into "
                        f"`data/{brand_dir.name}/images/`"
                    )

            st.divider()
            top_l, top_r = st.columns([2, 1])
            with top_l:
                st.markdown("**Strategic rationale**")
                st.markdown(c["strategic_rationale"])
                st.markdown("**Narrative**")
                st.markdown(c["narrative"])
                st.markdown("**Market change**")
                st.markdown(c["market_change"])
                st.markdown("**Distinctiveness vs the other four**")
                st.markdown(c["distinctiveness_note"])
                st.markdown("**Creative defense**")
                st.info(c["creative_defense"])
            with top_r:
                st.metric("Confidence", f"{c['confidence']:.2f}")
                st.markdown("**Mood**")
                st.caption(c["mood"])
                st.markdown("**Application examples**")
                for ex in c["application_examples"]:
                    st.markdown(f"- {ex}")

            st.divider()
            vg = c["visual_guidance"]
            vb = c["verbal_guidance"]
            am = c["application_map"]

            cols = st.columns(2)
            with cols[0]:
                st.markdown("### Visual guidance")
                st.markdown(f"**Color & mood:** {vg['color_mood']}")
                if vg.get("typography_direction"):
                    st.markdown(f"**Typography:** {vg['typography_direction']}")
                st.markdown(f"**Imagery:** {vg['imagery_direction']}")
                st.markdown("**Style principles**")
                for p in vg["style_principles"]:
                    st.markdown(f"- {p}")
                d_l, d_r = st.columns(2)
                with d_l:
                    st.markdown("**Do**")
                    for d in vg["dos"]:
                        st.markdown(f"✓ {d}")
                with d_r:
                    st.markdown("**Don't**")
                    for d in vg["donts"]:
                        st.markdown(f"✗ {d}")

            with cols[1]:
                st.markdown("### Verbal guidance")
                st.markdown(f"**Tone of voice:** {vb['tone_of_voice']}")
                st.markdown(f"**Message framing:** {vb['message_framing']}")
                if vb.get("signature_phrases"):
                    st.markdown("**Signature phrases**")
                    for p in vb["signature_phrases"]:
                        st.markdown(f"- *{p}*")
                d_l, d_r = st.columns(2)
                with d_l:
                    st.markdown("**Do**")
                    for d in vb["dos"]:
                        st.markdown(f"✓ {d}")
                with d_r:
                    st.markdown("**Don't**")
                    for d in vb["donts"]:
                        st.markdown(f"✗ {d}")

            st.divider()
            st.markdown("### Application map")
            am_cols = st.columns(3)
            am_items = [
                ("Marketing", am["marketing"]),
                ("Content", am["content"]),
                ("Sales", am["sales"]),
                ("Internal comms", am["internal_comms"]),
                ("Customer experience", am["customer_experience"]),
                ("Future campaigns", am["future_campaigns"]),
            ]
            for idx, (label, body) in enumerate(am_items):
                with am_cols[idx % 3]:
                    with st.container(border=True):
                        st.markdown(f"**{label}**")
                        st.caption(body)


# ─── Tab 3: Gallery (image previews per concept) ─────────────────────────────

with tab_gallery:
    st.markdown("## Ad Set Gallery")
    st.caption(
        f"{sum(len(s['ideas']) for s in ad_sets)} ad ideas across "
        f"{len(ad_sets)} concepts. Drop images into "
        f"`data/{brand_dir.name}/images/` named `<ad_id>.png` "
        "(any sub-folder works — V1, V2, etc.)."
    )

    for s in ad_sets:
        st.markdown(f"### {s['concept_name']}")
        st.caption(f"`{s['concept_id']}` — {len(s['ideas'])} ideas")

        # 4-up grid (one column per ad idea)
        idea_cols = st.columns(len(s["ideas"]))
        for col, idea in zip(idea_cols, s["ideas"]):
            with col:
                with st.container(border=True):
                    st.markdown(f"**[{idea['angle']}]**")
                    st.markdown(f"### {idea['headline']}")

                    # Image preview (or empty state)
                    imgs = find_ad_images(brand_dir, idea["id"])
                    if imgs:
                        st.image(
                            str(imgs[0]),
                            caption=imgs[0].name,
                            use_container_width=True,
                        )
                        if len(imgs) > 1:
                            st.caption(f"+{len(imgs) - 1} variant(s)")
                    else:
                        st.info(
                            f"`{idea['id']}.png`",
                            icon="🖼️",
                        )

                    st.caption(f"**Caption:** {idea['primary_text_first_line']}")
                    st.caption(f"**CTA:** `{idea['cta_label']}`")

                    if idea.get("palette_hexes"):
                        render_palette_swatches(idea["palette_hexes"])

        st.divider()


# ─── Tab 4: Compare (side-by-side strip) ─────────────────────────────────────

with tab_compare:
    st.markdown("## Side-by-side")
    st.caption("Five concepts, one row each. Designed for fast comparison.")

    for c in concepts:
        with st.container(border=True):
            cols = st.columns([1.2, 2, 2, 1])
            with cols[0]:
                st.markdown(f"### {c['name']}")
                st.caption(c["tagline"])
                st.metric("Confidence", f"{c['confidence']:.2f}")
            with cols[1]:
                st.markdown("**Rationale**")
                st.caption(c["strategic_rationale"])
            with cols[2]:
                st.markdown("**Distinctiveness**")
                st.caption(c["distinctiveness_note"])
            with cols[3]:
                st.markdown("**Mood**")
                st.caption(c["mood"])


# ─── Tab 4: Visual prompts ───────────────────────────────────────────────────

with tab_prompts:
    st.markdown("## Visual prompt package")
    st.caption(
        f"Format: **{data['visual_prompts']['format_default']}** · "
        f"Platform: **{data['visual_prompts']['target_platform']}** · "
        f"{sum(len(s['ideas']) for s in ad_sets)} ad ideas total. "
        "Each prompt is continuous prose — no hex codes, no labels, no font "
        "names, no slugs in the prompt body."
    )

    for s in ad_sets:
        st.markdown(f"### {s['concept_name']}")
        st.caption(f"`{s['concept_id']}`")

        for idea in s["ideas"]:
            with st.expander(
                f"**[{idea['angle']}]** {idea['headline']} — `{idea['id']}`",
                expanded=False,
            ):
                top_l, top_r = st.columns([3, 2])
                with top_l:
                    st.markdown(f"**Headline:** {idea['headline']}")
                    st.markdown(f"**First caption line:** {idea['primary_text_first_line']}")
                    st.markdown(f"**CTA button:** `{idea['cta_label']}`")
                    st.markdown(f"**Format:** `{idea['format']}`")
                    st.markdown(f"**Angle:** `{idea['angle']}`")
                with top_r:
                    if idea.get("trend_slugs"):
                        st.markdown("**Active trends**")
                        render_trend_chips(idea["trend_slugs"])
                    if idea.get("palette_hexes"):
                        st.markdown("**Locked palette**")
                        render_palette_swatches(idea["palette_hexes"])

                st.markdown("**Composition notes**")
                st.info(idea["composition_notes"])

                st.markdown("**Palette in plain English**")
                st.caption(idea["palette_words"])

                st.markdown("**Image prompt** (continuous prose, ready for Nano Banana / Imagen / Ideogram)")
                st.code(idea["image_prompt"], language="text")

                st.markdown("**Negative prompt**")
                st.caption(idea.get("negative_prompt") or "—")

        st.divider()


# ─── Tab 5: Raw JSON (debugging / audit) ─────────────────────────────────────

with tab_raw:
    st.markdown("## Raw DashboardSummary")
    st.caption("Full JSON payload. Useful for debugging and downstream integrations.")
    st.download_button(
        "Download dashboard.json",
        data=json.dumps(data, indent=2),
        file_name=f"{client['brand_name'].lower()}_dashboard.json",
        mime="application/json",
    )
    st.json(data, expanded=False)
