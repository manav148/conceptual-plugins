"""Parser for the 100-Question Self-Interrogation Protocol.

Loads the canonical markdown spec at
`DOCS/# Agent Self-Interrogation Protocol.md` and returns 100 typed
Question objects, grouped into the 10 categories defined in the brief.

The parser is strict: it expects exactly 100 questions across 10 categories.
If the source markdown changes shape, parsing fails loudly rather than
silently producing a wrong count — this protocol is the QC gate, not a
nice-to-have.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

# Canonical location of the protocol markdown.
DEFAULT_PROTOCOL_PATH = (
    Path(__file__).resolve().parents[3]
    / "DOCS"
    / "# Agent Self-Interrogation Protocol.md"
)

EXPECTED_TOTAL = 100
EXPECTED_CATEGORIES = 10

# Matches "## Category 3: Competitor Analysis & Red Ocean Mapping (21–30)"
# Accepts both en-dash (–) and ASCII hyphen (-) in the range.
_CATEGORY_RE = re.compile(
    r"^##\s+Category\s+(\d+):\s+(.+?)\s+\((\d+)[–-](\d+)\)\s*$"
)
# Matches "1. Have I fully internalized..." (allows optional trailing spaces)
_QUESTION_RE = re.compile(r"^(\d+)\.\s+(.+?)\s*$")


@dataclass(frozen=True)
class Question:
    id: int                # 1..100
    category_id: int       # 1..10
    category_name: str     # e.g. "Business DNA Alignment & Validation"
    text: str

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "category_id": self.category_id,
            "category_name": self.category_name,
            "text": self.text,
        }


def load_protocol(path: Path | str | None = None) -> list[Question]:
    """Parse the protocol markdown into 100 Question objects.

    Raises:
        FileNotFoundError: if the source file is missing.
        ValueError: if the parsed structure does not contain exactly
            10 categories and 100 questions.
    """
    src = Path(path) if path else DEFAULT_PROTOCOL_PATH
    if not src.exists():
        raise FileNotFoundError(f"Protocol file not found at {src}")

    questions: list[Question] = []
    current_cat_id: int | None = None
    current_cat_name: str | None = None

    for raw_line in src.read_text(encoding="utf-8").splitlines():
        line = raw_line.rstrip()

        cat_match = _CATEGORY_RE.match(line)
        if cat_match:
            current_cat_id = int(cat_match.group(1))
            current_cat_name = cat_match.group(2).strip()
            continue

        # Skip lines until we are inside a category.
        if current_cat_id is None:
            continue

        q_match = _QUESTION_RE.match(line)
        if not q_match:
            continue

        q_id = int(q_match.group(1))
        text = q_match.group(2).strip()
        questions.append(
            Question(
                id=q_id,
                category_id=current_cat_id,
                category_name=current_cat_name or "",
                text=text,
            )
        )

    # ── Strict validation ───────────────────────────────────────────────
    if len(questions) != EXPECTED_TOTAL:
        raise ValueError(
            f"Expected {EXPECTED_TOTAL} questions, parsed {len(questions)}. "
            "Protocol markdown shape may have changed."
        )

    distinct_cats = {q.category_id for q in questions}
    if len(distinct_cats) != EXPECTED_CATEGORIES:
        raise ValueError(
            f"Expected {EXPECTED_CATEGORIES} categories, parsed "
            f"{len(distinct_cats)}: {sorted(distinct_cats)}"
        )

    ids = [q.id for q in questions]
    if ids != list(range(1, EXPECTED_TOTAL + 1)):
        raise ValueError(
            "Question IDs are not contiguous 1..100 in document order. "
            f"First gap or duplicate near: {_first_anomaly(ids)}"
        )

    return questions


def _first_anomaly(ids: list[int]) -> int:
    for i, n in enumerate(ids, start=1):
        if i != n:
            return n
    return -1


def by_category(questions: list[Question]) -> dict[int, list[Question]]:
    """Group questions by their category id (1..10)."""
    out: dict[int, list[Question]] = {}
    for q in questions:
        out.setdefault(q.category_id, []).append(q)
    return out
