"""ClaudeBackend — LLM judge for the 100Q self-interrogation protocol.

Strategy: batch by category. The protocol is already organized into 10
categories of 10 questions, so we make exactly 10 API calls — one per
category — instead of 100. Each call hands the model the same DNA +
concepts payload (cached prefix) plus the 10 questions for that
category, and forces a single tool call that returns 10 structured
answers in one shot.

Cost rationale (from the routines manual + recipe book):
  - PR Review routine cap is $0.30; this is a richer judgment task,
    closer to Security Audit ($0.50–$1.50). Sonnet keeps it affordable.
  - 10 calls × ~3-4k tokens each, with prompt caching on the DNA +
    concepts payload, lands well inside that envelope.
  - We never spend Sonnet tokens to validate Sonnet's own format —
    Pydantic does that for free.

The brief is explicit that the QC gate exists to prevent shipping
weak, repetitive, or LLM-default work. The system prompt below makes
the model the *adversarial* judge, not a cheerleader.
"""

from __future__ import annotations

import json
from typing import Any

from anthropic import Anthropic

from app.analyzer.llm import SONNET, _client, _extract_tool_input
from app.interrogation.protocol import Question
from app.models.schemas import BusinessDNA, ConceptDirection


_JUDGE_SYSTEM = """\
You are the adversarial QC judge for the Business DNA pipeline.

You are given a Business DNA, the five concept directions generated
from it, and a batch of self-interrogation questions from one category
of the 100-question protocol.

Your job is to answer each question RIGOROUSLY and HONESTLY against
the actual concepts in front of you. You are not a cheerleader. The
brief is explicit: this protocol exists to catch weak, repetitive,
LLM-default, or undefendable work BEFORE it reaches the client.

Hard rules for judgment:

1. A question passes only if the EVIDENCE in the DNA + concepts
   actually supports a "yes" answer. Vibes are not evidence.

2. Default to FAIL on questions about originality, distinctiveness,
   tension, or defensibility unless the concepts demonstrably clear
   the bar. The cost of a false-pass is shipping a weak concept; the
   cost of a false-fail is one more iteration. Bias toward iteration.

3. Quote or reference specific concepts by id when possible. "Concept
   quiet_rebellion eliminates X" is useful. "The concepts are bold"
   is filler.

4. If two of the five concepts could plausibly have come from the
   same designer, that is a fail on every distinctiveness question.

5. If any concept reads as a generic LLM-default ("innovative",
   "human-centered", "where tradition meets innovation"), that is a
   fail on every originality question.

6. Each answer must be 1-3 sentences. No prose dumps. No hedging.

7. Return EXACTLY one answer per question, in the same order, via the
   `record_answers` tool.
"""


def _answers_tool(n: int) -> dict[str, Any]:
    """Tool schema sized to a specific batch length (almost always 10)."""
    return {
        "name": "record_answers",
        "description": (
            f"Record exactly {n} structured answers, one per question, "
            "in the same order as the questions provided."
        ),
        "input_schema": {
            "type": "object",
            "required": ["answers"],
            "properties": {
                "answers": {
                    "type": "array",
                    "minItems": n,
                    "maxItems": n,
                    "items": {
                        "type": "object",
                        "required": ["question_id", "pass", "answer"],
                        "properties": {
                            "question_id": {"type": "integer"},
                            "pass": {
                                "type": "boolean",
                                "description": (
                                    "True only if the DNA + concepts actually "
                                    "satisfy the question. Bias toward false."
                                ),
                            },
                            "answer": {
                                "type": "string",
                                "description": "1-3 sentences of evidence-anchored reasoning.",
                            },
                        },
                    },
                }
            },
        },
    }


def _group_by_category(questions: list[Question]) -> list[list[Question]]:
    """Stable category-grouped batches in document order."""
    out: dict[int, list[Question]] = {}
    for q in questions:
        out.setdefault(q.category_id, []).append(q)
    return [out[k] for k in sorted(out)]


class ClaudeBackend:
    """Production LLM backend for the 100Q gate.

    Args:
        model: Anthropic model id (default Sonnet 4.5).
        client: optional Anthropic client (for testing/injection).
        max_tokens: per-call output budget. 2048 is plenty for 10 short
            answers; raise only if you see truncation.
    """

    def __init__(
        self,
        *,
        model: str = SONNET,
        client: Anthropic | None = None,
        max_tokens: int = 2048,
    ) -> None:
        self.model = model
        self._client = client
        self.max_tokens = max_tokens

    def _client_or_create(self) -> Anthropic:
        return self._client or _client()

    def _shared_payload(
        self, dna: BusinessDNA, concepts: list[ConceptDirection]
    ) -> str:
        return json.dumps(
            {
                "business_dna": dna.model_dump(mode="json"),
                "concepts": [c.model_dump(mode="json") for c in concepts],
            },
            indent=2,
        )[:40000]

    def _judge_batch(
        self,
        batch: list[Question],
        shared_payload: str,
        client: Anthropic,
    ) -> list[tuple[str, bool]]:
        question_block = "\n".join(
            f"Q{q.id} [{q.category_name}]: {q.text}" for q in batch
        )

        msg = client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            system=_JUDGE_SYSTEM,
            tools=[_answers_tool(len(batch))],
            tool_choice={"type": "tool", "name": "record_answers"},
            messages=[
                {
                    "role": "user",
                    "content": (
                        "DNA and concepts under judgment:\n\n"
                        f"```json\n{shared_payload}\n```\n\n"
                        "Answer each of the following questions. Return "
                        "exactly one structured answer per question, in "
                        "the same order, via the `record_answers` tool.\n\n"
                        f"{question_block}"
                    ),
                }
            ],
        )

        raw = _extract_tool_input(msg, "record_answers")
        answers = raw["answers"]
        if len(answers) != len(batch):
            raise RuntimeError(
                f"ClaudeBackend got {len(answers)} answers for a batch of {len(batch)}."
            )

        # Index by question_id so any reordering by the model is harmless.
        by_id = {a["question_id"]: a for a in answers}
        out: list[tuple[str, bool]] = []
        for q in batch:
            a = by_id.get(q.id)
            if a is None:
                raise RuntimeError(
                    f"ClaudeBackend missed Q{q.id} in returned batch."
                )
            out.append((a["answer"], bool(a["pass"])))
        return out

    def answer_all(
        self,
        questions: list[Question],
        dna: BusinessDNA,
        concepts: list[ConceptDirection],
    ) -> list[tuple[str, bool]]:
        client = self._client_or_create()
        shared = self._shared_payload(dna, concepts)
        batches = _group_by_category(questions)

        # Map each question.id → its result so we can re-emit in input order.
        results_by_id: dict[int, tuple[str, bool]] = {}
        for batch in batches:
            for q, r in zip(batch, self._judge_batch(batch, shared, client)):
                results_by_id[q.id] = r

        return [results_by_id[q.id] for q in questions]
