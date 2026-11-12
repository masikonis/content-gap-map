"""Collect Google autocomplete suggestions for a client's seeds and the businesses it compares.

Each seed is expanded with question words and a to z, and each business name (the client's and
its competitors') with question words, the profile's brand words ("pricing", "alternatives") and a
to z, because category seeds alone never reach choosing-stage searches such as "acme pricing".
Queries go to Google's autocomplete one request every 2 seconds, and every suggestion is saved raw.
Filtering happens in a later step.
"""

import csv
import json
import string
import time
from datetime import datetime
from pathlib import Path

import httpx

from cgm.client import Client
from cgm.fetch import PAUSE, http_client
from cgm.files import read_rows
from cgm.profiles import QUESTION_WORDS, Profile, profile

URL = "https://suggestqueries.google.com/complete/search"
BACKOFF = 60.0

class Blocked(Exception):
    pass


def expand(seed: str, site: Profile) -> list[str]:
    """The seed alone, with the profile's words before and after it, and with a to z after it."""
    return ([seed]
            + [f"{word} {seed}" for word in site.before]
            + [f"{seed} {word}" for word in site.after]
            + [f"{seed} {letter}" for letter in string.ascii_lowercase])


def expand_brand(name: str, site: Profile) -> list[str]:
    """The name alone, with question words before it, and with brand words and a to z after it."""
    name = name.lower()
    return ([name]
            + [f"{word} {name}" for word in QUESTION_WORDS]
            + [f"{name} {word}" for word in site.brand]
            + [f"{name} {letter}" for letter in string.ascii_lowercase])


def brand_queries(client: Client) -> list[tuple[str, str]]:
    site = profile(client.site_type)
    names = dict.fromkeys(s.name for s in [client.primary] + client.competitors)
    return [(name, q) for name in names for q in expand_brand(name, site)]


def parse(reply: list) -> list[tuple[str, int | None]]:
    """Read a "chrome" format reply into (suggestion, relevance) pairs."""
    suggestions = reply[1]
    relevance = reply[4].get("google:suggestrelevance", []) if len(reply) > 4 else []
    return [(text, relevance[i] if i < len(relevance) else None)
            for i, text in enumerate(suggestions)]


def decode(response: httpx.Response) -> list:
    """Google sometimes answers in a non-UTF-8 charset; read the text in the charset it declares."""
    return json.loads(response.text)


def fetch(http: httpx.Client, query: str, language: str, country: str) -> list:
    params = {"client": "chrome", "hl": language, "gl": country, "q": query}
    for attempt in range(2):
        response = http.get(URL, params=params)
        if response.status_code not in (429, 503):
            response.raise_for_status()
            return decode(response)
        if attempt == 0:
            time.sleep(BACKOFF)
    raise Blocked(f"Google refused {query!r} with {response.status_code} twice.")


def run(client: Client) -> Path:
    out = client.folder / "runs" / datetime.now().strftime("%Y-%m-%d-%H%M%S")
    (out / "responses").mkdir(parents=True)
    site = profile(client.site_type)
    queries = [(seed, q) for seed in client.seeds for q in expand(seed, site)] + brand_queries(client)
    collect(client, out, queries)
    print(f"Saved to {out}")
    return out


def add_missing(client: Client, out: Path) -> None:
    """Add the searches for seeds and brands added to the client file after the run was collected."""
    done = {row["seed"] for row in read_rows(out / "autocomplete.csv")}
    site = profile(client.site_type)
    queries = ([(seed, q) for seed in client.seeds if seed not in done for q in expand(seed, site)]
               + [(name, q) for name, q in brand_queries(client) if name not in done])
    if not queries:
        print("This run already has every seed and brand.")
        return
    collect(client, out, queries)


def collect(client: Client, out: Path, queries: list[tuple[str, str]]) -> None:
    """Send the queries and append every suggestion to the run's autocomplete.csv."""
    path = out / "autocomplete.csv"
    new_file = not path.exists()
    first = len(list((out / "responses").glob("*.json"))) + 1
    requests, rows, started = 0, 0, time.monotonic()
    unique = set()

    with (http_client(timeout=10.0) as http, open(path, "a", newline="", encoding="utf-8") as f):
        writer = csv.writer(f)
        if new_file:
            writer.writerow(["seed", "query", "suggestion", "rank", "relevance", "time"])
        for n, (seed, query) in enumerate(queries, 1):
            try:
                reply = fetch(http, query, client.language, client.country)
            except Blocked as stop:
                print(f"Blocked after {n - 1} of {len(queries)} requests: {stop}")
                break
            requests += 1
            (out / "responses" / f"{first + n - 1:04d}.json").write_text(
                json.dumps({"query": query, "reply": reply}, ensure_ascii=False), encoding="utf-8")
            at = datetime.now().isoformat(timespec="seconds")
            for rank, (text, relevance) in enumerate(parse(reply), 1):
                writer.writerow([seed, query, text, rank, relevance, at])
                unique.add(text)
                rows += 1
            print(f"{n}/{len(queries)} {query!r}: {len(reply[1])} suggestions", flush=True)
            time.sleep(PAUSE)

    minutes = (time.monotonic() - started) / 60
    print(f"Done: {requests} requests, {rows} suggestions, {len(unique)} unique, {minutes:.1f} min.")
