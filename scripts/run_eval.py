"""Run a system variant on the evaluation question set and score it.

For each question: retrieve the top 100 chunks (for recall@k), answer from the top k, and have
Claude Opus judge the answer's correctness and citation support. Results are cached in
data/eval/results/<variant>.jsonl: re-running reuses answers and verdicts whose question and
settings haven't changed. A summary table by question type is printed and written to
data/eval/results/<variant>.summary.md.

Usage:
  uv run scripts/run_eval.py --variant baseline
  uv run scripts/run_eval.py --variant k10 -k 10
  uv run scripts/run_eval.py --variant baseline --rejudge     # re-run the judge only
  uv run scripts/run_eval.py --compare baseline k10
"""

import argparse
import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import anthropic
from dotenv import load_dotenv
from tqdm import tqdm

from applied_llm.answer import ANSWER_MODEL, Answerer
from applied_llm.evaluation import EVAL_MODEL, cost
from applied_llm.evaluation.scoring import RECALL_KS, format_table, judge, recall_at, summarize
from applied_llm.index import ChunkIndex, SearchResult

log = logging.getLogger("run_eval")

MAIN_COLUMNS = ["n", "recall@5", "recall@30", "correct", "partial", "key points", "cited claims supported",
                "claims uncited", "false refusals", "abstained (unanswerable)", "seconds", "answer $"]


def load_results(path: Path) -> dict[str, dict]:
    """Records by question id; later lines replace earlier ones."""
    if not path.exists():
        return {}
    with path.open(encoding="utf-8") as f:
        return {r["id"]: r for r in map(json.loads, f)}


def evaluate(q: dict, retrieved: list[SearchResult], answerer: Answerer, client: anthropic.Anthropic,
             config: dict, cached: dict | None, rejudge: bool) -> dict:
    if cached is None:
        a = answerer.ask(q["question"], config["k"], retrieved)
        record = {
            "id": q["id"], "type": q["type"], "question": q["question"], "config": config,
            "recall": {str(k): recall_at(q["gold"], [r.chunk for r in retrieved], k) for k in RECALL_KS}
            if q["gold"] else None,
            "sent": [r.chunk.chunk_id for r in retrieved[: config["k"]]],
            "answer": a.text, "coverage": a.coverage.value, "cited": a.cited,
            "invalid_citations": a.invalid_citations, "answer_usage": a.usage,
            "answer_cost": cost(config["model"], a.usage), "seconds": round(a.seconds, 2),
        }
    else:
        record = dict(cached)
    if q["type"] != "unanswerable" and record["coverage"] != "none" and (rejudge or not record.get("verdict")):
        sent = {n: r.chunk for n, r in enumerate(retrieved[: config["k"]], 1)}
        cited = {n: sent[n] for n in record["cited"] if n in sent}
        verdict, usage = judge(client, q, record["answer"], cited)
        record["verdict"] = verdict.model_dump() if verdict else None
        record["judge_cost"] = cost(EVAL_MODEL, usage)
    return record


def print_summary(variant: str, records: list[dict], out_path: Path | None = None) -> None:
    order = ["lookup", "scenario", "multihop", "broad", "negation", "unanswerable", "all"]
    summary = summarize(records)
    table = format_table(MAIN_COLUMNS, {t: summary[t] for t in order if t in summary})
    text = f"# {variant}\n\n{table}\n"
    print(text)
    if out_path:
        out_path.write_text(text, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--variant", help="name for this configuration's results")
    parser.add_argument("--compare", nargs="+", metavar="VARIANT", help="compare saved variants instead of running")
    parser.add_argument("--data-dir", type=Path, default=Path("data/philosophy"))
    parser.add_argument("--eval-dir", type=Path, default=Path("data/eval"))
    parser.add_argument("-k", type=int, default=30, help="number of chunks sent to Claude")
    parser.add_argument("--model", default=ANSWER_MODEL)
    parser.add_argument("--effort", default="medium")
    parser.add_argument("--rejudge", action="store_true", help="re-run the judge on cached answers")
    parser.add_argument("--limit", type=int, help="only the first N questions (for trying things out)")
    parser.add_argument("--workers", type=int, default=6)
    args = parser.parse_args()

    load_dotenv()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    for name in ("httpx", "httpx2"):
        logging.getLogger(name).setLevel(logging.WARNING)
    results_dir = args.eval_dir / "results"

    if args.compare:
        overall = {}
        for variant in args.compare:
            records = list(load_results(results_dir / f"{variant}.jsonl").values())
            overall[variant] = summarize(records)["all"]
            print_summary(variant, records)
        print("# Comparison (all questions)\n\n" + format_table(MAIN_COLUMNS, overall))
        return
    if not args.variant:
        parser.error("give --variant or --compare")

    with (args.eval_dir / "questions.jsonl").open(encoding="utf-8") as f:
        questions = [json.loads(line) for line in f][: args.limit]
    config = {"k": args.k, "model": args.model, "effort": args.effort}
    results_dir.mkdir(parents=True, exist_ok=True)
    results_path = results_dir / f"{args.variant}.jsonl"
    saved = load_results(results_path)

    index = ChunkIndex(args.data_dir)
    answerer = Answerer(index, args.model, args.effort)
    client = anthropic.Anthropic(max_retries=5)
    # Search sequentially (one embedding model); the API calls then run in parallel.
    retrieved = {q["id"]: index.search(q["question"], max(100, args.k)) for q in tqdm(questions, desc="retrieval")}

    def cached_for(q: dict) -> dict | None:
        r = saved.get(q["id"])
        return r if r and r["question"] == q["question"] and r["config"] == config else None

    records = {}
    with results_path.open("a", encoding="utf-8") as out, ThreadPoolExecutor(args.workers) as pool:
        futures = {}
        for q in questions:
            cached = cached_for(q)
            if cached and (cached.get("verdict") or q["type"] == "unanswerable" or cached["coverage"] == "none") \
                    and not args.rejudge:
                records[q["id"]] = cached
            else:
                futures[pool.submit(evaluate, q, retrieved[q["id"]], answerer, client, config, cached,
                                    args.rejudge)] = q["id"]
        for future in tqdm(as_completed(futures), total=len(futures), desc="answering and judging"):
            record = future.result()
            records[record["id"]] = record
            out.write(json.dumps(record, ensure_ascii=False) + "\n")
            out.flush()

    ordered = [records[q["id"]] for q in questions]
    print_summary(args.variant, ordered, results_dir / f"{args.variant}.summary.md")
    judge_cost = sum(r.get("judge_cost") or 0 for r in ordered)
    answer_cost = sum(r.get("answer_cost") or 0 for r in ordered)
    log.info("Answering cost $%.2f, judging cost $%.2f (including cached results)", answer_cost, judge_cost)


if __name__ == "__main__":
    main()
