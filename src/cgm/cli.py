"""The cgm command."""

import argparse
from pathlib import Path

from cgm import autocomplete, score
from cgm.client import load_client


def main() -> None:
    parser = argparse.ArgumentParser(prog="cgm", description="Buyer questions your site misses.")
    steps = parser.add_subparsers(dest="step", required=True)

    step = steps.add_parser("autocomplete", help="collect Google autocomplete suggestions")
    step.add_argument("client", help="client folder name under private/")

    step = steps.add_parser("score", help="score a run against the answer key")
    step.add_argument("client", help="client folder name under private/")
    step.add_argument("--run", help="run folder name (default: the latest run)")

    args = parser.parse_args()
    client = load_client(Path("private") / args.client)
    if args.step == "autocomplete":
        autocomplete.run(client)
    elif args.step == "score":
        runs = client.folder / "runs"
        folder = runs / args.run if args.run else max(runs.iterdir())
        score.run(client, folder)
