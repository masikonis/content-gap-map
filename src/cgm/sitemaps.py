"""Read each compared site's sitemap: every page address the site publishes (milestone 3, rung 1).

Sitemap locations come from robots.txt, or /sitemap.xml when it names none. A sitemap index is
followed to its child sitemaps, gzip files are unpacked, and every request goes through
`PageFetcher`: the honest crawler name, the pause, robots.txt and public addresses only. Plain
code throughout; deciding which pages could answer a buyer is a later step.
"""

import csv
import gzip
import io
import json
import re
from collections import deque
from pathlib import Path
from xml.etree.ElementTree import ParseError
from urllib.parse import urlsplit

import httpx
from defusedxml import DefusedXmlException
from defusedxml.ElementTree import fromstring

from cgm.client import Client, Site
from cgm.fetch import PageFetcher, http_client

SITEMAP_BYTES = 50_000_000  # the sitemap protocol's own limits for one file
SITEMAP_ENTRIES = 50_000
MAX_SITEMAPS = 500
MAX_PAGES = 200_000
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}[0-9T:.+\-Z]*$")


def parse(body: bytes) -> tuple[str, list[tuple[str, str]]]:
    """("index" or "urls", [(address, lastmod)]) from one sitemap file, gzipped or not."""
    if body[:2] == b"\x1f\x8b":
        # Read at most the protocol's limit, so a small file can't unpack into gigabytes.
        body = gzip.GzipFile(fileobj=io.BytesIO(body)).read(SITEMAP_BYTES)
    root = fromstring(body)  # defusedxml: these files come from the web
    kind = "index" if root.tag.endswith("sitemapindex") else "urls"
    entries = []
    for entry in list(root)[:SITEMAP_ENTRIES]:
        fields = {child.tag.rsplit("}", 1)[-1]: (child.text or "").strip() for child in entry}
        # Only web addresses and dates are kept, so no cell can start with a spreadsheet formula.
        if urlsplit(fields.get("loc", "")).scheme in ("http", "https"):
            lastmod = fields.get("lastmod", "")
            entries.append((fields["loc"], lastmod if DATE.match(lastmod) else ""))
    return kind, entries


def locations(pages: PageFetcher, site: Site) -> list[str]:
    parts = urlsplit(site.url)
    home = f"{parts.scheme}://{parts.netloc}"
    pages.allowed(home + "/")
    return list(dict.fromkeys(pages.robots[home].site_maps() or [home + "/sitemap.xml"]))[:MAX_SITEMAPS]


def read_site(pages: PageFetcher, site: Site) -> tuple[list[dict], dict]:
    """Every page address in the site's sitemaps, and a summary that names each problem."""
    queue, seen, rows, problems = deque(locations(pages, site)), set(), {}, []
    while queue and len(seen) < MAX_SITEMAPS and len(rows) < MAX_PAGES:
        url = queue.popleft()
        if url in seen:
            continue
        seen.add(url)
        try:
            status, body = pages.fetch_bytes(url, SITEMAP_BYTES)
        except httpx.HTTPError as error:
            problems.append(f"{url}: {type(error).__name__}")
            continue
        if status != 200:
            problems.append(f"{url}: {body if status is None else status}")
            continue
        if len(body[0]) >= SITEMAP_BYTES:
            problems.append(f"{url}: cut off at {SITEMAP_BYTES:,} bytes")
        try:
            kind, entries = parse(body[0])
        except (ParseError, DefusedXmlException, OSError, EOFError) as error:
            problems.append(f"{url}: not a readable sitemap ({type(error).__name__})")
            continue
        if kind == "index":
            room = max(0, MAX_SITEMAPS - len(seen) - len(queue))
            new = [loc for loc in dict.fromkeys(loc for loc, _ in entries)
                   if loc not in seen and loc not in queue]
            queue.extend(new[:room])
        else:
            for loc, lastmod in entries[:max(0, MAX_PAGES - len(rows))]:
                rows.setdefault(loc, {"site": site.name, "url": loc, "lastmod": lastmod, "sitemap": url})
    if queue:
        problems.append(f"stopped at {len(seen)} sitemaps and {len(rows)} pages; {len(queue)} sitemaps not read")
    return list(rows.values()), {"sitemaps_read": len(seen), "pages": len(rows), "problems": problems}


def run(client: Client, run_folder: Path) -> None:
    rows, summary = [], {}
    with http_client(timeout=30.0) as http:
        pages = PageFetcher(http)
        for site in [client.primary] + client.competitors:
            found, summary[site.name] = read_site(pages, site)
            rows += found
            print(f"{site.name}: {summary[site.name]['pages']} pages from "
                  f"{summary[site.name]['sitemaps_read']} sitemaps, "
                  f"{len(summary[site.name]['problems'])} problems", flush=True)
    with open(run_folder / "sitemaps.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["site", "url", "lastmod", "sitemap"])
        writer.writeheader()
        writer.writerows(rows)
    (run_folder / "sitemaps-summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
