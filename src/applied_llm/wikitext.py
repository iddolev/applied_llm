"""Convert MediaWiki wikitext into plain-text sections."""

import re
from dataclasses import asdict, dataclass

import mwparserfromhell as mw
from mwparserfromhell.nodes import Heading, Tag, Wikilink

# Trailing reference/navigation sections that carry no article content.
BOILERPLATE_SECTIONS = {
    "see also",
    "references",
    "notes",
    "notes and references",
    "footnotes",
    "citations",
    "sources",
    "bibliography",
    "works cited",
    "further reading",
    "external links",
}

_NON_TEXT_LINK_PREFIXES = ("file:", "image:", "media:", "category:")


@dataclass
class Section:
    heading: str  # "" for the lead section
    level: int  # 1 for the lead, otherwise the wikitext heading level (== is 2)
    text: str

    def to_dict(self) -> dict:
        return asdict(self)


def _remove_non_text(code: mw.wikicode.Wikicode) -> None:
    """Remove images, categories and tables, which strip_code would otherwise mangle into text."""
    for node in code.filter(recursive=True, forcetype=(Wikilink, Tag)):
        if isinstance(node, Wikilink):
            if str(node.title).strip().lower().startswith(_NON_TEXT_LINK_PREFIXES):
                _safe_replace(code, node, "")
        elif node.wiki_markup == "{|" or str(node.tag).lower() == "table":
            _safe_replace(code, node, "")
        elif str(node.tag).lower() == "math" and node.contents is not None:
            # strip_code drops <math> entirely; keep the LaTeX so formulas aren't lost.
            _safe_replace(code, node, f" {str(node.contents).strip()} ")


def _safe_replace(code: mw.wikicode.Wikicode, node, value: str) -> None:
    try:
        code.replace(node, value)
    except ValueError:
        pass  # already removed as part of an enclosing node


def _to_text(code: mw.wikicode.Wikicode) -> str:
    text = code.strip_code(normalize=True, collapse=True)
    # Malformed tables can survive parsing; drop their leftover markup lines.
    text = re.sub(r"^\s*(\{\||\|\}|\|-).*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def wikitext_to_sections(wikitext: str) -> list[Section]:
    """Split an article into its lead and sections, dropping boilerplate sections."""
    code = mw.parse(wikitext)
    sections: list[Section] = []
    skip_below_level: int | None = None

    for sec in code.get_sections(flat=True, include_lead=True):
        headings = sec.filter_headings(recursive=False)
        if headings and sec.nodes and isinstance(sec.nodes[0], Heading):
            heading_node = headings[0]
            heading = heading_node.title.strip_code().strip()
            level = heading_node.level
            sec.remove(heading_node)
        else:
            heading, level = "", 1

        # Skip boilerplate sections together with any of their subsections.
        if skip_below_level is not None:
            if level > skip_below_level:
                continue
            skip_below_level = None
        if heading.lower() in BOILERPLATE_SECTIONS:
            skip_below_level = level
            continue

        _remove_non_text(sec)
        text = _to_text(sec)
        if text or heading:
            sections.append(Section(heading=heading, level=level, text=text))

    return sections
