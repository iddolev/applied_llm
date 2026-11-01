"""Generate and validate evaluation questions from the corpus.

For each question type, `sample_seeds` picks the passages a question is written from:

  lookup      one random chunk
  scenario    the first chunks of a concept or position article (gold: the whole article)
  multihop    a chunk of article A that mentions article B, plus B's lead
  broad       several chunks of a section about criticisms, types, arguments, ... and its subsections
  negation    a chunk saying who rejected, opposed or influenced what
  unanswerable  a lead chunk, as the area for a question the corpus can't answer

Claude Opus writes a question and reference answer from each seed, naming the passages it
needs (these become the gold sections). A second call validates the question against only
those passages; an unanswerable question is instead checked against the top 50 retrieved
chunks, none of which may answer it.
"""

import random
import re
from collections import defaultdict
from dataclasses import dataclass, field

import anthropic
from pydantic import BaseModel, Field

from applied_llm.chunking import HEADING_SEPARATOR, Chunk
from applied_llm.evaluation import EVAL_MODEL, structured_call

QUESTION_TYPES = ["lookup", "scenario", "multihop", "broad", "negation", "unanswerable"]

_BROAD_HEADING = re.compile(
    r"critic|objection|respons|debate|argument|types|varieties|kinds|forms|schools|approaches|theories|views|"
    r"problems|interpretations",
    re.IGNORECASE,
)
_RELATION = re.compile(
    r"\b(rejected|rejects|denied|denies|opposed|opposes|criticized|criticised|argued against|disagreed|"
    r"influenced|did not|does not|unlike|contrary to)\b",
    re.IGNORECASE,
)


@dataclass
class Seed:
    type: str
    passages: list[Chunk]
    # Gold items for passages the generator says it used: the passage's section, or the whole
    # article for scenario questions.
    article_level_gold: bool = False
    note: str = ""


@dataclass
class Corpus:
    chunks: list[Chunk]
    categories: dict[str, str]  # title -> category
    by_article: dict[str, list[Chunk]] = field(init=False)

    def __post_init__(self):
        self.by_article = defaultdict(list)
        for c in self.chunks:
            self.by_article[c.title].append(c)


def _words(chunk: Chunk) -> int:
    return len(chunk.text.split())


def sample_seeds(corpus: Corpus, qtype: str, n: int, rng: random.Random) -> list[Seed]:
    """Sample n seeds of a type, each from a different article."""
    seeds: list[Seed] = []
    used: set[str] = set()

    def add(seed: Seed) -> None:
        seeds.append(seed)
        used.update(p.title for p in seed.passages)

    if qtype in ("lookup", "negation"):
        pool = [c for c in corpus.chunks if _words(c) >= 100]
        if qtype == "negation":
            pool = [c for c in pool if _RELATION.search(c.text)]
        for c in rng.sample(pool, len(pool)):
            if len(seeds) == n:
                break
            if c.title not in used:
                add(Seed(qtype, [c]))

    elif qtype in ("scenario", "unanswerable"):
        kept = {"concept_or_problem", "philosophical_position"} if qtype == "scenario" else None
        titles = [t for t in corpus.by_article if kept is None or corpus.categories.get(t) in kept]
        for title in rng.sample(titles, len(titles)):
            if len(seeds) == n:
                break
            chunks = corpus.by_article[title]
            if qtype == "scenario":
                add(Seed(qtype, chunks[:3], article_level_gold=True))
            else:
                add(Seed(qtype, chunks[:1]))

    elif qtype == "multihop":
        # Titles of at least two words, so mentions are specific ("Moral luck", not "Logic").
        titles = sorted((t for t in corpus.by_article if " " in t and "(" not in t), key=len, reverse=True)
        pattern = re.compile(r"\b(" + "|".join(re.escape(t) for t in titles) + r")\b", re.IGNORECASE)
        canonical = {t.lower(): t for t in titles}
        pool = [c for c in corpus.chunks if _words(c) >= 80]
        for c in rng.sample(pool, len(pool)):
            if len(seeds) == n:
                break
            mentioned = {canonical[m.lower()] for m in pattern.findall(c.text)} - {c.title}
            mentioned = [t for t in mentioned if t not in used]
            if c.title in used or not mentioned:
                continue
            other = rng.choice(sorted(mentioned))
            add(Seed(qtype, [c, corpus.by_article[other][0]], note=f"{c.title} mentions {other}"))

    elif qtype == "broad":
        # Sections whose heading matches, with their subsections, spanning at least 3 chunks.
        groups: dict[tuple[str, tuple[str, ...]], list[Chunk]] = defaultdict(list)
        for c in corpus.chunks:
            for depth in range(2, len(c.heading_path) + 1):
                if _BROAD_HEADING.search(c.heading_path[depth - 1]):
                    groups[(c.title, tuple(c.heading_path[:depth]))].append(c)
                    break
        candidates = [(k, v) for k, v in groups.items() if len(v) >= 3]
        for (title, path), chunks in rng.sample(candidates, len(candidates)):
            if len(seeds) == n:
                break
            if title in used:
                continue
            step = max(1, len(chunks) // 8)
            add(Seed(qtype, chunks[::step][:8], note=HEADING_SEPARATOR.join(path)))

    else:
        raise ValueError(qtype)
    return seeds


GENERATION_SYSTEM = """\
You write questions for evaluating a question-answering system over a corpus of English \
Wikipedia articles about philosophical concepts, problems, positions and disciplines (no \
biographies, books or history surveys). The system retrieves passages from the corpus and \
answers from them. You get numbered source passages and instructions for one question type.

General rules:
- The question must read like a natural question from a curious, educated user, and be \
self-contained: never refer to "the passage", "the text" or "the article".
- Paraphrase. Don't copy distinctive phrases from the passages; a user wouldn't know the \
article's wording. Using the standard name of a topic is fine where the type allows it.
- The question must have a clear answer that the passages support, unless the type says otherwise.
- The reference answer must be short (1-4 sentences, or key points for broad questions) and \
supported by the passages.
- used_passages lists the passage numbers the answer relies on.
- If the passages are unsuitable for this question type (fragments, lists of names, \
formulas only, off-topic), set skip to true and explain why in skip_reason."""

TYPE_INSTRUCTIONS = {
    "lookup": "Type: lookup. Ask for one specific fact stated in the passage (who, what, when, "
              "which, why). The answer should be a fact, not a summary of the whole passage.",
    "scenario": "Type: scenario. Describe one concrete situation (everyday or hypothetical) in 2-4 "
                "sentences and ask a question about it whose answer needs the concept or position "
                "these passages describe. Do NOT name the concept, the article's title, or its "
                "distinctive terms, and don't list the doctrine's tenets: a person in the situation "
                "wouldn't know the theory, only what happened. The reference answer names the "
                "concept and explains how it applies.",
    "multihop": "Type: multi-hop. Write a question that can only be answered by combining a fact "
                "from passage 1 with a fact from passage 2. Ideally refer to passage 2's topic "
                "indirectly, through its relation to passage 1 (e.g. 'the view that X criticized'), "
                "so that a reader must first work out what passage 2 is about. used_passages "
                "must be [1, 2].",
    "broad": "Type: broad. Ask a broad question whose full answer needs most of the passages, e.g. "
             "'What are the main objections to X?' or 'What kinds of X are there?'. Give the "
             "reference answer as key_points: 4-8 distinct points, each from the passages.",
    "negation": "Type: negation or relation. Ask about who rejected, opposed, influenced or "
                "differed from whom or what, phrased so that swapping the roles or dropping a "
                "'not' would change the answer (e.g. 'Which view of X did Y reject?').",
    "unanswerable": "Type: unanswerable. Write a realistic question in the same area as the "
                    "passage that this corpus is unlikely to answer, e.g. a biographical detail of "
                    "a philosopher, a publication date, or a specific fact the article doesn't "
                    "cover. It must have a real answer in the world (no false premises or "
                    "nonsense). reference_answer: what a correct answer would need; "
                    "used_passages: [].",
}


class GeneratedQuestion(BaseModel):
    skip: bool = Field(description="True if the passages are unsuitable for this question type.")
    skip_reason: str
    question: str
    reference_answer: str
    key_points: list[str] = Field(description="For broad questions only; otherwise empty.")
    used_passages: list[int]


class Validation(BaseModel):
    answerable: bool = Field(description="The passages fully answer the question.")
    unambiguous: bool = Field(description="The question has one clear intended answer.")
    self_contained: bool = Field(description="It reads naturally without seeing the passages.")
    copies_wording: bool = Field(description="It copies distinctive phrases from the passages.")
    reference_correct: bool = Field(description="The reference answer is correct per the passages.")
    matches_type: bool = Field(description="It fits the intended question type.")
    problems: str = Field(description="Short description of any problem; empty if none.")


class UnanswerableCheck(BaseModel):
    answering_passages: list[int] = Field(description="Passages that answer the question, fully or mostly.")
    realistic: bool = Field(description="A realistic question with a real answer, without false premises.")
    problems: str


VALIDATION_SYSTEM = """\
You check questions written for evaluating a question-answering system over Wikipedia \
articles about philosophy. You get the intended question type, the question, its reference \
answer and the source passages it was written from. Judge strictly; a flawed question \
makes the evaluation misleading."""

UNANSWERABLE_SYSTEM = """\
You check a question meant to be unanswerable from a corpus of Wikipedia articles about \
philosophy. You get the question and the 50 passages a search engine retrieved for it. List \
the passages that answer it fully or mostly (an answer the question asks for, stated in the \
passage); passages that are merely on the same topic don't count."""


def format_passages(passages: list[Chunk]) -> str:
    return "\n\n".join(
        f'<passage id="{i}" location="{HEADING_SEPARATOR.join(c.heading_path)}">\n{c.text}\n</passage>'
        for i, c in enumerate(passages, 1)
    )


def generate(client: anthropic.Anthropic, seed: Seed) -> tuple[GeneratedQuestion | None, dict]:
    user = f"{TYPE_INSTRUCTIONS[seed.type]}\n\n<passages>\n{format_passages(seed.passages)}\n</passages>"
    return structured_call(client, EVAL_MODEL, GENERATION_SYSTEM, user, GeneratedQuestion)


def validate(client: anthropic.Anthropic, qtype: str, gen: GeneratedQuestion,
             passages: list[Chunk]) -> tuple[Validation | None, dict]:
    reference = gen.reference_answer + ("\nKey points:\n- " + "\n- ".join(gen.key_points) if gen.key_points else "")
    user = (f"Intended type: {TYPE_INSTRUCTIONS[qtype]}\n\n<question>{gen.question}</question>\n"
            f"<reference_answer>{reference}</reference_answer>\n\n"
            f"<passages>\n{format_passages(passages)}\n</passages>")
    return structured_call(client, EVAL_MODEL, VALIDATION_SYSTEM, user, Validation)


def check_unanswerable(client: anthropic.Anthropic, question: str,
                       retrieved: list[Chunk]) -> tuple[UnanswerableCheck | None, dict]:
    user = f"<question>{question}</question>\n\n<passages>\n{format_passages(retrieved)}\n</passages>"
    return structured_call(client, EVAL_MODEL, UNANSWERABLE_SYSTEM, user, UnanswerableCheck)


_STOPWORDS = set("""a about above after again against all also although among an and any are as at be because been
before being between both but by can could did do does doing during each either few for from further had has have
having he her here hers him his how however i if in into is it its itself just many may might more most much must
my no nor not of off on once one only or other our out over own same she should so some such than that the their
them then there these they this those through to too under until up upon very was we were what when where whether
which while who whom whose why will with within without would you your""".split())


def content_words(text: str) -> set[str]:
    return {w for w in re.findall(r"[a-z]+", text.lower()) if len(w) >= 4 and w not in _STOPWORDS}


def word_overlap(question: str, passages: list[Chunk]) -> float:
    """Share of the question's content words that also occur in the passages."""
    q = content_words(question)
    if not q:
        return 0.0
    text = content_words(" ".join(p.text for p in passages))
    return len(q & text) / len(q)
