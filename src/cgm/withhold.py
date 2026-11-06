"""Mask private terms in a public demo run before it is committed.

The demo uses public data only, but a public site can still mention a term on the lab's private
blocklist (a client's name, for example). Every such term in the run's text files is replaced with
"[withheld]", so no row or call disappears and every count still adds up. A term of several words
also matches when its words are joined the way addresses join them ("acme-piano", "acme_piano",
"acme+piano", "acme%20piano").
"""

import re
from pathlib import Path

BLOCKLIST = Path("private/blocklist.txt")
MASK = "[withheld]"
TEXT = {".csv", ".json", ".jsonl", ".md"}


def terms(path: Path = BLOCKLIST) -> list[str]:
    if not path.exists():
        return []
    return [t.strip() for t in path.read_text(encoding="utf-8").splitlines() if t.strip()]


def mask(text: str, words: list[str]) -> tuple[str, int]:
    if not words:
        return text, 0
    forms = [r"(?:\s|-|_|\+|%20)+".join(map(re.escape, w.split())) for w in words]
    pattern = re.compile("|".join(sorted(forms, key=len, reverse=True)), re.I)
    return pattern.subn(MASK, text)


def run(run_folder: Path) -> None:
    words = terms()
    if not words:
        raise SystemExit(f"No {BLOCKLIST}; nothing to withhold.")
    for path in sorted(p for p in run_folder.rglob("*") if p.suffix.lower() in TEXT):
        text, count = mask(path.read_text(encoding="utf-8"), words)
        if count:
            path.write_text(text, encoding="utf-8")
            print(f"{path.relative_to(run_folder)}: {count} masked")
