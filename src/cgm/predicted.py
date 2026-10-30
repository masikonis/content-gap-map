"""Predict the questions buyers ask AI assistants, with Claude.

What people type into assistants is private, so these questions are predictions, not demand.
They are saved apart (predicted.csv) and never count in the headline score.
"""

import csv
from pathlib import Path

from cgm import claude
from cgm.client import Client
from cgm.profiles import profile

MODEL = "sonnet"
PER_SEED = 25

SCHEMA = {
    "type": "object",
    "properties": {"questions": {"type": "array", "items": {"type": "string"}}},
    "required": ["questions"],
}

PROMPT = """Write {count} questions a potential customer of a {site_type} business would ask an AI
assistant such as ChatGPT about "{seed}", in the language with code "{language}" and as someone
living in the country with code "{country}".

Write them the way people talk to an assistant: full sentences, often with their situation in
them. Cover these angles: {angles}. One question per item, no numbering."""


def run(client: Client, run_folder: Path) -> None:
    trace = run_folder / "trace.jsonl"
    with open(run_folder / "predicted.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["seed", "question"])
        total = 0
        for seed in client.seeds:
            prompt = PROMPT.format(count=PER_SEED, site_type=client.site_type, seed=seed,
                                   angles=profile(client.site_type).angles,
                                   language=client.language, country=client.country)
            answer = claude.ask(prompt, SCHEMA, MODEL, trace, f"predicted: {seed}")
            for question in answer["questions"]:
                writer.writerow([seed, question])
            total += len(answer["questions"])
            print(f"{seed}: {len(answer['questions'])} questions", flush=True)
    print(f"Done: {total} predicted questions saved to {run_folder / 'predicted.csv'}")
