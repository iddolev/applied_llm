"""Score a system's answers: retrieval recall, a Claude judge for correctness and citation support,
and per-type summaries."""

from collections import defaultdict
from typing import Literal

import anthropic
from pydantic import BaseModel, Field

from applied_llm.chunking import HEADING_SEPARATOR, Chunk
from applied_llm.evaluation import EVAL_MODEL, gold_matches, structured_call

RECALL_KS = (5, 10, 30, 100)


def recall_at(gold: list[dict], retrieved: list[Chunk], k: int) -> float:
    """Fraction of gold items with a matching chunk among the top k."""
    top = retrieved[:k]
    hits = sum(any(gold_matches(g, c.title, c.heading_path) for c in top) for g in gold)
    return hits / len(gold)


class Claim(BaseModel):
    sentence: str
    cited: list[int]
    support: Literal["supported", "partial", "unsupported", "uncited"] = Field(
        description="Whether the cited passages support the sentence; 'uncited' if it has no [n] marker "
                    "and makes a factual claim.")


class Verdict(BaseModel):
    correctness: Literal["correct", "partial", "wrong"]
    key_points_covered: list[bool] = Field(description="One entry per key point, in order; empty if none given.")
    claims: list[Claim] = Field(description="One entry per sentence of the answer that makes a factual claim.")
    notes: str = Field(description="One or two sentences justifying the correctness grade.")


JUDGE_SYSTEM = """\
You grade answers from a question-answering system over Wikipedia articles about philosophy. \
You get the question, a reference answer (and for broad questions, key points), the system's \
answer with [n] citation markers, and the passages the answer cites.

1. correctness, compared with the reference answer:
   - correct: states the essential content of the reference, without significant errors;
   - partial: gets some of it, or is right but misses an essential part;
   - wrong: misses it, contradicts it, or declines to answer.
   Judge content, not wording. Extra correct detail is fine. For broad questions, grade by how \
many key points are covered (most = correct, some = partial, few = wrong).
2. key_points_covered: for each key point, whether the answer covers it.
3. claims: split the answer into sentences that make factual claims. For each, list its [n] \
markers and judge whether those cited passages (only those) support it: supported, partial, \
unsupported, or uncited if it has no marker. Use your own knowledge only for correctness, \
never for support."""


def judge(client: anthropic.Anthropic, question: dict, answer: str,
          cited_passages: dict[int, Chunk]) -> tuple[Verdict | None, dict]:
    reference = question["reference_answer"]
    if question["key_points"]:
        reference += "\nKey points:\n" + "\n".join(f"{i}. {p}" for i, p in enumerate(question["key_points"], 1))
    passages = "\n\n".join(
        f'<passage id="{n}" location="{HEADING_SEPARATOR.join(c.heading_path)}">\n{c.text}\n</passage>'
        for n, c in sorted(cited_passages.items())
    )
    user = (f"<question>{question['question']}</question>\n<reference_answer>{reference}</reference_answer>\n\n"
            f"<answer>{answer}</answer>\n\n<cited_passages>\n{passages}\n</cited_passages>")
    return structured_call(client, EVAL_MODEL, JUDGE_SYSTEM, user, Verdict)


def _mean(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None


def summarize(records: list[dict]) -> dict[str, dict]:
    """Metrics per question type, plus "all"."""
    groups: dict[str, list[dict]] = defaultdict(list)
    for r in records:
        groups[r["type"]].append(r)
        groups["all"].append(r)

    summary = {}
    for qtype, rs in groups.items():
        answerable = [r for r in rs if r["type"] != "unanswerable"]
        judged = [r for r in answerable if r.get("verdict")]
        claims = [c for r in judged for c in r["verdict"]["claims"]]
        cited_claims = [c for c in claims if c["support"] != "uncited"]
        key_points = [kp for r in judged for kp in r["verdict"]["key_points_covered"]]
        unanswerable = [r for r in rs if r["type"] == "unanswerable"]
        row = {"n": len(rs)}
        for k in RECALL_KS:
            row[f"recall@{k}"] = _mean([r["recall"][str(k)] for r in answerable])
        # Answers declined on answerable questions count as wrong.
        grades = [r["verdict"]["correctness"] if r.get("verdict") else "wrong" for r in answerable]
        row["correct"] = _mean([g == "correct" for g in grades])
        row["partial"] = _mean([g == "partial" for g in grades])
        row["key points"] = _mean(key_points)
        row["cited claims supported"] = _mean([c["support"] == "supported" for c in cited_claims])
        row["claims uncited"] = _mean([c["support"] == "uncited" for c in claims])
        row["false refusals"] = _mean([r["coverage"] == "none" for r in answerable])
        row["abstained (unanswerable)"] = _mean([r["coverage"] == "none" for r in unanswerable])
        row["seconds"] = _mean([r["seconds"] for r in rs])
        row["answer $"] = _mean([r["answer_cost"] for r in rs if r.get("answer_cost") is not None])
        summary[qtype] = row
    return summary


def format_table(columns: list[str], rows: dict[str, dict]) -> str:
    """A markdown table: one row per key of `rows`, one column per metric."""
    def fmt(metric: str, v) -> str:
        if v is None:
            return "–"
        if metric == "n":
            return str(v)
        if metric == "seconds":
            return f"{v:.1f}"
        if metric.endswith("$"):
            return f"{v:.3f}"
        return f"{v:.0%}"

    lines = ["| | " + " | ".join(columns) + " |", "|---" * (len(columns) + 1) + "|"]
    for name, row in rows.items():
        lines.append(f"| {name} | " + " | ".join(fmt(c, row.get(c)) for c in columns) + " |")
    return "\n".join(lines)
