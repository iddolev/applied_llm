"""Embed chunks with a local model and search them by cosine similarity.

At about 30k chunks a brute-force dot product over a normalized float32 matrix takes
milliseconds, so the "vector store" is just a numpy file next to chunks.jsonl:

  embeddings.npy        one normalized row per line of chunks.jsonl, in the same order
  embeddings_meta.json  the model name and a hash of each embedded text, used to reuse
                        unchanged embeddings when the chunks are rebuilt
"""

import hashlib
import json
import logging
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from applied_llm.chunking import Chunk

log = logging.getLogger(__name__)

DEFAULT_MODEL = "BAAI/bge-small-en-v1.5"

# Instructions the BGE English models expect in front of queries (not passages).
QUERY_PROMPTS = {
    "BAAI/bge-small-en-v1.5": "Represent this sentence for searching relevant passages: ",
    "BAAI/bge-base-en-v1.5": "Represent this sentence for searching relevant passages: ",
    "BAAI/bge-large-en-v1.5": "Represent this sentence for searching relevant passages: ",
}


class Embedder:
    def __init__(self, model_name: str = DEFAULT_MODEL):
        from sentence_transformers import SentenceTransformer  # slow import; only when embedding

        self.model_name = model_name
        self._model = SentenceTransformer(model_name, device="cpu")
        self._query_prompt = QUERY_PROMPTS.get(model_name, "")

    def embed_passages(self, texts: list[str], batch_size: int = 64, progress: bool = True) -> np.ndarray:
        return self._model.encode(
            texts, batch_size=batch_size, show_progress_bar=progress, normalize_embeddings=True,
            convert_to_numpy=True,
        ).astype(np.float32)

    def embed_query(self, query: str) -> np.ndarray:
        return self._model.encode(
            [query], prompt=self._query_prompt, normalize_embeddings=True, convert_to_numpy=True,
        )[0].astype(np.float32)


def text_hash(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()


def read_chunks(path: Path) -> list[Chunk]:
    with path.open(encoding="utf-8") as f:
        return [Chunk(**json.loads(line)) for line in f]


def build_embeddings(data_dir: Path, embedder: Embedder) -> np.ndarray:
    """Embed every chunk in chunks.jsonl, reusing embeddings of texts embedded before by the same model."""
    chunks = read_chunks(data_dir / "chunks.jsonl")
    texts = [c.context_text for c in chunks]
    hashes = [text_hash(t) for t in texts]

    cached: dict[str, np.ndarray] = {}
    meta_path, emb_path = data_dir / "embeddings_meta.json", data_dir / "embeddings.npy"
    if meta_path.exists() and emb_path.exists():
        meta = json.loads(meta_path.read_text())
        if meta["model"] == embedder.model_name:
            old = np.load(emb_path)
            cached = dict(zip(meta["hashes"], old))

    todo = [i for i, h in enumerate(hashes) if h not in cached]
    log.info("%d chunks: %d embeddings reused, %d to compute", len(chunks), len(chunks) - len(todo), len(todo))
    if todo:
        for i, vec in zip(todo, embedder.embed_passages([texts[i] for i in todo])):
            cached[hashes[i]] = vec

    matrix = np.stack([cached[h] for h in hashes])
    np.save(emb_path, matrix)
    meta_path.write_text(json.dumps({"model": embedder.model_name, "hashes": hashes}))
    return matrix


@dataclass
class SearchResult:
    chunk: Chunk
    score: float


class ChunkIndex:
    """Chunks and their embeddings, searchable by a natural-language query."""

    def __init__(self, data_dir: Path, embedder: Embedder | None = None):
        meta = json.loads((data_dir / "embeddings_meta.json").read_text())
        self.chunks = read_chunks(data_dir / "chunks.jsonl")
        self.embeddings = np.load(data_dir / "embeddings.npy")
        if len(self.chunks) != len(self.embeddings) or meta["hashes"] != [
            text_hash(c.context_text) for c in self.chunks
        ]:
            raise ValueError("embeddings.npy is out of date with chunks.jsonl; run scripts/build_index.py")
        self.embedder = embedder or Embedder(meta["model"])
        if self.embedder.model_name != meta["model"]:
            raise ValueError(f"index was built with {meta['model']}, not {self.embedder.model_name}")

    def search(self, query: str, k: int = 10) -> list[SearchResult]:
        scores = self.embeddings @ self.embedder.embed_query(query)
        top = np.argpartition(-scores, min(k, len(scores) - 1))[:k]
        top = top[np.argsort(-scores[top])]
        return [SearchResult(self.chunks[i], float(scores[i])) for i in top]
