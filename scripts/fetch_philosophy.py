"""Build a corpus of English Wikipedia articles on philosophical concepts, positions and disciplines.

Resumable stages, each writing into the output directory:

  1. candidates.jsonl  articles rated Top/High/Mid importance by WikiProject Philosophy, with their
                       Wikidata types; people, works, lists and organizations are marked excluded
  2. raw.jsonl         raw wikitext of the non-excluded candidates (appended to; resumable)
  3. labels.jsonl      Claude Haiku's category for each candidate (appended to; resumable)
  4. articles.jsonl    cleaned, sectioned articles whose category is kept (rebuilt every run)

Stage 3 needs Anthropic credentials (ANTHROPIC_API_KEY, in the environment or .env); without them the script stops after stage 2.

Usage:
  uv run scripts/fetch_philosophy.py
  uv run scripts/fetch_philosophy.py --importance Top High Mid Low
"""

import argparse
import json
import logging
import os
from collections import Counter
from pathlib import Path

from dotenv import load_dotenv
from tqdm import tqdm

from applied_llm.selection import KEPT_CATEGORIES, ArticleClassifier, prefilter
from applied_llm.wikidata import instance_of_labels
from applied_llm.wikipedia import WikipediaClient, article_url
from applied_llm.wikitext import wikitext_to_sections

log = logging.getLogger("fetch_philosophy")


def read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f]


def build_candidates(client: WikipediaClient, path: Path, importances: list[str], refresh: bool) -> list[dict]:
    if path.exists() and not refresh:
        candidates = read_jsonl(path)
        log.info("Loaded %d candidates from %s", len(candidates), path)
        return candidates

    importance: dict[str, str] = {}
    for level in importances:
        for title in client.articles_with_talk_category(f"{level}-importance Philosophy articles"):
            importance.setdefault(title, level)
    log.info("Found %d articles rated %s importance", len(importance), "/".join(importances))

    qids = client.wikidata_ids(importance)
    types = instance_of_labels(qids.values())

    candidates = []
    for title in sorted(importance):
        qid = qids.get(title)
        title_types = types.get(qid, []) if qid else []
        candidates.append(
            {
                "title": title,
                "importance": importance[title],
                "qid": qid,
                "types": title_types,
                "excluded": prefilter(title, title_types),
            }
        )
    with path.open("w", encoding="utf-8") as out:
        for c in candidates:
            out.write(json.dumps(c, ensure_ascii=False) + "\n")
    log.info("Wrote %s: %s", path, dict(Counter(c["excluded"] or "candidate" for c in candidates)))
    return candidates


def fetch_raw(client: WikipediaClient, titles: list[str], path: Path) -> None:
    done = {rec["requested_title"] for rec in read_jsonl(path)}
    todo = [t for t in titles if t not in done]
    log.info("%d articles already fetched, %d to go", len(titles) - len(todo), len(todo))
    if not todo:
        return

    with path.open("a", encoding="utf-8") as out, tqdm(total=len(todo), unit="article") as bar:
        batch_size = 50
        for i in range(0, len(todo), batch_size):
            chunk = todo[i : i + batch_size]
            fetched = {rec["title"]: rec for rec in client.fetch_wikitext(chunk)}
            for requested in chunk:
                # Missing pages and redirects are recorded too, so they aren't re-requested.
                rec = fetched.pop(requested, None)
                entry = {"requested_title": requested, **rec} if rec else {"requested_title": requested}
                out.write(json.dumps(entry, ensure_ascii=False) + "\n")
            # Whatever is left came back under a redirect target's title.
            for title, rec in fetched.items():
                out.write(json.dumps({"requested_title": title, **rec}, ensure_ascii=False) + "\n")
            out.flush()
            bar.update(len(chunk))


def load_articles(raw_path: Path, min_chars: int) -> dict[str, dict]:
    """Clean every fetched article, keyed by title, dropping duplicates and near-empty pages."""
    articles: dict[str, dict] = {}
    seen: set[int] = set()
    for rec in tqdm(read_jsonl(raw_path), desc="cleaning", unit="article"):
        if "wikitext" not in rec or rec["pageid"] in seen:
            continue
        seen.add(rec["pageid"])
        sections = wikitext_to_sections(rec["wikitext"])
        n_chars = sum(len(s.text) for s in sections)
        if n_chars < min_chars:
            continue
        articles[rec["title"]] = {
            "id": rec["pageid"],
            "title": rec["title"],
            "url": article_url(rec["title"]),
            "revid": rec["revid"],
            "timestamp": rec["timestamp"],
            "n_chars": n_chars,
            "sections": [s.to_dict() for s in sections],
        }
    return articles


def classify(articles: dict[str, dict], types: dict[str, list[str]], path: Path) -> dict[str, str]:
    labels = {rec["title"]: rec["category"] for rec in read_jsonl(path) if rec["category"]}
    todo = [t for t in articles if t not in labels]
    log.info("%d articles already classified, %d to go", len(labels), len(todo))
    if not todo:
        return labels

    items = [(t, types.get(t, []), articles[t]["sections"][0]["text"]) for t in todo]
    with path.open("a", encoding="utf-8") as out:
        for title, category in tqdm(ArticleClassifier().classify_many(items), total=len(items), unit="article"):
            value = category.value if category else None
            out.write(json.dumps({"title": title, "category": value}, ensure_ascii=False) + "\n")
            out.flush()
            if value:
                labels[title] = value
    return labels


def has_anthropic_credentials() -> bool:
    return bool(os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN"))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out-dir", type=Path, default=Path("data/philosophy"))
    parser.add_argument("--importance", nargs="+", default=["Top", "High", "Mid"],
                        help="WikiProject Philosophy importance ratings to include")
    parser.add_argument("--refresh-candidates", action="store_true", help="rebuild candidates.jsonl")
    parser.add_argument("--min-chars", type=int, default=500, help="drop articles with less cleaned text than this")
    parser.add_argument("--contact", help="email or URL for the User-Agent (default: the project's GitHub URL)")
    args = parser.parse_args()

    load_dotenv()  # picks up ANTHROPIC_API_KEY from .env
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    for name in ("httpx", "httpx2"):  # don't log every HTTP request
        logging.getLogger(name).setLevel(logging.WARNING)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    client_kwargs = {"user_agent": f"applied-llm-corpus-builder/0.1 ({args.contact})"} if args.contact else {}

    with WikipediaClient(**client_kwargs) as client:
        candidates = build_candidates(
            client, args.out_dir / "candidates.jsonl", args.importance, args.refresh_candidates
        )
        to_fetch = [c["title"] for c in candidates if not c["excluded"]]
        fetch_raw(client, to_fetch, args.out_dir / "raw.jsonl")

    articles = load_articles(args.out_dir / "raw.jsonl", args.min_chars)
    if not has_anthropic_credentials():
        log.warning("No Anthropic credentials set; stopping before classification (%d articles fetched).",
                    len(articles))
        return

    types = {c["title"]: c["types"] for c in candidates}
    labels = classify(articles, types, args.out_dir / "labels.jsonl")
    log.info("Categories: %s", dict(Counter(labels.get(t, "unclassified") for t in articles)))

    kept = {c.value for c in KEPT_CATEGORIES}
    out_path = args.out_dir / "articles.jsonl"
    n = 0
    with out_path.open("w", encoding="utf-8") as out:
        for title, article in articles.items():
            if labels.get(title) in kept:
                out.write(json.dumps({**article, "category": labels[title]}, ensure_ascii=False) + "\n")
                n += 1
    log.info("Wrote %d articles to %s", n, out_path)


if __name__ == "__main__":
    main()
