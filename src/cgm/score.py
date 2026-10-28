"""Score a collector run against the answer key ("People also ask", collected by hand).

For each seed, Claude sees the seed's answer-key questions and everything the collector found for
that seed, and says which questions were found. Plain code then checks every quoted match exists.
The scorer runs in passes, and the share of verdicts that flip between passes is reported.
"""

import csv
import json
from collections import defaultdict
from pathlib import Path

from cgm import claude
from cgm.client import Client

MODEL = "sonnet"

SCHEMA = {
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

PROMPT = """Below are questions buyers ask (numbered) and search phrases that people typed.

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


def load_answer_key(client: Client) -> dict[str, list[str]]:
    key = defaultdict(list)
    for path in sorted((client.folder / "answer-key").glob("google-serp-*.csv")):
        for row in csv.DictReader(open(path)):
            if row["kind"] == "people_also_ask" and row["text"] not in key[row["seed"]]:
                key[row["seed"]].append(row["text"])
    return key


def load_collected(run: Path) -> dict[str, list[str]]:
    found = defaultdict(list)
    for row in csv.DictReader(open(run / "autocomplete.csv")):
        if row["suggestion"] not in found[row["seed"]]:
            found[row["seed"]].append(row["suggestion"])
    return found


def check(results: list[dict], questions: list[str], phrases: list[str]) -> list[dict]:
    """Keep one verdict per question; a match whose quote isn't in the collected phrases is a miss."""
    known = set(phrases)
    by_id = {r["id"]: r for r in results}
    checked = []
    for i, question in enumerate(questions, 1):
        r = by_id.get(i, {"found": False, "suggestion": "", "reason": "no verdict returned"})
        found = r["found"] and r["suggestion"] in known
        reason = r["reason"] if found or not r["found"] else "quoted phrase not in the collected data"
        checked.append({"question": question, "found": found,
                        "suggestion": r["suggestion"] if found else "", "reason": reason})
    return checked


def run(client: Client, run_folder: Path, passes: int = 2) -> None:
    key, collected = load_answer_key(client), load_collected(run_folder)
    trace = run_folder / "trace.jsonl"
    verdicts = []  # one list of rows per pass
    for p in range(1, passes + 1):
        rows = []
        for seed, questions in key.items():
            phrases = collected.get(seed, [])
            prompt = PROMPT.format(
                questions="\n".join(f"{i}. {q}" for i, q in enumerate(questions, 1)),
                phrases="\n".join(phrases))
            answer = claude.ask(prompt, SCHEMA, MODEL, trace, f"score pass {p}: {seed}")
            for row in check(answer["results"], questions, phrases):
                rows.append({"pass": p, "seed": seed, **row})
            print(f"pass {p} {seed}: {sum(r['found'] for r in rows if r['seed'] == seed)}"
                  f"/{len(questions)} found", flush=True)
        verdicts.append(rows)

    with open(run_folder / "score.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, ["pass", "seed", "question", "found", "suggestion", "reason"])
        writer.writeheader()
        for rows in verdicts:
            writer.writerows(rows)

    summary = summarize(verdicts)
    (run_folder / "score-summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))


def summarize(verdicts: list[list[dict]]) -> dict:
    first = verdicts[0]
    per_seed = defaultdict(lambda: [0, 0])
    for r in first:
        per_seed[r["seed"]][0] += r["found"]
        per_seed[r["seed"]][1] += 1
    flips = sum(a["found"] != b["found"] for rows in verdicts[1:] for a, b in zip(first, rows))
    compared = len(first) * (len(verdicts) - 1)
    return {
        "questions": len(first),
        "found": sum(r["found"] for r in first),
        "share_found": round(sum(r["found"] for r in first) / len(first), 3),
        "per_seed": {s: f"{f}/{n}" for s, (f, n) in per_seed.items()},
        "passes": len(verdicts),
        "flip_rate": round(flips / compared, 3) if compared else None,
    }
