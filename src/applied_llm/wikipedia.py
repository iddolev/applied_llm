"""Minimal, polite client for the English Wikipedia MediaWiki API."""

import logging
import time
from collections.abc import Iterable, Iterator
from typing import Any

import httpx

log = logging.getLogger(__name__)

API_URL = "https://en.wikipedia.org/w/api.php"
DEFAULT_USER_AGENT = "applied-llm-corpus-builder/0.1 (https://github.com/iddolev/applied_llm)"

# The API accepts at most 50 titles per query for regular (non-bot) clients.
MAX_TITLES_PER_QUERY = 50


class WikipediaClient:
    """Wraps the MediaWiki API with throttling, retries and query continuation.

    Follows https://www.mediawiki.org/wiki/API:Etiquette: requests are sequential,
    carry a descriptive User-Agent, and send `maxlag` so we back off when the
    servers are under load.
    """

    def __init__(
        self,
        user_agent: str = DEFAULT_USER_AGENT,
        min_interval: float = 0.5,
        max_retries: int = 6,
        timeout: float = 120.0,
    ):
        self._http = httpx.Client(
            headers={"User-Agent": user_agent, "Accept-Encoding": "gzip"},
            timeout=timeout,
        )
        self._min_interval = min_interval
        self._max_retries = max_retries
        self._last_request = 0.0

    def close(self) -> None:
        self._http.close()

    def __enter__(self) -> "WikipediaClient":
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    def _request(self, params: dict[str, Any]) -> dict[str, Any]:
        params = {"format": "json", "formatversion": "2", "maxlag": "5", **params}
        for attempt in range(self._max_retries):
            wait = self._min_interval - (time.monotonic() - self._last_request)
            if wait > 0:
                time.sleep(wait)
            self._last_request = time.monotonic()

            try:
                # POST avoids URL-length limits when sending 50 long titles.
                resp = self._http.post(API_URL, data=params)
            except httpx.TransportError as e:
                delay = 2**attempt
                log.warning("Network error (%s); retrying in %ds", e, delay)
                time.sleep(delay)
                continue

            if resp.status_code in (429, 500, 502, 503, 504):
                delay = int(resp.headers.get("Retry-After", 2**attempt))
                log.warning("HTTP %d; retrying in %ds", resp.status_code, delay)
                time.sleep(delay)
                continue
            resp.raise_for_status()

            data = resp.json()
            error = data.get("error")
            if error and error.get("code") == "maxlag":
                delay = int(resp.headers.get("Retry-After", 5))
                log.info("Server lagged; retrying in %ds", delay)
                time.sleep(delay)
                continue
            if error:
                raise RuntimeError(f"MediaWiki API error: {error}")
            return data
        raise RuntimeError(f"Giving up after {self._max_retries} attempts: {params}")

    def query(self, params: dict[str, Any]) -> Iterator[dict[str, Any]]:
        """Run an action=query request, yielding each result batch and following `continue`."""
        cont: dict[str, Any] = {}
        while True:
            data = self._request({"action": "query", **params, **cont})
            if "query" in data:
                yield data["query"]
            if "continue" not in data:
                return
            cont = data["continue"]

    def articles_with_talk_category(self, category: str) -> list[str]:
        """Titles of articles whose talk page is in `category`.

        WikiProject banners put talk pages into assessment categories such as
        "Mid-importance Philosophy articles".
        """
        titles = []
        for batch in self.query(
            {
                "list": "categorymembers",
                "cmtitle": f"Category:{category}",
                "cmnamespace": "1",  # Talk:
                "cmlimit": "max",
            }
        ):
            for page in batch["categorymembers"]:
                titles.append(page["title"].removeprefix("Talk:"))
        return titles

    def wikidata_ids(self, titles: Iterable[str]) -> dict[str, str]:
        """Map article titles to their Wikidata item IDs (e.g. "Q9471"), keyed by the requested title."""
        titles = list(titles)
        ids = {}
        for i in range(0, len(titles), MAX_TITLES_PER_QUERY):
            chunk = titles[i : i + MAX_TITLES_PER_QUERY]
            for batch in self.query(
                {"titles": "|".join(chunk), "prop": "pageprops", "ppprop": "wikibase_item", "redirects": "1"}
            ):
                redirected_from = {r["to"]: r["from"] for r in batch.get("redirects", [])}
                for page in batch.get("pages", []):
                    qid = page.get("pageprops", {}).get("wikibase_item")
                    if qid:
                        ids[redirected_from.get(page["title"], page["title"])] = qid
        return ids

    def fetch_wikitext(self, titles: Iterable[str]) -> Iterator[dict[str, Any]]:
        """Yield {pageid, title, revid, timestamp, wikitext} for each existing article.

        Redirects are resolved, so the yielded title may differ from the requested one.
        """
        titles = list(titles)
        for i in range(0, len(titles), MAX_TITLES_PER_QUERY):
            chunk = titles[i : i + MAX_TITLES_PER_QUERY]
            # Large batches come back in several continuation rounds; each page's
            # content appears in exactly one of them.
            for batch in self.query(
                {
                    "titles": "|".join(chunk),
                    "prop": "revisions",
                    "rvprop": "ids|timestamp|content",
                    "rvslots": "main",
                    "redirects": "1",
                }
            ):
                for page in batch.get("pages", []):
                    if page.get("missing") or page.get("invalid") or page.get("ns") != 0:
                        continue
                    revisions = page.get("revisions")
                    if not revisions:
                        continue  # content delivered in a later continuation round
                    rev = revisions[0]
                    yield {
                        "pageid": page["pageid"],
                        "title": page["title"],
                        "revid": rev["revid"],
                        "timestamp": rev["timestamp"],
                        "wikitext": rev["slots"]["main"]["content"],
                    }


def article_url(title: str) -> str:
    return "https://en.wikipedia.org/wiki/" + title.replace(" ", "_")
