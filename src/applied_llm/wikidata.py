"""Look up Wikidata "instance of" (P31) types through the Wikidata Query Service."""

import logging
import time
from collections import defaultdict
from collections.abc import Iterable

import httpx

from applied_llm.wikipedia import DEFAULT_USER_AGENT

log = logging.getLogger(__name__)

SPARQL_URL = "https://query.wikidata.org/sparql"
ITEMS_PER_QUERY = 300


def instance_of_labels(
    qids: Iterable[str], user_agent: str = DEFAULT_USER_AGENT, max_retries: int = 8
) -> dict[str, list[str]]:
    """Map each Wikidata item ID to the English labels of its P31 types (e.g. ["human"]).

    Items without any P31 statement are omitted.
    """
    qids = sorted(set(qids))
    types: dict[str, list[str]] = defaultdict(list)
    with httpx.Client(
        headers={"User-Agent": user_agent, "Accept": "application/sparql-results+json"}, timeout=120
    ) as http:
        for i in range(0, len(qids), ITEMS_PER_QUERY):
            values = " ".join(f"wd:{q}" for q in qids[i : i + ITEMS_PER_QUERY])
            query = f"""
                SELECT ?item ?typeLabel WHERE {{
                  VALUES ?item {{ {values} }}
                  ?item wdt:P31 ?type .
                  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
                }}"""
            for row in _sparql(http, query, max_retries):
                qid = row["item"]["value"].rsplit("/", 1)[1]
                types[qid].append(row["typeLabel"]["value"])
            time.sleep(1)  # be gentle with the shared query service
    return dict(types)


def _sparql(http: httpx.Client, query: str, max_retries: int) -> list[dict]:
    for attempt in range(max_retries):
        try:
            resp = http.post(SPARQL_URL, data={"query": query})
        except httpx.TransportError as e:
            delay = 10 * (attempt + 1)
            log.warning("Network error (%s); retrying in %ds", e, delay)
            time.sleep(delay)
            continue
        if resp.status_code == 200:
            return resp.json()["results"]["bindings"]
        delay = int(resp.headers.get("Retry-After", 10 * (attempt + 1)))
        log.warning("SPARQL HTTP %d; retrying in %ds", resp.status_code, delay)
        time.sleep(delay)
    raise RuntimeError(f"SPARQL query failed after {max_retries} attempts")
