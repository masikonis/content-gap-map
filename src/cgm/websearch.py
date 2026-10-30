"""Find real questions people wrote online, with Claude web search, and verify each on its page.

Claude searches once per seed and returns questions with the URL where each appeared, skipping
sites that forbid crawlers. Plain code then fetches every URL politely and checks the question is
on the page. Questions it can't check are kept and marked unverified, with the reason.
"""

import csv
import re
from html.parser import HTMLParser
from pathlib import Path

import httpx

from cgm import claude
from cgm.client import Client
from cgm.fetch import PageFetcher, http_client
from cgm.profiles import profile

MODEL = "sonnet"
TOOLS = "WebSearch,WebFetch"

SCHEMA = {
    "type": "object",
    "properties": {"questions": {"type": "array", "items": {
        "type": "object",
        "properties": {"question": {"type": "string"}, "url": {"type": "string"}},
        "required": ["question", "url"],
    }}},
    "required": ["questions"],
}

PROMPT = """Use web search to find about 25 real questions people asked online about "{seed}",
as potential customers of a {site_type} business that offers it.

Cover these angles: {angles}. Cost questions are
already well covered elsewhere, so include only a few.

Only include questions a person asked in their own words, on forums, Q&A sites, community threads
or comments. Do not include questions from a business's own FAQ page, or questions written as
headings in articles. Skip sites that forbid crawlers, such as Quora, Reddit, Facebook and X:
every question will be checked on its page by a polite crawler. Prefer questions from people in
the country with code "{country}", written in the language with code "{language}". Copy each
question exactly as the person wrote it, and give the URL of the page where it appears."""


class _Text(HTMLParser):
    """Collects a page's visible text, skipping scripts and styles. Linear in the page size."""

    def __init__(self):
        super().__init__()
        self.parts, self.skip = [], 0

    def handle_starttag(self, tag, attrs):
        self.skip += tag in ("script", "style")

    def handle_endtag(self, tag):
        self.skip -= tag in ("script", "style") and self.skip > 0

    def handle_data(self, data):
        if not self.skip:
            self.parts.append(data)


def normalize(text: str) -> str:
    return " ".join(re.sub(r"[^\w]+", " ", text.lower()).split())


def page_text(raw_html: str) -> str:
    parser = _Text()
    parser.feed(raw_html)
    return normalize(" ".join(parser.parts))


def on_page(question: str, raw_html: str) -> bool:
    return normalize(question) in page_text(raw_html)


def check(pages: PageFetcher, question: str, url: str) -> tuple[bool, str]:
    """Whether the question appears on the page at url, and why not if it doesn't."""
    try:
        status, text = pages.fetch(url)
    except httpx.HTTPError as error:
        return False, f"fetch failed: {type(error).__name__}"
    if status is None:
        return False, text
    if status != 200:
        return False, f"fetch failed: {status}"
    if not on_page(question, text):
        return False, "question not found on the page"
    return True, ""


def run(client: Client, run_folder: Path) -> None:
    trace = run_folder / "trace.jsonl"
    found = []
    for seed in client.seeds:
        prompt = PROMPT.format(seed=seed, site_type=client.site_type,
                               angles=profile(client.site_type).angles,
                               language=client.language, country=client.country)
        answer = claude.ask(prompt, SCHEMA, MODEL, trace, f"websearch: {seed}", tools=TOOLS)
        found += [(seed, q["question"], q["url"]) for q in answer["questions"]]
        print(f"{seed}: {len(answer['questions'])} questions", flush=True)

    verified = 0
    with (http_client(timeout=15.0) as http,
          open(run_folder / "websearch.csv", "w", newline="", encoding="utf-8") as f):
        pages = PageFetcher(http)
        writer = csv.writer(f)
        writer.writerow(["seed", "question", "url", "verified", "reason"])
        for seed, question, url in found:
            ok, reason = check(pages, question, url)
            verified += ok
            writer.writerow([seed, question, url, ok, reason])

    print(f"Done: {len(found)} questions, {verified} verified on their page.")
    print(f"Saved to {run_folder / 'websearch.csv'}")
