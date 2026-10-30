"""Reading the plain files a run is made of. Every file is UTF-8, whatever the platform."""

import csv
from pathlib import Path


def read_rows(path: Path) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))
