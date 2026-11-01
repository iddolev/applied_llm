"""Answer questions about the philosophy corpus, with citations to Wikipedia sections.

Retrieves the top-k chunks for each question, has Claude answer from them with [n]
markers, and prints the answer with its sources. Every run is logged to data/runs/.
Without questions on the command line, it reads questions interactively, so the
embedding model is loaded only once.

Usage:
  uv run scripts/ask.py "What is moral luck?"
  uv run scripts/ask.py -k 20 --show-retrieved "Why is justified true belief not knowledge?"
  uv run scripts/ask.py            # interactive
"""

import argparse
import json
import logging
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

from applied_llm.answer import ANSWER_MODEL, Answer, Answerer
from applied_llm.chunking import HEADING_SEPARATOR
from applied_llm.index import ChunkIndex


def print_answer(a: Answer, show_retrieved: bool) -> None:
    print(f"\n{a.text}\n")
    print(f"Coverage: {a.coverage.value}")
    if a.invalid_citations:
        print(f"WARNING: cited passages that were never sent: {a.invalid_citations}")
    print("Sources:")
    for n, r in a.sources():
        print(f"  [{n}] {HEADING_SEPARATOR.join(r.chunk.heading_path)}\n       {r.chunk.url}")
    if show_retrieved:
        print("Retrieved:")
        for n, r in enumerate(a.retrieved, 1):
            mark = "*" if n in a.cited else " "
            print(f" {mark}[{n:2}] {r.score:.3f}  {HEADING_SEPARATOR.join(r.chunk.heading_path)}")
    print(f"({a.seconds:.1f}s, {a.usage['input_tokens']} input / {a.usage['output_tokens']} output tokens)")


def log_run(a: Answer, model: str, k: int, runs_dir: Path) -> None:
    runs_dir.mkdir(parents=True, exist_ok=True)
    record = {
        "time": datetime.now().isoformat(timespec="seconds"),
        "model": model,
        "k": k,
        "question": a.question,
        "answer": a.text,
        "coverage": a.coverage.value,
        "cited": a.cited,
        "invalid_citations": a.invalid_citations,
        "retrieved": [{"chunk_id": r.chunk.chunk_id, "score": round(r.score, 4)} for r in a.retrieved],
        "usage": a.usage,
        "seconds": round(a.seconds, 2),
    }
    with (runs_dir / f"{datetime.now():%Y-%m-%d}.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("questions", nargs="*")
    parser.add_argument("--data-dir", type=Path, default=Path("data/philosophy"))
    parser.add_argument("--runs-dir", type=Path, default=Path("data/runs"))
    parser.add_argument("-k", type=int, default=30, help="number of chunks to send to Claude")
    parser.add_argument("--model", default=ANSWER_MODEL)
    parser.add_argument("--effort", default="medium", choices=["low", "medium", "high", "xhigh", "max"])
    parser.add_argument("--show-retrieved", action="store_true", help="list all retrieved chunks, marking cited ones")
    args = parser.parse_args()

    load_dotenv()
    logging.basicConfig(level=logging.WARNING)
    answerer = Answerer(ChunkIndex(args.data_dir), args.model, args.effort)

    def answer(question: str) -> None:
        a = answerer.ask(question, args.k)
        print_answer(a, args.show_retrieved)
        log_run(a, args.model, args.k, args.runs_dir)

    if args.questions:
        for question in args.questions:
            print(f"\n=== {question}")
            answer(question)
        return
    print("Ask a question (empty line or Ctrl-D to quit).")
    while True:
        try:
            question = input("\n> ").strip()
        except EOFError:
            break
        if not question:
            break
        answer(question)


if __name__ == "__main__":
    main()
