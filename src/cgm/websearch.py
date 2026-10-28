"""Find real questions people wrote online, with Claude web search, and verify each on its page.

Claude searches once per seed and returns questions with the URL where each appeared, skipping
sites that forbid crawlers. Plain code then fetches every URL politely and checks the question is
on the page. Questions it can't check are kept and marked unverified, with the reason.
"""

import csv
import ipaddress
import re
import socket
import time
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlsplit
from urllib.robotparser import RobotFileParser

import httpx

from cgm import claude
from cgm.autocomplete import PAUSE, USER_AGENT
from cgm.client import Client

MODEL = "sonnet"
TOOLS = "WebSearch,WebFetch"
MAX_BYTES = 2_000_000
MAX_REDIRECTS = 5

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


def public_address(host: str) -> str | None:
    """One address for the host, only if every address it resolves to is on the public internet."""
    try:
        addresses = sorted({info[4][0] for info in socket.getaddrinfo(host, None)})
    except (socket.gaierror, UnicodeError):
        return None
    if not addresses or not all(ipaddress.ip_address(a.split("%")[0]).is_global for a in addresses):
        return None
    return addresses[0]


class NotPublic(Exception):
    pass


class Verifier:
    """Fetches pages politely and safely: public hosts only, each request sent to the address that
    was checked (so a second lookup can't swap in a private one), robots.txt respected at every
    redirect hop, one request every PAUSE seconds, at most MAX_BYTES read per page."""

    def __init__(self, http: httpx.Client):
        self.http, self.robots = http, {}

    def read(self, url: str) -> tuple[int, str, str | None]:
        parts = urlsplit(url)
        address = public_address(parts.hostname or "")
        if address is None:
            raise NotPublic(url)
        ip = f"[{address}]" if ":" in address else address
        pinned = parts._replace(netloc=f"{ip}:{parts.port}" if parts.port else ip).geturl()
        host = f"{parts.hostname}:{parts.port}" if parts.port else parts.hostname
        extensions = {"sni_hostname": parts.hostname} if parts.scheme == "https" else {}
        time.sleep(PAUSE)
        with self.http.stream("GET", pinned, headers={"Host": host}, extensions=extensions) as response:
            body = b""
            for chunk in response.iter_bytes():
                body += chunk
                if len(body) >= MAX_BYTES:
                    break
            text = body[:MAX_BYTES].decode(response.encoding or "utf-8", errors="replace")
            return response.status_code, text, response.headers.get("location")

    def allowed(self, url: str) -> bool:
        parts = urlsplit(url)
        host = f"{parts.scheme}://{parts.netloc}"
        if host not in self.robots:
            rules = RobotFileParser()
            try:
                status, text, _ = self.read(f"{host}/robots.txt")
                rules.parse(text.splitlines() if status == 200 else [])
            except (httpx.HTTPError, NotPublic):
                rules.parse([])
            self.robots[host] = rules
        return self.robots[host].can_fetch(USER_AGENT, url)

    def fetch(self, url: str) -> tuple[int | None, str]:
        """Follows redirects by hand, re-checking each hop. Returns (status, text) or (None, reason)."""
        for _ in range(MAX_REDIRECTS + 1):
            parts = urlsplit(url)
            if parts.scheme not in ("http", "https") or not parts.hostname:
                return None, "not a web address"
            if public_address(parts.hostname) is None:
                return None, "not a public address"
            if not self.allowed(url):
                return None, "robots.txt forbids crawlers"
            try:
                status, text, location = self.read(url)
            except NotPublic:
                return None, "not a public address"
            if status in (301, 302, 303, 307, 308) and location:
                url = urljoin(url, location)
                continue
            return status, text
        return None, "too many redirects"

    def check(self, question: str, url: str) -> tuple[bool, str]:
        try:
            status, text = self.fetch(url)
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
                               language=client.language, country=client.country)
        answer = claude.ask(prompt, SCHEMA, MODEL, trace, f"websearch: {seed}", tools=TOOLS)
        found += [(seed, q["question"], q["url"]) for q in answer["questions"]]
        print(f"{seed}: {len(answer['questions'])} questions", flush=True)

    verified = 0
    with (httpx.Client(headers={"User-Agent": USER_AGENT}, timeout=15.0, trust_env=False) as http,
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
