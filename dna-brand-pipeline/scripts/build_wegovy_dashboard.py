"""Build a complete DashboardSummary for Wegovy without an Anthropic API call.

Demo path: scrape is real, the LLM stages are authored by Claude (the
session running this build), the deterministic stages run via the
existing pipeline modules. Output is a JSON file the Streamlit
dashboard reads.

Run from python_service/:
    .venv/bin/python scripts/build_wegovy_dashboard.py

Output:
    data/wegovy/dashboard.json
"""

from __future__ import annotations

import json
from pathlib import Path

from app.analyzer.visual_prompts import build_visual_prompt_package
from app.models.schemas import (
    AdIdea,
    ApplicationMap,
    BrandAnalysis,
    BrandPalette,
    BusinessDNA,
    ClassifiedSignal,
    ClientProfile,
    ConceptDirection,
    ConceptPillars,
    DashboardSummary,
    VerbalGuidance,
    VisualGuidance,
)


# ─── Brand palette ───────────────────────────────────────────────────────────
# Approximated from the public Wegovy / Novo Nordisk visual identity:
# a deep navy primary, a lighter brand blue, and an amber accent.
# Concept-level palette overrides (below) can reframe these for tonal effect.

WEGOVY_PALETTE = BrandPalette(
    primary="#0033A0",
    secondary="#00A0DF",
    accent="#FF9E1B",
    background="#FFFFFF",
    notes=(
        "Novo Nordisk lineage — navy + brand blue + amber accent. "
        "Concepts may strip or invert this palette for tonal effect, but "
        "no concept may introduce colors outside the override."
    ),
)


# ─── 1. Client intake ────────────────────────────────────────────────────────

client = ClientProfile(
    brand_name="Wegovy",
    website="https://www.wegovy.com",
    category="Prescription weight management (GLP-1)",
    geo="US",
    notes=(
        "Novo Nordisk's branded semaglutide for chronic weight management. "
        "Originally injection-only; recently added an FDA-approved oral form. "
        "Also indicated for cardiovascular risk reduction and adolescents 12+."
    ),
)


# ─── 2. Brand analysis ───────────────────────────────────────────────────────
# Authored by Claude from the scraped signals at data/wegovy/signals.json.
# Anchors every claim in language that actually appears on wegovy.com.

brand_analysis = BrandAnalysis(
    brand_name="Wegovy",
    summary=(
        "Wegovy presents itself as a clinically anchored, FDA-led weight "
        "management product backed by Novo Nordisk's diabetes/metabolic "
        "heritage. The site organizes the brand around three indications "
        "(adult obesity, adolescent obesity, cardiovascular risk) and now "
        "two delivery forms (pen and pill). The voice is consistently "
        "patient-facing-but-physician-mediated: every CTA routes back to "
        '"talk to your healthcare professional," and every patient story '
        'is footnoted with "compensated by Novo Nordisk" and "actor portrayal" '
        "compliance language. The brand is doing two things at once: "
        "(a) defending its category-defining authority against newer GLP-1s "
        "and telehealth wellness brands, and (b) softening the clinical "
        "register with relatable family narratives."
    ),
    messaging_patterns=[
        '"FDA-approved" used as primary trust anchor',
        "Indication switching as a navigation pattern (adult / adolescent / heart)",
        '"The first" / "the only" framing for category leadership',
        "Compensated patient ambassadors with named, identity-rich profiles",
        "Persistent routing to healthcare professional consultation",
        "Cost & insurance access framed as a separate destination",
        "Weight loss + cardiovascular risk reduction increasingly co-promoted",
    ],
    tone_of_voice=[
        "Clinical-meets-conversational",
        "Patient-led but physician-bounded",
        "Reassuring without overpromising",
        "Heavy on regulatory compliance language",
        "Family- and identity-centered in the testimonial layer",
    ],
    value_propositions=[
        "The original FDA-approved semaglutide for chronic weight management",
        "Now available as both an injectable pen and an oral pill",
        "May also reduce major cardiovascular events in adults with heart disease",
        "Approved for adolescents 12+, expanding the eligible population",
        "Backed by Novo Nordisk savings programs and insurance navigation",
    ],
    promises=[
        "Weight loss supported by clinical study results",
        "An option that fits adult, adolescent, and cardiovascular indications",
        "A path to access regardless of insurance status",
        "Ongoing support via the WeGo Together® program",
    ],
    audience_cues=[
        "Adults with obesity or overweight + a weight-related condition",
        "Adolescents 12+ with obesity (pen only)",
        "Adults with established cardiovascular disease",
        "Insurance-anxious patients (cost section is a top-level destination)",
        "Patients motivated by family identity (recurring testimonial theme)",
    ],
    positioning_language=[
        '"The first GLP-1 weight-loss medication available in a pill"',
        '"The only semaglutide tablet that\'s FDA-approved for weight loss"',
        '"Goes beyond weight management for adults"',
        '"WeGo Together®"',
    ],
    trust_markers=[
        "FDA approval cited at first scroll",
        "Boxed warning + prescribing information surfaced in nav",
        "Novo Nordisk corporate brand anchoring",
        "Healthcare professional site cross-link in primary nav",
        "Compensation disclosure on every patient quote",
    ],
    visual_clues=[
        "Photographic patient ambassadors (real, compensated)",
        '"Actor portrayal" disclaimers under lifestyle imagery',
        "Carousel-driven hero with rotating CTAs",
        "Conservative pharma palette (clean whites, brand teal/blue)",
        "Menu architecture prioritizes navigation breadth over visual punch",
    ],
    strengths=[
        "Category authority — first mover in GLP-1 weight loss",
        "Multi-indication footprint (obesity + heart + adolescents)",
        "New oral form is a genuine product-level differentiator",
        "Novo Nordisk scientific lineage is unmatched in this category",
    ],
    weaknesses=[
        "Voice is indistinguishable from generic pharma at the surface level",
        "Patient testimonials follow the same compensated-ambassador format every competitor uses",
        "The clinical authority story is buried under lifestyle warmth",
        "No visible position on the cultural conversation around GLP-1s",
    ],
    contradictions=[
        "Brand claims to 'go beyond weight management' but the homepage hero is still about weight loss",
        "Positions as scientific leader but presents like a wellness brand",
        "Compliance language ('actor portrayal') visually competes with the emotional warmth it's attached to",
    ],
    classified_signals=[
        ClassifiedSignal(
            bucket="positioning",
            value="The original FDA-approved semaglutide for weight loss",
            evidence='"the first GLP-1 weight-loss medication available in a pill" / "the only semaglutide tablet"',
            strength="strong",
        ),
        ClassifiedSignal(
            bucket="trust_markers",
            value="Regulatory authority anchoring",
            evidence='Boxed warning, prescribing information, and FDA references in primary nav',
            strength="strong",
        ),
        ClassifiedSignal(
            bucket="audience_signals",
            value="Family-identity motivation",
            evidence='"My wife and my kids—they\'re why I\'m staying on Wegovy"',
            strength="moderate",
        ),
        ClassifiedSignal(
            bucket="emotional_value",
            value="Long-term commitment and maintenance",
            evidence='"My goal is to keep making progress with Wegovy, and to keep going."',
            strength="moderate",
        ),
        ClassifiedSignal(
            bucket="functional_value",
            value="Cardiovascular risk reduction beyond weight loss",
            evidence='"may help reduce the risk of major heart events"',
            strength="strong",
        ),
        ClassifiedSignal(
            bucket="offers",
            value="Two delivery forms (pen + pill) of the same molecule",
            evidence='"Wegovy® is now a once-daily pill" / "Results With the Pen / Results With the Pill"',
            strength="strong",
        ),
        ClassifiedSignal(
            bucket="visual_language",
            value="Compliance-bound photographic warmth",
            evidence='"Actor portrayal" disclaimers attached to every lifestyle image',
            strength="moderate",
        ),
    ],
)


# ─── 3. Business DNA ─────────────────────────────────────────────────────────

business_dna = BusinessDNA(
    brand_name="Wegovy",
    purpose=(
        "To make obesity treatable as the chronic, biological condition it "
        "actually is — using the medicine that started the GLP-1 era."
    ),
    personality=(
        "A specialist who refuses to talk down. Deeply credentialed but "
        "patient-fluent. Treats the body like a system, not a moral failing. "
        "The voice that gets quieter when the stakes get higher — and never "
        "ends a sentence with an exclamation mark."
    ),
    positioning=(
        "The original FDA-approved semaglutide for weight management — and "
        "now for cardiovascular risk, adolescents, and a daily pill. The "
        "medicine the rest of the category was built around."
    ),
    promise=(
        "A treatment that works on the biology of obesity, supported by the "
        "company that made GLP-1 medicine real. Today as a weekly pen or a "
        "daily pill; tomorrow, wherever the science goes next."
    ),
    uncontested_space=(
        "The clinical-grade authority lane in a category that has been "
        "overrun by wellness branding, telehealth aesthetics, and "
        "transformation-narrative pharma. The brand that talks about obesity "
        "the way oncology talks about cancer — quietly, biologically, "
        "and with the receipts."
    ),
    one_line_summary=(
        "Wegovy: the medicine that made GLP-1 real — and the only one that "
        "talks about your body like a doctor, not a coach."
    ),
    palette=WEGOVY_PALETTE,
)


# ─── 4. Concept pillars ──────────────────────────────────────────────────────

concept_pillars = ConceptPillars(
    identity=(
        "Wegovy is a clinical-authority brand. Every concept must read as "
        "credentialed, never as wellness or coaching."
    ),
    tone=(
        "Quiet, exact, biological. The volume gets lower as the stakes get "
        "higher. No exclamation marks. No 'transformation' language."
    ),
    visuals=(
        "Editorial, anatomical, archival. White space as authority. "
        "Lifestyle photography is the exception, not the default."
    ),
    message=(
        "Obesity is biology. Wegovy is the medicine the category was built "
        "around. Every claim must trace back to FDA, science, or Novo Nordisk's "
        "scientific lineage."
    ),
    experience=(
        "Treatment first, lifestyle second. The brand respects the patient's "
        "intelligence. Every touchpoint should feel closer to a teaching "
        "hospital than to a wellness app."
    ),
)


# ─── 5. Five concept directions ──────────────────────────────────────────────
# Each occupies a different strategic axis. None are LLM-default. None are
# variations of "patient transformation". Each is defendable in front of a
# Novo Nordisk creative review.

def _concept_class_started_class() -> ConceptDirection:
    """Heritage / scientific lineage axis."""
    return ConceptDirection(
        id="class_that_started_class",
        name="The Class That Started The Class",
        tagline="Before there was a category, there was a molecule.",
        strategic_rationale=(
            "Every other GLP-1 in the weight-loss category — Zepbound, Mounjaro, "
            "off-label Ozempic, the compounded telehealth knockoffs — descends "
            "from the scientific work that produced semaglutide. Wegovy is the "
            "only one that can credibly own that lineage. This concept turns "
            "Wegovy from 'a weight-loss option' into 'the founding member of "
            "modern metabolic medicine.' It is a heritage play, but heritage "
            "in the way Rolex or Steinway own heritage: not nostalgia, "
            "ownership of a category's origin."
        ),
        narrative=(
            "Wegovy is not a participant in the GLP-1 era. It is the GLP-1 era. "
            "Every concept, every competitor, every compounded knockoff exists "
            "because of a molecule that Novo Nordisk made possible. We tell "
            "that story directly — without nostalgia and without humility."
        ),
        visual_logic=(
            "Archival-but-modern. Single molecule rendered like a constellation. "
            "Type-driven, almost monumental, with editorial restraint. Black "
            "background, single hero element. The aesthetic is closer to a "
            "Nature cover than a pharma ad."
        ),
        verbal_logic=(
            "First-position language. 'First. Only. Original.' Never 'better.' "
            "Sentences are short and definitive. No qualifiers, no hedging. "
            "The voice is the voice of the source."
        ),
        mood=(
            "Authoritative, monumental, quietly proud. The feeling of standing "
            "in the lobby of a research hospital named after the person who "
            "discovered the disease."
        ),
        application_examples=[
            "OOH: a single molecular diagram with the line 'It started here.'",
            "Out-of-home billboards in oncology and cardiology conference cities — without explanation.",
            "Sponsored anatomy education content for medical schools.",
            "Print ads in JAMA and NEJM that look like editorial spreads, not pharma.",
            "A dedicated 'Origin' page on wegovy.com that reads like a museum wall.",
        ],
        market_change=(
            "Reframes the category from 'which weight-loss drug is best' to "
            "'which weight-loss drug is the source.' Forces every competitor "
            "to argue against lineage they cannot claim."
        ),
        distinctiveness_note=(
            "This is the only concept rooted in the *past*. The other four "
            "look at the body (Inside the Body), the future (The Maintenance), "
            "the volume (Quiet Authority), or the form (Two Bodies). Heritage "
            "is the axis no telehealth competitor can copy."
        ),
        visual_guidance=VisualGuidance(
            color_mood=(
                "Deep ink, archival cream, single accent. Reduced palette. "
                "The opposite of pharma teal."
            ),
            style_principles=[
                "Single hero element per composition",
                "Type as monument, not decoration",
                "No people in hero imagery",
                "Black space is structural, not decorative",
            ],
            typography_direction=(
                "A serif with editorial weight. Think Atlas Grotesk paired with "
                "Founders Grotesk Mono for technical callouts."
            ),
            imagery_direction=(
                "Molecular diagrams, anatomical etchings, archival "
                "Novo Nordisk research photography reframed for modern composition."
            ),
            dos=[
                "Use first-position language: 'first', 'only', 'original'",
                "Show the molecule itself as a hero element",
                "Quote scientific publications, not patients",
            ],
            donts=[
                "Do not show before/after photography",
                "Do not use lifestyle imagery in hero positions",
                "Do not soften with wellness language",
            ],
        ),
        verbal_guidance=VerbalGuidance(
            tone_of_voice="Editorial, monumental, definitive.",
            message_framing=(
                "Position Wegovy as the source of the category. Every claim "
                "ties back to scientific lineage."
            ),
            signature_phrases=[
                "Before there was a category, there was a molecule.",
                "It started here.",
                "The medicine the rest of the category was built around.",
            ],
            dos=[
                "Use one sentence when one sentence is enough.",
                "Cite the science directly.",
                "Let silence do work the copy doesn't need to.",
            ],
            donts=[
                "No exclamation marks. None.",
                "No 'transformation' or 'journey' language.",
                "No comparative claims against named competitors.",
            ],
        ),
        application_map=ApplicationMap(
            marketing=(
                "A heritage campaign anchored by a single OOH execution: "
                "the molecule and a date. Print in major medical journals. "
                "No paid social in the launch wave."
            ),
            content=(
                "An 'Origin' editorial series — long-form, archival, written "
                "in the voice of a medical historian, not a brand."
            ),
            sales=(
                "Rep materials reframed from 'efficacy data' to 'category "
                "origin.' Physicians get a pocket-sized monograph, not a leave-behind."
            ),
            internal_comms=(
                "Novo Nordisk employees see themselves as custodians of a "
                "category, not sellers of a product. Helps with retention."
            ),
            customer_experience=(
                "Patient touchpoints (welcome kit, app onboarding) open with "
                "'You're starting the medicine that started the category.' "
                "Frames adherence as participation in something historical."
            ),
            future_campaigns=(
                "Every line extension and new indication slots cleanly: each "
                "is another chapter of the same origin story."
            ),
        ),
        creative_defense=(
            "We are sitting on the most defensible heritage claim in the entire "
            "weight-loss category and we are not using it. Zepbound cannot say "
            "this. The compounding pharmacies cannot say this. The telehealth "
            "brands selling our molecule definitely cannot say this. Heritage "
            "is the one axis where Wegovy has zero competition — and the moment "
            "we name it, every other brand has to argue against a story that "
            "is verifiably true. This concept moves Wegovy out of the 'best "
            "weight-loss drug' fight and into a fight no one else can enter."
        ),
        confidence=0.88,
        trend_slugs=[
            "hyper_bold_typography",  # type as monumental hero
            "grain_and_tactile",      # archival feel, photochemical warmth
            "retro_futurism",         # blueprint / schematic heritage
        ],
        palette_override=BrandPalette(
            primary="#0A0A0F",          # deep ink
            secondary="#F5EFE0",        # archival cream
            accent="#FF9E1B",           # the only brand color that survives
            background="#0A0A0F",       # black-on-cream, monumental
            notes="Strip the brand blues. Heritage lives in ink and cream.",
        ),
    )


def _concept_inside_the_body() -> ConceptDirection:
    """Biology / mechanism axis."""
    return ConceptDirection(
        id="inside_the_body",
        name="Inside the Body",
        tagline="Your hunger lives in your brain stem. So does our medicine.",
        strategic_rationale=(
            "Every weight-loss brand — pharma, wellness, telehealth — frames "
            "obesity as a behavior problem with a biological assist. This "
            "concept inverts the equation. Obesity is biology. Behavior is "
            "the assist. By making the *mechanism* the hero, Wegovy becomes "
            "the only brand telling the truth the science actually supports — "
            "and exits the willpower-narrative fight entirely."
        ),
        narrative=(
            "We open the body and show you what's happening. Hunger is not a "
            "moral failing — it is a signal from a specific structure in your "
            "brain. Wegovy works on that structure. We make the invisible "
            "visible, in the brand, in the campaign, in every touchpoint."
        ),
        visual_logic=(
            "Anatomical illustration meets contemporary data viz. Cross-sections, "
            "MRI overlays, hormone pathway diagrams. Brutalist information "
            "design. The aesthetic of a teaching hospital reissued by Pentagram."
        ),
        verbal_logic=(
            "Physiological. Specific. Names structures. 'GLP-1 receptors in "
            "the hypothalamus,' not 'feel less hungry.' Treats the patient "
            "as someone capable of learning."
        ),
        mood=(
            "Quietly clinical, intellectually generous. The mood of a great "
            "biology lecture, not a sales pitch."
        ),
        application_examples=[
            "Hero ad: a labeled cross-section of a head with the line 'this is where appetite begins.'",
            "Patient education series that reads like a Coursera course.",
            "Animated explainers showing GLP-1 receptor binding in real time.",
            "A clinic-facing print kit with anatomical posters, not patient posters.",
            "App: a 'Why It Works' tab that opens with mechanism, not motivation.",
        ],
        market_change=(
            "Replaces willpower narrative with biology narrative. Forces "
            "the entire category to either elevate its science or look "
            "shallow next to Wegovy."
        ),
        distinctiveness_note=(
            "Where Class-That-Started-Class owns the past, this concept owns "
            "the *body* itself. It is the only direction that refuses to put "
            "people in the hero imagery. It treats the patient as a learner, "
            "not a testimonial."
        ),
        visual_guidance=VisualGuidance(
            color_mood=(
                "Anatomical neutrals — bone, tissue, ink. A single accent "
                "color reserved for the active site of the medicine."
            ),
            style_principles=[
                "Anatomical illustration as primary imagery",
                "Information design over photography",
                "Labels are part of the composition, not annotation",
                "The body is shown, not implied",
            ],
            typography_direction=(
                "A modernist sans paired with a technical mono. Suprema or "
                "Söhne for headers; JetBrains Mono for callouts."
            ),
            imagery_direction=(
                "Cross-sections, neural pathways, hormone diagrams, MRI-style "
                "overlays. Commission a single illustrator for the whole world."
            ),
            dos=[
                "Name structures: hypothalamus, GLP-1 receptor, brain stem.",
                "Use information design as decoration.",
                "Make the medicine's mechanism literally visible.",
            ],
            donts=[
                "No before/after photography. Ever.",
                "No lifestyle imagery in hero positions.",
                "No emotional language about 'feeling better.'",
            ],
        ),
        verbal_guidance=VerbalGuidance(
            tone_of_voice="Physiological, specific, intellectually generous.",
            message_framing=(
                "Lead with biology. Use behavior only as the patient-facing "
                "consequence of the biology."
            ),
            signature_phrases=[
                "Your hunger lives in your brain stem.",
                "The medicine for the place the medicine works.",
                "Biology, not willpower.",
            ],
            dos=[
                "Use the actual anatomical names.",
                "Quote mechanism-of-action papers.",
                "Treat the reader as a future med student.",
            ],
            donts=[
                "No 'journey,' 'transformation,' or 'breakthrough' language.",
                "No hedging that softens the science.",
                "No emotional appeals dressed as data.",
            ],
        ),
        application_map=ApplicationMap(
            marketing=(
                "A campaign of educational hero ads — each one teaches a "
                "single biological concept. Distribution leans into longer, "
                "more thoughtful placements: print, podcasts, sponsored medical content."
            ),
            content=(
                "An anatomy-first content library. 'Why It Works' becomes "
                "a course, not a FAQ."
            ),
            sales=(
                "Rep materials become teaching aids. The brand-to-physician "
                "conversation moves from efficacy data to mechanism conviction."
            ),
            internal_comms=(
                "Helps Novo Nordisk's clinical teams feel proud of the brand "
                "for the right reasons — it sounds like the science they do."
            ),
            customer_experience=(
                "Patient onboarding includes a short anatomy walkthrough. "
                "Patients leave understanding *why*, which is the strongest "
                "predictor of adherence."
            ),
            future_campaigns=(
                "Every new indication (cardiovascular, adolescent, future) "
                "becomes a new chapter of biology — same world, new region."
            ),
        ),
        creative_defense=(
            "Every weight-loss brand on earth is fighting over willpower "
            "narratives. We are the only brand that can credibly tell people "
            "the truth: this is biology, and we are the medicine for the "
            "biology. The category is begging to be told this story by "
            "someone with the science to back it up — and we are the only "
            "brand with the science to back it up. This concept doesn't just "
            "reposition Wegovy; it reframes the entire category."
        ),
        confidence=0.91,
        trend_slugs=[
            "naive_handdrawn_mixed",   # anatomical illustration as hand-rendered
            "retro_futurism",          # blueprint / schematic vocabulary
            "hyper_bold_typography",   # body-part labels at monumental scale
        ],
        palette_override=BrandPalette(
            primary="#1A1A1A",          # near-black ink for the linework
            secondary="#E8DFD0",        # bone / tissue neutral
            accent="#0033A0",           # brand navy reserved for the active site
            background="#F2EBDC",       # warm anatomical paper
            notes="Bone, ink, and a single drop of brand navy at the active site.",
        ),
    )


def _concept_the_maintenance() -> ConceptDirection:
    """Time / long-term axis."""
    return ConceptDirection(
        id="the_maintenance",
        name="The Maintenance",
        tagline="The question isn't how much. It's how long.",
        strategic_rationale=(
            "Every brand in the category sells the loss. Wegovy can be the "
            "only one that sells the *staying*. The clinical reality is that "
            "obesity is a chronic disease and weight regain is the rule, not "
            "the exception — but no brand wants to talk about it because the "
            "loss is the seductive part. By owning maintenance, Wegovy claims "
            "the part of the journey every patient eventually arrives at, "
            "and every competitor avoids. It also aligns the brand with what "
            "Novo Nordisk actually wants commercially: long-tenure patients."
        ),
        narrative=(
            "Most weight-loss stories end at the loss. Ours starts there. "
            "Wegovy is the medicine for the years after the headline. We "
            "build a brand around the second chapter — the maintenance — "
            "because that's where the disease is actually treated."
        ),
        visual_logic=(
            "Time-based composition. Calendars, blister packs across years, "
            "long exposures, repeated objects. The aesthetic of a routine, "
            "not an event."
        ),
        verbal_logic=(
            "Calm, durable, future-tense. 'Year three.' 'Still here.' Sentences "
            "that imply continuation rather than transformation."
        ),
        mood=(
            "Patient and confident. The mood of a long marriage, not a "
            "wedding day."
        ),
        application_examples=[
            "Hero ad: a single Wegovy pen with three date stamps spanning years.",
            "Campaign: 'Year Three' — patients photographed exactly where they were in year one.",
            "Renewal-moment communications that read like anniversary cards.",
            "A 'Stay' content series for patients past the six-month mark.",
            "Pharmacy refill packaging that quietly references duration.",
        ],
        market_change=(
            "Reframes success in the category from 'how much weight came off' "
            "to 'how long it stayed off.' Every competitor either has to "
            "match this language and admit the chronic-disease truth, or "
            "look short-term."
        ),
        distinctiveness_note=(
            "This is the only concept that takes the *time axis* as its hero. "
            "Class-That-Started owns the past, Inside the Body owns the body, "
            "Quiet Authority owns the volume, Two Bodies owns the form. The "
            "Maintenance owns the future."
        ),
        visual_guidance=VisualGuidance(
            color_mood=(
                "Aged paper, soft sun, quiet domestic light. Warm but not "
                "wellness-warm — the warmth of a kitchen, not a spa."
            ),
            style_principles=[
                "Time-based composition (sequences, repetition, dates)",
                "Object photography over portrait photography",
                "Subtle wear and use — nothing pristine",
                "Calendars and dates as visual elements",
            ],
            typography_direction=(
                "A humanist serif with quiet authority. Tiempos Text or "
                "Lyon. Numerals get extra weight."
            ),
            imagery_direction=(
                "Pens, pill packs, calendars, kitchen counters. Long-take "
                "photography over commercial styling. People appear, but "
                "always as part of a routine, not a moment."
            ),
            dos=[
                "Show duration explicitly — dates, year numbers, repeats.",
                "Use objects to imply people.",
                "Photograph the routine, not the breakthrough.",
            ],
            donts=[
                "No before/after.",
                "No 'transformation' arc imagery.",
                "No new-product gloss.",
            ],
        ),
        verbal_guidance=VerbalGuidance(
            tone_of_voice="Calm, durable, anniversary-card honest.",
            message_framing=(
                "Anchor every claim in time. Use tenure language: 'Year three.' "
                "'Still here.' 'The second chapter.'"
            ),
            signature_phrases=[
                "The question isn't how much. It's how long.",
                "Year three.",
                "The medicine for the second chapter.",
            ],
            dos=[
                "Use the future tense.",
                "Reference duration specifically.",
                "Treat maintenance as the achievement.",
            ],
            donts=[
                "No weight numbers.",
                "No 'lose' verbs.",
                "No language that implies an end point.",
            ],
        ),
        application_map=ApplicationMap(
            marketing=(
                "An 'anniversary' communication architecture. Patients hear "
                "from the brand at month 6, year 1, year 2, etc. — each "
                "communication is part of the campaign."
            ),
            content=(
                "A 'Stay' editorial track aimed at patients who are past the "
                "newcomer phase. Practical, calm, tenure-respecting."
            ),
            sales=(
                "Reps lead with adherence data, not first-six-months data. "
                "Reframes the conversation with physicians."
            ),
            internal_comms=(
                "Anchors Novo Nordisk teams in the long-term outcome the "
                "company actually cares about commercially and clinically."
            ),
            customer_experience=(
                "The app, the welcome kit, the refill experience — all of it "
                "is built around the second year, not the first month."
            ),
            future_campaigns=(
                "The longer the brand runs this concept, the stronger it gets. "
                "It compounds — every year, the patient cohort that proves "
                "the concept gets bigger."
            ),
        ),
        creative_defense=(
            "Obesity is a chronic disease. Every regulator, every guideline, "
            "every Novo Nordisk scientist agrees on this — and not a single "
            "weight-loss brand acts like it. The Maintenance lets Wegovy be "
            "the first brand to act like the science is actually true. It's "
            "also the rare creative concept that aligns perfectly with "
            "commercial reality: long-tenure patients are what the business "
            "actually needs. We get strategy and creativity pulling in exactly "
            "the same direction, which is rare."
        ),
        confidence=0.86,
        trend_slugs=[
            "grain_and_tactile",            # photochemical warmth, lived-in
            "organic_freeform",             # anti-grid, domestic looseness
            "ai_assisted_human_curated",    # human flaws on top of system
        ],
        palette_override=BrandPalette(
            primary="#3A3024",          # warm brown ink
            secondary="#E8D7B8",        # aged paper
            accent="#0033A0",           # brand navy for the date stamp only
            background="#F4E8CE",       # afternoon light
            notes="Domestic warmth. Brand navy reserved for the calendar mark.",
        ),
    )


def _concept_quiet_authority() -> ConceptDirection:
    """Tone / volume axis."""
    return ConceptDirection(
        id="quiet_authority",
        name="Quiet Authority",
        tagline="In a category that screams, the medicine whispers.",
        strategic_rationale=(
            "The entire weight-loss category is loud. Wellness brands shout "
            "transformation, telehealth brands shout convenience, pharma "
            "competitors shout safety statistics. Wegovy can be the only "
            "brand that lowers its voice — and in doing so, becomes the "
            "only voice anyone actually hears. This is a tonal play, not "
            "a content play. It can run in parallel with any of the other "
            "concepts as a brand-system layer."
        ),
        narrative=(
            "We strip everything out. No exclamation marks. No 'amazing.' "
            "No carousel. The whole brand world becomes a single black "
            "sentence on a single white card. We earn attention by refusing "
            "to ask for it."
        ),
        visual_logic=(
            "Editorial typography on negative space. One image or one "
            "sentence per surface. The aesthetic of a New York Times "
            "centerfold ad in 1979."
        ),
        verbal_logic=(
            "Monosyllabic when possible. Period as ammunition. Every line "
            "could be carved in stone."
        ),
        mood=(
            "Cardiologist explaining a diagnosis. Quiet, exact, completely "
            "undistracted by anything decorative."
        ),
        application_examples=[
            "Hero ad: black on white. One sentence: 'Heart attack. Stroke. Now we have something.'",
            "OOH: a single word per billboard, run as a sequence across a city.",
            "Print spreads in The Economist that look almost like editorial.",
            "Patient communications stripped of every visual element except the message.",
            "Conference rooms at Novo Nordisk repainted to match.",
        ],
        market_change=(
            "Resets the volume of the entire category. Forces every "
            "competitor's exuberance to look like overcompensation."
        ),
        distinctiveness_note=(
            "This is the only concept that owns the *tonal* axis. It is also "
            "the most flexible — Quiet Authority can be the brand-system "
            "layer that wraps any of the other four concepts. But on its own "
            "it's also a complete world."
        ),
        visual_guidance=VisualGuidance(
            color_mood=(
                "Pure white, deep ink, nothing else. One color total. "
                "Maximum contrast, minimum gesture."
            ),
            style_principles=[
                "Negative space is the hero",
                "One element per surface",
                "Type as the only image",
                "No gradient, no decoration, no carousel",
            ],
            typography_direction=(
                "A serious editorial serif with strong italic. Times Today, "
                "Caslon Doric, or a custom display serif."
            ),
            imagery_direction=(
                "Almost no imagery. When imagery is used, it's a single "
                "object photographed like a museum artifact."
            ),
            dos=[
                "Use the period as a design element.",
                "Set one sentence in 96pt and let it sit.",
                "Trust silence.",
            ],
            donts=[
                "No carousels.",
                "No exclamation marks. None.",
                "No more than one idea per surface.",
            ],
        ),
        verbal_guidance=VerbalGuidance(
            tone_of_voice="Monosyllabic, undecorated, definitive.",
            message_framing=(
                "Each surface holds exactly one idea. Sentences end early. "
                "The reader fills in the rest."
            ),
            signature_phrases=[
                "Now we have something.",
                "It's medicine.",
                "Quiet on purpose.",
            ],
            dos=[
                "Cut the sentence in half. Then in half again.",
                "End on the period that hurts.",
                "Trust the reader to do the work.",
            ],
            donts=[
                "No adjectives unless they pay rent.",
                "No phrases longer than they need to be.",
                "No emotional cushioning.",
            ],
        ),
        application_map=ApplicationMap(
            marketing=(
                "A campaign that can be run with a fraction of the media "
                "budget — because every surface earns its own attention. "
                "OOH, print, sponsored editorial."
            ),
            content=(
                "A 'one card a day' content rhythm. Each post is a single "
                "sentence. The internet does the rest."
            ),
            sales=(
                "Leave-behinds become single-sentence cards. Reps stop "
                "carrying decks."
            ),
            internal_comms=(
                "Wegovy email signatures, conference room signage, slide "
                "templates — all rebuilt in this language."
            ),
            customer_experience=(
                "App copy is rewritten to match. Each screen says one thing. "
                "Patients leave understanding more, not less."
            ),
            future_campaigns=(
                "This is the easiest concept to scale — the rules are so "
                "tight that future creative work practically writes itself."
            ),
        ),
        creative_defense=(
            "The weight-loss category has trained patients to tune out. "
            "Every brand sounds like every other brand. The single fastest "
            "way to be heard inside that noise is to refuse to make any. "
            "Quiet Authority is a tonal asset — once Wegovy owns this volume, "
            "no one else can take it without looking like a copycat. It also "
            "happens to be the cheapest of the five concepts to produce, "
            "which the CFO will appreciate."
        ),
        confidence=0.84,
        trend_slugs=[
            "hyper_bold_typography",  # one sentence, monumental scale
            "organic_freeform",       # off-axis hero, off-center weight
            "grain_and_tactile",      # newspaper grain on the type
        ],
        palette_override=BrandPalette(
            primary="#000000",          # pure black type
            secondary="#FFFFFF",        # pure white field
            accent="#0033A0",           # brand navy as the only accent
            background="#FFFFFF",
            notes="Two colors, one accent. The brand exists in the negative space.",
        ),
    )


def _concept_two_bodies() -> ConceptDirection:
    """Form / pen+pill duality axis."""
    return ConceptDirection(
        id="two_bodies",
        name="Two Bodies",
        tagline="One molecule. Two ways to live with it.",
        strategic_rationale=(
            "Wegovy is now the only FDA-approved semaglutide available as "
            "both a weekly injection and a daily pill. Most pharma brands "
            "treat multi-form launches awkwardly, with two product pages "
            "that compete with each other. This concept turns the duality "
            "into the brand's defining gesture: a single molecule offered "
            "in two embodiments. It also gives Wegovy a clear, unique "
            "story to tell *right now*, in the moment of the pill launch."
        ),
        narrative=(
            "The same medicine. Two bodies for it. Some patients want a "
            "weekly pen and the certainty of a routine that lives in the "
            "fridge. Some patients want a daily pill and the privacy of "
            "swallowing it with breakfast. Wegovy is the only brand that "
            "doesn't make you choose the molecule based on the form. "
            "We make the duality the point."
        ),
        visual_logic=(
            "Split-screen everything. Every composition is exactly halved. "
            "Pen on left, pill on right. Same molecule, two embodiments. "
            "The world is built around the line down the middle."
        ),
        verbal_logic=(
            "Parallel construction. Every sentence has two halves. "
            "'For the pen patient. For the pill patient.' Symmetry as voice."
        ),
        mood=(
            "Modernist and slightly playful. The mood of a beautifully "
            "designed product family — Apple's pen + pencil, but for medicine."
        ),
        application_examples=[
            "Hero ad: a single image divided by a thin line — pen left, pill right, identical typography.",
            "Out-of-home as diptychs: two billboards side by side, same molecule, two forms.",
            "Pharmacy POS that physically splits product information into two columns.",
            "App: a 'Choose Your Form' onboarding that becomes the brand's signature gesture.",
            "Conference booth designed around a literal axis — pen on one side of the table, pill on the other.",
        ],
        market_change=(
            "Turns the multi-form awkwardness most pharma brands hide into "
            "Wegovy's defining brand asset. Forces single-form competitors "
            "to either match (years away) or look limited."
        ),
        distinctiveness_note=(
            "This is the only concept anchored in the *product itself* — "
            "not the past, not the body, not the future, not the volume. "
            "It is also the most timely: the pill launch is happening now, "
            "and this concept exists because the product exists."
        ),
        visual_guidance=VisualGuidance(
            color_mood=(
                "Two complementary tones — one warm, one cool — meeting at "
                "the centerline. The line itself is the brand."
            ),
            style_principles=[
                "Every composition is a diptych",
                "Symmetry is mandatory, not optional",
                "Parallel construction in type as well as image",
                "The line down the middle is a brand asset",
            ],
            typography_direction=(
                "A symmetric sans with tight metrics. Söhne, Inter Display, "
                "or a custom geometric. Two weights, never more."
            ),
            imagery_direction=(
                "Diptychs of objects. Pen and pill photographed identically. "
                "When people appear, they appear in pairs."
            ),
            dos=[
                "Build every layout around a vertical centerline.",
                "Use parallel construction in headlines.",
                "Treat the line itself as a logo element.",
            ],
            donts=[
                "Never show pen and pill in different visual languages.",
                "No 'choose one' framing — the brand stance is 'have both available.'",
                "No asymmetric layouts.",
            ],
        ),
        verbal_guidance=VerbalGuidance(
            tone_of_voice="Symmetric, modern, slightly playful.",
            message_framing=(
                "Every message has two halves. The brand voice is parallel "
                "construction at sentence level."
            ),
            signature_phrases=[
                "One molecule. Two ways to live with it.",
                "For the pen. For the pill.",
                "Same medicine. Your form.",
            ],
            dos=[
                "Use parallel construction in every headline.",
                "Make the duality the point.",
                "Treat the form choice as freedom, not difficulty.",
            ],
            donts=[
                "Never describe one form as 'better' than the other.",
                "No asymmetric copy.",
                "No 'we used to be a pen, now we're also a pill' framing.",
            ],
        ),
        application_map=ApplicationMap(
            marketing=(
                "A launch campaign anchored entirely on the duality. "
                "Diptych OOH, pharmacy POS, paired social posts."
            ),
            content=(
                "A 'Two Patients, Two Forms' editorial series. Two voices "
                "per piece. Symmetric across the entire content library."
            ),
            sales=(
                "Reps carry a single physical artifact: pen and pill in "
                "one frame. Reframes the conversation as 'choose the form, "
                "we'll match the molecule.'"
            ),
            internal_comms=(
                "Helps Novo Nordisk's teams stop treating the pen and pill "
                "as competing internal businesses. They are one brand."
            ),
            customer_experience=(
                "Patient onboarding starts with a form preference question. "
                "Refills can switch between forms over time."
            ),
            future_campaigns=(
                "If a third form ever launches (oral spray, weekly tablet, "
                "etc.), the brand world is already built to absorb it."
            ),
        ),
        creative_defense=(
            "We just launched the most strategically important new form in "
            "the history of the brand and we are talking about it like it's "
            "an inventory update. Two Bodies makes the pill launch into a "
            "brand event, not a product event. It's also the only one of "
            "the five concepts that uses the actual fact pattern of *now* — "
            "the others are evergreen, this one is timely. That makes it the "
            "right concept to lead with if Novo Nordisk wants the pill "
            "launch to define the next year of the brand."
        ),
        confidence=0.83,
        trend_slugs=[
            "vibrant_high_contrast",  # diptych in saturated brand color
            "3d_motion_signal",       # subtle depth on each form
            "hyper_bold_typography",  # parallel construction at scale
        ],
        # Two Bodies keeps the brand palette but inverts the dominance:
        # the brighter blue takes the lead so the diptych pops.
        palette_override=BrandPalette(
            primary="#00A0DF",          # bright brand blue (LED)
            secondary="#0033A0",        # navy (the line down the middle)
            accent="#FF9E1B",           # amber accent on type only
            background="#F2F4F7",       # neutral display surface
            notes="Brand palette inverted — bright blue leads, navy structures.",
        ),
    )


concepts: list[ConceptDirection] = [
    _concept_class_started_class(),
    _concept_inside_the_body(),
    _concept_the_maintenance(),
    _concept_quiet_authority(),
    _concept_two_bodies(),
]


# ─── 6. Ad ideas — 4 per concept × 5 = 20 total ──────────────────────────────
#
# Each idea is one Meta ad creative. The image_prompt is hand-authored
# CONTINUOUS PROSE. It contains no hex codes, no bracket labels, no font
# names, no slugs, no quoted taglines. The headline + cta_label are
# rendered LATER by the layout step (designer or post-processing), never
# by the image model. The palette travels as natural-language words in
# the prompt body and as hex codes in palette_hexes for the renderer.
#
# Hook angles cycle across the four ideas per concept:
#   1. hook              — pattern-interrupt visual that stops the scroll
#   2. proof_point       — anchored in a defensible, real claim
#   3. identity_callout  — speaks to a specific patient identity
#   4. demonstration     — shows the mechanism, the product, or one fact

WEGOVY_AD_IDEAS: list[AdIdea] = [

    # ── Concept 1: The Class That Started The Class ──────────────────────────
    AdIdea(
        id="class_that_started_class_01_hook",
        concept_id="class_that_started_class",
        angle="hook",
        headline="Before there was a category, there was a molecule.",
        primary_text_first_line=(
            "Every GLP-1 weight-loss brand on the market today exists because "
            "of one molecule."
        ),
        cta_label="Talk to your doctor",
        image_prompt=(
            "A single hand-drawn ink rendering of a molecular structure, "
            "centered on a deep ink-black background, the molecular bonds "
            "drawn with the precise calligraphic hand of an early 20th "
            "century chemistry textbook, the image grainy and slightly "
            "foxed as if reproduced from an archival paper, warm cream "
            "highlights bleeding through, an editorial monumental "
            "composition with abundant black space around the molecule."
        ),
        composition_notes=(
            "Hero molecule sits dead-center occupying the middle 50% of the "
            "frame. Top sixth is pure black space for headline overlay. "
            "Bottom fifth is pure black space for CTA button + small logo."
        ),
        palette_words="deep ink black, archival cream highlights, a single warm amber accent",
        palette_hexes=["#0A0A0F", "#F5EFE0", "#FF9E1B"],
        trend_slugs=["grain_and_tactile", "retro_futurism"],
    ),
    AdIdea(
        id="class_that_started_class_02_proof_point",
        concept_id="class_that_started_class",
        angle="proof_point",
        headline="Forty years of metabolic science.",
        primary_text_first_line=(
            "Novo Nordisk has been studying GLP-1 since 1986. Every weight-"
            "loss medicine in the category descends from that work."
        ),
        cta_label="See the science",
        image_prompt=(
            "A close-up photograph of an aged scientific journal page on a "
            "weathered wooden lab bench, the page dog-eared and slightly "
            "yellowed, the lighting warm and low, a single deep navy ink "
            "fountain pen resting across the page diagonally, visible 35mm "
            "film grain over the entire image, the composition simple and "
            "almost still-life, no human presence, abundant cream paper "
            "negative space around the central object."
        ),
        composition_notes=(
            "Pen and journal sit lower-center. Top third is empty paper "
            "with grain — perfect for headline overlay. Bottom fifth is "
            "the wooden bench surface — calm enough for CTA + logo."
        ),
        palette_words="aged paper cream, warm wood brown, deep navy ink, soft tungsten light",
        palette_hexes=["#F5EFE0", "#3A3024", "#0033A0"],
        trend_slugs=["grain_and_tactile", "ai_assisted_human_curated"],
    ),
    AdIdea(
        id="class_that_started_class_03_identity_callout",
        concept_id="class_that_started_class",
        angle="identity_callout",
        headline="For people who read the studies.",
        primary_text_first_line=(
            "If you research the medicine before you take it, you'll want "
            "to know which one started the category."
        ),
        cta_label="Read the trial data",
        image_prompt=(
            "A single open hardcover book photographed straight down on a "
            "dark wooden surface, the book filled with technical diagrams "
            "and dense paragraphs of text rendered as abstract gray lines "
            "(no readable words, no rendered letters), a vintage anatomical "
            "sketch of an internal organ visible on one page, the entire "
            "image overlaid with subtle paper grain and the soft warm "
            "shadow of a desk lamp falling from the upper right."
        ),
        composition_notes=(
            "Book occupies central two-thirds of the frame. Top sixth and "
            "bottom fifth are dark wood surface — quiet zones for overlay."
        ),
        palette_words="dark cocoa wood, warm bone paper, sepia shadow, tungsten highlight",
        palette_hexes=["#2C1F12", "#E8DFD0", "#0033A0"],
        trend_slugs=["grain_and_tactile", "naive_handdrawn_mixed"],
    ),
    AdIdea(
        id="class_that_started_class_04_demonstration",
        concept_id="class_that_started_class",
        angle="demonstration",
        headline="One molecule. The whole category.",
        primary_text_first_line=(
            "This is what every GLP-1 weight-loss medicine on the market "
            "is built around."
        ),
        cta_label="Learn the lineage",
        image_prompt=(
            "A single editorial photograph of an architectural blueprint "
            "schematic of a complex molecule, drawn in white precise lines "
            "on a deep ink-blue paper background, the schematic centered "
            "and surrounded by generous quiet space, the texture of the "
            "blueprint paper visible with soft fold lines and a hint of "
            "paper grain, no human presence, no other elements."
        ),
        composition_notes=(
            "Schematic centered. Top sixth is empty deep blue paper for "
            "headline. Bottom fifth is empty deep blue paper for CTA."
        ),
        palette_words="deep blueprint navy, crisp architectural white, very soft paper grain",
        palette_hexes=["#0A1F4A", "#F5EFE0", "#FF9E1B"],
        trend_slugs=["retro_futurism", "hyper_bold_typography"],
    ),

    # ── Concept 2: Inside the Body ───────────────────────────────────────────
    AdIdea(
        id="inside_the_body_01_hook",
        concept_id="inside_the_body",
        angle="hook",
        headline="Hunger lives here.",
        primary_text_first_line=(
            "Your body has a structure that decides how hungry you feel. "
            "We have a medicine that talks to it."
        ),
        cta_label="See how it works",
        image_prompt=(
            "A single anatomical illustration of a human brain stem in "
            "cross-section, drawn in the style of a 1970s medical textbook "
            "with confident hand-inked lines on a warm bone-colored paper, "
            "a small precise area at the base subtly highlighted in deep "
            "navy ink as the visual focal point, the entire image has "
            "warm photochemical grain, a single thin hand-drawn arrow "
            "pointing at the highlighted area, no labels, no text."
        ),
        composition_notes=(
            "Brain stem illustration centered. Top sixth and bottom fifth "
            "are quiet bone-paper background for overlay text and CTA."
        ),
        palette_words="warm bone paper, deep ink black, a single drop of navy at the focal point",
        palette_hexes=["#E8DFD0", "#1A1A1A", "#0033A0"],
        trend_slugs=["naive_handdrawn_mixed", "retro_futurism"],
    ),
    AdIdea(
        id="inside_the_body_02_proof_point",
        concept_id="inside_the_body",
        angle="proof_point",
        headline="Biology, not willpower.",
        primary_text_first_line=(
            "Obesity is a disease of biology — and the science says so. "
            "Here is the receptor we work on."
        ),
        cta_label="Read the mechanism",
        image_prompt=(
            "A close-up cross-section illustration of a single cell membrane "
            "with a receptor protein embedded in it, drawn in the warm "
            "naive linework of a vintage biology workbook, the membrane "
            "in soft sepia tones, the receptor in deep navy ink, surrounded "
            "by abundant warm paper space, slightly grainy, as if "
            "photocopied from an old textbook."
        ),
        composition_notes=(
            "Receptor close-up sits center-left. Right third and top sixth "
            "are quiet bone paper for overlay. Bottom fifth is warm paper "
            "field for CTA."
        ),
        palette_words="warm bone paper, sepia ink linework, single deep navy accent",
        palette_hexes=["#F2EBDC", "#3A3024", "#0033A0"],
        trend_slugs=["naive_handdrawn_mixed", "grain_and_tactile"],
    ),
    AdIdea(
        id="inside_the_body_03_identity_callout",
        concept_id="inside_the_body",
        angle="identity_callout",
        headline="For people who want to understand.",
        primary_text_first_line=(
            "If you want the medicine, you should also want the biology. "
            "Here it is."
        ),
        cta_label="See the explainer",
        image_prompt=(
            "A vintage anatomical drawing of a stylized human silhouette "
            "in profile, rendered in confident hand-inked black lines on "
            "warm cream paper, the figure simple and dignified, with a "
            "small subtle highlight in deep navy at the location where "
            "the brain stem would be, surrounded by generous empty paper "
            "space, soft photochemical grain across the entire image, no "
            "facial features rendered in detail."
        ),
        composition_notes=(
            "Silhouette occupies center-left. Right third and top/bottom "
            "are empty cream paper — perfect for overlay copy."
        ),
        palette_words="warm cream paper, deep ink black, a single navy accent, soft grain",
        palette_hexes=["#F5EFE0", "#1A1A1A", "#0033A0"],
        trend_slugs=["naive_handdrawn_mixed", "retro_futurism"],
    ),
    AdIdea(
        id="inside_the_body_04_demonstration",
        concept_id="inside_the_body",
        angle="demonstration",
        headline="The map, not the metaphor.",
        primary_text_first_line=(
            "This is the actual pathway. We work here."
        ),
        cta_label="Talk to your doctor",
        image_prompt=(
            "A single hand-drawn pathway diagram of a hormonal signaling "
            "cascade, drawn as a series of small connected ink shapes "
            "linked by flowing curved lines in the style of a teaching "
            "diagram, on a warm bone-colored paper background, the entire "
            "composition off-axis and slightly asymmetric like a doodle "
            "in a notebook margin, soft grain over the whole image, one "
            "node in the cascade subtly accented in deep navy ink."
        ),
        composition_notes=(
            "Diagram lives center-right. Left third and top/bottom are "
            "quiet paper for overlay. Diagram does not touch any edge."
        ),
        palette_words="warm bone paper, hand-drawn ink, single navy accent on one node",
        palette_hexes=["#F2EBDC", "#1A1A1A", "#0033A0"],
        trend_slugs=["naive_handdrawn_mixed", "organic_freeform"],
    ),

    # ── Concept 3: The Maintenance ───────────────────────────────────────────
    AdIdea(
        id="the_maintenance_01_hook",
        concept_id="the_maintenance",
        angle="hook",
        headline="Year three.",
        primary_text_first_line=(
            "Most weight-loss stories end at the loss. Ours starts there."
        ),
        cta_label="Talk to your doctor",
        image_prompt=(
            "A still-life photograph of a single weekly pill organizer on "
            "a worn wooden kitchen counter, the organizer slightly used "
            "and lived-in, soft afternoon light from a window falling at "
            "an angle from the upper-left, visible film grain across the "
            "entire image, a small folded paper calendar partially "
            "visible behind it, no people, no text, no logos, the mood "
            "is patient, domestic, and quietly hopeful."
        ),
        composition_notes=(
            "Pill organizer is center-bottom. Top half is the wooden wall "
            "and ambient light — perfect quiet zone for headline overlay. "
            "Very bottom strip is wood counter — calm enough for CTA."
        ),
        palette_words="warm afternoon wood, soft cream window light, faded paper, gentle navy for the calendar",
        palette_hexes=["#3A3024", "#F4E8CE", "#0033A0"],
        trend_slugs=["grain_and_tactile", "ai_assisted_human_curated"],
    ),
    AdIdea(
        id="the_maintenance_02_proof_point",
        concept_id="the_maintenance",
        angle="proof_point",
        headline="The medicine for the second chapter.",
        primary_text_first_line=(
            "Obesity is a chronic disease. Treatment doesn't end after "
            "the first month — it starts then."
        ),
        cta_label="Find a long-term plan",
        image_prompt=(
            "An overhead photograph of a small cluster of three blister "
            "packs of medicine arranged on a soft cream linen surface, "
            "each blister pack stamped with a different month, the linen "
            "showing the soft texture of natural fibers, soft daylight "
            "from above, slight 35mm grain, no labels readable, no "
            "branding visible, the composition calm and intentional like "
            "a design magazine still-life."
        ),
        composition_notes=(
            "Blister packs arranged in lower-center. Top half of frame is "
            "empty linen for headline. Bottom strip is empty linen for CTA."
        ),
        palette_words="warm linen cream, faded clay accents, soft ambient daylight",
        palette_hexes=["#F4E8CE", "#C4A581", "#0033A0"],
        trend_slugs=["grain_and_tactile", "organic_freeform"],
    ),
    AdIdea(
        id="the_maintenance_03_identity_callout",
        concept_id="the_maintenance",
        angle="identity_callout",
        headline="For people who stay.",
        primary_text_first_line=(
            "We made this brand for the year-three patient, not the "
            "first-month one."
        ),
        cta_label="Talk to your doctor",
        image_prompt=(
            "A photograph of a worn paper wall calendar pinned to a soft "
            "cream wall, several days marked with small hand-drawn ink "
            "circles in a quiet rhythm, the calendar slightly creased and "
            "lived-in, warm afternoon light from the side, soft grain "
            "across the image, no people, no readable text on the "
            "calendar (the days are abstract numbers), no logos."
        ),
        composition_notes=(
            "Calendar fills the center half. Top sixth and bottom fifth "
            "are empty cream wall — quiet zones for overlay."
        ),
        palette_words="cream paper wall, faded brown ink, soft afternoon warmth",
        palette_hexes=["#F5EFE0", "#3A3024", "#0033A0"],
        trend_slugs=["grain_and_tactile", "ai_assisted_human_curated"],
    ),
    AdIdea(
        id="the_maintenance_04_demonstration",
        concept_id="the_maintenance",
        angle="demonstration",
        headline="The dose that doesn't end.",
        primary_text_first_line=(
            "A weekly routine, photographed in year three."
        ),
        cta_label="Start the conversation",
        image_prompt=(
            "A still-life photograph of a single Wegovy-style injection "
            "pen (generic, no branding, no labels) lying horizontally on "
            "a soft cream tablecloth next to a small porcelain dish "
            "holding a folded napkin, soft warm window light from the "
            "left, gentle film grain, the composition spare and "
            "domestic, no people, no rendered text on the pen."
        ),
        composition_notes=(
            "Pen and dish in lower-center. Top half is empty tablecloth — "
            "headline zone. Bottom strip is tablecloth — CTA zone."
        ),
        palette_words="cream tablecloth, soft porcelain white, warm tungsten window light",
        palette_hexes=["#F4E8CE", "#FFFFFF", "#3A3024"],
        trend_slugs=["grain_and_tactile", "ai_assisted_human_curated"],
    ),

    # ── Concept 4: Quiet Authority ───────────────────────────────────────────
    AdIdea(
        id="quiet_authority_01_hook",
        concept_id="quiet_authority",
        angle="hook",
        headline="Now we have something.",
        primary_text_first_line=(
            "For adults with cardiovascular risk, there is finally a "
            "medicine that does both."
        ),
        cta_label="Talk to your doctor",
        image_prompt=(
            "A pure white frame, almost completely empty, with a single "
            "small black ink dot positioned in the lower-right third of "
            "the composition, the dot has visible photochemical grain "
            "around its edges as if printed on newspaper, the rest of "
            "the frame is uncluttered white space with the soft texture "
            "of fine paper, no other elements, no figures, no objects."
        ),
        composition_notes=(
            "The single dot is the ONLY visual element. Top sixth and "
            "bottom fifth are empty white — overlay headline goes top, "
            "CTA + logo goes bottom. Pure negative space everywhere else."
        ),
        palette_words="pure white paper field, single deep black ink mark, very soft grain",
        palette_hexes=["#FFFFFF", "#000000", "#0033A0"],
        trend_slugs=["organic_freeform", "grain_and_tactile"],
    ),
    AdIdea(
        id="quiet_authority_02_proof_point",
        concept_id="quiet_authority",
        angle="proof_point",
        headline="Heart attack. Stroke. Now we have something.",
        primary_text_first_line=(
            "Approved for adults with established heart disease."
        ),
        cta_label="See the indication",
        image_prompt=(
            "An almost entirely empty white field, with a single thin "
            "horizontal black line drawn slightly off-center toward the "
            "lower portion of the frame, the line has the soft uneven "
            "edge of hand-pulled ink, the rest of the frame is uncluttered "
            "white paper with the texture of fine cotton stock, no "
            "objects, no figures, no decorative elements."
        ),
        composition_notes=(
            "The single line is the only mark. Empty white above for "
            "headline, empty white below for CTA + logo."
        ),
        palette_words="white cotton paper, deep ink black, faint shadow",
        palette_hexes=["#FFFFFF", "#000000", "#0033A0"],
        trend_slugs=["organic_freeform", "hyper_bold_typography"],
    ),
    AdIdea(
        id="quiet_authority_03_identity_callout",
        concept_id="quiet_authority",
        angle="identity_callout",
        headline="For people who want a calm doctor.",
        primary_text_first_line=(
            "Some medicines shout. This one explains."
        ),
        cta_label="Find a doctor",
        image_prompt=(
            "A single small object resting in the center of an otherwise "
            "completely empty white frame, the object is a folded sheet "
            "of crisp white paper, photographed from slightly above with "
            "neutral overhead light, the paper casts a soft shadow on "
            "the cream surface beneath it, fine grain across the image, "
            "no other elements, no rendered text or markings on the paper."
        ),
        composition_notes=(
            "Folded paper centered. Top sixth and bottom fifth are empty "
            "for overlay copy. Composition is almost minimalist still life."
        ),
        palette_words="white cotton paper, soft warm cream surface beneath, faint gray shadow",
        palette_hexes=["#FFFFFF", "#F5EFE0", "#9A9A9A"],
        trend_slugs=["organic_freeform", "grain_and_tactile"],
    ),
    AdIdea(
        id="quiet_authority_04_demonstration",
        concept_id="quiet_authority",
        angle="demonstration",
        headline="One sentence is enough.",
        primary_text_first_line=(
            "We don't have a slogan. We have a medicine."
        ),
        cta_label="Read the indication",
        image_prompt=(
            "A pure white field with a single small black dot positioned "
            "exactly in the geometric center of the frame, the dot has "
            "the soft uneven edge of a hand-stamped ink mark, the rest "
            "of the frame is empty white paper with very subtle texture, "
            "no other elements at all, no objects, no figures, no "
            "decorative marks."
        ),
        composition_notes=(
            "Dead-center single dot. Maximum negative space top and "
            "bottom for overlay copy. The minimalism IS the brand."
        ),
        palette_words="pure white, deep ink black, single navy accent reserved for the headline overlay",
        palette_hexes=["#FFFFFF", "#000000", "#0033A0"],
        trend_slugs=["organic_freeform"],
    ),

    # ── Concept 5: Two Bodies ────────────────────────────────────────────────
    AdIdea(
        id="two_bodies_01_hook",
        concept_id="two_bodies",
        angle="hook",
        headline="One molecule. Two ways to live with it.",
        primary_text_first_line=(
            "Same medicine. Your form."
        ),
        cta_label="Choose your form",
        image_prompt=(
            "A vertical diptych composition: the left half of the frame "
            "contains a single weekly injection pen photographed straight "
            "on, the right half contains a single small daily pill "
            "photographed straight on, both objects centered in their "
            "halves, separated by a thin clean vertical line down the "
            "exact middle of the frame, both objects shot with identical "
            "neutral lighting on a soft duotone background of bright "
            "blue on the left and deep navy on the right, no labels on "
            "either object, no rendered text, no logos."
        ),
        composition_notes=(
            "Vertical diptych. Pen in upper-center of left half, pill in "
            "upper-center of right half. Top sixth is the duotone field "
            "(quiet) for headline. Bottom fifth is the duotone field for CTA."
        ),
        palette_words="bright LED brand blue on left, deep navy on right, soft white object highlights",
        palette_hexes=["#00A0DF", "#0033A0", "#FFFFFF"],
        trend_slugs=["vibrant_high_contrast", "3d_motion_signal"],
    ),
    AdIdea(
        id="two_bodies_02_proof_point",
        concept_id="two_bodies",
        angle="proof_point",
        headline="The only semaglutide in both forms.",
        primary_text_first_line=(
            "FDA-approved as a weekly pen and a daily pill — same molecule, "
            "your choice."
        ),
        cta_label="See both forms",
        image_prompt=(
            "Two identical white spheres of light photographed against a "
            "split background, the left half a vivid bright brand blue, "
            "the right half a deep navy blue, the two spheres positioned "
            "symmetrically with a thin vertical white line between them "
            "marking the exact center of the frame, soft 3D depth on the "
            "spheres, abundant negative space above and below, no other "
            "elements, no text, no logos."
        ),
        composition_notes=(
            "Two spheres center-stage. Top sixth and bottom fifth of "
            "frame are pure duotone for headline + CTA overlay."
        ),
        palette_words="bright LED blue, deep navy, soft white sphere highlight",
        palette_hexes=["#00A0DF", "#0033A0", "#FFFFFF"],
        trend_slugs=["vibrant_high_contrast", "3d_motion_signal"],
    ),
    AdIdea(
        id="two_bodies_03_identity_callout",
        concept_id="two_bodies",
        angle="identity_callout",
        headline="For pen people. For pill people.",
        primary_text_first_line=(
            "Some patients want a weekly routine. Some want a daily one. "
            "Same medicine for both."
        ),
        cta_label="See your option",
        image_prompt=(
            "A symmetric vertical split composition: the left half is a "
            "vivid bright blue field, the right half is a deep navy blue "
            "field, separated by a thin clean vertical line down the "
            "exact middle, on the left half a single small white circle "
            "in the upper center, on the right half a single small white "
            "rectangle in the upper center, perfectly aligned across the "
            "centerline, no other elements, no rendered text, no labels, "
            "no logos."
        ),
        composition_notes=(
            "Two abstract symbols in mirrored positions. Top sixth and "
            "bottom fifth of each half are clean color fields for overlay."
        ),
        palette_words="vivid LED blue, deep navy, single bright white symbols",
        palette_hexes=["#00A0DF", "#0033A0", "#FFFFFF"],
        trend_slugs=["vibrant_high_contrast", "hyper_bold_typography"],
    ),
    AdIdea(
        id="two_bodies_04_demonstration",
        concept_id="two_bodies",
        angle="demonstration",
        headline="Same molecule. Two doses. Your call.",
        primary_text_first_line=(
            "Switch between forms over time as your routine changes."
        ),
        cta_label="See the comparison",
        image_prompt=(
            "A close-up overhead photograph of two identical small glass "
            "vials side by side on a clean white surface, separated by a "
            "thin vertical shadow line, the left vial slightly larger "
            "than the right, both objects shot with crisp neutral light, "
            "the left vial has a soft bright blue tint, the right vial "
            "has a deep navy tint, abundant white surface around them, "
            "no labels, no rendered text, no logos."
        ),
        composition_notes=(
            "Vials center-frame. Top sixth and bottom fifth are clean "
            "white surface for overlay copy."
        ),
        palette_words="clean white surface, bright LED blue glass, deep navy glass, single amber accent",
        palette_hexes=["#FFFFFF", "#00A0DF", "#0033A0"],
        trend_slugs=["vibrant_high_contrast", "3d_motion_signal"],
    ),
]


# ─── 7. Visual prompts (deterministic builder) ───────────────────────────────

def _ideas_for_concept(concept_id: str) -> list[AdIdea]:
    return [i for i in WEGOVY_AD_IDEAS if i.concept_id == concept_id]


visual_prompts = build_visual_prompt_package(
    business_dna,
    [(c, _ideas_for_concept(c.id)) for c in concepts],
)


# ─── 7. Assemble + persist ───────────────────────────────────────────────────

dashboard = DashboardSummary(
    client=client,
    business_dna=business_dna,
    concept_pillars=concept_pillars,
    concepts=concepts,
    visual_prompts=visual_prompts,
    interrogation=None,  # gate skipped for demo (no API key)
)


def main() -> None:
    out_dir = Path(__file__).resolve().parents[1] / "data" / "wegovy"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "dashboard.json"

    js = dashboard.model_dump_json(indent=2)
    out_path.write_text(js, encoding="utf-8")

    print(f"wrote {len(js):,} chars -> {out_path}")
    print(f"  brand        : {dashboard.client.brand_name}")
    print(f"  concepts     : {len(dashboard.concepts)}")
    total_ideas = sum(len(s.ideas) for s in dashboard.visual_prompts.ad_sets)
    print(f"  ad sets      : {len(dashboard.visual_prompts.ad_sets)}")
    print(f"  ad ideas     : {total_ideas} ({total_ideas // len(dashboard.concepts)} per concept)")
    print(f"  classified   : {len(brand_analysis.classified_signals)} signals")
    print(f"  format       : {dashboard.visual_prompts.format_default}")
    print(f"  platform     : {dashboard.visual_prompts.target_platform}")


if __name__ == "__main__":
    main()
