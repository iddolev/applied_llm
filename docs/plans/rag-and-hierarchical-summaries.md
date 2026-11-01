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
- **Heading path:** keep the path for each chunk (e.g. `["Moral luck", "Criticism"]`), including parent headings for subsections, computed from the heading levels. The lead section's path is just the title. The text that gets embedded or shown to Claude starts with `Moral luck › Criticism\n\n`, so chunks that say "Nagel rejects this…" stay on topic. The stored `text` doesn't include this prefix.
- **Empty sections:** 1,933 sections are parent headings with no text of their own, because their content is in their subsections. They produce no chunk; their heading survives in their subsections' heading paths.
- **Short sections:** merge non-empty sections under about 30 words (about 775 sections, mostly a sentence introducing the subsections that follow):
  - into the next section, if that is one of their subsections, so the intro stays with what it introduces;
  - otherwise into the previous section, with the short section's heading kept as a line in the text;
  - into the next section if there is no previous one.
- **Long sections:** split sections over about 300 words into chunks of about 300 words, with an overlap of about 50 words:
  - pieces are balanced in size, so a 320-word section doesn't leave a 20-word tail;
  - cuts fall at paragraph boundaries where possible, otherwise at sentence boundaries, never mid-sentence;
  - the overlap consists of whole sentences.
- **Settings:** the 300-word target, 50-word overlap and 30-word minimum are command-line options, so other values can be tried once the evaluation exists.
- **Chunk record:**
  - `chunk_id`, e.g. `Moral_luck#3` (numbered within the article)
  - `title`
  - `article_id`
  - `section_index`: the section's position in the output of `wikitext_to_sections`
  - `part`: the n-th piece of a split section
  - `heading_path`
  - `text`
  - `url`: links to the section via its anchor, `https://en.wikipedia.org/wiki/Moral_luck#Criticism`, with these anchor rules:
    - the anchor is the heading text with spaces turned into underscores;
    - special characters are percent-encoded;
    - repeated headings get `_2`, `_3`, … as on Wikipedia;
    - lead chunks link to the article itself.
- **Edge cases to check:** duplicate headings, headings with special characters, and the longest section (19,381 words).
- **Tokenizer:** add the embedding model's tokenizer (`tokenizers`) as a dependency in this phase, for the token-length check; Phase 2 needs it anyway.

**Done when:**
- every chunk's embedded text is at most about 450 tokens (checked with the embedding model's tokenizer; the model's hard limit is 512);
- statistics for chunk count and lengths are logged;
- a spot-check of 20 random chunks reads well.

**Result (done):**
- 27,847 chunks: median 191 words and 265 tokens, at most 450 tokens.
- Formulas (LaTeX) take many tokens per word, so chunks over `--max-tokens` are split again at a proportionally smaller word size.
- The spot-check found citation text from `<ref>` footnotes inside sentences, so `wikitext.py` now removes footnotes.
- Reading the chunks also showed that dropping every template lost real text. Examples: foreign terms in `{{lang}}` (the first chunk of "A priori and a posteriori" lost both terms), quotations in `{{blockquote}}`, dashes and formula variables. `wikitext.py` now replaces content-bearing templates with their text before stripping the rest. 19% of chunks changed; leftover gaps such as "( )" dropped from 1,279 to 151.
- `build_chunks.py` also writes `chunks_pretty.txt`, a readable view of all chunks.
- Known leftovers:
  - remaining gaps from rarer templates;
  - about 100 split pieces that start mid-sentence, in lists and other text without sentence punctuation.

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

**Result (done):**
- 27,847 × 384 embeddings (43 MB).
- The first full run took 95 minutes, because another CPU-heavy job was running at the same time; rebuilds only embed changed chunks.
- `scripts/search.py "query"` prints the top chunks for checking retrieval by eye.
- Six test queries:
  - "Who coined the term moral luck?": the Moral luck lead section ranked 1st.
  - "Can a drunk driver who got home safely be less blameworthy than one who killed a child?" (a scenario that never names its concept): Moral luck chunks ranked 1st and 2nd.
  - "If you replace every plank of a ship one at a time, is it still the same ship?": all of the top 5 are Ship of Theseus chunks.
  - "What are the main objections to utilitarianism?": the criticism sections of Utilitarianism and the Demandingness objection article fill the top 5.
  - "Is it wrong to lie to a murderer who asks where your friend is hiding?": the exact section (Categorical imperative › Lying to a murderer) ranked 3rd, below generic Lie chunks.
  - "Why is justified true belief not sufficient for knowledge?": general JTB chunks fill the top 5, and the Gettier problem chunks rank only around 30th. This is a candidate case for a reranker or query rewriting.

## Phase 3: Answering with citations

**Module:** `src/applied_llm/answer.py`
**Script:** `scripts/ask.py "question"`

- **Retrieve:** the top `k` chunks; start with k = 30. No reranker at first.
- **Prompt:** the chunks are numbered `[1]`…`[k]`, each labelled with its article and heading path. The instructions are:
  - answer **only** from the sources;
  - put inline `[n]` markers after each claim;
  - say explicitly when the sources don't cover the question, rather than answering from general knowledge.
- **Output:** use Claude structured output (Pydantic, via the streaming helper) to get `{answer: str, cited: list[int], coverage: full | partial | none}`. Coverage has three levels rather than a yes/no flag, because many questions are only partly covered.
- **Post-processing:**
  - take the cited passages from the `[n]` markers in the answer text (the authoritative source), and flag any number outside 1..k;
  - turn markers into section links.
- **Model:** configurable; the default is Claude Sonnet 5.5 at effort `medium` (`--model`, `--effort`).
- **Logging:** write each run (question, chunk ids with scores, answer, citations, coverage, tokens, latency) to `data/runs/<date>.jsonl`.
- **Interactive mode:** `ask.py` without questions reads them one at a time, so the libraries and the embedding model load only once.

**Done when** `ask.py` answers a handful of questions with correct, clickable citations and declines a question outside the corpus.

**Result (done):**
- All six test questions were answered correctly with section links, and the off-corpus question ("What is the boiling point of tungsten?") was declined.
- Each answer took 4–9 seconds, at about $0.03 per question.
- Claude used the right sections even where embeddings ranked them low.
- Details and full answers are in [../../sandbox/answering-test-questions.md](../../sandbox/answering-test-questions.md).
- The first run exposed a parsing bug: unbalanced italic markup made mwparserfromhell merge the rest of an article into one section (32 articles). `wikitext.py` now parses without style tags and removes footnotes with a regex before parsing.

## Phase 4: Question set and evaluation

**Module:** `src/applied_llm/evaluation/`
**Scripts:** `scripts/build_questions.py`, `scripts/run_eval.py`

**Question set** (`data/eval/questions.jsonl`): about 150 questions, deliberately mixed, because each type tests a different weakness:

| Type | ~Count | How it's generated | Gold (what counts as right) | Tests |
|---|---|---|---|---|
| Lookup | 40 | Pick a random chunk; Claude writes a question the chunk answers, in different words from the chunk | That chunk's section and a reference answer | Basic retrieval |
| Scenario | 30 | Pick a concept article; Claude writes a concrete situation that never names the concept or its key terms (e.g. the drunk-driver question for moral luck) | The article's relevant sections | Vocabulary mismatch |
| Multi-hop | 25 | Pick article A and an article B that A links to; the question needs one fact from each | One section from each article | Single-shot retrieval |
| Broad or comparative | 25 | Pick an article with a Criticism or Objections section, or two related positions (e.g. rationalism vs empiricism) | A set of sections plus a list of key points the answer should contain | Coverage of many sections |
| Negation or relation | 15 | Pick a chunk that states who rejected or influenced what; the question reverses roles or uses "not" | That chunk's section | Bag-of-words weakness of embeddings |
| Unanswerable | 15 | Plausible questions the corpus can't answer, e.g. biographical details about philosophers (people were excluded from the corpus) | None; the right behaviour is to decline | Grounding and abstention |

**Avoiding bias:** questions written by looking at a chunk tend to reuse its words, which flatters retrieval. So:
- **Generation prompt:** it requires paraphrase.
- **Validation pass:** a second Claude call checks each question against only its gold sections: it must be answerable from them, unambiguous, and not copy their wording. Questions that fail are regenerated or dropped.
- **Unanswerable questions:** the validation pass checks the top 50 retrieved chunks to confirm none of them answers the question.

**Models:** Claude Opus 5.5 generates and validates the questions, and also serves as the judge. That keeps question and grading quality high, and uses a different model from the Sonnet answerer, which reduces the bias of a model grading its own kind of output.

**Review (decided):** I review the questions and write only the flagged ones (ambiguous, too easy, wrong gold, etc.) to a readable file, `sandbox/eval-questions-flagged.md`, with their gold sections and reference answers, for the user to decide on. After that the set stays fixed, so scores remain comparable over time. Whether `questions.jsonl` goes into git is decided once its size is known.

**Metrics**, per question and averaged per type:
- **Retrieval recall@k** (k = 5, 10, 30, 100): was a gold section among the retrieved chunks? For broad questions, it is the fraction of gold sections retrieved. It needs no LLM, so it costs nothing, and it isolates retrieval from answering.
- **Answer correctness:** the judge compares the answer with the reference answer and gives correct, partially correct or wrong. For broad questions it reports the share of key points covered.
- **Citation support:** for each sentence with `[n]` markers, the judge checks whether the cited chunks actually support it. This catches answers that are right but drew on Claude's own knowledge rather than the sources.
- **Abstention:** the system declines unanswerable questions (coverage `none`) and doesn't decline answerable ones (no false refusals).
- **Cost and latency** per question.

**Checking the judge:** check about 20 of its verdicts by hand, and show the user any disagreements, before relying on it.

**Harness** (`scripts/run_eval.py`):
- **Running a variant:** `run_eval.py --variant baseline -k 30 --model claude-sonnet-5-5` runs every question, writes per-question results to `data/eval/results/<variant>.jsonl`, and prints a summary table by question type.
- **Comparing variants:** `run_eval.py --compare baseline k10 ...` puts variants side by side.
- **Caching:** answers and judge verdicts are cached, so re-scoring or adding a variant doesn't pay again for the parts that didn't change.

**Cost (approved):**

| Item | Cost |
|---|---|
| Building the set: generation and validation with Opus 5.5 ($4 / $20 per million tokens) | About $10, once |
| Each evaluation run: Sonnet answers (~$4.50) plus Opus judging (~$6) | About $10 per variant |
| Retrieval-only metrics | Free |

**Done when:**
- the baseline has a full set of scores per question type;
- its failures have been examined by hand to see where they come from: retrieval, answering or the question itself;
- a short write-up says which Phase 5 improvements to try.

**Result (done):**
- 150 questions (from 207 candidates; $7.89).
- Baseline: 81% correct, 15% partial, 97% of cited claims supported, about $0.03 and 4 seconds per question.
- Weakest: multi-hop questions (56% correct), because the second hop isn't retrieved. Next weakest: scenario questions (73%).
- Full results, the judge check and the Phase 5 recommendations are in [../../sandbox/baseline-evaluation.md](../../sandbox/baseline-evaluation.md). Flagged questions are in `sandbox/eval-questions-flagged.md`.

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
