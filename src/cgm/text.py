"""Plain-code word matching shared by scoring and grouping."""

import re
from collections import Counter


def stem(word: str) -> str:
    """A light English stem, so "prices", "price" and "pricing" meet, as do "cleaning" and "clean"."""
    for suffix in ("ing", "ed"):
        if word.endswith(suffix) and len(word) - len(suffix) >= 3:
            word = word[:-len(suffix)]
            break
    else:
        if word.endswith("es") and word[:-2].endswith(("s", "x", "z", "ch", "sh")) and len(word) >= 5:
            word = word[:-2]
        elif word.endswith("s") and not word.endswith("ss") and len(word) >= 4:
            word = word[:-1]
    return word[:-1] if word.endswith("e") and len(word) > 3 else word


def words(text: str) -> set[str]:
    return {stem(w) for w in re.findall(r"\w+", text.lower())}


def seed_words(phrases: list[str], seeds: list[str]) -> dict[str, str]:
    """Each seed's most specific word: the one the fewest phrases use."""
    df = Counter(w for p in phrases for w in words(p))
    return {s: min(sorted(words(s)), key=lambda w: df[w]) for s in seeds}
