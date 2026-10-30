"""Score a collector run against the answer key ("People also ask").

Each unique answer-key question is checked against a shortlist of what the sources found: every
phrase that contains the most specific word of one of the question's seeds. Each match is
credited to the sources that found it. Questions are tagged once as buyer questions or not, and the headline score counts buyer
questions only. Two passes by the main judge measure how often verdicts flip, and one pass by a
second judge shows where the two disagree, for a person to review.
"""

import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

from cgm import claude
from cgm.client import Client

JUDGE = "sonnet"
SECOND_JUDGE = "opus"
TAGGER = "sonnet"
BATCH = 15

MATCH_SCHEMA = {
    "type": "object",
    "properties": {"results": {"type": "array", "items": {
        "type": "object",
        "properties": {
            "id": {"type": "integer"},
            "found": {"type": "boolean"},
            "phrases": {"type": "array", "items": {"type": "integer"}},
            "reason": {"type": "string"},
        },
        "required": ["id", "found", "phrases", "reason"],
    }}},
    "required": ["results"],
}

MATCH_PROMPT = """Below are questions buyers ask, and phrases people typed or wrote, both numbered.

For each question, decide whether any phrase asks the same thing. They match only if one
answer would satisfy both. The same topic is not enough: "piano lesson books" does not match
"Are piano lessons worth it?", but "piano lessons cost" matches "How much do piano lessons cost?".
A phrase whose answer would only cover the question along the way does not match either: "what
are piano lessons" does not match "What does a first piano lesson include?".

Return one result per question. If found, list the numbers of every matching phrase in "phrases".
If not found, leave "phrases" empty. Keep "reason" under 15 words.

Questions:
{questions}

Phrases:
{phrases}"""

SOURCES = {"autocomplete": "autocomplete", "searchconsole": "searchconsole", "websearch": "websearch",
           "websearch-unverified": "websearch, unverified"}
VERIFIED = {"autocomplete", "searchconsole", "websearch"}

TAG_SCHEMA = {
    "type": "object",
    "properties": {"results": {"type": "array", "items": {
        "type": "object",
        "properties": {
            "id": {"type": "integer"},
            "buyer": {"type": "boolean"},
            "reason": {"type": "string"},
        },
        "required": ["id", "buyer", "reason"],
    }}},
    "required": ["results"],
}

TAG_PROMPT = """A {site_type} business offers: {services}.

For each numbered question, decide whether it is a buyer question: one a person would ask while
deciding whether, when or whom to hire for these services (price, value, what is included, how
often, which option, what to expect). It is not a buyer question if it is about doing the job
yourself, buying equipment or supplies, running or pricing a business that offers the service, or
one specific other company. Keep "reason" under 15 words.

Questions:
{questions}"""


def load_answer_key(client: Client) -> dict[str, list[str]]:
    """Each unique "People also ask" question, with the seeds it appeared under."""
    key = defaultdict(list)
    for path in sorted((client.folder / "answer-key").glob("google-serp-*.csv")):
        for row in csv.DictReader(open(path)):
            if row["kind"] == "people_also_ask" and row["seed"] not in key[row["text"]]:
                key[row["text"]].append(row["seed"])
    return dict(key)


def load_collected(run: Path) -> tuple[list[str], dict[str, set[str]]]:
    """Every phrase any source found in the run, and which sources found it."""
    sources = defaultdict(set)
    for row in csv.DictReader(open(run / "autocomplete.csv")):
        sources[row["suggestion"]].add("autocomplete")
    if (run / "searchconsole.csv").exists():
        for row in csv.DictReader(open(run / "searchconsole.csv")):
            sources[row["query"]].add("searchconsole")
    if (run / "websearch.csv").exists():
        for row in csv.DictReader(open(run / "websearch.csv")):
            sources[row["question"]].add("websearch" if row["verified"] == "True" else "websearch-unverified")
    return sorted(sources), dict(sources)


def numbered(items: list[str]) -> str:
    return "\n".join(f"{i}. {item}" for i, item in enumerate(items, 1))


def batches(items: list[str]) -> list[list[str]]:
    return [items[i:i + BATCH] for i in range(0, len(items), BATCH)]


def tag_buyers(client: Client, questions: list[str], trace: Path) -> dict[str, dict]:
    """Tag each question once and save the tags beside the answer key."""
    path = client.folder / "answer-key" / "buyer-tags.csv"
    if path.exists():
        tags = {row["question"]: row for row in csv.DictReader(open(path))}
        if all(q in tags for q in questions):
            return {q: {"buyer": tags[q]["buyer"] == "True", "reason": tags[q]["reason"]}
                    for q in questions}
    tags = {}
    for group in batches(questions):
        answer = claude.ask(TAG_PROMPT.format(site_type=client.site_type,
                                              services=", ".join(client.seeds),
                                              questions=numbered(group)),
                            TAG_SCHEMA, TAGGER, trace, "tag buyer questions")
        by_id = {r["id"]: r for r in answer["results"]}
        for i, q in enumerate(group, 1):
            r = by_id.get(i, {"buyer": True, "reason": "no tag returned, kept as buyer"})
            tags[q] = {"buyer": r["buyer"], "reason": r["reason"]}
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["question", "buyer", "reason"])
        for q, t in tags.items():
            writer.writerow([q, t["buyer"], t["reason"]])
    return tags


def check(results: list[dict], questions: list[str], phrases: list[str]) -> list[dict]:
    """Keep one verdict per question; phrase numbers outside the list are dropped, and a match
    left with no valid phrase is a miss."""
    by_id = {r["id"]: r for r in results}
    checked = []
    for i, question in enumerate(questions, 1):
        r = by_id.get(i, {"found": False, "phrases": [], "reason": "no verdict returned"})
        matches = [phrases[n - 1] for n in r["phrases"] if 1 <= n <= len(phrases)] if r["found"] else []
        found = bool(matches)
        reason = r["reason"] if found or not r["found"] else "phrase numbers not in the list"
        checked.append({"question": question, "found": found, "matches": matches, "reason": reason})
    return checked


def found_by(row: dict, sources: dict[str, set[str]], wanted: set[str]) -> bool:
    return any(sources[m] & wanted for m in row["matches"])


def stem(word: str) -> str:
    for suffix in ("ing", "es", "ed", "s"):
        if word.endswith(suffix) and len(word) - len(suffix) >= 3:
            return word[:-len(suffix)]
    return word


def words(text: str) -> set[str]:
    return {stem(w) for w in re.findall(r"\w+", text.lower())}


def shortlists(key: dict[str, list[str]], phrases: list[str], seeds: list[str]) -> dict[str, list[str]]:
    """For each question, the phrases containing the most specific word (the one fewest phrases
    use) of any of its seeds, or of any seed whose word the question itself contains."""
    phrase_words = {p: words(p) for p in phrases}
    df = Counter(w for ws in phrase_words.values() for w in ws)
    seed_word = {s: min(sorted(words(s)), key=lambda w: df[w]) for s in seeds}
    by_seed = {s: {p for p in phrases if w in phrase_words[p]} for s, w in seed_word.items()}
    lists = {}
    for question, own in key.items():
        question_seeds = set(own) | {s for s, w in seed_word.items() if w in words(question)}
        lists[question] = sorted(set().union(*(by_seed[s] for s in question_seeds if s in by_seed)))
    return lists


def judge(questions: list[str], lists: dict[str, list[str]], model: str, trace: Path,
          label: str) -> list[dict]:
    """Questions that share a shortlist are judged together, 15 per call."""
    groups = defaultdict(list)
    for q in questions:
        groups[tuple(lists[q])].append(q)
    verdicts, n = {}, 0
    for phrases, group_questions in groups.items():
        for group in batches(group_questions):
            n += 1
            prompt = MATCH_PROMPT.format(questions=numbered(group), phrases=numbered(list(phrases)))
            answer = claude.ask(prompt, MATCH_SCHEMA, model, trace, f"{label}, batch {n}")
            for row in check(answer["results"], group, list(phrases)):
                verdicts[row["question"]] = row
    rows = [verdicts[q] for q in questions]
    print(f"{label}: {sum(r['found'] for r in rows)}/{len(rows)} found", flush=True)
    return rows


def run(client: Client, run_folder: Path) -> None:
    key = load_answer_key(client)
    phrases, sources = load_collected(run_folder)
    questions = list(key)
    trace = run_folder / "trace.jsonl"
    tags = tag_buyers(client, questions, trace)

    seeds = list(dict.fromkeys(client.seeds + [s for own in key.values() for s in own]))
    lists = shortlists(key, phrases, seeds)
    sizes = sorted(len(v) for v in lists.values())
    print(f"shortlists: {len(phrases)} phrases, {sizes[0]} to {sizes[-1]} per question", flush=True)

    passes = {"judge pass 1": judge(questions, lists, JUDGE, trace, "judge pass 1"),
              "judge pass 2": judge(questions, lists, JUDGE, trace, "judge pass 2"),
              "second judge": judge(questions, lists, SECOND_JUDGE, trace, "second judge")}

    with open(run_folder / "score.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["pass", "question", "seeds", "buyer", "found", "sources", "matches", "reason"])
        for name, rows in passes.items():
            for r in rows:
                found_in = sorted({SOURCES[s] for m in r["matches"] for s in sources[m]})
                writer.writerow([name, r["question"], "; ".join(key[r["question"]]),
                                 tags[r["question"]]["buyer"], r["found"], "; ".join(found_in),
                                 " | ".join(r["matches"]), r["reason"]])

    first, second = passes["judge pass 1"], passes["second judge"]
    with open(run_folder / "disagreements.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["question", "buyer", f"{JUDGE} found", f"{JUDGE} match", f"{JUDGE} reason",
                         f"{SECOND_JUDGE} found", f"{SECOND_JUDGE} match", f"{SECOND_JUDGE} reason"])
        for a, b in zip(first, second):
            if a["found"] != b["found"]:
                writer.writerow([a["question"], tags[a["question"]]["buyer"], a["found"],
                                 " | ".join(a["matches"]), a["reason"], b["found"],
                                 " | ".join(b["matches"]), b["reason"]])

    summary = summarize(passes, tags, sources)
    reviewed = run_folder / "reviewed.csv"
    if reviewed.exists():
        # Reviewed verdicts cover autocomplete only, so judges are compared on those matches.
        truth = {r["question"]: r["found"] == "True" for r in csv.DictReader(open(reviewed))}
        summary["accuracy_against_reviewed"] = {
            name: accuracy([{**r, "found": found_by(r, sources, {"autocomplete"})} for r in rows], truth)
            for name, rows in passes.items()}
    (run_folder / "score-summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))


def share(rows: list[dict], test=lambda r: r["found"]) -> float | None:
    return round(sum(map(test, rows)) / len(rows), 3) if rows else None


def accuracy(rows: list[dict], truth: dict[str, bool]) -> float:
    known = [r for r in rows if r["question"] in truth]
    return round(sum(r["found"] == truth[r["question"]] for r in known) / len(known), 3)


def agreement(a: list[dict], b: list[dict]) -> float:
    return round(sum(x["found"] == y["found"] for x, y in zip(a, b)) / len(a), 3)


def summarize(passes: dict[str, list[dict]], tags: dict[str, dict],
              sources: dict[str, set[str]]) -> dict:
    first = passes["judge pass 1"]
    buyers = [r for r in first if tags[r["question"]]["buyer"]]
    by = {label: lambda r, w=wanted: found_by(r, sources, w)
          for label, wanted in [("all sources", VERIFIED),
                                ("all sources, with unverified", set(SOURCES)),
                                ("autocomplete", {"autocomplete"}),
                                ("searchconsole", {"searchconsole"}),
                                ("websearch", {"websearch"}),
                                ("websearch, with unverified", {"websearch", "websearch-unverified"})]}
    single = {"autocomplete": {"autocomplete"}, "searchconsole": {"searchconsole"},
              "websearch, with unverified": {"websearch", "websearch-unverified"}}
    only = {label: [r["question"] for r in buyers if found_by(r, sources, mine)
                    and not found_by(r, sources, set(SOURCES) - mine)]
            for label, mine in single.items()}
    return {
        "questions": len(first),
        "buyer_questions": len(buyers),
        "share_found_buyer": share(buyers, by["all sources"]),
        "share_found_all": share(first, by["all sources"]),
        "share_found_buyer_by_source": {label: share(buyers, test) for label, test in by.items()},
        "buyer_questions_only_one_source_found": only,
        "flip_rate": round(1 - agreement(first, passes["judge pass 2"]), 3),
        "judge_agreement": agreement(first, passes["second judge"]),
        "disagreements": sum(a["found"] != b["found"] for a, b in zip(first, passes["second judge"])),
    }
