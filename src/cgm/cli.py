"""The cgm command."""

import argparse
from pathlib import Path

from cgm import (autocomplete, pages, predicted, score, searchconsole, sitemaps, topics, websearch,
                 withhold)
from cgm.client import load_client


def main() -> None:
    parser = argparse.ArgumentParser(prog="cgm", description="Commercial buyer questions your site misses.")
    steps = parser.add_subparsers(dest="step", required=True)

    step = steps.add_parser("autocomplete", help="collect Google autocomplete suggestions (starts a new run)")
    step.add_argument("client", help="client folder under private/, or a path such as demo/email-marketing")

    for name, help_text in [("brands", "add brand searches to a run collected before they existed"),
                            ("searchconsole", "import Search Console exports into a run"),
                            ("websearch", "find questions people wrote online, and verify them"),
                            ("predicted", "predict questions buyers ask AI assistants (never counted as demand)"),
                            ("score", "score a run against the answer key"),
                            ("topics", "group a run's buyer phrases into topics"),
                            ("sitemaps", "read every compared site's sitemap into a run"),
                            ("pages", "keep the sitemap pages that could answer a buyer"),
                            ("withhold", "mask private blocklist terms in a public demo run")]:
        step = steps.add_parser(name, help=help_text)
        step.add_argument("client", help="client folder under private/, or a path such as demo/email-marketing")
        step.add_argument("--run", help="run folder name (default: the latest run)")

    args = parser.parse_args()
    # A bare name is a private client folder; a path (such as demo/email-marketing) is used as is.
    where = Path(args.client) if "/" in args.client else Path("private") / args.client
    client = load_client(where)
    if args.step == "autocomplete":
        autocomplete.run(client)
        return
    runs = sorted(p for p in (client.folder / "runs").glob("*") if p.is_dir())
    if not runs:
        raise SystemExit(f"No runs in {client.folder / 'runs'}. Start one with: cgm autocomplete {args.client}")
    folder = client.folder / "runs" / args.run if args.run else runs[-1]
    if args.step == "brands":
        autocomplete.add_brands(client, folder)
    elif args.step == "searchconsole":
        searchconsole.run(client, folder)
    elif args.step == "websearch":
        websearch.run(client, folder)
    elif args.step == "predicted":
        predicted.run(client, folder)
    elif args.step == "score":
        score.run(client, folder)
    elif args.step == "topics":
        topics.run(client, folder)
    elif args.step == "sitemaps":
        sitemaps.run(client, folder)
    elif args.step == "pages":
        pages.run(client, folder)
    elif args.step == "withhold":
        withhold.run(folder)
