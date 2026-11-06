"""Keep the sitemap pages that could answer a commercial buyer (milestone 3, rung 1).

1. Plain code drops the exact cases: another language than the client's, another website, files
   that aren't pages, and duplicate addresses.
2. Claude reads the remaining addresses and keeps the pages that could answer a buyer who is
   comparing options or choosing a provider. A page with no verdict is dropped and counted.

With a site-search answer key, the step reports the share of Google's first-ranked pages it kept,
which milestone 3's target is measured on.
"""

import csv
import json
import re
from collections import Counter
from pathlib import Path
from urllib.parse import urlsplit

from cgm import claude
from cgm.client import Client
from cgm.files import read_rows
from cgm.score import numbered

MODEL = "sonnet"
BATCH = 500
TARGET = 0.9
LANGUAGE = re.compile(r"^[a-z]{2}(-[a-z]{2})?$")
FILES = re.compile(r"\.(pdf|jpe?g|png|gif|svg|webp|mp4|zip|xml|txt|csv|docx?|xlsx?|pptx?)$")

SCHEMA = {"type": "object", "properties": {"keep": {"type": "array", "items": {"type": "integer"}}},
          "required": ["keep"]}

PROMPT = """These are numbered page addresses from the website of {site}, one of these businesses:
{brands}. They sell: {services}.

List the numbers of the pages that could answer a question a buyer asks while comparing options
or choosing a provider: pricing and plans, features and what the product offers, comparisons and
alternatives, buying guides and "best" lists, reviews, case studies and customer stories, trust
and security, signing up, and whether the activity is worth doing at all (trends, statistics,
results, return on investment). Leave out pages for people who already use the product (help
articles, how-to inside the product, developer docs, release notes), legal pages, careers, press,
and pages that only teach the subject (definitions, general how-to, templates and example
galleries). When an address could go either way, keep it.

Addresses:
{addresses}"""


def key(url: str) -> tuple[str, str]:
    """An address without scheme, "www." or trailing slash, so variants count once."""
    parts = urlsplit(url)
    return parts.netloc.lower().removeprefix("www."), parts.path.rstrip("/") or "/"


def code_reason(url: str, home: str, language: str, seen: set) -> str | None:
    """Why plain code drops this address, or None when Claude should judge it."""
    parts = urlsplit(url)
    host = parts.netloc.lower().removeprefix("www.")
    if host != home and not host.endswith("." + home):
        return "other website"
    first = parts.path.strip("/").split("/")[0].lower()
    if LANGUAGE.match(first) and first.split("-")[0] != language:
        return "other language"
    if FILES.search(parts.path.lower()):
        return "not a page"
    if key(url) in seen:
        return "duplicate"
    seen.add(key(url))
    return None


def judge(site: str, brands: str, services: str, urls: list[str], trace: Path) -> set[str]:
    kept = set()
    for i in range(0, len(urls), BATCH):
        batch = urls[i:i + BATCH]
        answer = claude.ask(PROMPT.format(site=site, brands=brands, services=services,
                                          addresses=numbered(batch)),
                            SCHEMA, MODEL, trace, f"pages: {site} {i // BATCH + 1}")
        kept.update(batch[n - 1] for n in answer["keep"] if 1 <= n <= len(batch))
    return kept


def key_test(client: Client, verdicts: dict[tuple[str, str], bool]) -> dict | None:
    """The share of Google's first-ranked pages, one per question and site, that were kept."""
    files = sorted((client.folder / "answer-key").glob("site-search-*.csv"))
    if not files:
        return None
    first = [r for r in read_rows(files[-1]) if r["rank"] == "1"]
    missed = [{"site": r["site"], "question": r["question"], "url": r["url"]}
              for r in first if not verdicts.get(key(r["url"]))]
    kept = len(first) - len(missed)
    return {"searches": len(first), "kept": kept, "share_kept": round(kept / len(first), 3),
            "target": TARGET, "passes": kept / len(first) >= TARGET, "missed": missed}


def run(client: Client, run_folder: Path) -> None:
    trace = run_folder / "trace.jsonl"
    rows = read_rows(run_folder / "sitemaps.csv")
    brands = ", ".join([client.primary.name] + [c.name for c in client.competitors])
    out, summary, verdicts = [], {}, {}
    for site in [client.primary] + client.competitors:
        home = urlsplit(site.url).netloc.lower().removeprefix("www.")
        seen, reasons, judged = set(), {}, []
        for r in rows:
            if r["site"] == site.name:
                reasons[r["url"]] = code_reason(r["url"], home, client.language, seen)
                if reasons[r["url"]] is None:
                    judged.append(r["url"])
        kept = judge(site.name, brands, ", ".join(client.seeds), judged, trace)
        for url, reason in reasons.items():
            reason = reason or ("kept by Claude" if url in kept else "dropped by Claude")
            out.append({"site": site.name, "url": url, "kept": url in kept, "reason": reason})
            verdicts[key(url)] = verdicts.get(key(url), False) or url in kept
        counts = Counter(row["reason"] for row in out if row["site"] == site.name)
        summary[site.name] = {"pages": len(reasons), "kept": len(kept), "by_reason": dict(counts)}
        print(f"{site.name}: kept {len(kept)} of {len(reasons)} pages", flush=True)
    test = key_test(client, verdicts)
    if test:
        summary["key_test"] = test
    with open(run_folder / "pages.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["site", "url", "kept", "reason"])
        writer.writeheader()
        writer.writerows(out)
    (run_folder / "pages-summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
