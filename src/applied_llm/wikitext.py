"""Convert MediaWiki wikitext into plain-text sections."""

import re
from dataclasses import asdict, dataclass

import mwparserfromhell as mw
from mwparserfromhell.nodes import Heading, Tag, Template, Wikilink

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

# Footnotes, removed before parsing: a malformed one (e.g. "<ref><ref>...</ref>") can make the
# parser swallow the rest of the article, headings included.
_REF = re.compile(r"<ref[^>]*/>|<ref(?:\s[^>]*)?>.*?</ref\s*>", re.DOTALL | re.IGNORECASE)
# Italic/bold quotes, left in the text because style tags aren't parsed (see wikitext_to_sections).
_STYLE_QUOTES = re.compile(r"'{2,}")


@dataclass
class Section:
    heading: str  # "" for the lead section
    level: int  # 1 for the lead, otherwise the wikitext heading level (== is 2)
    text: str

    def to_dict(self) -> dict:
        return asdict(self)


def _remove_non_text(code: mw.wikicode.Wikicode) -> None:
    """Remove images, categories, tables and footnotes, which strip_code would otherwise mangle into text."""
    for node in code.filter(recursive=True, forcetype=(Wikilink, Tag)):
        if isinstance(node, Wikilink):
            if str(node.title).strip().lower().startswith(_NON_TEXT_LINK_PREFIXES):
                _safe_replace(code, node, "")
        elif node.wiki_markup == "{|" or str(node.tag).lower() in ("table", "ref"):
            # Footnotes (<ref>) would otherwise leave citation text in the middle of sentences.
            _safe_replace(code, node, "")
        elif str(node.tag).lower() == "math" and node.contents is not None:
            # strip_code drops <math> entirely; keep the LaTeX so formulas aren't lost.
            _safe_replace(code, node, f" {str(node.contents).strip()} ")


def _positional(t: Template) -> list[str]:
    params = [p for p in t.params if str(p.name).strip().isdigit()]
    return [str(p.value).strip() for p in sorted(params, key=lambda p: int(str(p.name)))]


def _arg(t: Template, *keys: str) -> str:
    """The value of the first of `keys` the template has ("1" is the first positional parameter)."""
    for key in keys:
        if t.has(key):
            return str(t.get(key).value).strip()
    return ""


def _quote(t: Template) -> str:
    text = _arg(t, "text", "quote", "2" if _normalize(t) == "rquote" else "1")
    return f"\n{text}\n" if text else ""


# Templates whose rendered text is part of the article; strip_code drops every template, so
# these are replaced by their text first. Citation, maintenance and navigation templates are
# still dropped.
_FIXED_TEXT = {
    "snd": " – ", "spaced ndash": " – ", "ndash": "–", "en dash": "–", "mdash": "—", "em dash": "—",
    "nbsp": " ", "nbs": " ", "spaces": " ", "'": "'", "'\"": "'\"", "\"'": "\"'", "' \"": "' \"", "-\"": "\"",
}
_FIRST_ARG = {
    "annotated link", "anl", "anli", "iast", "mvar", "var", "math", "tmath", "em", "nowrap", "nobr", "small",
    "sc", "sub", "sup", "mono", "lit", "not a typo", "ill", "interlanguage link", "grc-transl", "val",
    "section link", "slink",
}
_SECOND_ARG = {"lang", "langx", "wikt-lang"}
_LAST_ARG = {"transliteration", "transl", "translit", "tlit"}
_QUOTES = {"blockquote", "quote", "quotation", "cquote", "rquote", "quote frame", "poem quote", "verse translation"}
_CHINESE = {"zh", "zhi", "zhp", "lang-zh", "cjkv"}
_CHINESE_KEYS = ("c", "t", "s", "p", "tp", "w", "j", "cy", "poj", "l")


def _normalize(t: Template) -> str:
    return str(t.name).strip().lower().replace("_", " ").removeprefix("template:")


def _template_text(t: Template) -> str | None:
    """The text a content-bearing template renders as, or None to drop the template."""
    name = _normalize(t)
    if name in _FIXED_TEXT:
        return _FIXED_TEXT[name]
    if name in _FIRST_ARG:
        return _arg(t, "1")
    if name in _SECOND_ARG:
        return _arg(t, "2", "text")
    if name in _LAST_ARG:
        args = _positional(t)
        return args[-1] if args else ""
    if name in _QUOTES:
        return _quote(t)
    if name == "quote box":
        return f"\n{_arg(t, 'quote')}\n"
    if name in _CHINESE:
        return " ".join(_arg(t, k) for k in _CHINESE_KEYS if _arg(t, k))
    if name.startswith("lang-"):  # e.g. {{lang-de|Weltanschauung}}
        return _arg(t, "1")
    if name == "gloss":
        return f"‘{_arg(t, '1')}’"
    if name == "nihongo":
        english, _, romaji = (_positional(t) + ["", "", ""])[:3]
        return f"{english} ({romaji})" if romaji else english
    if name == "circa":
        return f"c. {_arg(t, '1')}".strip()
    if name in ("bce", "ce"):
        return f"{_arg(t, '1')} {name.upper()}"
    if name == "sfrac":
        args = _positional(t)
        return "/".join(args[-2:]) if len(args) >= 2 else "".join(args)
    if name == "convert":
        return " ".join(_positional(t)[:2])
    if name == "as of":
        return f"As of {_arg(t, '1')}"
    if name in ("bibleverse", "bibleref", "sic", "linktext"):
        return (" " if name != "linktext" else "").join(_positional(t))
    if name == "mset":
        return f"{{{', '.join(_positional(t))}}}"
    if t.has("text"):  # inline cleanup tags wrap article text, e.g. {{clarify|text=...|reason=...}}
        return _arg(t, "text")
    return None


def _expand_templates(code: mw.wikicode.Wikicode) -> None:
    # Innermost first, so a template nested in another's argument is expanded before the outer
    # one copies that argument.
    for t in reversed(code.filter_templates(recursive=True)):
        text = _template_text(t)
        if text is not None:
            _safe_replace(code, t, text)


def _safe_replace(code: mw.wikicode.Wikicode, node, value: str) -> None:
    try:
        code.replace(node, value)
    except ValueError:
        pass  # already removed as part of an enclosing node


def _to_text(code: mw.wikicode.Wikicode) -> str:
    text = _STYLE_QUOTES.sub("", code.strip_code(normalize=True, collapse=True))
    # Malformed tables can survive parsing; drop their leftover markup lines.
    text = re.sub(r"^\s*(\{\||\|\}|\|-).*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def wikitext_to_sections(wikitext: str) -> list[Section]:
    """Split an article into its lead and sections, dropping boilerplate sections."""
    # Unbalanced italic or bold quotes make mwparserfromhell nest every later heading inside a
    # style tag, merging the rest of the article into one section. So style tags aren't parsed,
    # and their quotes are removed from the text instead.
    code = mw.parse(_REF.sub("", wikitext), skip_style_tags=True)
    sections: list[Section] = []
    skip_below_level: int | None = None

    for sec in code.get_sections(flat=True, include_lead=True):
        headings = sec.filter_headings(recursive=False)
        if headings and sec.nodes and isinstance(sec.nodes[0], Heading):
            heading_node = headings[0]
            heading = _STYLE_QUOTES.sub("", heading_node.title.strip_code()).strip()
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
        _expand_templates(sec)
        text = _to_text(sec)
        if text or heading:
            sections.append(Section(heading=heading, level=level, text=text))

    return sections
