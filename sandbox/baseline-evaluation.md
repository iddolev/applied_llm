# Baseline evaluation (Phase 4)

Date: 2026-11-01

## Setup

| Item | Value |
|---|---|
| System | Plain RAG: top 30 chunks (`bge-small-en-v1.5`), answered by Claude Sonnet 5.5 at effort `medium` |
| Questions | 150, from `data/eval/questions.jsonl` |
| Judge | Claude Opus 5.5 |
| Command | `uv run scripts/run_eval.py --variant baseline` |
| Cost | $4.64 for answers ($0.031 per question), $3.84 for judging |

## Results

| | n | recall@5 | recall@30 | correct | partial | key points | cited claims supported | claims uncited | false refusals | abstained (unanswerable) | seconds |
|---|---|---|---|---|---|---|---|---|---|---|---|
| lookup | 40 | 80% | 98% | 100% | 0% | – | 99% | 16% | 0% | – | 2.8 |
| scenario | 30 | 37% | 67% | 73% | 20% | – | 94% | 24% | 3% | – | 5.0 |
| multihop | 25 | 46% | 70% | 56% | 32% | – | 93% | 10% | 8% | – | 4.1 |
| broad | 25 | 49% | 82% | 76% | 24% | 80% | 99% | 10% | 0% | – | 6.7 |
| negation | 15 | 100% | 100% | 100% | 0% | – | 100% | 15% | 0% | – | 3.7 |
| unanswerable | 15 | – | – | – | – | – | – | – | – | 80% | 2.6 |
| **all** | 150 | 61% | 83% | 81% | 15% | 80% | 97% | 15% | 2% | 80% | 4.2 |

## Findings

1. **Overall, plain RAG is strong.** 81% of answers are correct and 15% partially correct. 97% of cited claims are supported by the passages they cite.
2. **Multi-hop questions are the clear weakness: 56% correct.** The typical failure has recall 0.5: the first article is retrieved, but the second, which the question only describes indirectly, isn't, even among the top 100 chunks. A single search with the question can't find a document whose topic is only revealed by the first one. This is the case for query decomposition, iterative retrieval or the navigation agent.
3. **Scenario questions: 73% correct.** Recall (67% at 30) understates retrieval, because the gold is too narrow:
   - **Narrow gold:** the gold is a single article, but concepts are often covered by several. Seven scenario answers were correct and well-cited with "recall 0", e.g. one drew on *Infinite regress (epistemology)* while the gold was *Infinite regress*.
   - **Real failures:** a few concepts weren't retrieved at all. One example is the tomato question about primary vs secondary qualities: the answer said so honestly and was graded wrong.
4. **Broad questions: 76% correct, 80% of key points covered.** Recall rises from 82% at 30 chunks to more at 100, so some key points sit just outside the 30 chunks sent.
5. **Grounding works.** When retrieval missed, Claude said the passages don't cover the question rather than answering from its own knowledge (e.g. the tomato question).
6. **The unanswerable score (80%) understates the system.** Of the 3 "misses", 2 are good partial answers: the system answered the part the corpus covers (Ryle at Oxford; Locke's *Letter* in 1689) and said the rest isn't covered. The third is the question I had already flagged as having no clear answer.
7. **"Uncited claims" (15%) are mostly a citation-placement issue, not invented facts.** Typically an opening sentence restates the answer ("The Tiantai thinker was Zhanran.") and the marker comes on the next sentence.
8. **Lookup and negation are at 100%, so they're too easy.** Negation questions name their entities, so retrieval finds them trivially. As generated, they don't test what they were meant to (word order and negation).

## Judge check

I read 10 verdicts in full: both "wrong" grades, four "partial" and four "correct".
- **8 of 10:** I agree with the grade.
- **2 of 10:** the judge was stricter than I would be:
  - it graded an answer "partial" for omitting Leibniz's name, although it identified the identity of indiscernibles and its controversy correctly;
  - it graded another "partial" for giving a valid alternative definition of "limiting case".

So the "correct" rate is, if anything, a conservative estimate.

## Recommendations for Phase 5

| Weakness | Variant to try |
|---|---|
| Multi-hop retrieval (biggest gap) | Query decomposition or iterative retrieval: answer the first hop, then search again with what was learned. This is also the strongest argument for the Phase 7 agent. |
| Scenario retrieval | Query rewriting or HyDE: have Claude name candidate concepts or write a hypothetical answer, then search with that. |
| Broad coverage | k = 50, or a cross-encoder reranker over the top 100 (cheap to test). |

## Fixes to the evaluation itself

- **Scenario gold:** widen it to every article that covers the concept, e.g. by having the judge-side model mark which of the top 100 chunks answer the question.
- **Unanswerable scoring:** score with the judge (does the answer assert the missing facts?) instead of requiring coverage `none`.
- **Negation questions:** regenerate so that they don't name both sides of the relation.
- **Answer prompt:** require a marker on every sentence, including the opening one.
