"""Score a collector run against the answer key ("People also ask").

Each unique answer-key question is checked against everything the collector found, across all
seeds. Questions are tagged once as buyer questions or not, and the headline score counts buyer
questions only. Two passes by the main judge measure how often verdicts flip, and one pass by a
second judge shows where the two disagree, for a person to review.
"""

import csv
import json
from collections import defaultdict
from pathlib import Path

from cgm import claude
from cgm.client import Client

JUDGE = "sonnet"
SECOND_JUDGE = "opus"
BATCH = 15

MATCH_SCHEMA = {
    "type": "object",
    "properties": {"results": {"type": "array", "items": {
        "type": "object",
        "properties": {
            "id": {"type": "integer"},
            "found": {"type": "boolean"},
            "suggestion": {"type": "string"},
            "reason": {"type": "string"},
        },
        "required": ["id", "found", "suggestion", "reason"],
    }}},
    "required": ["results"],
}

MATCH_PROMPT = """Below are questions buyers ask (numbered) and search phrases that people typed.

For each question, decide whether any search phrase asks the same thing. They match only if one
answer would satisfy both. The same topic is not enough: "gutter cleaning tools" does not match
"Is it worth paying for gutter cleaning?", but "gutter cleaning cost" matches "How much does
gutter cleaning cost?".

Return one result per question. If found, copy the single best matching phrase exactly as written
into "suggestion". If not found, leave "suggestion" empty. Keep "reason" under 15 words.

Questions:
{questions}

Search phrases:
{phrases}"""

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


def load_collected(run: Path) -> list[str]:
    return sorted({row["suggestion"] for row in csv.DictReader(open(run / "autocomplete.csv"))})


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
                            TAG_SCHEMA, JUDGE, trace, "tag buyer questions")
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


def check(results: list[dict], questions: list[str], phrases: set[str]) -> list[dict]:
    """Keep one verdict per question; a match whose quote isn't in the collected phrases is a miss."""
    by_id = {r["id"]: r for r in results}
    checked = []
    for i, question in enumerate(questions, 1):
        r = by_id.get(i, {"found": False, "suggestion": "", "reason": "no verdict returned"})
        found = r["found"] and r["suggestion"] in phrases
        reason = r["reason"] if found or not r["found"] else "quoted phrase not in the collected data"
        checked.append({"question": question, "found": found,
                        "suggestion": r["suggestion"] if found else "", "reason": reason})
    return checked


def judge(questions: list[str], phrases: list[str], model: str, trace: Path, label: str) -> list[dict]:
    known, rows = set(phrases), []
    for n, group in enumerate(batches(questions), 1):
        prompt = MATCH_PROMPT.format(questions=numbered(group), phrases="\n".join(phrases))
        answer = claude.ask(prompt, MATCH_SCHEMA, model, trace, f"{label}, batch {n}")
        rows += check(answer["results"], group, known)
    print(f"{label}: {sum(r['found'] for r in rows)}/{len(rows)} found", flush=True)
    return rows


def run(client: Client, run_folder: Path) -> None:
    key, phrases = load_answer_key(client), load_collected(run_folder)
    questions = list(key)
    trace = run_folder / "trace.jsonl"
    tags = tag_buyers(client, questions, trace)

    passes = {"judge pass 1": judge(questions, phrases, JUDGE, trace, "judge pass 1"),
              "judge pass 2": judge(questions, phrases, JUDGE, trace, "judge pass 2"),
              "second judge": judge(questions, phrases, SECOND_JUDGE, trace, "second judge")}

    with open(run_folder / "score.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["pass", "question", "seeds", "buyer", "found", "suggestion", "reason"])
        for name, rows in passes.items():
            for r in rows:
                writer.writerow([name, r["question"], "; ".join(key[r["question"]]),
                                 tags[r["question"]]["buyer"], r["found"], r["suggestion"], r["reason"]])

    first, second = passes["judge pass 1"], passes["second judge"]
    with open(run_folder / "disagreements.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["question", "buyer", f"{JUDGE} found", f"{JUDGE} match", f"{JUDGE} reason",
                         f"{SECOND_JUDGE} found", f"{SECOND_JUDGE} match", f"{SECOND_JUDGE} reason"])
        for a, b in zip(first, second):
            if a["found"] != b["found"]:
                writer.writerow([a["question"], tags[a["question"]]["buyer"], a["found"],
                                 a["suggestion"], a["reason"], b["found"], b["suggestion"], b["reason"]])

    summary = summarize(passes, tags)
    (run_folder / "score-summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))


def share(rows: list[dict]) -> float | None:
    return round(sum(r["found"] for r in rows) / len(rows), 3) if rows else None


def agreement(a: list[dict], b: list[dict]) -> float:
    return round(sum(x["found"] == y["found"] for x, y in zip(a, b)) / len(a), 3)


def summarize(passes: dict[str, list[dict]], tags: dict[str, dict]) -> dict:
    first = passes["judge pass 1"]
    buyers = [r for r in first if tags[r["question"]]["buyer"]]
    return {
        "questions": len(first),
        "buyer_questions": len(buyers),
        "share_found_buyer": share(buyers),
        "share_found_all": share(first),
        "flip_rate": round(1 - agreement(first, passes["judge pass 2"]), 3),
        "judge_agreement": agreement(first, passes["second judge"]),
        "disagreements": sum(a["found"] != b["found"] for a, b in zip(first, passes["second judge"])),
    }
