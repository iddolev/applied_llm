# Plan: RAG baseline, evaluation and hierarchical-summary agent

## Goal

Answer user questions from the philosophy corpus, citing the Wikipedia sections the answer came from. We build this in four stages:

1. A plain RAG baseline.
2. A question set and an evaluation harness, to measure the baseline.
3. Improvements to retrieval, made only where the evaluation shows a weakness.
4. An agent that navigates hierarchical summaries, compared against the baseline on the same question set.

The reasons for the technology choices (no framework, the Anthropic SDK, LangFuse later) are in [../conclusions.md](../conclusions.md).

## Starting point (done)

These files are in `data/philosophy/`:
- `articles/<Title>.mediawiki`: the original wikitext of 1,725 articles (concepts and problems, philosophical positions, disciplines).
- `index.jsonl`: one line of metadata per article: id, title, url, revid, timestamp, n_chars, category, file.
- `applied_llm.wikitext.wikitext_to_sections` cleans the wikitext into sections (heading, level, text).

The cleaned corpus is about 32M characters in 21,918 sections:
- the median section has 163 words, and 90% have at most 484;
- the longest section has 19,381 words;
- 3,626 sections exceed about 380 words, roughly the 512-token limit of small embedding models;
- 2,708 sections are under 30 words.

## Phase 1: Chunking

**Module:** `src/applied_llm/chunking.py`
**Script:** `scripts/build_chunks.py`, which writes `data/philosophy/chunks.jsonl`

Rules:
- **Unit:** each section, as produced by `wikitext_to_sections`.
- **Long sections:** split sections over about 300 words into chunks of about 300 words, with an overlap of about 50 words. Split at paragraph boundaries where possible, otherwise at sentence boundaries.
- **Short sections:** merge sections under about 30 words into the next section of the same article; if there is no next section, into the previous one.
- **Heading path:** keep the path for each chunk (e.g. `["Moral luck", "Criticism"]`), including parent headings for subsections. The text that gets embedded starts with `Moral luck › Criticism\n\n`, so chunks that say "Nagel rejects this…" stay on topic.
- **Chunk record:**
  - `chunk_id`, e.g. `Moral_luck#3`
  - `title`
  - `heading_path`
  - `text`
  - `url`: links to the section via its anchor, `https://en.wikipedia.org/wiki/Moral_luck#Criticism`. The anchor is the heading with spaces turned into underscores.
  - `article_id`
  - `section_index`
  - `part`, the n-th piece of a split section

**Done when:**
- every chunk's embedded text is at most about 450 tokens (checked with the embedding model's tokenizer);
- statistics for chunk count and lengths are logged;
- a spot-check of 20 random chunks reads well.

## Phase 2: Embeddings and vector index

**Module:** `src/applied_llm/index.py`
**Script:** `scripts/build_index.py`, which writes `data/philosophy/embeddings.npy` (float32, normalized) and stores the model name with it

- **Model:** `BAAI/bge-small-en-v1.5` via `sentence-transformers`, on CPU.
  - Install CPU-only torch through uv's index configuration, to avoid downloading CUDA.
  - The model is configurable, so `bge-base` or another model can be tried later.
- **Text prefixes:** passages are embedded as they are. Questions get the model's query instruction: `Represent this sentence for searching relevant passages: `.
- **Search:** `search(query, k) -> list[(chunk, score)]`, a brute-force dot product over the normalized matrix, which takes milliseconds at about 30k vectors. Switch to LanceDB only if filtering or persistence needs grow.
- **Incremental rebuild:** cache embeddings by a hash of the chunk text, so re-chunking only re-embeds changed chunks.

**Done when:**
- the index builds in about 10–20 minutes on CPU;
- a few hand-written queries return sensible top-10 results, including one scenario query that never names its concept.

## Phase 3: Answering with citations

**Module:** `src/applied_llm/answer.py`
**Script:** `scripts/ask.py "question"`

- **Retrieve:** the top `k` chunks; start with k = 30. No reranker at first.
- **Prompt:** the chunks are numbered `[1]`…`[k]`, each labelled with its article and heading path. The instructions are:
  - answer **only** from the sources;
  - put inline `[n]` markers after each claim;
  - say explicitly when the sources don't cover the question, rather than answering from general knowledge.
- **Output:** use Claude structured output (`messages.parse` with Pydantic) to get `{answer: str, cited: list[int], sufficient: bool}`.
- **Post-processing:**
  - check that every `[n]` in the answer is between 1 and k and appears in `cited`;
  - turn markers into section links;
  - log any mismatch.
- **Model:** configurable; start with Claude Sonnet or Opus for answers.
- **Logging:** write each run (question, chunk ids with scores, prompt, answer, citations, tokens, latency) to `data/runs/*.jsonl`.

**Done when** `ask.py` answers a handful of questions with correct, clickable citations and declines a question outside the corpus.

## Phase 4: Question set and evaluation

**Module:** `src/applied_llm/evaluation/`
**Scripts:** `scripts/build_questions.py`, `scripts/run_eval.py`

**Question set:** about 150–200 questions, with a mix of types, since each type tests a different weakness:

| Type | Example | Tests |
|---|---|---|
| Lookup | "Who coined the term *moral luck*?" | Basic retrieval |
| Paraphrase or scenario | "Can you be blamed for a drunk drive that harmed no one only by luck?" | Vocabulary mismatch |
| Multi-hop | Needs facts from two articles, where the second depends on the first | Single-shot retrieval |
| Broad or comparative | "What are the main objections to utilitarianism?" | Coverage of many sections |
| Negation or relation | Questions where word order or "not" matters | Bag-of-words weakness of embeddings |
| Unanswerable | A plausible question the corpus doesn't cover | Grounding and abstention |

**How to build it:**
- Claude generates questions from sampled sections, articles or pairs of articles, and records the gold sections and a reference answer for each.
- Instruct it to avoid copying the section's wording; otherwise the questions are biased toward lexical overlap and flatter retrieval.
- Review questions by hand, at least for a subset, and fix or drop bad ones.
- Store as `data/eval/questions.jsonl`, under version control if it's small enough (decide later).

**Metrics**, per question type:
- **Retrieval recall@k:** was a gold section among the retrieved chunks? Computed for k = 5, 10, 30, 100.
- **Answer correctness:** an LLM judge compares the answer with the reference answer.
- **Citation support:** for each cited chunk, an LLM judge checks whether it supports the claim it is attached to.
- **Abstention:** the system declines unanswerable questions and doesn't decline answerable ones.
- **Cost and latency** per question.

**Output:** a per-variant results file and a summary table that compares variants by question type.

**Done when** the baseline has a full set of scores per question type, and the failures have been examined by hand to see where they come from: retrieval, answering or the question itself.

## Phase 5: Retrieval improvements (only where Phase 4 shows a need)

Try each change as a variant and measure it with `run_eval.py`:

- **Low recall on rare terms and names:** hybrid search, with BM25 (e.g. `bm25s`) merged with embeddings by reciprocal rank fusion.
- **Gold section ranked below k:** a local cross-encoder (`BAAI/bge-reranker-base`) over the top 100–200 candidates, keeping the top 30. It mainly boosts recall.
- **Vocabulary mismatch on scenario questions:**
  - query rewriting: Claude rewrites the question before search;
  - HyDE: embed a hypothetical answer instead of the question.
- **Distractors hurting answers or citations:** send fewer chunks, or rerank with Claude Haiku.
- **Embedding quality:** try `bge-base-en-v1.5` or another local model.

## Phase 6: Hierarchical summaries

**Module:** `src/applied_llm/summaries.py`
**Script:** `scripts/build_summaries.py`, which writes `data/philosophy/summaries.jsonl` and is resumable like the labels stage

- **Section summary:** one sentence plus a list of key terms, people and examples. The term list keeps summaries useful for navigating to specific details.
- **Article summary:** one sentence plus key terms, written from the lead section and the section summaries.
- **Discipline tags:** 1–3 per article. The tags are taken from the corpus's discipline articles (Epistemology, Ethics, Logic, …), cut down to a manageable list of about 20–30. Articles can belong to several disciplines, because philosophy topics cross-cut.
- **Discipline summaries:** one sentence plus key terms for each discipline, for overview.
- **Model:** Claude Haiku. There are about 22k section summaries, so consider the Batch API to halve the cost.
- **Embeddings:** embed the summaries too, so `search` can return summaries as well as chunks (RAPTOR-style).

**Done when** a spot-check of summaries for 20 articles shows accurate sentences and useful key terms.

## Phase 7: Navigation agent

**Module:** `src/applied_llm/agent.py`
**Script:** `scripts/ask.py --agent "question"`

- **Loop:** a ReAct loop with the Anthropic SDK tool runner and a step limit (e.g. 12 tool calls).
- **Context:** the system prompt includes all 1,725 article summaries (about 60k tokens), cached with prompt caching. This lets the agent choose articles by judgment from the start. At this corpus size the discipline level is a tool, not a required first step.
- **Tools:**
  - `list_articles(discipline)`: the articles tagged with a discipline, with their summaries.
  - `article_sections(title)`: the section headings and section summaries of an article.
  - `read_section(title, section)`: the full chunk text, with chunk ids for citation.
  - `search(query, k)`: embedding search (plus BM25, if Phase 5 adopted it) over chunks and summaries.
- **Final answer:** the same format as Phase 3, with inline citations of the chunks it read. The same citation validation applies.
- **Logging:** each step (tool call, arguments, result size) goes into the run log, so wrong navigation choices can be diagnosed.

**Done when** the agent answers the evaluation set end to end within the step limit.

## Phase 8: Comparison and observability

- **Variants:** run the baseline, the best Phase 5 variant and the agent on the full question set.
- **Comparison:** compare by question type. We expect the agent to win on broad, multi-hop and scenario questions, and expect RAG to match it on lookups at much lower cost and latency. The comparison should check this rather than assume it.
- **LangFuse:**
  - introduce it here, self-hosted, using its decorator with the plain SDK;
  - send traces of every run, with agent steps shown as a tree;
  - store the question set as a dataset and each variant as an experiment, with judge scores attached.
- **Write-up:** add the conclusions to `docs/conclusions.md`: which design to use for which question types, and at what cost.

## Open decisions

- **Answering model:** Sonnet vs Opus as the default, chosen on the cost and quality seen in Phase 4.
- **Tags:** the final list of disciplines used as tags.
- **Question set:** whether to commit it to git or keep it under `data/`.
- **Corpus size:** whether to expand the corpus (e.g. add Low-importance articles) after the first comparison. A larger corpus is where the hierarchy should matter more.
