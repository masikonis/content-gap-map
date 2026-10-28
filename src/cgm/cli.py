"""The cgm command."""

import argparse
from pathlib import Path

from cgm import autocomplete, score, websearch
from cgm.client import load_client


def main() -> None:
    parser = argparse.ArgumentParser(prog="cgm", description="Buyer questions your site misses.")
    steps = parser.add_subparsers(dest="step", required=True)

    step = steps.add_parser("autocomplete", help="collect Google autocomplete suggestions (starts a new run)")
    step.add_argument("client", help="client folder name under private/")

    for name, help_text in [("websearch", "find questions people wrote online, and verify them"),
                            ("score", "score a run against the answer key")]:
        step = steps.add_parser(name, help=help_text)
        step.add_argument("client", help="client folder name under private/")
        step.add_argument("--run", help="run folder name (default: the latest run)")

    args = parser.parse_args()
    client = load_client(Path("private") / args.client)
    if args.step == "autocomplete":
        autocomplete.run(client)
        return
    runs = client.folder / "runs"
    folder = runs / args.run if args.run else max(runs.iterdir())
    if args.step == "websearch":
        websearch.run(client, folder)
    elif args.step == "score":
        score.run(client, folder)
