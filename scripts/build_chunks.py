"""Split the corpus articles into retrieval-sized chunks.

Reads index.jsonl and the articles/<Title>.mediawiki files written by fetch_philosophy.py,
cleans each article into sections, and writes one chunk per line to chunks.jsonl. Reports
chunk length statistics, in words and in tokens of the embedding model's tokenizer.

Usage:
  uv run scripts/build_chunks.py
  uv run scripts/build_chunks.py --max-words 250 --overlap-words 40
"""

import argparse
import json
import logging
import statistics
from pathlib import Path

from tokenizers import Tokenizer
from tqdm import tqdm

from applied_llm.chunking import chunk_article, count_words
from applied_llm.wikitext import wikitext_to_sections

log = logging.getLogger("build_chunks")

EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"


def describe(name: str, values: list[int]) -> str:
    values = sorted(values)
    pct = lambda p: values[min(len(values) - 1, int(len(values) * p))]  # noqa: E731
    return (f"{name}: median {statistics.median(values):.0f}, p10 {pct(0.1)}, p90 {pct(0.9)}, "
            f"p99 {pct(0.99)}, max {values[-1]}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--data-dir", type=Path, default=Path("data/philosophy"))
    parser.add_argument("--max-words", type=int, default=300, help="split sections longer than this")
    parser.add_argument("--overlap-words", type=int, default=50, help="overlap between pieces of a split section")
    parser.add_argument("--min-words", type=int, default=30, help="merge shorter sections into a neighbour")
    parser.add_argument("--max-tokens", type=int, default=450, help="split chunks further if their text with the heading path has more tokens")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    with (args.data_dir / "index.jsonl").open(encoding="utf-8") as f:
        articles = [json.loads(line) for line in f]

    tokenizer = Tokenizer.from_pretrained(EMBEDDING_MODEL)
    count_tokens = lambda text: len(tokenizer.encode(text).ids)  # noqa: E731

    chunks = []
    for article in tqdm(articles, desc="chunking", unit="article"):
        wikitext = (args.data_dir / article["file"]).read_text(encoding="utf-8")
        chunks += chunk_article(
            article["title"], article["id"], wikitext_to_sections(wikitext),
            args.max_words, args.overlap_words, args.min_words, count_tokens, args.max_tokens,
        )

    out_path = args.data_dir / "chunks.jsonl"
    with out_path.open("w", encoding="utf-8") as out:
        for chunk in chunks:
            out.write(json.dumps(chunk.to_dict(), ensure_ascii=False) + "\n")
    log.info("Wrote %d chunks from %d articles to %s", len(chunks), len(articles), out_path)

    tokens = [len(e.ids) for e in tokenizer.encode_batch([c.context_text for c in chunks])]
    log.info(describe("words per chunk", [count_words(c.text) for c in chunks]))
    log.info(describe("tokens per chunk (with heading path)", tokens))
    too_long = [(c.chunk_id, n) for c, n in zip(chunks, tokens) if n > args.max_tokens]
    if too_long:
        log.warning("%d chunks exceed %d tokens, e.g. %s", len(too_long), args.max_tokens, too_long[:5])


if __name__ == "__main__":
    main()
