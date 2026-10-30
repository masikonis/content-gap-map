"""Group a run's buyer phrases into topics (milestone 2).

1. Claude tags each real collected phrase as a buyer phrase or not, under the site's profile rule.
2. Plain code merges near-duplicates: phrases with the same words in any order or form.
3. Claude groups each seed's phrases into topics: one topic is one question a buyer wants
   answered, so one answer would satisfy every phrase in it.
4. Claude merges topics that mean the same thing across seeds.

Code checks every answer: a phrase assigned twice keeps its first topic, and a phrase left out
becomes a topic of its own and is counted. If the run has reviewed verdicts, the pair test checks
that phrases matched to the same answer-key question share a topic.
"""

import csv
import json
from collections import defaultdict
from itertools import combinations
from pathlib import Path

from cgm import claude
from cgm.client import Client
from cgm.files import read_rows
from cgm.profiles import profile
from cgm.score import VERIFIED, load_collected, numbered
from cgm.text import seed_words, words

MODEL = "sonnet"
TAG_BATCH = 150
GROUP_BATCH = 250

TAG_SCHEMA = {"type": "object", "properties": {"buyer": {"type": "array", "items": {"type": "integer"}}},
              "required": ["buyer"]}

TAG_PROMPT = """A {site_type} business offers: {services}.

Below are numbered search phrases people typed. List the numbers of the buyer phrases: a buyer
phrase is {buyer}

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
while "piano lessons cost", "how much are piano lessons" and "piano lesson prices" are one.

Put every phrase in exactly one topic; a phrase unlike any other is a topic of its own. Name each
topic as a short plain question, such as "How much do piano lessons cost?".

Phrases:
{phrases}"""

MERGE_SCHEMA = {
    "type": "object",
    "properties": {"merges": {"type": "array", "items": {"type": "array", "items": {"type": "integer"}}}},
    "required": ["merges"],
}

MERGE_PROMPT = """Below are numbered topics, each a question buyers ask, with example phrases.
Some came from different batches and mean the same thing. List the groups of topic numbers that
should be merged because one answer would satisfy all of them. Leave out topics that have no
duplicate. Do not merge topics that only share a subject.

Topics:
{topics}"""


def variant_key(phrase: str) -> frozenset[str]:
    return frozenset(words(phrase))


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
        members = [phrases[n - 1] for n in t["phrases"] if 1 <= n <= len(phrases) and n not in seen]
        seen.update(n for n in t["phrases"] if 1 <= n <= len(phrases))
        if members:
            result.append((t["name"], members))
    missing = [p for n, p in enumerate(phrases, 1) if n not in seen]
    return result + [(p, [p]) for p in missing], len(missing)


def apply_merges(topics: list[tuple[str, list[str]]], merges: list[list[int]]) -> list[tuple[str, list[str]]]:
    """Merge groups of topic numbers; each topic joins at most one group, keeping the first name."""
    used, merged = set(), []
    for group in merges:
        ids = [n for n in dict.fromkeys(group) if 1 <= n <= len(topics) and n not in used]
        if len(ids) > 1:
            used.update(ids)
            merged.append((topics[ids[0] - 1][0], [p for n in ids for p in topics[n - 1][1]]))
    return merged + [t for n, t in enumerate(topics, 1) if n not in used]


def tag(client: Client, phrases: list[str], trace: Path) -> set[str]:
    rule = profile(client.site_type).buyer
    buyers = set()
    for i in range(0, len(phrases), TAG_BATCH):
        batch = phrases[i:i + TAG_BATCH]
        prompt = TAG_PROMPT.format(site_type=client.site_type, services=", ".join(client.seeds),
                                   buyer=rule, phrases=numbered(batch))
        answer = claude.ask(prompt, TAG_SCHEMA, MODEL, trace, f"topics: tag batch {i // TAG_BATCH + 1}")
        buyers.update(batch[n - 1] for n in answer["buyer"] if 1 <= n <= len(batch))
    return buyers


def group(phrases_by_seed: dict[str, list[str]], trace: Path) -> tuple[list[tuple[str, list[str]]], int]:
    topics, missing = [], 0
    for seed, phrases in phrases_by_seed.items():
        for i in range(0, len(phrases), GROUP_BATCH):
            batch = phrases[i:i + GROUP_BATCH]
            answer = claude.ask(GROUP_PROMPT.format(phrases=numbered(batch)), GROUP_SCHEMA, MODEL,
                                trace, f"topics: group {seed} {i // GROUP_BATCH + 1}")
            found, left_out = assign(answer["topics"], batch)
            topics += found
            missing += left_out
    return topics, missing


def merge(topics: list[tuple[str, list[str]]], trace: Path) -> list[tuple[str, list[str]]]:
    listing = numbered([f"{name} (e.g. {'; '.join(members[:3])})" for name, members in topics])
    answer = claude.ask(MERGE_PROMPT.format(topics=listing), MERGE_SCHEMA, MODEL, trace, "topics: merge")
    return apply_merges(topics, answer["merges"])


def pair_test(topic_of: dict[str, str], same_groups: list[set[str]]) -> dict:
    """Share of phrase pairs matched to the same question that share a topic, and share of pairs
    matched to different questions that are kept apart."""
    groups = [{p for p in g if p in topic_of} for g in same_groups]
    same = [(a, b) for g in groups for a, b in combinations(sorted(g), 2)]
    apart = [(a, b) for g, h in combinations(groups, 2) for a in g for b in h if a not in h and b not in g]
    together = lambda pairs: round(sum(topic_of[a] == topic_of[b] for a, b in pairs) / len(pairs), 3) if pairs else None
    kept_apart = together(apart)
    return {"same_question_pairs": len(same), "share_together": together(same),
            "different_question_pairs": len(apart),
            "share_apart": round(1 - kept_apart, 3) if kept_apart is not None else None}


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

    seeds = list(dict.fromkeys(client.seeds))
    seed_word = seed_words(real, seeds)
    by_seed = defaultdict(list)
    for p in variants:
        by_seed[next((s for s in seeds if seed_word[s] in words(p)), "other")].append(p)

    topics, missing = group(dict(by_seed), trace)
    before = len(topics)
    topics = sorted(merge(topics, trace), key=lambda t: -sum(len(variants[p]) for p in t[1]))
    print(f"{before} topics from grouping, {len(topics)} after merging; {missing} phrases left out "
          f"by Claude kept as their own topics", flush=True)

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
    summary = {"real_phrases": len(real), "buyer_phrases": len(buyers), "after_merging_rewordings": len(variants),
               "topics": len(topics), "largest_topics": sizes[:5], "single_phrase_topics": sizes.count(1),
               "left_out_by_claude": missing}
    groups = reviewed_groups(run_folder)
    if groups:
        summary["pair_test"] = pair_test({p: t for p, t in topic_of.items()}, groups)
    (run_folder / "topics-summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
