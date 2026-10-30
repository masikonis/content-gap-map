"""The cgm command."""

import argparse
from pathlib import Path

from cgm import autocomplete, predicted, score, searchconsole, websearch
from cgm.client import load_client


def main() -> None:
    parser = argparse.ArgumentParser(prog="cgm", description="Buyer questions your site misses.")
    steps = parser.add_subparsers(dest="step", required=True)

    step = steps.add_parser("autocomplete", help="collect Google autocomplete suggestions (starts a new run)")
    step.add_argument("client", help="client folder under private/, or a path such as demo/email-marketing")

    for name, help_text in [("searchconsole", "import Search Console exports into a run"),
                            ("websearch", "find questions people wrote online, and verify them"),
                            ("predicted", "predict questions buyers ask AI assistants (never counted as demand)"),
                            ("score", "score a run against the answer key")]:
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
    if args.step == "searchconsole":
        searchconsole.run(client, folder)
    elif args.step == "websearch":
        websearch.run(client, folder)
    elif args.step == "predicted":
        predicted.run(client, folder)
    elif args.step == "score":
        score.run(client, folder)
