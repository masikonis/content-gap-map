"""Import Search Console exports into a run.

Search Console's own "Export > Download CSV" gives a zip per filtered view, capped at 1,000
queries. Exports for a client go in private/<client>/search-console/, one per filter, each under
the cap. This step merges their Queries.csv files into the run's searchconsole.csv.
"""

import csv
import io
import zipfile
from pathlib import Path

from cgm.client import Client

CAP = 1000


def read_export(path: Path) -> list[dict]:
    with zipfile.ZipFile(path) as z:
        rows = list(csv.DictReader(io.TextIOWrapper(z.open("Queries.csv"), encoding="utf-8")))
    return [{"query": r["Top queries"], "clicks": r["Clicks"], "impressions": r["Impressions"],
             "position": r["Position"], "export": path.name} for r in rows]


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
                rows.append(r)
    with open(run_folder / "searchconsole.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, ["query", "clicks", "impressions", "position", "export"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"Done: {len(rows)} unique queries saved to {run_folder / 'searchconsole.csv'}")
