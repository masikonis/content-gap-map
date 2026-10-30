"""Plain-code word matching shared by scoring and grouping."""

import re
from collections import Counter


def stem(word: str) -> str:
    """A light English stem, so "prices" meets "price" and "cleaning" meets "clean"."""
    for suffix in ("ing", "ed"):
        if word.endswith(suffix) and len(word) - len(suffix) >= 3:
            return word[:-len(suffix)]
    if word.endswith("es") and word[:-2].endswith(("s", "x", "z", "ch", "sh")) and len(word) >= 5:
        return word[:-2]
    if word.endswith("s") and not word.endswith("ss") and len(word) >= 4:
        return word[:-1]
    return word


def words(text: str) -> set[str]:
    return {stem(w) for w in re.findall(r"\w+", text.lower())}


def seed_words(phrases: list[str], seeds: list[str]) -> dict[str, str]:
    """Each seed's most specific word: the one the fewest phrases use."""
    df = Counter(w for p in phrases for w in words(p))
    return {s: min(sorted(words(s)), key=lambda w: df[w]) for s in seeds}
