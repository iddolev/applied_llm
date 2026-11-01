"""Build the evaluation question set.

Samples seed passages for each question type, has Claude Opus write a question from each,
and validates it. About 30% more candidates than needed are generated; the first ones that
pass validation are kept. Writes, under data/eval/:

  candidates.jsonl  every candidate with its generation, validation and verdict (appended to;
                    resumable: re-running only processes missing candidates)
  questions.jsonl   the final question set

and sandbox/eval-questions-flagged.md, listing rejected questions and included ones that
look suspicious, for human review.

Usage:
  uv run scripts/build_questions.py
"""

import argparse
import json
import logging
import math
import random
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import anthropic
from dotenv import load_dotenv
from tqdm import tqdm

from applied_llm.chunking import HEADING_SEPARATOR, Chunk
from applied_llm.evaluation import EVAL_MODEL, cost
from applied_llm.evaluation.questions import (
    QUESTION_TYPES, Corpus, Seed, check_unanswerable, generate, sample_seeds, validate, word_overlap,
)
from applied_llm.index import ChunkIndex, read_chunks

log = logging.getLogger("build_questions")

TARGETS = {"lookup": 40, "scenario": 30, "multihop": 25, "broad": 25, "negation": 15, "unanswerable": 15}
OVERSAMPLE = {"unanswerable": 2.0}  # many unanswerable candidates turn out to be answerable
DEFAULT_OVERSAMPLE = 1.3
HIGH_OVERLAP = 0.8  # flag included questions sharing this much vocabulary with their passages


def add_usage(total: dict, usage: dict) -> None:
    for key in ("input_tokens", "output_tokens"):
        total[key] = total.get(key, 0) + usage[key]


def gold_items(seed: Seed, used: list[int]) -> list[dict]:
    items: list[dict] = []
    for n in used:
        c = seed.passages[n - 1]
        item = {"title": c.title, "heading_path": None if seed.article_level_gold else c.heading_path}
        if item not in items:
            items.append(item)
    return items


def process(client: anthropic.Anthropic, cid: str, seed: Seed, index_search) -> dict:
    """Generate and validate one candidate question."""
    record = {"id": cid, "type": seed.type, "seed_chunks": [c.chunk_id for c in seed.passages], "note": seed.note}
    usage: dict = {}
    record["usage"] = usage
    gen, u = generate(client, seed)
    add_usage(usage, u)
    if gen is None or gen.skip:
        return {**record, "accepted": False, "reasons": [f"generation skipped: {gen.skip_reason if gen else 'refused'}"]}
    record["generated"] = gen.model_dump()
    reasons = []

    if seed.type == "unanswerable":
        retrieved = index_search(gen.question, 50)
        check, u = check_unanswerable(client, gen.question, retrieved)
        add_usage(usage, u)
        if check is None:
            reasons.append("check refused")
        else:
            record["unanswerable_check"] = check.model_dump()
            if check.answering_passages:
                found = [HEADING_SEPARATOR.join(retrieved[n - 1].heading_path)
                         for n in check.answering_passages if 1 <= n <= len(retrieved)]
                reasons.append(f"answered by retrieved passages: {found}")
            if not check.realistic:
                reasons.append(f"not realistic: {check.problems}")
        record.update(gold=[], overlap=None)
    else:
        bad_refs = [n for n in gen.used_passages if not 1 <= n <= len(seed.passages)]
        used = [n for n in gen.used_passages if n not in bad_refs] or list(range(1, len(seed.passages) + 1))
        passages = [seed.passages[n - 1] for n in used]
        v, u = validate(client, seed.type, gen, passages)
        add_usage(usage, u)
        if v is None:
            reasons.append("validation refused")
        else:
            record["validation"] = v.model_dump()
            for name, ok in [("not answerable from its passages", v.answerable), ("ambiguous", v.unambiguous),
                             ("not self-contained", v.self_contained), ("wrong reference answer", v.reference_correct),
                             ("doesn't fit its type", v.matches_type), ("copies wording", not v.copies_wording)]:
                if not ok:
                    reasons.append(f"{name}: {v.problems}")
        if seed.type == "multihop" and sorted(used) != [1, 2]:
            reasons.append(f"multi-hop question uses passages {used}, not both")
        if bad_refs:
            reasons.append(f"cited passages that don't exist: {bad_refs}")
        record.update(gold=gold_items(seed, used), overlap=round(word_overlap(gen.question, passages), 2))
    return {**record, "accepted": not reasons, "reasons": reasons}


def write_flagged(candidates: list[dict], questions: list[dict], chunks: dict[str, Chunk], path: Path,
                  notes: dict[str, str]) -> None:
    def describe(c: dict) -> list[str]:
        g = c.get("generated") or {}
        lines = [f"### {c['id']} ({c['type']})", ""]
        if g:
            lines += [f"**Q:** {g['question']}", "", f"**Reference answer:** {g['reference_answer']}"]
            if g.get("key_points"):
                lines += [""] + [f"- {p}" for p in g["key_points"]]
        lines += ["", "**Seed passages:** " + "; ".join(
            HEADING_SEPARATOR.join(chunks[cid].heading_path) for cid in c["seed_chunks"])]
        if c.get("overlap") is not None:
            lines.append(f"**Word overlap with passages:** {c['overlap']}")
        for reason in c.get("reasons", []):
            lines.append(f"- {reason}")
        return lines + [""]

    included = {q["id"] for q in questions}
    rejected = [c for c in candidates if not c["accepted"] and c.get("generated")]
    suspicious = [c for c in candidates if c["id"] in included and (c.get("overlap") or 0) >= HIGH_OVERLAP]
    reviewed = [c for c in candidates if c["id"] in notes and c["id"] in included]
    lines = [
        "# Evaluation questions: flagged for review", "",
        f"{len(questions)} questions were kept. This file lists questions that need a human decision.", "",
        f"## Included, but flagged in manual review ({len(reviewed)})", "",
        "Notes from data/eval/review_notes.json. Keep, reword or drop?", "",
    ]
    for c in reviewed:
        lines += describe(c)[:-1] + [f"- **Review note:** {notes[c['id']]}", ""]
    lines += [
        f"## Included, but sharing at least {HIGH_OVERLAP:.0%} of their vocabulary with their passages "
        f"({len(suspicious)})", "",
        "These may be too easy for retrieval. Keep, reword or drop?", "",
    ]
    for c in suspicious:
        lines += describe(c)
    lines += [f"## Rejected by validation ({len(rejected)})", "",
              "Excluded from the set. Any that look fine can be rescued.", ""]
    for c in rejected:
        lines += describe(c)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--data-dir", type=Path, default=Path("data/philosophy"))
    parser.add_argument("--eval-dir", type=Path, default=Path("data/eval"))
    parser.add_argument("--flagged", type=Path, default=Path("sandbox/eval-questions-flagged.md"))
    parser.add_argument("--seed", type=int, default=13)
    parser.add_argument("--workers", type=int, default=8)
    args = parser.parse_args()

    load_dotenv()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    for name in ("httpx", "httpx2"):
        logging.getLogger(name).setLevel(logging.WARNING)
    args.eval_dir.mkdir(parents=True, exist_ok=True)

    chunks = read_chunks(args.data_dir / "chunks.jsonl")
    with (args.data_dir / "index.jsonl").open(encoding="utf-8") as f:
        categories = {a["title"]: a["category"] for a in map(json.loads, f)}
    corpus = Corpus(chunks, categories)
    by_id = {c.chunk_id: c for c in chunks}

    rng = random.Random(args.seed)
    seeds: dict[str, Seed] = {}
    for qtype in QUESTION_TYPES:
        for i, seed in enumerate(sample_seeds(corpus, qtype, math.ceil(TARGETS[qtype] * OVERSAMPLE.get(qtype, DEFAULT_OVERSAMPLE)), rng)):
            seeds[f"{qtype}-{i:03d}"] = seed

    cand_path = args.eval_dir / "candidates.jsonl"
    done = {}
    if cand_path.exists():
        with cand_path.open(encoding="utf-8") as f:
            done = {c["id"]: c for c in map(json.loads, f)}
    todo = [cid for cid in seeds if cid not in done]
    log.info("%d candidates: %d done, %d to process", len(seeds), len(done), len(todo))

    index = None
    lock = threading.Lock()

    def index_search(question: str, k: int) -> list[Chunk]:
        nonlocal index
        with lock:  # one embedding model, used from several threads
            if index is None:
                index = ChunkIndex(args.data_dir)
            return [r.chunk for r in index.search(question, k)]

    client = anthropic.Anthropic(max_retries=5)
    with cand_path.open("a", encoding="utf-8") as out, ThreadPoolExecutor(args.workers) as pool:
        futures = {pool.submit(process, client, cid, seeds[cid], index_search): cid for cid in todo}
        for future in tqdm(as_completed(futures), total=len(futures), unit="question"):
            record = future.result()
            out.write(json.dumps(record, ensure_ascii=False) + "\n")
            out.flush()
            done[record["id"]] = record

    candidates = [done[cid] for cid in seeds]
    questions = []
    for qtype in QUESTION_TYPES:
        accepted = [c for c in candidates if c["type"] == qtype and c["accepted"]][: TARGETS[qtype]]
        if len(accepted) < TARGETS[qtype]:
            log.warning("Only %d of %d %s questions passed validation", len(accepted), TARGETS[qtype], qtype)
        for c in accepted:
            g = c["generated"]
            questions.append({
                "id": c["id"], "type": qtype, "question": g["question"],
                "reference_answer": g["reference_answer"], "key_points": g["key_points"],
                "gold": c["gold"], "seed_chunks": c["seed_chunks"], "overlap": c["overlap"],
            })
    with (args.eval_dir / "questions.jsonl").open("w", encoding="utf-8") as f:
        for q in questions:
            f.write(json.dumps(q, ensure_ascii=False) + "\n")
    notes_path = args.eval_dir / "review_notes.json"
    notes = json.loads(notes_path.read_text()) if notes_path.exists() else {}
    write_flagged(candidates, questions, by_id, args.flagged, notes)

    total: dict = {}
    for c in candidates:
        add_usage(total, c.get("usage") or {"input_tokens": 0, "output_tokens": 0})
    log.info("Kept %d questions; %d of %d candidates passed. Tokens: %s, cost $%.2f", len(questions),
             sum(c["accepted"] for c in candidates), len(candidates), total, cost(EVAL_MODEL, total))


if __name__ == "__main__":
    main()
