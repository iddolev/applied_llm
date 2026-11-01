"""Show the chunks most similar to a query, for checking retrieval by eye.

Usage:
  uv run scripts/search.py "Can you be blamed for outcomes you didn't control?"
  uv run scripts/search.py -k 20 "Gettier problem"
"""

import argparse
import logging
from pathlib import Path

from applied_llm.chunking import HEADING_SEPARATOR
from applied_llm.index import ChunkIndex


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("queries", nargs="+")
    parser.add_argument("--data-dir", type=Path, default=Path("data/philosophy"))
    parser.add_argument("-k", type=int, default=10)
    args = parser.parse_args()
    logging.basicConfig(level=logging.WARNING)

    index = ChunkIndex(args.data_dir)
    for query in args.queries:
        print(f"\n=== {query}")
        for rank, r in enumerate(index.search(query, args.k), 1):
            snippet = " ".join(r.chunk.text.split())[:110]
            print(f"{rank:2}. {r.score:.3f}  {HEADING_SEPARATOR.join(r.chunk.heading_path)}\n      {snippet}")


if __name__ == "__main__":
    main()
