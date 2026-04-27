# DNA Brand — Strategic Positioning Pipeline

An automated system that transforms a brand's website into a complete strategic positioning framework: Business DNA + 5 mutually exclusive strategic concepts.

**Input:** Brand name + website URL  
**Output:** Complete DNA + 5 strategic concepts (schema v1.1)  
**Time:** ~2-3 minutes per brand

## Quick Start

### Prerequisites
- Python 3.8+
- `ANTHROPIC_API_KEY` environment variable set

### Installation

```bash
# Clone the repo
git clone <repository-url>
cd python_service

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
echo "ANTHROPIC_API_KEY=your_key_here" > .env
```

### Usage

#### Option 1: Direct Python
```python
from app.simple_pipeline import run_simple_pipeline
from app.analyzer.dna_developer import develop_dna_and_concepts
import json

# Step 1: Get perception from website
result = run_simple_pipeline(
    brand_name="Console",
    website="https://www.console.com/"
)

# Step 2: Develop DNA + Concepts
dna, concepts = develop_dna_and_concepts(
    brand_name=result.brand_name,
    perception_data=result.perception
)

# Output
output = {
    "schema_version": "1.1",
    "brand_name": result.brand_name,
    "website": result.website,
    "dna": dna,
    "concepts": concepts
}
```

#### Option 2: FastAPI Server
```bash
# Start the server
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000

# POST /strategy/develop
# {
#   "brand_name": "Console",
#   "website": "https://www.console.com/"
# }
```

## Project Structure

```
.
├── app/
│   ├── main.py                      # FastAPI endpoints
│   ├── simple_pipeline.py           # Website scrape → perception
│   ├── analyzer/
│   │   ├── brand_perception.py      # LLM perception extraction
│   │   ├── dna_developer.py         # DNA + concepts generation
│   │   └── llm.py                   # Claude API client & utilities
│   ├── models/
│   │   └── schemas.py               # Pydantic data models
│   └── scrapers/
│       ├── website.py               # Website scraper
│       └── trends.py                # Trends scraper
├── data/
│   ├── [brand_name]/
│   │   ├── perception.json          # Perception research
│   │   └── strategy.json            # DNA + Concepts output
│   └── ...
├── .env                             # Environment variables
├── .gitignore
├── NOTION_GUIDE.md                  # Team documentation
└── requirements.txt
```

## The Pipeline: 3 Stages

### Stage 1: Website Scraping → Brand Perception
- Scrapes website for design, copy, messaging, testimonials
- Extracts perception data: feelings, sentiment, positioning, audience, promises
- Output: `perception.json`

### Stage 2: Perception → Business DNA
- Analyzes perception to extract core brand DNA
- Captures: Purpose, Personality, Positioning, Promise, Unique Space, Essence
- Output: `dna` object in `strategy.json`

### Stage 3: DNA → 5 Strategic Concepts
- Generates 5 mutually exclusive strategic directions (C01-C05)
- Each breaks 2+ industry norms and owns uncontested territory
- Each includes: visual world, verbal world, copy constraints, norm-breaking insights
- Output: `concepts` array in `strategy.json`

## Example Output

See `data/remnote/strategy.json`, `data/perplexity/strategy.json`, or `data/console/strategy.json` for complete examples.

**RemNote DNA Essence:**  
"The AI-powered knowledge system that gives ambitious learners the superpower of permanent memory and higher grades with half the effort."

**RemNote Concepts:**
- C01: The Forgetting Killer
- C02: The Academic Arms Race
- C03: The Compound Knowledge Machine
- C04: The Anti-Grind Movement
- C05: The Second Brain Institute

## Configuration

Create a `.env` file in the project root:
```
ANTHROPIC_API_KEY=sk-...
```

## API Reference

### POST /strategy/develop
Full pipeline: website scrape → perception → DNA → concepts

**Request:**
```json
{
  "brand_name": "string",
  "website": "https://..."
}
```

**Response:**
```json
{
  "schema_version": "1.1",
  "brand_name": "string",
  "website": "https://...",
  "dna": { /* DNA object */ },
  "concepts": [ /* 5 concept objects */ ],
  "perception": { /* perception data */ }
}
```

### POST /perception/analyze
Just the perception research stage

**Request:**
```json
{
  "brand_name": "string",
  "website": "https://..."
}
```

**Response:**
```json
{
  "brand_name": "string",
  "website": "https://...",
  "perception": { /* perception data */ },
  "scrape_status": 200
}
```

## Key Principles

- **Machine-Driven**: System generates everything from perception data, no manual work
- **Mutually Exclusive Concepts**: Each concept is incompatible with others (real strategic choices)
- **Research-Rooted**: Every claim traces back to website scrape data
- **Norm-Breaking**: Each concept explicitly breaks 2+ industry norms
- **Uncontested Territory**: Each concept owns unique strategic space

## Troubleshooting

**Rate Limiting**: API has built-in rate limits. Wait 30 seconds and retry.

**Scrape Failed**: Website may block scrapers. Check URL is valid and accessible.

**Generic Output**: Website perception wasn't specific enough. Check brand has clear, distinctive messaging.

## Documentation

See `NOTION_GUIDE.md` for comprehensive team documentation and examples.

## License

Proprietary — CONCEPTUAL HQ

## Author

Built by CONCEPTUAL HQ
