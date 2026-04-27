# DNA Brand — Concept Architect System

## What This System Does

The **DNA Brand system** is an automated pipeline that transforms a brand's website into a complete strategic positioning and concept framework. It answers: *"What is this brand really about? What unique positions can it own?"*

**Input:** Brand name + website URL  
**Output:** Complete DNA + 5 mutually exclusive strategic concepts (schema v1.1)  
**Time:** ~2-3 minutes per brand

---

## The Pipeline in 3 Stages

### Stage 1: Website Scraping → Brand Perception Research
**What happens:**
- System scrapes the brand's website for visual design, copy, messaging, customer testimonials
- Uses web signals (colors, typography, imagery, tone, positioning) to understand how the brand presents itself
- Condenses this into perception data: feelings, sentiment, positioning, audience, promises

**Output:** `perception.json`
```json
{
  "brand_name": "RemNote",
  "primary_feelings": ["efficient", "empowered", "smart"],
  "sentiment_score": 1.0,
  "positioning": "All-in-one AI-powered study tool...",
  "tone_of_voice": "Confident yet accessible...",
  "perceived_audience": "Serious students...",
  "key_promises": ["Study less and remember more", ...],
  "brand_personality": "Super-organized friend who discovered a study hack..."
}
```

---

### Stage 2: Perception → Business DNA
**What happens:**
- LLM analyzes perception data to extract the core DNA of the brand
- DNA captures: Purpose, Personality, Positioning, Promise, Unique Space, Essence
- Everything is rooted in the perception data—no invented facts

**Output:** `dna` object in strategy.json
```json
{
  "purpose": "Why does this brand exist?",
  "personality": ["ambitious", "efficiency-obsessed", "supportive"],
  "positioning": "What unique market position does it own?",
  "promise": "What is the core promise to customers?",
  "unique_space": "What territory can only this brand own?",
  "essence": "The AI-powered knowledge system that gives ambitious learners the superpower of permanent memory..."
}
```

---

### Stage 3: DNA → 5 Strategic Concepts
**What happens:**
- LLM generates 5 **mutually exclusive** strategic directions (C01-C05)
- Each concept breaks 2+ industry norms and owns uncontested territory
- Each includes:
  - **Visual World**: Archetype, colors, typography, imagery, mood
  - **Verbal World**: Tone, language to use/avoid, example copy
  - **Copy Constraints**: Headline word limits, banned patterns, required tone
  - **How It Challenges Norms**: What makes it bold

**Output:** `concepts` array in strategy.json
```json
{
  "id": "C01",
  "title": "The Forgetting Killer",
  "tagline": "Every fact you learn stays learned. Forever.",
  "strategic_insight": "Students fear forgetting, not studying...",
  "core_promise": "Your brain becomes a vault...",
  "visual_world": {
    "archetype": "The Fortress",
    "colors": ["obsidian black", "vault gold"],
    "typography": "Heavy, industrial sans-serifs...",
    "imagery": "Knowledge locked in, sealed, reinforced...",
    "mood": "Monumental, certain, unshakeable"
  },
  "verbal_world": {
    "tone": "Declarative and absolute",
    "use": ["lock in", "permanent", "retention rate"],
    "avoid": ["remember better", "improve memory"],
    "example": "You read it once. Our algorithm handles the rest. Retention rate: 95%..."
  },
  "copy_constraints": {
    "max_headline_words": 6,
    "banned_patterns": ["helps you", "makes it easy"],
    "required_tone": "absolute certainty"
  },
  "how_it_challenges_norms": "Rejects industry focus on 'learning faster' in favor of 'never forgetting'..."
}
```

---

## How to Use It

### Option 1: Direct Function Call (Python)
```python
from app.analyzer.dna_developer import develop_dna_and_concepts
from app.simple_pipeline import run_simple_pipeline

# Step 1: Get perception
result = run_simple_pipeline(
    brand_name="Console",
    website="https://www.console.com/"
)

# Step 2: Develop DNA + Concepts
dna, concepts = develop_dna_and_concepts(
    brand_name=result.brand_name,
    perception_data=result.perception
)
```

### Option 2: FastAPI Endpoints
Start the service:
```bash
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

**Endpoint 1: Brand Perception Analysis**
```bash
POST /perception/analyze
{
  "brand_name": "Perplexity",
  "website": "https://www.perplexity.ai/"
}
```
Returns: Perception data only

**Endpoint 2: Full Strategy Development**
```bash
POST /strategy/develop
{
  "brand_name": "Perplexity",
  "website": "https://www.perplexity.ai/"
}
```
Returns: Complete DNA + 5 Concepts (schema v1.1)

---

## What You Get: schema_version 1.1

Every output follows this structure:
```json
{
  "schema_version": "1.1",
  "brand_name": "Brand Name",
  "website": "https://...",
  "dna": { /* DNA object */ },
  "concepts": [ /* 5 concept objects */ ],
  "perception": { /* Optional: perception data */ }
}
```

---

## Real Examples

### RemNote
**DNA Essence:** "The AI-powered knowledge system that gives ambitious learners the superpower of permanent memory and higher grades with half the effort."

**5 Concepts:**
- C01: **The Forgetting Killer** — Permanence through algorithms
- C02: **The Academic Arms Race** — Competitive advantage positioning
- C03: **The Compound Knowledge Machine** — Lifetime knowledge accumulation
- C04: **The Anti-Grind Movement** — Efficiency rebellion against hustle culture
- C05: **The Second Brain Institute** — Cognitive enhancement/transhumanist positioning

### Perplexity
**DNA Essence:** "The no-nonsense expert who gives you the real answer, not ten blue links."

**5 Concepts:**
- C01: **The Citation Engine** — Every answer comes with receipts (transparency)
- C02: **The Anti-Search Search** — We killed the results page
- C03: **The Real-Time Oracle** — What's true right now (live data)
- C04: **The Question Dignifier** — Your question deserved better than ten blue links
- C05: **The Hallucination-Free Zone** — AI that admits what it doesn't know

### Console
**DNA Essence:** "The sharp, pragmatic disruptor that frees IT teams from repetitive work by auto-resolving support requests with AI that deploys fast and delivers receipts."

**5 Concepts:**
- C01: **The Anti-Enterprise** — Enterprise results, startup speed, zero BS
- C02: **The Liberation Movement** — Return IT teams to strategic work
- C03: **The Proof Machine** — Customer outcomes as the only marketing metric
- C04: **The Inbox Zero Guarantee** — Promise of complete ticket resolution
- C05: **The Evidence Board** — Customer success stories and data as proof

---

## Key Design Principles

### 1. Machine-Driven (Not Manual)
The system generates everything from the perception data. You don't write the concepts—the machine does.

### 2. Mutually Exclusive Concepts
Each of the 5 concepts is incompatible with the others. You can't execute two concepts simultaneously. They represent real strategic choices, not variations on a theme.

### 3. Rooted in Research
Every claim traces back to the website scrape and perception data. No invented facts.

### 4. Norm-Breaking Required
Each concept explicitly breaks 2+ industry norms. This ensures they're bold and differentiated, not generic.

### 5. Uncontested Territory
Each concept owns a unique strategic space. No overlaps.

---

## Files & Data Structure

```
python_service/
├── app/
│   ├── main.py                      # FastAPI endpoints
│   ├── simple_pipeline.py           # Scrape → Perception
│   └── analyzer/
│       ├── brand_perception.py      # Perception extraction
│       └── dna_developer.py         # DNA + Concepts generation
├── data/
│   ├── remnote/
│   │   ├── perception.json          # Scrape signals → perception
│   │   └── strategy.json            # Final DNA + Concepts output
│   ├── perplexity/
│   │   ├── perception.json
│   │   └── strategy.json
│   ├── console/
│   │   ├── perception.json
│   │   └── strategy.json
│   └── [brand_name]/
│       ├── perception.json
│       └── strategy.json
└── .env                             # ANTHROPIC_API_KEY
```

---

## Workflow for New Brand

1. **Get brand info**  
   Name: ___________  
   Website: ___________

2. **Run the pipeline**  
   ```python
   python << 'EOF'
   from app.simple_pipeline import run_simple_pipeline
   from app.analyzer.dna_developer import develop_dna_and_concepts
   import json
   
   result = run_simple_pipeline(brand_name="Brand", website="https://...")
   dna, concepts = develop_dna_and_concepts(result.brand_name, result.perception)
   
   with open(f"data/{brand_name.lower()}/strategy.json", "w") as f:
       json.dump({
           "schema_version": "1.1",
           "brand_name": result.brand_name,
           "website": result.website,
           "dna": dna,
           "concepts": concepts
       }, f, indent=2)
   EOF
   ```

3. **Output**: `data/[brand_name]/strategy.json` with complete DNA + 5 concepts

---

## Troubleshooting

**Error: Rate limiting / API timeout**
- Check `.env` has valid `ANTHROPIC_API_KEY`
- Try again in 30 seconds (API has built-in rate limiting)

**Error: Website scrape failed**
- Website may block scrapers or be down
- Check website URL is valid and accessible

**Error: DNA/Concepts seem generic**
- This means the website perception data wasn't specific enough
- Check the brand's website has clear, distinctive messaging
- Consider manual perception input if auto-scrape doesn't capture nuance

---

## Next Steps

Once you have DNA + Concepts, you can:
- **Generate ads & image prompts** from each concept (separate system)
- **Brief creative teams** on concept positioning
- **Build campaign frameworks** around each concept
- **Test concepts with audience** to see which resonates
- **Choose one concept** to execute, or **test multiple** in parallel

