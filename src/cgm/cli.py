"""The cgm command."""

import argparse
from pathlib import Path

from cgm import autocomplete
from cgm.client import load_client


def main() -> None:
    parser = argparse.ArgumentParser(prog="cgm", description="Buyer questions your site misses.")
    steps = parser.add_subparsers(dest="step", required=True)

    step = steps.add_parser("autocomplete", help="collect Google autocomplete suggestions")
    step.add_argument("client", help="client folder name under private/")

    args = parser.parse_args()
    client = load_client(Path("private") / args.client)
    if args.step == "autocomplete":
        autocomplete.run(client)
