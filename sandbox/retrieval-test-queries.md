# Retrieval test queries (Phase 2)

Date: 2026-11-01

## Setup

| Item | Value |
|---|---|
| Chunks | 27,847 |
| Embedding model | `BAAI/bge-small-en-v1.5` (384 dimensions), on CPU |
| Search | Dot product over the normalized embeddings |
| Query instruction | `Represent this sentence for searching relevant passages: ` |
| Command | `uv run scripts/search.py -k 5 "…"` |

## Results

Each query shows its top 5 results.

| Query | Result |
|---|---|
| "Who coined the term moral luck?" | ✅ Moral luck lead section ranked 1st |
| "Can a drunk driver who got home safely be less blameworthy than one who killed a child?" (never names the concept) | ✅ Moral luck chunks ranked 1st and 2nd |
| "If you replace every plank of a ship one at a time, is it still the same ship?" | ✅ All 5 are Ship of Theseus chunks |
| "What are the main objections to utilitarianism?" | ✅ Utilitarianism's criticism sections and the Demandingness objection article fill the top 5 |
| "Is it wrong to lie to a murderer who asks where your friend is hiding?" | ⚠️ The exact section, *Categorical imperative › Lying to a murderer*, ranked 3rd, below generic "Lie" chunks |
| "Why is justified true belief not sufficient for knowledge?" | ⚠️ General justified-true-belief chunks fill the top 5; the Gettier problem chunks (the real answer) rank only around 30th |

## Observations

- **Scenarios and paraphrases work.** Embeddings handle questions that don't use the concept's name. The drunk-driver scenario is exactly the case the "bag of senses" argument predicted would fail.
- **The two weaker results** are the kind a reranker, or Claude reading the top 30 chunks, should fix:
  - The murderer query ranked generic chunks about lying above the specific section.
  - The Gettier problem chunks are the actual answer to the justified-true-belief query, but they ranked only about 30th.

  The Gettier case is a good item for the evaluation question set.
- **Speed:** each run of `search.py` took about 13–24 seconds, depending on machine load. Measured breakdown of one run:

  | Step | Time |
  |---|---|
  | Importing PyTorch and sentence-transformers | 9.0 s |
  | Loading the embedding model | 1.5 s |
  | Loading the chunks and embeddings | 0.5 s |
  | First query (embedding the question, including warm-up) | 1.8 s |

  The dot product over the 27,847 embeddings takes milliseconds.
