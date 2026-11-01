"""Embed the chunks in chunks.jsonl with a local embedding model.

Writes embeddings.npy and embeddings_meta.json next to chunks.jsonl. Re-running after
rebuilding the chunks only embeds chunks whose text changed.

Usage:
  uv run scripts/build_index.py
  uv run scripts/build_index.py --model BAAI/bge-base-en-v1.5
"""

import argparse
import logging
import time
from pathlib import Path

from applied_llm.index import DEFAULT_MODEL, Embedder, build_embeddings

log = logging.getLogger("build_index")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--data-dir", type=Path, default=Path("data/philosophy"))
    parser.add_argument("--model", default=DEFAULT_MODEL, help="sentence-transformers model name")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    for name in ("httpx", "httpx2", "huggingface_hub"):
        logging.getLogger(name).setLevel(logging.WARNING)

    start = time.monotonic()
    matrix = build_embeddings(args.data_dir, Embedder(args.model))
    log.info("Wrote %d x %d embeddings to %s in %.0fs", *matrix.shape, args.data_dir / "embeddings.npy",
             time.monotonic() - start)


if __name__ == "__main__":
    main()
