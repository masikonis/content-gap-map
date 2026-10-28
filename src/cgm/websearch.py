"""Find real questions people wrote online, with Claude web search, and verify each on its page.

Claude searches once per seed and returns questions with the URL where each appeared. Plain code
then fetches every URL politely and checks the question is on the page. Questions it can't check
are kept and marked unverified, with the reason.
"""

import csv
import html
import re
import time
from pathlib import Path
from urllib.parse import urlsplit
from urllib.robotparser import RobotFileParser

import httpx

from cgm import claude
from cgm.autocomplete import PAUSE, USER_AGENT
from cgm.client import Client

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

Cover these angles: why, what happens if, when and when not, risks and worries, what is included,
comparisons between options, and hiring someone versus doing it yourself. Cost questions are
already well covered elsewhere, so include only a few.

Only include questions a person asked in their own words, on forums, Q&A sites, community threads
or comments. Do not include questions from a business's own FAQ page, or questions written as
headings in articles. Copy each question exactly as the person wrote it, and give the URL of the
page where it appears. Search in {language} for {country}."""


def normalize(text: str) -> str:
    return " ".join(re.sub(r"[^\w]+", " ", text.lower()).split())


def page_text(raw_html: str) -> str:
    raw_html = re.sub(r"(?is)<(script|style).*?</\1>", " ", raw_html)
    return normalize(html.unescape(re.sub(r"(?s)<[^>]+>", " ", raw_html)))


def on_page(question: str, raw_html: str) -> bool:
    return normalize(question) in page_text(raw_html)


class Verifier:
    """Fetches pages politely: robots.txt respected per host, one request every PAUSE seconds."""

    def __init__(self, http: httpx.Client):
        self.http, self.robots = http, {}

    def get(self, url: str) -> httpx.Response:
        time.sleep(PAUSE)
        return self.http.get(url)

    def allowed(self, url: str) -> bool:
        parts = urlsplit(url)
        host = f"{parts.scheme}://{parts.netloc}"
        if host not in self.robots:
            rules = RobotFileParser()
            try:
                response = self.get(f"{host}/robots.txt")
                rules.parse(response.text.splitlines() if response.status_code == 200 else [])
            except httpx.HTTPError:
                rules.parse([])
            self.robots[host] = rules
        return self.robots[host].can_fetch(USER_AGENT, url)

    def check(self, question: str, url: str) -> tuple[bool, str]:
        if not url.startswith(("http://", "https://")):
            return False, "not a web address"
        if not self.allowed(url):
            return False, "robots.txt forbids crawlers"
        try:
            response = self.get(url)
        except httpx.HTTPError as error:
            return False, f"fetch failed: {type(error).__name__}"
        if response.status_code != 200:
            return False, f"fetch failed: {response.status_code}"
        if not on_page(question, response.text):
            return False, "question not found on the page"
        return True, ""


def run(client: Client, run_folder: Path) -> None:
    trace = run_folder / "trace.jsonl"
    found = []
    for seed in client.seeds:
        prompt = PROMPT.format(seed=seed, site_type=client.site_type,
                               language=client.language, country=client.country)
        answer = claude.ask(prompt, SCHEMA, MODEL, trace, f"websearch: {seed}", tools=TOOLS)
        found += [(seed, q["question"], q["url"]) for q in answer["questions"]]
        print(f"{seed}: {len(answer['questions'])} questions", flush=True)

    verified = 0
    with (httpx.Client(headers={"User-Agent": USER_AGENT}, timeout=15.0, follow_redirects=True) as http,
          open(run_folder / "websearch.csv", "w", newline="") as f):
        verifier = Verifier(http)
        writer = csv.writer(f)
        writer.writerow(["seed", "question", "url", "verified", "reason"])
        for seed, question, url in found:
            ok, reason = verifier.check(question, url)
            verified += ok
            writer.writerow([seed, question, url, ok, reason])

    print(f"Done: {len(found)} questions, {verified} verified on their page.")
    print(f"Saved to {run_folder / 'websearch.csv'}")
