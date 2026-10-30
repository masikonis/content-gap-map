"""Group a run's buyer phrases into topics (milestone 2).

1. Claude tags each real collected phrase as a buyer phrase or not, under the site's profile rule,
   leaving out other languages and junk.
2. Plain code merges rewordings: phrases with the same words in any order or form, ignoring years
   and site names such as "reddit".
3. Claude groups the phrases into topics: one topic is one question a buyer wants answered, so
   one answer would satisfy every phrase in it. A list up to ONE_PASS phrases is grouped in one
   call; a longer one is split by seed. A merge pass, seeing every topic's phrases, then joins
   topics that mean the same and folds topics about other vendors into the general question.
4. Every topic name must be a question; Claude renames the ones that aren't.

Code checks every answer: a phrase assigned twice keeps its first topic, and a phrase left out
becomes a topic of its own and is counted. With reviewed verdicts, the pair test checks that
phrases matched to the same answer-key question share a topic, next to a random baseline. A name
audit asks Claude which topic names mean the same thing, to count over-splitting.
"""

import csv
import json
import random
import re
from collections import defaultdict
from itertools import combinations
from pathlib import Path

from cgm import claude
from cgm.client import Client
from cgm.files import read_rows
from cgm.profiles import profile
from cgm.score import VERIFIED, load_collected, numbered
from cgm.text import words

MODEL = "sonnet"
TAG_BATCH = 150
ONE_PASS = 1000
GROUP_BATCH = 400
MERGE_EXAMPLES = 15

TAG_SCHEMA = {"type": "object", "properties": {"buyer": {"type": "array", "items": {"type": "integer"}}},
              "required": ["buyer"]}

TAG_PROMPT = """A {site_type} business offers: {services}.

Below are numbered search phrases people typed. List the numbers of the buyer phrases: a buyer
phrase is {buyer}

Also leave out phrases not written in the language with code "{language}", and navigation or junk
searches: logins, downloads, phrases that contain a dollar amount, or a place far outside the
country with code "{country}".

Phrases:
{phrases}"""

GROUP_SCHEMA = {
    "type": "object",
    "properties": {"topics": {"type": "array", "items": {
        "type": "object",
        "properties": {"name": {"type": "string"},
                       "phrases": {"type": "array", "items": {"type": "integer"}}},
        "required": ["name", "phrases"],
    }}},
    "required": ["topics"],
}

GROUP_PROMPT = """Group these numbered search phrases into topics. A topic is one question a buyer
wants answered: phrases belong together only if one answer would satisfy all of them. The same
subject is not enough: "piano lessons cost" and "piano lessons for adults" are different topics,
while "piano lessons cost", "how much are piano lessons" and "piano lesson prices" are one. Words
like a year, "best" or "reddit" don't make a new topic on their own.

The businesses being compared are {brands}. A phrase about one of them is its own topic when it
asks about that business itself. A phrase about any other vendor goes in the general topic it
asks about: "does acme offer piano lessons for adults" belongs with "piano lessons for adults".

Put every phrase in exactly one topic; a phrase unlike any other is a topic of its own. Name each
topic as a short plain question ending in "?", such as "How much do piano lessons cost?".

Phrases:
{phrases}"""

MERGE_SCHEMA = {
    "type": "object",
    "properties": {"merges": {"type": "array", "items": {
        "type": "object",
        "properties": {"topics": {"type": "array", "items": {"type": "integer"}},
                       "name": {"type": "string"}},
        "required": ["topics", "name"],
    }}},
    "required": ["merges"],
}

MERGE_PROMPT = """Below are numbered topics, each a question buyers ask, with its phrases. They
were grouped in separate batches, so some mean the same thing. List the groups of topics that
should be merged because one answer would satisfy every phrase in them, and give each merged group
a new short question as its name, ending in "?". Leave out topics with no duplicate. Do not merge
topics that only share a subject or a vendor.

The businesses being compared are {brands}. A topic about any other single vendor (for example
"Does acme offer piano lessons?") should be merged into the general topic it asks about.

Topics:
{topics}"""

RENAME_SCHEMA = {"type": "object", "properties": {"names": {"type": "array", "items": {
    "type": "object", "properties": {"id": {"type": "integer"}, "name": {"type": "string"}},
    "required": ["id", "name"]}}}, "required": ["names"]}

RENAME_PROMPT = """Each numbered topic below is a group of search phrases. Give each a short plain
question that names what its phrases ask, ending in "?".

Topics:
{topics}"""

AUDIT_SCHEMA = {"type": "object", "properties": {"pairs": {"type": "array", "items": {
    "type": "array", "items": {"type": "integer"}}}}, "required": ["pairs"]}

AUDIT_PROMPT = """Below are numbered topic names, each a question buyers ask. List every pair of
numbers whose questions one answer would satisfy, so the two topics should have been one.

Topics:
{topics}"""

NOISE = re.compile(r"^(19|20)\d\d$|^reddit$|^quora$|^youtube$")


def variant_key(phrase: str) -> frozenset[str]:
    """The phrase's words, without years and site names that don't change the question."""
    return frozenset(w for w in words(phrase) if not NOISE.match(w))


def merge_variants(phrases: list[str]) -> dict[str, list[str]]:
    """Representative phrase -> every phrase with the same words. The shortest one represents."""
    by_key = defaultdict(list)
    for p in phrases:
        by_key[variant_key(p)].append(p)
    return {min(group, key=lambda p: (len(p), p)): sorted(group) for group in by_key.values()}


def assign(topics: list[dict], phrases: list[str]) -> tuple[list[tuple[str, list[str]]], int]:
    """Turn a grouping answer into (name, phrases) topics. A phrase number outside the list is
    dropped, a phrase assigned twice keeps its first topic, and a phrase left out becomes a topic
    of its own. Returns the topics and how many phrases were left out."""
    seen, result = set(), []
    for t in topics:
        members = [phrases[n - 1] for n in dict.fromkeys(t["phrases"])
                   if 1 <= n <= len(phrases) and n not in seen]
        seen.update(n for n in t["phrases"] if 1 <= n <= len(phrases))
        if members:
            result.append((t["name"], members))
    missing = [p for n, p in enumerate(phrases, 1) if n not in seen]
    return result + [(p, [p]) for p in missing], len(missing)


def apply_merges(topics: list[tuple[str, list[str]]], merges: list[dict]) -> list[tuple[str, list[str]]]:
    """Merge groups of topic numbers under their new names; each topic joins at most one group."""
    used, merged = set(), []
    for m in merges:
        ids = [n for n in dict.fromkeys(m["topics"]) if 1 <= n <= len(topics) and n not in used]
        if len(ids) > 1:
            used.update(ids)
            merged.append((m["name"], [p for n in ids for p in topics[n - 1][1]]))
    return merged + [t for n, t in enumerate(topics, 1) if n not in used]


def nearest_seed(phrase: str, seeds: list[str]) -> str:
    """The seed sharing the most words with the phrase; the first seed on a tie."""
    pw = words(phrase)
    return max(seeds, key=lambda s: len(words(s) & pw))


def tag(client: Client, phrases: list[str], trace: Path) -> set[str]:
    rule = profile(client.site_type).buyer
    buyers = set()
    for i in range(0, len(phrases), TAG_BATCH):
        batch = phrases[i:i + TAG_BATCH]
        prompt = TAG_PROMPT.format(site_type=client.site_type, services=", ".join(client.seeds),
                                   buyer=rule, language=client.language, country=client.country,
                                   phrases=numbered(batch))
        answer = claude.ask(prompt, TAG_SCHEMA, MODEL, trace, f"topics: tag batch {i // TAG_BATCH + 1}")
        buyers.update(batch[n - 1] for n in answer["buyer"] if 1 <= n <= len(batch))
    return buyers


def group_batch(phrases: list[str], brands: str, trace: Path, label: str) -> tuple[list, int]:
    answer = claude.ask(GROUP_PROMPT.format(brands=brands, phrases=numbered(phrases)),
                        GROUP_SCHEMA, MODEL, trace, label)
    return assign(answer["topics"], phrases)


def group(phrases: list[str], seeds: list[str], brands: str, trace: Path) -> tuple[list, int, int]:
    """Topics, phrases left out by the grouping calls, and topics before the merge pass."""
    if len(phrases) <= ONE_PASS:
        topics, missing = group_batch(phrases, brands, trace, "topics: group all")
    else:
        by_seed = defaultdict(list)
        for p in phrases:
            by_seed[nearest_seed(p, seeds)].append(p)
        topics, missing = [], 0
        for seed, members in by_seed.items():
            for i in range(0, len(members), GROUP_BATCH):
                found, left_out = group_batch(members[i:i + GROUP_BATCH], brands, trace,
                                              f"topics: group {seed} {i // GROUP_BATCH + 1}")
                topics += found
                missing += left_out
    # The merge pass always runs: it rejoins split questions and folds stray vendors and the
    # phrases a grouping call left out.
    listing = numbered([f"{name}: {'; '.join(members[:MERGE_EXAMPLES])}" for name, members in topics])
    answer = claude.ask(MERGE_PROMPT.format(brands=brands, topics=listing), MERGE_SCHEMA, MODEL,
                        trace, "topics: merge")
    return apply_merges(topics, answer["merges"]), missing, len(topics)


def ensure_questions(topics: list[tuple[str, list[str]]], trace: Path) -> tuple[list, int]:
    """Rename topics whose name is not a question. Returns the topics and how many were renamed."""
    bad = [n for n, (name, _) in enumerate(topics, 1) if not name.strip().endswith("?")]
    if not bad:
        return topics, 0
    listing = "\n".join(f"{n}. {'; '.join(topics[n - 1][1][:MERGE_EXAMPLES])}" for n in bad)
    answer = claude.ask(RENAME_PROMPT.format(topics=listing), RENAME_SCHEMA, MODEL, trace, "topics: rename")
    names = {r["id"]: r["name"] for r in answer["names"] if r["id"] in bad and r["name"].strip().endswith("?")}
    return [(names.get(n, name), members) for n, (name, members) in enumerate(topics, 1)], len(names)


def audit(topics: list[tuple[str, list[str]]], trace: Path) -> int:
    """How many topic pairs Claude says one answer would satisfy: a count of over-splitting."""
    answer = claude.ask(AUDIT_PROMPT.format(topics=numbered([name for name, _ in topics])),
                        AUDIT_SCHEMA, MODEL, trace, "topics: name audit")
    return len({tuple(sorted(p[:2])) for p in answer["pairs"]
                if len(p) >= 2 and p[0] != p[1] and all(1 <= n <= len(topics) for n in p[:2])})


def pair_test(topic_of: dict[str, int], same_groups: list[set[str]]) -> dict:
    """Pairs of phrases matched to the same question that share a topic (pooled, and averaged per
    question so one big question can't dominate), pairs matched to different questions kept apart,
    and the same measures for a random grouping with the same topic sizes."""
    groups = [g for g in ({p for p in g if p in topic_of} for g in same_groups) if len(g) > 1]

    def measure(of: dict[str, int]) -> dict:
        same = [(a, b) for g in groups for a, b in combinations(sorted(g), 2)]
        apart = [(a, b) for g, h in combinations(groups, 2) for a in g for b in h if a not in h and b not in g]
        ratio = lambda pairs: round(sum(of[a] == of[b] for a, b in pairs) / len(pairs), 3) if pairs else None
        per = [ratio(list(combinations(sorted(g), 2))) for g in groups]
        kept = ratio(apart)
        return {"share_together": ratio(same),
                "share_together_per_question": round(sum(per) / len(per), 3) if per else None,
                "share_apart": round(1 - kept, 3) if kept is not None else None}

    phrases = sorted(topic_of)
    labels = [topic_of[p] for p in phrases]
    random.Random(0).shuffle(labels)
    return {"questions": len(groups),
            "same_question_pairs": sum(len(g) * (len(g) - 1) // 2 for g in groups),
            **measure(topic_of), "random_baseline": measure(dict(zip(phrases, labels)))}


def reviewed_groups(run_folder: Path) -> list[set[str]]:
    """For each answer-key question the review marked found, the real phrases the first judge pass
    matched to it."""
    if not (run_folder / "reviewed.csv").exists():
        return []
    found = {r["question"] for r in read_rows(run_folder / "reviewed.csv") if r["found"] == "True"}
    _, sources = load_collected(run_folder)
    groups = []
    for r in read_rows(run_folder / "score.csv"):
        if r["pass"] == "judge pass 1" and r["question"] in found and r["matches"]:
            real = {m for m in r["matches"].split(" | ") if sources.get(m, set()) & VERIFIED}
            if len(real) > 1:
                groups.append(real)
    return groups


def run(client: Client, run_folder: Path) -> None:
    trace = run_folder / "trace.jsonl"
    phrases, sources = load_collected(run_folder)
    real = [p for p in phrases if sources[p] & VERIFIED]
    buyers = sorted(tag(client, real, trace))
    variants = merge_variants(buyers)
    print(f"{len(real)} real phrases, {len(buyers)} buyer phrases, {len(variants)} after merging "
          f"rewordings", flush=True)

    brands = ", ".join([client.primary.name] + [c.name for c in client.competitors])
    topics, missing, before_merge = group(list(variants), list(dict.fromkeys(client.seeds)), brands, trace)
    topics, renamed = ensure_questions(topics, trace)
    topics = sorted(topics, key=lambda t: -sum(len(variants[p]) for p in t[1]))
    print(f"{before_merge} topics grouped, {len(topics)} after the merge pass; {missing} phrases left "
          f"out by grouping; {renamed} names fixed", flush=True)

    topic_of = {}
    with open(run_folder / "topics.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["topic_id", "topic", "phrase", "same_words_as", "sources"])
        for n, (name, members) in enumerate(topics, 1):
            for rep in members:
                for p in variants[rep]:
                    topic_of[p] = n
                    writer.writerow([n, name, p, rep if p != rep else "", "; ".join(sorted(sources[p]))])

    sizes = sorted((sum(len(variants[p]) for p in members) for _, members in topics), reverse=True)
    summary = {"real_phrases": len(real), "buyer_phrases": len(buyers),
               "after_merging_rewordings": len(variants), "topics": len(topics),
               "topics_before_merge": before_merge, "largest_topics": sizes[:5],
               "single_phrase_topics": sizes.count(1), "left_out_by_claude": missing,
               "names_fixed": renamed,
               "names_not_questions": sum(not name.strip().endswith("?") for name, _ in topics),
               "possible_duplicate_topic_pairs": audit(topics, trace)}
    groups = reviewed_groups(run_folder)
    if groups:
        summary["pair_test"] = pair_test(topic_of, groups)
    (run_folder / "topics-summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
