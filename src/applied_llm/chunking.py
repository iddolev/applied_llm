"""Split cleaned article sections into retrieval-sized chunks.

Each chunk keeps the path of headings above it (e.g. ["Moral luck", "Criticism"]), which is
put in front of its text when the chunk is embedded or shown to an LLM, so that a chunk
starting "Nagel rejects this..." still says what it is about.
"""

import math
import re
from collections import Counter
from collections.abc import Callable
from dataclasses import asdict, dataclass
from urllib.parse import quote

from applied_llm.wikipedia import article_url
from applied_llm.wikitext import Section

HEADING_SEPARATOR = " › "

# A sentence ends at . ! or ? (optionally followed by a closing quote or bracket) before
# whitespace and an uppercase letter, digit or opening quote/bracket.
_SENTENCE_END = re.compile(r"""(?<=[.!?])["'”’)\]]?\s+(?=["'“‘(\[]?[A-Z0-9])""")
# Abbreviations after which a period doesn't end the sentence.
_ABBREVIATION = re.compile(
    r"\b(e\.g|i\.e|cf|vs|etc|al|St|Dr|Mr|Mrs|Ms|Prof|Jr|Sr|ca|c|vol|no|pp?|ch|ed|eds|trans|[A-Z])\.$"
)


@dataclass
class Chunk:
    chunk_id: str
    title: str
    article_id: int
    section_index: int
    part: int
    heading_path: list[str]
    text: str
    url: str

    def to_dict(self) -> dict:
        return asdict(self)

    @property
    def context_text(self) -> str:
        """The text to embed or show to an LLM: the heading path, a blank line, then the chunk text."""
        return f"{HEADING_SEPARATOR.join(self.heading_path)}\n\n{self.text}"


@dataclass
class _Block:
    """A section (possibly with short neighbours merged in) before it is split."""

    section_index: int
    heading_path: list[str]
    anchor: str | None
    text: str


def count_words(text: str) -> int:
    return len(text.split())


def section_anchor(heading: str, seen: Counter) -> str:
    """Wikipedia's anchor for a heading; repeated headings get _2, _3, ... like on Wikipedia."""
    anchor = heading.replace(" ", "_")
    seen[anchor] += 1
    return anchor if seen[anchor] == 1 else f"{anchor}_{seen[anchor]}"


def section_url(title: str, anchor: str | None) -> str:
    url = article_url(title)
    return f"{url}#{quote(anchor, safe=":/,;()!*@$&+=~._-'")}" if anchor else url


def split_sentences(paragraph: str) -> list[str]:
    """Split a paragraph into sentences, rejoining splits made after common abbreviations."""
    sentences: list[str] = []
    for part in _SENTENCE_END.split(paragraph):
        if sentences and _ABBREVIATION.search(sentences[-1]):
            sentences[-1] = f"{sentences[-1]} {part}"
        else:
            sentences.append(part)
    return [s for s in sentences if s.strip()]


def _units(text: str, max_words: int) -> list[tuple[str, bool]]:
    """Split text into (sentence, ends_paragraph) units no longer than max_words each."""
    units = []
    for paragraph in text.split("\n"):
        sentences = split_sentences(paragraph.strip())
        for i, sentence in enumerate(sentences):
            words = sentence.split()
            # A "sentence" longer than a whole chunk (e.g. a run-on list) is cut into word windows.
            pieces = [" ".join(words[j : j + max_words]) for j in range(0, len(words), max_words)]
            for k, piece in enumerate(pieces):
                units.append((piece, i == len(sentences) - 1 and k == len(pieces) - 1))
    return units


def split_text(text: str, max_words: int, overlap_words: int) -> list[str]:
    """Split text into pieces of about equal size, at most max_words each, overlapping by whole sentences.

    Pieces end at paragraph boundaries where that doesn't make them much shorter than the
    target size, otherwise at sentence boundaries.
    """
    total = count_words(text)
    if total <= max_words:
        return [text]
    n_pieces = math.ceil((total - overlap_words) / (max_words - overlap_words))
    target = min(max_words, math.ceil((total - overlap_words) / n_pieces) + overlap_words)

    units = _units(text, max_words)
    pieces: list[str] = []
    start = 0
    while start < len(units):
        if sum(count_words(u[0]) for u in units[start:]) <= max_words:
            pieces.append(_join_units(units[start:]))  # the rest fits, so don't leave a small tail
            break
        # Take sentences until the next one would pass max_words (always at least one).
        end, words, last_paragraph_end = start, 0, None
        while end < len(units):
            n = count_words(units[end][0])
            if end > start and words + n > max_words:
                break
            words += n
            end += 1
            if units[end - 1][1] and words >= 0.7 * target:
                last_paragraph_end = end
            if words >= target:
                break
        if end < len(units) and last_paragraph_end is not None:
            end = last_paragraph_end
        pieces.append(_join_units(units[start:end]))
        if end >= len(units):
            break
        # Start the next piece with the last sentences of this one, up to overlap_words.
        next_start, overlap = end, 0
        while next_start - 1 > start and overlap + count_words(units[next_start - 1][0]) <= overlap_words:
            next_start -= 1
            overlap += count_words(units[next_start][0])
        start = next_start
    return pieces


def _join_units(units: list[tuple[str, bool]]) -> str:
    out = []
    for sentence, ends_paragraph in units:
        out.append(sentence)
        out.append("\n" if ends_paragraph else " ")
    return "".join(out).strip()


def _blocks(title: str, sections: list[Section], min_words: int) -> list[_Block]:
    """Turn sections into blocks: drop empty ones and merge short ones into a neighbour."""
    seen_anchors: Counter = Counter()
    path: list[tuple[int, str]] = []  # (level, heading) of the current section and its parents
    nonempty: list[_Block] = []
    for i, sec in enumerate(sections):
        if sec.level == 1:
            path, anchor = [], None
        else:
            path = [p for p in path if p[0] < sec.level] + [(sec.level, sec.heading)]
            anchor = section_anchor(sec.heading, seen_anchors)
        if sec.text:  # sections without text only contribute their heading to their subsections' paths
            nonempty.append(_Block(i, [title] + [h for _, h in path], anchor, sec.text))

    blocks: list[_Block] = []
    pending: list[_Block] = []  # short blocks waiting to be merged into the next block
    for i, block in enumerate(nonempty):
        if count_words(block.text) >= min_words:
            if pending:
                block.text = "\n".join([p.text for p in pending] + [block.text])
                pending = []
            blocks.append(block)
            continue
        nxt = nonempty[i + 1] if i + 1 < len(nonempty) else None
        is_parent_of_next = (
            nxt is not None
            and len(nxt.heading_path) > len(block.heading_path)
            and nxt.heading_path[: len(block.heading_path)] == block.heading_path
        )
        if is_parent_of_next or pending or (not blocks and nxt is not None):
            pending.append(block)
        elif blocks:
            blocks[-1].text += f"\n{block.heading_path[-1]}\n{block.text}"
        else:
            blocks.append(block)  # the article's only text is short
    if pending:
        if blocks:
            for p in pending:
                blocks[-1].text += f"\n{p.heading_path[-1]}\n{p.text}"
        else:
            blocks.extend(pending)
    return blocks


def _fit_tokens(
    text: str,
    prefix: str,
    max_words: int,
    overlap_words: int,
    count_tokens: Callable[[str], int] | None,
    max_tokens: int,
) -> list[str]:
    """Split text by words, then split again any piece whose prefix + text has more than max_tokens.

    Words are a poor proxy for tokens in formulas: LaTeX can take five tokens per word.
    """
    pieces = split_text(text, max_words, overlap_words)
    if count_tokens is None:
        return pieces
    fitted = []
    for piece in pieces:
        n_tokens, n_words = count_tokens(prefix + piece), count_words(piece)
        if n_tokens <= max_tokens or n_words <= 20:
            fitted.append(piece)
            continue
        smaller = max(20, int(n_words * max_tokens / n_tokens * 0.9))
        fitted += _fit_tokens(piece, prefix, smaller, min(overlap_words, smaller // 5), count_tokens, max_tokens)
    return fitted


def chunk_article(
    title: str,
    article_id: int,
    sections: list[Section],
    max_words: int = 300,
    overlap_words: int = 50,
    min_words: int = 30,
    count_tokens: Callable[[str], int] | None = None,
    max_tokens: int = 450,
) -> list[Chunk]:
    """Split an article's sections into chunks.

    If count_tokens is given, chunks are also kept within max_tokens, counting the heading path.
    """
    chunks = []
    for block in _blocks(title, sections, min_words):
        prefix = f"{HEADING_SEPARATOR.join(block.heading_path)}\n\n"
        pieces = _fit_tokens(block.text, prefix, max_words, overlap_words, count_tokens, max_tokens)
        for part, text in enumerate(pieces):
            chunks.append(
                Chunk(
                    chunk_id=f"{title.replace(' ', '_')}#{len(chunks)}",
                    title=title,
                    article_id=article_id,
                    section_index=block.section_index,
                    part=part,
                    heading_path=block.heading_path,
                    text=text,
                    url=section_url(title, block.anchor),
                )
            )
    return chunks
