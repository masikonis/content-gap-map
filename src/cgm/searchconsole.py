"""Import Search Console exports into a run.

Search Console's own "Export > Download CSV" gives a zip per filtered view, capped at 1,000
queries. Exports for a client go in private/<client>/search-console/, one per filter, each under
the cap. This step merges their Queries.csv files into the run's searchconsole.csv, and marks the
queries that look typed by an AI assistant searching on someone's behalf rather than by a person.
It also writes ai-demand.md: how much of the site's search demand already comes through AI
assistants, in plain words for the client.
"""

import csv
import io
import re
import zipfile
from pathlib import Path

from cgm.client import Client

CAP = 1000
AI_COMMANDS = re.compile(r'(-?filetype:|intitle:|inurl:|-?site:|"|^context:|^question:)')
AI_LENGTH = 10


def ai_style(query: str) -> bool:
    """People rarely type search commands or ten-word searches; assistants searching for them do."""
    return bool(AI_COMMANDS.search(query)) or len(query.split()) >= AI_LENGTH


def read_export(path: Path) -> list[dict]:
    with zipfile.ZipFile(path) as z:
        rows = list(csv.DictReader(io.TextIOWrapper(z.open("Queries.csv"), encoding="utf-8")))
    return [{"query": r["Top queries"], "clicks": r["Clicks"], "impressions": r["Impressions"],
             "position": r["Position"], "export": path.name} for r in rows]


def totals(rows: list[dict]) -> dict:
    impressions = sum(int(r["impressions"]) for r in rows)
    clicks = sum(int(r["clicks"]) for r in rows)
    return {"queries": len(rows), "impressions": impressions, "clicks": clicks,
            "ctr": clicks / impressions if impressions else 0.0}


def ai_demand(client: Client, rows: list[dict], exports: list[Path]) -> str:
    """A short client-facing summary of the AI-assistant share of search demand."""
    every, ai = totals(rows), totals([r for r in rows if r["ai"]])
    people = totals([r for r in rows if not r["ai"]])
    share = lambda part, whole: f"{part / whole:.0%}" if whole else "n/a"
    top = sorted((r for r in rows if r["ai"]), key=lambda r: -int(r["impressions"]))[:15]
    lines = [
        f"# AI-assistant searches: {client.primary.name}",
        "",
        f"When someone asks an AI assistant a question, the assistant often runs its own Google",
        f"searches to answer it. Those searches reach this site's Search Console. Of the searches in",
        f"these exports, **{share(ai['queries'], every['queries'])} look typed by an AI assistant**,",
        f"and they carry **{share(ai['impressions'], every['impressions'])} of the impressions**.",
        "",
        "| | Searches | Impressions | Clicks | Click rate |",
        "|---|---|---|---|---|",
        f"| AI assistants | {ai['queries']} | {ai['impressions']} | {ai['clicks']} | {ai['ctr']:.1%} |",
        f"| People | {people['queries']} | {people['impressions']} | {people['clicks']} | {people['ctr']:.1%} |",
        "",
        "## Top AI-assistant searches by impressions",
        "",
        "| Search | Impressions | Clicks |",
        "|---|---|---|",
        *[f"| {r['query'].replace('|', '/')} | {r['impressions']} | {r['clicks']} |" for r in top],
        "",
        "## How to read this",
        "",
        "- A search counts as AI-typed if it uses search commands people rarely type (such as",
        "  `filetype:` or `site:`), reads like a prompt, or runs to 10 words or more. It is a rule of",
        "  thumb: some long searches are typed by people, and some assistant searches look ordinary.",
        "- An assistant reads the pages it finds and answers the person itself, so few of these",
        "  searches become clicks. Being in the results is what gets a site into the answer.",
        f"- The shares cover the exported searches only: {', '.join(p.name for p in exports)}.",
    ]
    return "\n".join(lines) + "\n"


def run(client: Client, run_folder: Path) -> None:
    exports = sorted((client.folder / "search-console").glob("*.zip"))
    if not exports:
        raise SystemExit(f"No exports in {client.folder / 'search-console'}.")
    seen, rows = set(), []
    for path in exports:
        export = read_export(path)
        note = " (at the cap: rare queries were cut off, narrow this export's filter)" if len(export) >= CAP else ""
        print(f"{path.name}: {len(export)} queries{note}")
        for r in export:
            if r["query"] not in seen:
                seen.add(r["query"])
                rows.append({**r, "ai": ai_style(r["query"])})
    with open(run_folder / "searchconsole.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, ["query", "clicks", "impressions", "position", "ai", "export"])
        writer.writeheader()
        writer.writerows(rows)
    ai = [r for r in rows if r["ai"]]
    impressions = sum(int(r["impressions"]) for r in rows) or 1
    print(f"Done: {len(rows)} unique queries, {len(ai)} AI-style, carrying "
          f"{sum(int(r['impressions']) for r in ai) / impressions:.0%} of impressions.")
    (run_folder / "ai-demand.md").write_text(ai_demand(client, rows, exports))
    print(f"Saved to {run_folder / 'searchconsole.csv'} and {run_folder / 'ai-demand.md'}")
