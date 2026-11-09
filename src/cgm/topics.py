"""Group a run's buyer phrases into topics (milestone 2).

1. Claude tags each real collected phrase as a buyer phrase or not, under the site's profile rule,
   leaving out other languages and junk.
2. Plain code merges rewordings: phrases with the same words in any order or form, ignoring years
   and site names such as "reddit".
3. Claude groups the phrases into topics: one topic is what one good page would answer, so one
   page could fully answer every phrase in it. A list up to ONE_PASS phrases is grouped in one
   call; a longer one is split by seed. A merge pass, seeing every topic's phrases, then joins
   topics that mean the same. This is done VOTES times, and two phrases share a topic only when
   most of the groupings put them together, which steadies Claude's run-to-run variation.
4. A split pass shows Claude each topic of two or more phrases and moves out phrases that a page
   answering the rest would not answer, into new topics.
5. Every topic name must be a question; Claude renames the ones that aren't.
6. Claude marks each topic's funnel stage: learning, comparing or choosing. Learning-stage topics
   stay in topics.csv as evidence but are dropped from every later step.

Code checks every answer: a phrase assigned twice keeps its first topic, and a phrase left out
becomes a topic of its own and is counted. With reviewed verdicts, the pair test checks that
phrases matched to the same answer-key question share a topic, next to a random baseline. A name
audit asks Claude which topic names mean the same thing, to count over-splitting. The lump check
has an outside model judge LUMP_SAMPLE random topics blind, to count topics that need more than
one page. The stage check has the outside model mark STAGE_SAMPLE random topics blind, and counts
how often it agrees on which topics are kept.
"""

import csv
import json
import random
import re
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path

from cgm import claude, stage
from cgm.client import Client
from cgm.files import read_rows
from cgm.profiles import profile
from cgm.score import VERIFIED, load_collected, numbered
from cgm.text import words

MODEL = "sonnet"
TAG_BATCH = 150
ONE_PASS = 3000
VOTES = 3  # grouping runs; two phrases share a topic only when most runs put them together
GROUP_BATCH = 400
MERGE_EXAMPLES = 15
LUMP_MODEL = "fable"  # an outside judge: not the model that made the topics
LUMP_SAMPLE = 40
LUMP_PASS = 36
SPLIT_PASS = 0.85
STAGE_SAMPLE = 40
STAGE_PASS = 36

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

GROUP_PROMPT = """Group these numbered search phrases into topics. A topic is what one good page on
a site would answer: phrases belong together only if one page could fully answer all of them. The
same subject is not enough: "piano lessons cost" and "piano lessons for adults" need different
pages, while "piano lessons cost", "how much are piano lessons" and "piano lesson prices" are one.
A variation the same page would cover in a section, such as a year, "free", "best", "reddit" or a
device, doesn't make a new topic on its own.

Three kinds of phrase need different answers, so keep them apart even on the same subject:
- asking about the activity itself: "is piano hard to learn", "are piano lessons worth it";
- how to do it yourself: "how to learn piano at home";
- choosing a provider: "easiest piano school for beginners", "cheapest piano lessons".
A phrase that names one vendor asks about that vendor: "does acme offer piano lessons" is not the
same topic as "piano lessons for adults". A phrase that names a place (a town, city or area) is
about that place, and each place is its own topic, since a business would answer it with a page
for that place: "piano lessons springfield" and "piano lessons shelbyville" are two topics, and
neither belongs with "piano lessons near me".

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
should be merged because one page could fully answer every phrase in them, and give each merged group
a new short question as its name, ending in "?". Leave out topics with no duplicate. Do not merge
topics that only share a subject or a vendor, and do not merge a topic about one vendor or one
place into a general one or into another place's.

Topics:
{topics}"""

SPLIT_SCHEMA = {"type": "object", "properties": {"splits": {"type": "array", "items": {
    "type": "object", "properties": {"topic": {"type": "integer"},
                                     "phrases": {"type": "array", "items": {"type": "integer"}},
                                     "name": {"type": "string"}},
    "required": ["topic", "phrases", "name"]}}}, "required": ["splits"]}

SPLIT_PROMPT = """Each numbered topic below is a group of search phrases meant to be answered by one
good page. For each topic, find the phrases that a page answering the rest would not fully answer,
and move them out. Common cases: asking about the activity itself ("are piano lessons worth it")
next to choosing a provider ("cheapest piano school"); how to do it yourself next to which provider
to pick; setup next to price; two different vendors or products; what one vendor offers next to
a comparison of several vendors; one audience or use next to another ("for schools", "for
choirs"); two different places ("springfield", "shelbyville"), each of which gets its own topic.
A variation one page covers in a section, such as a device or a free option, stays.

For each group of phrases to move out, give the topic number, the phrase numbers within that topic,
and a short question ending in "?" as the new topic's name. Phrases moved out together must share
one page. Leave out topics that are fine.

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
numbers whose questions one page could fully answer, so the two topics should have been one.

Topics:
{topics}"""

LUMP_SCHEMA = {"type": "object", "properties": {"topics": {"type": "array", "items": {
    "type": "object", "properties": {"id": {"type": "integer"}, "one_page": {"type": "boolean"},
                                     "reason": {"type": "string"}},
    "required": ["id", "one_page", "reason"]}}}, "required": ["topics"]}

LUMP_PROMPT = """Each numbered group below holds search phrases that were put together as one
topic. For each group, decide whether one good page could fully answer every phrase in it.
Variations one page would cover in a section, such as a device or a free option, are fine. A group
fails when it needs different pages: for example price and setup, whether the activity is worth
doing next to which provider to choose, or questions about different vendors or different
places (towns, cities, areas). Give a short reason,
naming the phrases that differ.

Groups:
{groups}"""

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


def apply_splits(topics: list[tuple[str, list[str]]], splits: list[dict]) -> tuple[list, int]:
    """Move phrases out of topics into new named topics. A phrase number outside its topic is
    dropped, a phrase moves at most once, and a topic emptied by its splits disappears. Returns
    the topics and how many new topics were made."""
    taken, new = defaultdict(set), []
    for sp in splits:
        if not 1 <= sp["topic"] <= len(topics):
            continue
        members = topics[sp["topic"] - 1][1]
        ids = [n for n in dict.fromkeys(sp["phrases"])
               if 1 <= n <= len(members) and n not in taken[sp["topic"]]]
        if ids:
            taken[sp["topic"]].update(ids)
            new.append((sp["name"], [members[n - 1] for n in ids]))
    kept = [(name, [p for i, p in enumerate(members, 1) if i not in taken[n]])
            for n, (name, members) in enumerate(topics, 1)]
    return [t for t in kept if t[1]] + new, len(new)


def split(topics: list[tuple[str, list[str]]], trace: Path) -> tuple[list, int]:
    multi = [n for n, (_, members) in enumerate(topics, 1) if len(members) > 1]
    if not multi:
        return topics, 0
    listing = "\n".join(f"Topic {i}: " + "; ".join(f"{j}. {p}" for j, p in enumerate(topics[n - 1][1], 1))
                         for i, n in enumerate(multi, 1))
    answer = claude.ask(SPLIT_PROMPT.format(topics=listing), SPLIT_SCHEMA, MODEL, trace, "topics: split")
    # The answer numbers topics within the list shown; map them back to positions in `topics`.
    splits = [{**sp, "topic": multi[sp["topic"] - 1]} for sp in answer["splits"]
              if 1 <= sp["topic"] <= len(multi)]
    return apply_splits(topics, splits)


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


def group_batch(phrases: list[str], trace: Path, label: str) -> tuple[list, int]:
    answer = claude.ask(GROUP_PROMPT.format(phrases=numbered(phrases)),
                        GROUP_SCHEMA, MODEL, trace, label)
    return assign(answer["topics"], phrases)


def group(phrases: list[str], seeds: list[str], trace: Path, vote: int = 1) -> tuple[list, int, int]:
    """Topics, phrases left out by the grouping calls, and topics before the merge pass."""
    if len(phrases) <= ONE_PASS:
        topics, missing = group_batch(phrases, trace, f"topics: group all (vote {vote})")
    else:
        by_seed = defaultdict(list)
        for p in phrases:
            by_seed[nearest_seed(p, seeds)].append(p)
        topics, missing = [], 0
        for seed, members in by_seed.items():
            for i in range(0, len(members), GROUP_BATCH):
                found, left_out = group_batch(members[i:i + GROUP_BATCH], trace,
                                              f"topics: group {seed} {i // GROUP_BATCH + 1} (vote {vote})")
                topics += found
                missing += left_out
    # The merge pass always runs: it rejoins split questions and the phrases a grouping call
    # left out.
    listing = numbered([f"{name}: {'; '.join(members[:MERGE_EXAMPLES])}" for name, members in topics])
    answer = claude.ask(MERGE_PROMPT.format(topics=listing), MERGE_SCHEMA, MODEL,
                        trace, f"topics: merge (vote {vote})")
    return apply_merges(topics, answer["merges"]), missing, len(topics)


def vote(groupings: list[list[tuple[str, list[str]]]]) -> list[tuple[str, list[str]]]:
    """Join two phrases when most groupings put them in the same topic, and keep the joined sets
    as topics (a phrase no majority places with another is a topic of its own). Each topic takes
    the name its phrases carried most often."""
    together, names = Counter(), defaultdict(Counter)
    for topics in groupings:
        for name, members in topics:
            for p in members:
                names[p][name] += 1
            together.update(combinations(sorted(members), 2))
    parent = {p: p for p in names}

    def root(p):
        while parent[p] != p:
            parent[p] = parent[parent[p]]
            p = parent[p]
        return p

    for (a, b), count in together.items():
        if count * 2 > len(groupings):
            parent[root(a)] = root(b)
    sets = defaultdict(list)
    for p in sorted(names):
        sets[root(p)].append(p)
    result = []
    for members in sets.values():
        tally = Counter()
        for p in members:
            tally.update(names[p])
        result.append((min(tally, key=lambda n: (-tally[n], n)), members))
    return result


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
    """How many topic pairs Claude says one page could answer: a count of over-splitting."""
    answer = claude.ask(AUDIT_PROMPT.format(topics=numbered([name for name, _ in topics])),
                        AUDIT_SCHEMA, MODEL, trace, "topics: name audit")
    return len({tuple(sorted(p[:2])) for p in answer["pairs"]
                if len(p) >= 2 and p[0] != p[1] and all(1 <= n <= len(topics) for n in p[:2])})


def lump_sample(topics: list[tuple[str, list[str]]], marked: list[str]) -> list[int]:
    """Up to LUMP_SAMPLE topic numbers, picked with a fixed seed from kept topics of two or more
    phrases (a single phrase can't be lumped, and dropped topics don't reach the report)."""
    candidates = [n for n, (_, members) in enumerate(topics, 1)
                  if len(members) > 1 and stage.kept(marked[n - 1])]
    return sorted(random.Random(0).sample(candidates, min(LUMP_SAMPLE, len(candidates))))


def lump_check(topics: list[tuple[str, list[str]]], marked: list[str], trace: Path) -> dict:
    """An outside model judges sampled topics blind: it sees the phrases, not the names or scores.
    A topic with no verdict counts as needing more than one page."""
    picked = lump_sample(topics, marked)
    groups = "\n".join(f"{i}. {'; '.join(topics[n - 1][1])}" for i, n in enumerate(picked, 1))
    answer = claude.ask(LUMP_PROMPT.format(groups=groups), LUMP_SCHEMA, LUMP_MODEL, trace,
                        "topics: lump check")
    verdicts = {v["id"]: v for v in answer["topics"] if 1 <= v["id"] <= len(picked)}
    failed = [{"topic": topics[n - 1][0], "reason": verdicts.get(i, {}).get("reason", "no verdict")}
              for i, n in enumerate(picked, 1) if not verdicts.get(i, {}).get("one_page")]
    return {"judge": LUMP_MODEL, "topics_checked": len(picked), "one_page": len(picked) - len(failed),
            "passes": len(picked) == LUMP_SAMPLE and len(picked) - len(failed) >= LUMP_PASS,
            "not_one_page": failed}


def phrases_of(topics: list[tuple[str, list[str]]], ids: list[int]) -> list[str]:
    """Topics shown by their phrases only, in the order of `ids`."""
    return ["; ".join(topics[n - 1][1][:MERGE_EXAMPLES]) for n in ids]


def stages(topics: list[tuple[str, list[str]]], trace: Path) -> list[str]:
    """Each topic's funnel stage; an unknown stage is kept."""
    return stage.mark(phrases_of(topics, list(range(1, len(topics) + 1))), MODEL, trace, "topics: stage")


def stage_check(topics: list[tuple[str, list[str]]], marked: list[str], trace: Path) -> dict:
    """An outside model marks STAGE_SAMPLE random topics blind; counts agreement on keep or drop
    (learning is dropped). A missing verdict counts as a disagreement."""
    picked = sorted(random.Random(0).sample(range(1, len(topics) + 1), min(STAGE_SAMPLE, len(topics))))
    theirs = stage.mark(phrases_of(topics, picked), LUMP_MODEL, trace, "topics: stage check")
    pairs = [(n, marked[n - 1], t) for n, t in zip(picked, theirs)]
    differ = [{"topic": topics[n - 1][0], "marked": m, "judge": t if t != "unknown" else "no verdict"}
              for n, m, t in pairs if t == "unknown" or stage.kept(t) != stage.kept(m)]
    return {"judge": LUMP_MODEL, "topics_checked": len(picked), "same_keep_or_drop": len(picked) - len(differ),
            "same_stage": sum(m == t for _, m, t in pairs),
            "passes": len(picked) == STAGE_SAMPLE and len(picked) - len(differ) >= STAGE_PASS,
            "keep_or_drop_differs": differ}


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


def reviewed_groups(run_folder: Path, commercial: set[str]) -> list[set[str]]:
    """For each commercial answer-key question the review marked found, the real phrases the first
    judge pass matched to it."""
    if not (run_folder / "reviewed.csv").exists():
        return []
    found = {r["question"] for r in read_rows(run_folder / "reviewed.csv")
             if r["found"] == "True" and r["question"] in commercial}
    _, sources = load_collected(run_folder)
    groups = []
    for r in read_rows(run_folder / "score.csv"):
        if r["pass"] == "judge pass 1" and r["question"] in found and r["matches"]:
            real = {m for m in r["matches"].split(" | ") if sources.get(m, set()) & VERIFIED}
            if len(real) > 1:
                groups.append(real)
    return groups


def commercial_questions(client: Client) -> set[str]:
    """Answer-key buyer questions marked comparing or choosing, from the score step's stage tags."""
    path = client.folder / "answer-key" / "stage-tags.csv"
    if not path.exists():
        raise SystemExit(f"No {path}. Run `cgm score` first: it marks each answer-key question's stage.")
    return {r["question"] for r in read_rows(path) if stage.kept(r["stage"])}


def run(client: Client, run_folder: Path) -> None:
    trace = run_folder / "trace.jsonl"
    phrases, sources = load_collected(run_folder)
    real = [p for p in phrases if sources[p] & VERIFIED]
    buyers = sorted(tag(client, real, trace))
    variants = merge_variants(buyers)
    print(f"{len(real)} real phrases, {len(buyers)} buyer phrases, {len(variants)} after merging "
          f"rewordings", flush=True)

    brands = [site.name.lower() for site in [client.primary] + client.competitors]
    seeds = list(dict.fromkeys(client.seeds + brands))
    groupings = [group(list(variants), seeds, trace, v) for v in range(1, VOTES + 1)]
    topics = vote([g[0] for g in groupings])
    missing, before_merge = sum(g[1] for g in groupings), [len(g[0]) for g in groupings]
    topics, split_off = split(topics, trace)
    topics, renamed = ensure_questions(topics, trace)
    topics = sorted(topics, key=lambda t: -sum(len(variants[p]) for p in t[1]))
    marked = stages(topics, trace)
    print(f"{before_merge} topics in the {VOTES} groupings, {len(topics)} after the vote and splitting "
          f"({split_off} split off); {missing} phrases left out by grouping; {renamed} names fixed",
          flush=True)

    topic_of = {}
    with open(run_folder / "topics.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["topic_id", "topic", "stage", "phrase", "same_words_as", "sources"])
        for n, (name, members) in enumerate(topics, 1):
            for rep in members:
                for p in variants[rep]:
                    topic_of[p] = n
                    writer.writerow([n, name, marked[n - 1], p, rep if p != rep else "",
                                     "; ".join(sorted(sources[p]))])

    sizes = sorted((sum(len(variants[p]) for p in members) for _, members in topics), reverse=True)
    summary = {"real_phrases": len(real), "buyer_phrases": len(buyers),
               "after_merging_rewordings": len(variants), "topics": len(topics),
               "topics_in_each_grouping": before_merge, "topics_split_off": split_off,
               "largest_topics": sizes[:5],
               "single_phrase_topics": sizes.count(1), "left_out_by_claude": missing,
               "names_fixed": renamed,
               "names_not_questions": sum(not name.strip().endswith("?") for name, _ in topics),
               "possible_duplicate_topic_pairs": audit(topics, trace),
               "topics_by_stage": {st: marked.count(st) for st in stage.STAGES + ["unknown"]},
               "phrases_by_stage": {st: sum(len(variants[p]) for (_, m), s in zip(topics, marked)
                                            if s == st for p in m) for st in stage.STAGES + ["unknown"]},
               "kept_topics": sum(map(stage.kept, marked))}
    groups = reviewed_groups(run_folder, commercial_questions(client))
    if groups:
        summary["pair_test"] = pair_test(topic_of, groups)
        per = summary["pair_test"]["share_together_per_question"]
        summary["split_check_passes"] = per is not None and per >= SPLIT_PASS
    summary["lump_check"] = lump_check(topics, marked, trace)
    summary["stage_check"] = stage_check(topics, marked, trace)
    (run_folder / "topics-summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
