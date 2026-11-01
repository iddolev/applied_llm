"""Decide which Wikipedia articles belong in the corpus.

Two passes:
  1. `prefilter` drops articles whose Wikidata types make them clearly out of scope
     (people, works, list pages, organizations and events), before we download them.
  2. `ArticleClassifier` asks Claude Haiku to label each remaining article from its
     title, Wikidata types and lead paragraph; only some labels are kept.
"""

import logging
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from enum import Enum

import anthropic
from pydantic import BaseModel

log = logging.getLogger(__name__)

CLASSIFIER_MODEL = "claude-haiku-5-5"

_LIST_TITLE = re.compile(r"^((List|Index|Outline|Glossary|Timeline) of |\d{3,4}s? in )")

# Patterns over Wikidata P31 labels, checked in order; the first match decides.
_EXCLUDED_TYPES = [
    ("list", r"wikimedia|events in a specific year"),
    ("person", r"^human$|group of humans"),
    ("work", r"(literary|written|philosophical|creative) work|work of art|\b(book|dialogue|upanishads?"
             r"|journal|treatise|essay|poem|novel|film|periodical|magazine|sutra|scripture"
             r"|encyclopedia|website|podcast)\b"),
    ("organization/event", r"\b(organization|institution|university|conference|award|city|country"
                           r"|genocide|war|event)\b"),
]


def prefilter(title: str, types: list[str]) -> str | None:
    """Return the reason to exclude an article, or None if it is a candidate."""
    if _LIST_TITLE.match(title):
        return "list"
    for reason, pattern in _EXCLUDED_TYPES:
        if any(re.search(pattern, t.lower()) for t in types):
            return reason
    return None


class Category(str, Enum):
    concept_or_problem = "concept_or_problem"
    philosophical_position = "philosophical_position"
    discipline = "discipline"
    ideology_or_movement = "ideology_or_movement"
    history_or_survey = "history_or_survey"
    person = "person"
    work = "work"
    other = "other"


KEPT_CATEGORIES = {Category.concept_or_problem, Category.philosophical_position, Category.discipline}


class Classification(BaseModel):
    category: Category


SYSTEM_PROMPT = """\
You classify Wikipedia articles for a corpus about philosophical ideas. Pick the single best category:

- concept_or_problem: a philosophical concept, distinction, problem, paradox, argument, thought \
experiment, principle, fallacy or rule of inference (e.g. "Moral luck", "Liar paradox", \
"Teleological argument", "Noumenon", "Modus ponens").
- philosophical_position: a philosophical view, theory or school of thought defined by its \
claims (e.g. "Eliminative materialism", "Externalism", "Utilitarianism", "Phenomenology (philosophy)").
- discipline: a branch or subfield of philosophy or of logic (e.g. "Epistemology", "Metaethics", \
"Modal logic", "Philosophy of science").
- ideology_or_movement: a political ideology, religious movement or cultural/social movement \
(e.g. "Neoliberalism", "Hindutva", "Modernism", "Environmentalism").
- history_or_survey: the history of a field, a period of thought or a regional tradition as a \
whole (e.g. "History of ethics", "Contemporary philosophy", "Ancient Egyptian philosophy").
- person: an individual or group of people.
- work: a specific book, essay, dialogue, scripture, journal or other publication.
- other: anything else, including everyday topics only loosely related to philosophy \
(e.g. "Hanging", "Organization").

Judge by what the article is about, not by its title alone."""


def _user_message(title: str, types: list[str], lead: str) -> str:
    return (
        f"Title: {title}\n"
        f"Wikidata types: {', '.join(types) if types else '(none)'}\n\n"
        f"Lead section:\n{lead[:2000]}"
    )


class ArticleClassifier:
    def __init__(self, model: str = CLASSIFIER_MODEL, max_workers: int = 8):
        self._client = anthropic.Anthropic(max_retries=5)
        self._model = model
        self._max_workers = max_workers

    def classify(self, title: str, types: list[str], lead: str) -> Category | None:
        """Return the article's category, or None if Claude declined to answer."""
        response = self._client.messages.parse(
            model=self._model,
            max_tokens=2048,
            output_config={"effort": "low"},
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": _user_message(title, types, lead)}],
            output_format=Classification,
        )
        if response.stop_reason == "refusal" or response.parsed_output is None:
            log.warning("No classification for %r (stop_reason=%s)", title, response.stop_reason)
            return None
        return response.parsed_output.category

    def classify_many(self, items: list[tuple[str, list[str], str]]):
        """Classify (title, types, lead) items concurrently, yielding (title, category) as they finish."""
        with ThreadPoolExecutor(self._max_workers) as pool:
            futures = {pool.submit(self.classify, *item): item[0] for item in items}
            for future in as_completed(futures):
                title = futures[future]
                yield title, future.result()
