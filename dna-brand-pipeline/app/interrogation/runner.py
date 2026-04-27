"""Interrogation runner — executes the 100Q protocol against draft concepts.

Two backends:
  - StubBackend: deterministic, no LLM. Used for unit tests and to wire the
    pipeline end-to-end before the analyzer lands. Marks every question as
    pass with a placeholder answer; useful for shape testing only.
  - ClaudeBackend: real LLM judge. Filled in once the analyzer module is
    in place — kept as a thin Protocol so the pipeline never has to know
    which backend it is talking to.

The runner is responsible for the *gate*, not the *answers*: it produces
an InterrogationReport that the orchestrator uses to decide whether the
five concepts are allowed to ship.
"""

from __future__ import annotations

from typing import Protocol

from app.interrogation.protocol import Question, load_protocol
from app.models.schemas import (
    BusinessDNA,
    ConceptDirection,
    InterrogationAnswer,
    InterrogationReport,
)

# Categories that examine concept-level distinctiveness/originality.
# A failure in any of these is a hard block — the brief is explicit that
# we do not ship five variations of one idea, nor LLM-default territory.
HARD_GATE_CATEGORIES = {5, 6, 10}  # originality, distinctiveness, justification


class InterrogationBackend(Protocol):
    """Backend that answers a *batch* of protocol questions in one call.

    Batched (not per-question) so real LLM backends can group all 10
    questions in a category into a single API call — keeps the QC pass
    inside the routines manual's budget cap for this stage.
    """

    def answer_all(
        self,
        questions: list[Question],
        dna: BusinessDNA,
        concepts: list[ConceptDirection],
    ) -> list[tuple[str, bool]]: ...


class StubBackend:
    """Deterministic placeholder backend.

    Returns pass=True for every question with a templated answer.
    Use ONLY for plumbing tests — never for real concept validation.
    """

    def answer_all(
        self,
        questions: list[Question],
        dna: BusinessDNA,
        concepts: list[ConceptDirection],
    ) -> list[tuple[str, bool]]:
        return [
            (
                f"[stub] Q{q.id} acknowledged for {dna.brand_name} "
                f"with {len(concepts)} concepts.",
                True,
            )
            for q in questions
        ]


def run_interrogation(
    dna: BusinessDNA,
    concepts: list[ConceptDirection],
    *,
    backend: InterrogationBackend | None = None,
) -> InterrogationReport:
    """Execute the full 100Q protocol against a DNA + concept set.

    The runner enforces preconditions before answering anything:
      - Exactly 5 concepts must be supplied (the brief is explicit).
      - The DNA must have a non-empty uncontested_space.
    These are cheap, deterministic checks that catch wiring bugs early.
    """
    if len(concepts) != 5:
        raise ValueError(
            f"Interrogation requires exactly 5 concepts, got {len(concepts)}."
        )
    if not dna.uncontested_space.strip():
        raise ValueError("DNA.uncontested_space must be non-empty before QC.")

    backend = backend or StubBackend()
    questions = load_protocol()
    results = backend.answer_all(questions, dna, concepts)

    if len(results) != len(questions):
        raise RuntimeError(
            f"Backend returned {len(results)} answers for "
            f"{len(questions)} questions."
        )

    answers: list[InterrogationAnswer] = []
    failed: list[int] = []
    for q, (text, ok) in zip(questions, results):
        answers.append(
            InterrogationAnswer(
                question_id=q.id,
                category=q.category_name,
                question=q.text,
                answer=text,
                **{"pass": ok},
            )
        )
        if not ok:
            failed.append(q.id)

    hard_failures = [
        a.question_id
        for a in answers
        if not a.pass_
        and _category_id_for(questions, a.question_id) in HARD_GATE_CATEGORIES
    ]
    overall_pass = len(failed) == 0 or (
        len(failed) <= 3 and not hard_failures
    )

    notes = _build_notes(len(failed), hard_failures)

    return InterrogationReport(
        answers=answers,
        passed=len(answers) - len(failed),
        failed_questions=failed,
        overall_pass=overall_pass,
        notes=notes,
    )


def _category_id_for(questions: list[Question], qid: int) -> int:
    return questions[qid - 1].category_id


def _build_notes(failed_count: int, hard_failures: list[int]) -> str:
    if failed_count == 0:
        return "All 100 questions passed."
    if hard_failures:
        return (
            f"BLOCK: {failed_count} failures including hard-gate categories "
            f"(originality/distinctiveness/justification) at questions "
            f"{hard_failures}. Concepts must be revised."
        )
    return (
        f"SOFT FAIL: {failed_count} failures, all outside hard-gate categories. "
        "Acceptable for shipping but flag for human review."
    )
